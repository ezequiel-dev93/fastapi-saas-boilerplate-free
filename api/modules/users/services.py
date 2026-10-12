from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from api.core.exceptions import (
    ActiveTrialExistsError,
    TrialAlreadyUsedError,
    UserValidationError,
)
from api.modules.users.models import UserProfile, UserSettings
from api.modules.users.repository import (
    SqlAlchemyUserRepository,
    UserRepositoryProtocol,
)


class UserService:
    """Casos de uso y reglas de negocio para usuarios y perfiles (Clean Architecture)."""

    def __init__(self, repository: Optional[UserRepositoryProtocol] = None):
        self._repository = repository

    def _get_repo(self, db: Session) -> UserRepositoryProtocol:
        if self._repository is not None:
            return self._repository
        return SqlAlchemyUserRepository(db)

    def update_profile(
        self,
        db: Session,
        user: UserProfile,
        first_name: str,
        last_name: str,
    ) -> UserProfile:
        """Actualiza nombres y apellidos del perfil de usuario aplicando reglas de dominio."""
        clean_first = first_name.strip()
        clean_last = last_name.strip()

        if len(clean_first) > 150 or len(clean_last) > 150:
            raise UserValidationError("Los nombres deben contener 150 caracteres o menos.")

        repo = self._get_repo(db)
        return repo.update_profile(user, first_name=clean_first, last_name=clean_last)

    def update_settings(
        self,
        db: Session,
        user: UserProfile,
        notify_comments: Optional[bool] = None,
        notify_updates: Optional[bool] = None,
        notify_marketing: Optional[bool] = None,
    ) -> UserSettings:
        """Actualiza las preferencias de notificaciones del usuario."""
        repo = self._get_repo(db)
        settings = repo.get_or_create_settings(user)
        return repo.update_settings(
            settings,
            notify_comments=notify_comments,
            notify_updates=notify_updates,
            notify_marketing=notify_marketing,
        )

    def start_trial(
        self,
        db: Session,
        user: UserProfile,
    ) -> datetime:
        """Inicia un período de prueba de 14 días verificando que no haya sido utilizado previamente."""
        repo = self._get_repo(db)
        settings = repo.get_or_create_settings(user)

        if settings.is_subscription_active or settings.is_trial_active:
            raise ActiveTrialExistsError("Ya posees una suscripción o período de prueba activo.")

        if settings.trial_end_date:
            raise TrialAlreadyUsedError("Tu período de prueba gratuito ya ha sido utilizado (already been used).")

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
