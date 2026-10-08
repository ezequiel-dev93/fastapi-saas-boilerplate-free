from __future__ import annotations

from typing import Optional

from api.core.protocols.api_key import ApiKeyValidatorProtocol, ValidatedApiKey
from api.core.protocols.jwt import JwtAuthenticatorProtocol

# Variables globales para los validadores (inyectadas al arrancar la app)
_api_key_validator: Optional[ApiKeyValidatorProtocol] = None
_jwt_authenticator: Optional[JwtAuthenticatorProtocol] = None


def get_api_key_validator() -> ApiKeyValidatorProtocol:
    """
    Dependencia FastAPI para obtener el validador de API keys.

    En producción: retorna la implementación real (ApiKeyService).
    En tests: se sobreecribe con app.dependency_overrides[get_api_key_validator] = fake_validator.
    """
    if _api_key_validator is None:
        raise RuntimeError("API key validator not configured. Call set_api_key_validator() at application startup.")
    return _api_key_validator


def set_api_key_validator(validator: ApiKeyValidatorProtocol, *, force: bool = False) -> None:
    """
    Establece la implementación del validador de API keys.

    Debe llamarse una sola vez al inicio de la aplicación (en main.py lifespan).

    Args:
        validator: La implementación del protocolo ApiKeyValidatorProtocol
        force: Si True, permite sobrescribir un validador ya configurado (solo para tests)
    """
    global _api_key_validator
    if _api_key_validator is not None and not force:
        raise RuntimeError("API key validator already configured")
    _api_key_validator = validator


def reset_api_key_validator() -> None:
    """Resetea el validador (solo para tests)."""
    global _api_key_validator
    _api_key_validator = None


def get_jwt_authenticator() -> JwtAuthenticatorProtocol:
    """
    Dependencia FastAPI para obtener el autenticador JWT.

    En producción: retorna la implementación real (CognitoJwtAuthenticator).
    En tests: se sobreecribe con app.dependency_overrides[get_jwt_authenticator] = fake_jwt_auth.
    """
    if _jwt_authenticator is None:
        raise RuntimeError("JWT authenticator not configured. Call set_jwt_authenticator() at application startup.")
    return _jwt_authenticator


def set_jwt_authenticator(authenticator: JwtAuthenticatorProtocol, *, force: bool = False) -> None:
    """Establece la implementación del autenticador JWT."""
    global _jwt_authenticator
    if _jwt_authenticator is not None and not force:
        raise RuntimeError("JWT authenticator already configured")
    _jwt_authenticator = authenticator


def reset_jwt_authenticator() -> None:
    """Resetea el autenticador JWT (solo para tests)."""
    global _jwt_authenticator
    _jwt_authenticator = None


async def validate_api_key(raw_key: str) -> ValidatedApiKey | None:
    """
    Helper de conveniencia para validar una key usando el validador configurado.

    Usado por security.py para mantener la lógica de extracción separada
    de la validación de negocio.
    """
    validator = get_api_key_validator()
    return await validator.validate(raw_key)
