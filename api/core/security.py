from __future__ import annotations

import hashlib
import json
import logging
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from api.core.auth_context import AuthContext, Scope
from api.core.config import settings
from api.core.protocols import (
    ApiKeyValidatorProtocol,
    JwtAuthenticatorProtocol,
    get_api_key_validator,
    get_jwt_authenticator,
)
from api.modules.users.models import UserProfile

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# ──────────────────────────────────────────────────────────────────────────
# Helpers de formato y entorno (sin tocar la base)
# ──────────────────────────────────────────────────────────────────────────

_JWT_RE = re.compile(r"^[^.]+\.[^.]+\.[^.]+$")  # exactamente 2 puntos
_SK_RE = re.compile(r"^sk_(live|test)_[A-Za-z0-9_-]{43}$")  # sk_live_ + 43 urlsafe


def _is_jwt(token: str) -> bool:
    """Un JWT real tiene exactamente 2 puntos (o token mock en DEBUG)."""
    if settings.DEBUG and token.startswith("test-token-"):
        return True
    return bool(_JWT_RE.match(token))


def _is_org_api_key_format(token: str) -> bool:
    """Formato sk_live_ / sk_test_ + 43 caracteres urlsafe."""
    return bool(_SK_RE.match(token))


def _expected_prefix() -> str:
    """Prefijo según entorno: sk_live_ en prod, sk_test_ en dev/staging."""
    return "sk_live_" if settings.ENVIRONMENT == "production" else "sk_test_"


def _check_env(token: str) -> bool:
    """Valida que el prefijo coincida con ENVIRONMENT (barato, antes de la base)."""
    return token.startswith(_expected_prefix())


# ──────────────────────────────────────────────────────────────────────────
# Cognito JWT & Dev JWT (Desarrollo Local sin AWS)
# ──────────────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_cognito_jwks() -> dict[str, Any]:
    if not settings.COGNITO_USER_POOL_ID or not settings.AWS_REGION:
        logger.warning("Cognito settings not fully configured.")
        return {"keys": []}
    jwks_url = (
        f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    )
    try:
        with urllib.request.urlopen(jwks_url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"Failed to fetch Cognito JWKS: {e}")
        return {"keys": []}


def verify_cognito_token(token: str) -> dict[str, Any]:
    jwks = get_cognito_jwks()
    keys = jwks.get("keys", [])
    if not keys:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Cognito JWKS not available")
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token header")
    kid = unverified_header.get("kid")
    key = next((k for k in keys if k.get("kid") == kid), None)
    if not key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Public key not found in JWKS")
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
    try:
        return jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.COGNITO_APP_CLIENT_ID or None,
            options={"verify_aud": bool(settings.COGNITO_APP_CLIENT_ID)},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has expired")
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Token validation failed: {e}")


def create_dev_access_token(user: UserProfile, expires_delta: Optional[timedelta] = None) -> str:
    """Genera un JWT firmado con HS256 para autenticación en desarrollo (prohibido en producción)."""
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Dev JWT token generation is strictly forbidden in production.",
        )
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))
    claims = {
        "sub": user.cognito_sub,
        "email": user.email,
        "given_name": user.first_name,
        "family_name": user.last_name,
        "exp": expire,
        "iss": "fastapi-saas-dev",
    }
    return jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")


def verify_jwt_token(token: str) -> dict[str, Any]:
    """
    Verifica un token JWT.
    - En desarrollo: Admite tokens HS256 generados localmente por /auth/dev-login.
    - En producción: Exige exclusivamente verificación criptográfica RS256 contra Cognito JWKS.
    """
    if settings.ENVIRONMENT != "production":
        try:
            unverified = jwt.get_unverified_header(token)
            if unverified.get("alg") == "HS256":
                return jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=["HS256"],
                )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has expired")
        except jwt.PyJWTError:
            pass
    return verify_cognito_token(token)


# ──────────────────────────────────────────────────────────────────────────
# Hash de API Keys
# ──────────────────────────────────────────────────────────────────────────


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()


# ──────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA ÚNICO: get_auth_context
# ──────────────────────────────────────────────────────────────────────────


