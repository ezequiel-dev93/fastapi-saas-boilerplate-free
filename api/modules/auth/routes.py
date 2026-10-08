from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.database import get_db
from api.core.security import create_dev_access_token
from api.modules.auth.schemas import (
    DevLoginRequest,
    DevLoginResponse,
    DevUserOrg,
    DevUserRead,
)
from api.modules.users.models import UserProfile, UserSettings

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _ensure_dev_environment():
    """Garantiza que los endpoints dev nunca estén disponibles en producción."""
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dev authentication endpoints are disabled in production.",
        )


def _serialize_user(user: UserProfile, db: Session) -> DevUserRead:
    return DevUserRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        cognito_sub=user.cognito_sub,
    )


@router.get("/dev-users", response_model=List[DevUserRead])
def list_dev_users(db: Session = Depends(get_db)):
    """
    Retorna la lista de usuarios locales para inicio de sesión rápido en desarrollo.
    Estrictamente prohibido y deshabilitado (404) en producción.
    """
    _ensure_dev_environment()
    users = db.query(UserProfile).filter(UserProfile.deleted_at.is_(None)).all()
    return [_serialize_user(u, db) for u in users]


@router.post("/dev-login", response_model=DevLoginResponse)
def dev_login(payload: DevLoginRequest, db: Session = Depends(get_db)):
    """
    Genera un JWT válido para el usuario especificado en entorno de desarrollo.
    Si el usuario no existe en la base de datos local, lo aprovisiona automáticamente.
    Estrictamente prohibido y deshabilitado (404) en producción.
    """
    _ensure_dev_environment()
    email = payload.email.strip().lower()
    user = db.query(UserProfile).filter(UserProfile.email == email).first()

    if not user:
        # Aprovisionar usuario dev automáticamente si no existe
        sub = f"dev-user-{email.split('@')[0]}"
        user = UserProfile(
            cognito_sub=sub,
            email=email,
            first_name="Dev",
            last_name="User",
        )
        db.add(user)
        db.flush()

        settings_obj = UserSettings(user_id=user.id, subscription_status="inactive")
        db.add(settings_obj)
        db.commit()
        db.refresh(user)

    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta cuenta ha sido eliminada.",
        )

    token = create_dev_access_token(user)
    return DevLoginResponse(
        access_token=token,
        token_type="bearer",
        user=_serialize_user(user, db),
    )
