from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from api.modules.users.models import UserProfile
from api.modules.users.privacy_schemas import (
    AccountDeletionResponse,
    ExportUserProfile,
    ExportUserSettings,
    UserDataExport,
)
from api.modules.users.repository import (
    SqlAlchemyUserRepository,
    UserRepositoryProtocol,
)
from api.worker import enqueue_job

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PrivacyService:
    """Servicio de dominio para el cumplimiento de privacidad y GDPR (Art. 15, 17 y 20)."""

    def __init__(self, repository: Optional[UserRepositoryProtocol] = None):
        self._repository = repository

    def _get_repo(self, db: Session) -> UserRepositoryProtocol:
        if self._repository is not None:
            return self._repository
        return SqlAlchemyUserRepository(db)

    def export_user_data(self, db: Session, user: UserProfile) -> UserDataExport:
        """Exporta los datos personales del usuario bajo GDPR (Derecho de Acceso y Portabilidad)."""
        user_export = ExportUserProfile(
            id=user.id,
            cognito_sub=user.cognito_sub,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            created_at=user.created_at,
        )

        settings_export = None
        if user.settings:
            settings_export = ExportUserSettings(
                subscription_status=user.settings.subscription_status,
                subscription_start_date=user.settings.subscription_start_date,
                subscription_end_date=user.settings.subscription_end_date,
                notify_comments=user.settings.notify_comments,
                notify_updates=user.settings.notify_updates,
                notify_marketing=user.settings.notify_marketing,
            )

        return UserDataExport(
            user=user_export,
            settings=settings_export,
            memberships=[],
            stripe_customer=None,
            created_api_keys=[],
            ai_usage_events=[],
            exported_at=utcnow(),
        )

    async def delete_user_account(
        self,
        db: Session,
        user: UserProfile,
    ) -> AccountDeletionResponse:
        """Anonimiza y suprime la cuenta del usuario bajo GDPR Art. 17 (Derecho al Olvido)."""
        now = utcnow()
        saved_cognito_sub = user.cognito_sub

        anon_id = uuid.uuid4().hex[:12]
        anon_email = f"deleted_{anon_id}@deleted.invalid"

        repo = self._get_repo(db)
        repo.soft_delete_user(user, anon_email=anon_email)

        try:
            await enqueue_job("task_finalize_account_deletion", cognito_sub=saved_cognito_sub)
        except Exception as exc:
            logger.error("Error al encolar borrado en Cognito para %s: %s", saved_cognito_sub, exc)

        return AccountDeletionResponse(deleted_at=now)


_privacy_service_instance: Optional[PrivacyService] = None


def get_privacy_service() -> PrivacyService:
    """Inyector de dependencias para PrivacyService."""
    global _privacy_service_instance
    if _privacy_service_instance is None:
        _privacy_service_instance = PrivacyService()
    return _privacy_service_instance
