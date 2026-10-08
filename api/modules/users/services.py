from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.modules.users.models import UserProfile, UserSettings


class UserService:
    """Casos de uso y reglas de negocio para usuarios, perfiles y llaves de API."""

    def update_profile(
        self,
        db: Session,
        user: UserProfile,
        first_name: str,
        last_name: str,
    ) -> UserProfile:
        """Actualiza nombres y apellidos del perfil de usuario con validación."""
        clean_first = first_name.strip()
        clean_last = last_name.strip()

        if len(clean_first) > 150 or len(clean_last) > 150:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los nombres deben contener 150 caracteres o menos.",
            )

        user.first_name = clean_first
        user.last_name = clean_last
        db.commit()
        db.refresh(user)
        return user

    def update_settings(
        self,
        db: Session,
        user: UserProfile,
        notify_comments: Optional[bool] = None,
        notify_updates: Optional[bool] = None,
        notify_marketing: Optional[bool] = None,
    ) -> UserSettings:
        """Actualiza las preferencias de notificaciones del usuario."""
        settings = user.settings
        if not settings:
            settings = UserSettings(user_id=user.id)
            db.add(settings)
            db.flush()

        if notify_comments is not None:
            settings.notify_comments = notify_comments
        if notify_updates is not None:
            settings.notify_updates = notify_updates
        if notify_marketing is not None:
            settings.notify_marketing = notify_marketing

        db.commit()
        db.refresh(settings)
        return settings

    def start_trial(
        self,
        db: Session,
        user: UserProfile,
    ) -> datetime:
        """Inicia un período de prueba de 14 días verificando que no haya sido utilizado previamente."""
        settings = user.settings
        if not settings:
            settings = UserSettings(user_id=user.id)
            db.add(settings)
            db.flush()

        if settings.is_subscription_active or settings.is_trial_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya posees una suscripción o período de prueba activo.",
            )

        if settings.trial_end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tu período de prueba gratuito ya ha sido utilizado (already been used).",
            )

        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=14)
        settings.subscription_status = "trial"
        settings.trial_end_date = trial_end
        db.commit()

        return trial_end


_user_service = UserService()


def get_user_service() -> UserService:
    """Inyector de dependencias para UserService."""
    return _user_service