async def get_auth_context(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    api_key: Optional[str] = Depends(api_key_header),
    jwt_auth: JwtAuthenticatorProtocol = Depends(get_jwt_authenticator),
    api_key_val: ApiKeyValidatorProtocol = Depends(get_api_key_validator),
) -> AuthContext:
    """
    Punto único de autenticación. Devuelve AuthContext unificado.

    Flujo canónico:
    1. Extraer credencial: X-API-Key O Authorization: Bearer (nunca ambas)
    2. Decidir por HEADER y FORMATO:
       - X-API-Key: SOLO API keys de organización (sk_live_ / sk_test_)
       - Authorization: Bearer: API key de organización O JWT de Cognito
    3. Validaciones baratas (formato + entorno) ANTES de consultar infraestructura
    4. Llamar al validador correspondiente (ApiKeyValidatorProtocol o JwtAuthenticatorProtocol)
    5. Setear request.state para rate limiter, logs y cuotas
    """
    has_hdr = api_key is not None
    has_auth = auth is not None and auth.credentials is not None

    if has_hdr and has_auth:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot provide both X-API-Key and Authorization header")
    if not has_hdr and not has_auth:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing authorization credentials")

    cred = api_key if has_hdr else auth.credentials.strip()

    # ── X-API-Key header: SOLO API keys de organización ──────────────────────
    if has_hdr:
        if not _is_org_api_key_format(cred) or not _check_env(cred):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API Key")
        validated = await api_key_val.validate(cred)
        if not validated:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API Key")
        ctx = AuthContext(
            kind="api_key",
            user=None,
            org_id=validated.org_id,
            scopes=validated.scopes,
            api_key_id=validated.key_id,
        )
        request.state.auth_context = ctx
        request.state.api_key_id = validated.key_id
        request.state.org_id = validated.org_id
        return ctx

    # ── Authorization: Bearer header: API key de org O JWT de Cognito ───────
    else:
        if _is_org_api_key_format(cred):
            if not _check_env(cred):
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API Key")
            validated = await api_key_val.validate(cred)
            if not validated:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API Key")
            ctx = AuthContext(
                kind="api_key",
                user=None,
                org_id=validated.org_id,
                scopes=validated.scopes,
                api_key_id=validated.key_id,
            )
            request.state.auth_context = ctx
            request.state.api_key_id = validated.key_id
            request.state.org_id = validated.org_id
            return ctx
        elif _is_jwt(cred):
            user = await jwt_auth.authenticate(cred)
            if not user or getattr(user, "deleted_at", None) is not None:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
            ctx = AuthContext(kind="jwt", user=user, org_id=None, scopes=None, api_key_id=None)
            request.state.auth_context = ctx
            return ctx
        else:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API Key")


# ──────────────────────────────────────────────────────────────────────────
# Wrappers de autenticación / deny-by-default
# ──────────────────────────────────────────────────────────────────────────


async def get_current_user(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
) -> UserProfile:
    """Retorna UserProfile para endpoints de usuario.
    Requiere autenticación JWT de persona. Las API Keys reciben 403 Forbidden.
    """
    if ctx.kind == "jwt" and ctx.user is not None:
        if getattr(ctx.user, "deleted_at", None) is not None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Esta cuenta ha sido eliminada.")
        return ctx.user
    if ctx.is_api_key:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Organization API keys cannot access user-level endpoints. Use JWT authentication.",
        )
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication")


async def require_jwt(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    """Endpoints que NO aceptan keys (CRUD de keys, GDPR, etc.)."""
    if ctx.kind != "jwt":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This operation requires user authentication (JWT)")
    if ctx.user is not None and getattr(ctx.user, "deleted_at", None) is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Esta cuenta ha sido eliminada.")
    return ctx


def require_scope(scope: Scope):
    """
    Guard de scope para API keys.
    - Key: valida scope + coincidencia de org_id si hay {org_id} en la ruta
    - JWT: pasa (permisos por rol en require_org_access)
    """

    async def checker(
        request: Request,
        ctx: AuthContext = Depends(get_auth_context),
    ) -> AuthContext:
        if ctx.is_api_key:
            if scope not in ctx.scopes:
                raise HTTPException(status.HTTP_403_FORBIDDEN, f"Missing required scope: {scope}")
            # Validar org_id de la ruta contra el de la key
            path_org = request.path_params.get("org_id")
            if path_org is not None:
                try:
                    if int(path_org) != ctx.org_id:
                        raise HTTPException(status.HTTP_403_FORBIDDEN, "API key not valid for this organization")
                except ValueError:
                    pass
            return ctx
        return ctx  # JWT: permisos por rol en require_org_access

    return checker
