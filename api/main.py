from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.database import get_db
from api.core.limiter import limiter
from api.core.logging import LoggingMiddleware, setup_logging
from api.core.protocols import set_jwt_authenticator
from api.core.security import verify_jwt_token
from api.modules.auth.routes import router as auth_router
from api.modules.users.models import UserProfile
from api.modules.users.routes import router as users_router


# Real JWT Authenticator implementation
class CognitoJwtAuthenticator:
    """Implementación real del autenticador JWT usando Cognito (y Dev JWT en desarrollo local)."""

    async def authenticate(self, token: str) -> Any | None:
        """Verifica el token JWT (Cognito o Dev) y retorna el UserProfile o None."""
        try:
            claims = verify_jwt_token(token)
        except HTTPException:
            return None

        sub = claims.get("sub")
        if not sub:
            return None

        # Import here to avoid circular imports
        from api.core.database import SessionLocal
        from api.modules.users.models import UserSettings

        db = SessionLocal()
        try:
            email = claims.get("email", f"{sub}@example.com")
            user = db.query(UserProfile).filter(UserProfile.cognito_sub == sub).first()

            if user and user.deleted_at is not None:
                return None

            if not user:
                # Check if a user with this email already exists
                user = db.query(UserProfile).filter(UserProfile.email == email).first()
                if user and user.deleted_at is not None:
                    return None
                if user:
                    user.cognito_sub = sub
                else:
                    user = UserProfile(
                        cognito_sub=sub,
                        email=email,
                        first_name=claims.get("given_name", ""),
                        last_name=claims.get("family_name", ""),
                    )
                    db.add(user)
                    db.flush()

                # Ensure user settings exist
                if not user.settings:
                    user_settings = UserSettings(
                        user_id=user.id,
                        subscription_status="inactive",
                    )
                    db.add(user_settings)

                db.commit()
                db.refresh(user)

            return user
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configura las dependencias globales al arrancar la aplicación."""
    # Configurar autenticador JWT real (force=True para permitir reconfiguración en tests)
    set_jwt_authenticator(CognitoJwtAuthenticator(), force=True)

    # Configurar proveedor de identidad (Cognito en producción, Mock en dev/test)
    from api.core.protocols.identity import (
        CognitoIdentityProvider,
        MockIdentityProvider,
        set_identity_provider,
    )

    if settings.ENVIRONMENT == "production":
        set_identity_provider(CognitoIdentityProvider(), force=True)
    else:
        try:
            set_identity_provider(MockIdentityProvider(), force=False)
        except RuntimeError:
            pass

    yield

    # Cleanup si es necesario


# Inicializar sistema de logging enriquecido (Rich en dev/test, JSON en prod)
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Boilerplate backend para aplicaciones SaaS con FastAPI, AWS Cognito y pagos con Stripe.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Conectar rate limiter y su manejador de excepciones (HTTP 429)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware de trazabilidad con X-Request-ID y cálculo de latencias
app.add_middleware(LoggingMiddleware)

# Configuración de middleware CORS
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)

# Herramientas de desarrollo (solo activas en modo DEBUG)
if settings.DEBUG:
    from api.core.dev_emails import router as dev_emails_router

    app.include_router(dev_emails_router)


@app.get("/health", tags=["Salud"])
async def health_check(db: Session = Depends(get_db)):
    """Endpoint de verificación de estado (Health Check) para monitoreo y contenedores.
    Verifica activamente la conectividad con la base de datos ejecutando SELECT 1.
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "project": settings.PROJECT_NAME,
            "database": "connected",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(exc)}",
        )


@app.get("/", tags=["Inicio"])
async def root():
    """Endpoint raíz con información general y enlaces a la documentación interactiva."""
    return {
        "message": f"Bienvenido a {settings.PROJECT_NAME}",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
    }
