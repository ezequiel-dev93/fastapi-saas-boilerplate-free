from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.modules.users.models import UserProfile
from api.modules.users.privacy_schemas import (
    AccountDeletionResponse,
    ExportUserProfile,
    ExportUserSettings,
    UserDataExport,
)
from api.worker import enqueue_job

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PrivacyService:
    def export_user_data(self, db: Session, user: UserProfile) -> UserDataExport:
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
        now = utcnow()
        saved_cognito_sub = user.cognito_sub

        anon_id = uuid.uuid4().hex[:12]
        user.email = f"deleted_{anon_id}@deleted.invalid"
        user.first_name = "Deleted"
        user.last_name = "User"
        user.deleted_at = now

        if user.settings:
            user.settings.notify_comments = False
            user.settings.notify_updates = False
            user.settings.notify_marketing = False

        db.commit()

        try:
            await enqueue_job("task_finalize_account_deletion", cognito_sub=saved_cognito_sub)
        except Exception as exc:
            logger.error("Error al encolar borrado en Cognito para %s: %s", saved_cognito_sub, exc)

        return AccountDeletionResponse(deleted_at=now)


_privacy_service_instance: Optional[PrivacyService] = None


def get_privacy_service() -> PrivacyService:
    global _privacy_service_instance
    if _privacy_service_instance is None:
        _privacy_service_instance = PrivacyService()
    return _privacy_service_instance
