from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Protocol, runtime_checkable

from fastapi import Depends
from sqlalchemy.orm import Session

from api.core.database import get_db
from api.modules.users.models import UserProfile, UserSettings


@runtime_checkable
class UserRepositoryProtocol(Protocol):
    """Contrato abstracto para el repositorio de persistencia de usuarios (DIP)."""

    def get_by_id(self, user_id: int) -> Optional[UserProfile]: ...
    def get_by_email(self, email: str) -> Optional[UserProfile]: ...
    def get_by_cognito_sub(self, cognito_sub: str) -> Optional[UserProfile]: ...
    def list_active(self) -> list[UserProfile]: ...
    def create_user(self, cognito_sub: str, email: str, first_name: str = "", last_name: str = "") -> UserProfile: ...
    def update_profile(self, user: UserProfile, first_name: str, last_name: str) -> UserProfile: ...
    def get_or_create_settings(self, user: UserProfile) -> UserSettings: ...
    def update_settings(
        self,
        settings: UserSettings,
        notify_comments: Optional[bool] = None,
        notify_updates: Optional[bool] = None,
        notify_marketing: Optional[bool] = None,
    ) -> UserSettings: ...
    def soft_delete_user(self, user: UserProfile, anon_email: str) -> None: ...


class SqlAlchemyUserRepository(UserRepositoryProtocol):
    """Implementación de UserRepository usando SQLAlchemy 2.0."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[UserProfile]:
        return self.db.query(UserProfile).filter(UserProfile.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[UserProfile]:
        return self.db.query(UserProfile).filter(UserProfile.email == email).first()

    def get_by_cognito_sub(self, cognito_sub: str) -> Optional[UserProfile]:
        return self.db.query(UserProfile).filter(UserProfile.cognito_sub == cognito_sub).first()

    def list_active(self) -> list[UserProfile]:
        return self.db.query(UserProfile).filter(UserProfile.deleted_at.is_(None)).all()

    def create_user(self, cognito_sub: str, email: str, first_name: str = "", last_name: str = "") -> UserProfile:
        user = UserProfile(
            cognito_sub=cognito_sub,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        self.db.add(user)
        self.db.flush()

        # Asegurar configuración por defecto
        settings = UserSettings(user_id=user.id, subscription_status="inactive")
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_profile(self, user: UserProfile, first_name: str, last_name: str) -> UserProfile:
        user.first_name = first_name
        user.last_name = last_name
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_or_create_settings(self, user: UserProfile) -> UserSettings:
        if user.settings:
            return user.settings
        settings = self.db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
        if not settings:
            settings = UserSettings(user_id=user.id)
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        return settings

    def update_settings(
        self,
        settings: UserSettings,
        notify_comments: Optional[bool] = None,
        notify_updates: Optional[bool] = None,
        notify_marketing: Optional[bool] = None,
    ) -> UserSettings:
        if notify_comments is not None:
            settings.notify_comments = notify_comments
        if notify_updates is not None:
            settings.notify_updates = notify_updates
        if notify_marketing is not None:
            settings.notify_marketing = notify_marketing
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def soft_delete_user(self, user: UserProfile, anon_email: str) -> None:
        now = datetime.now(timezone.utc)
        user.email = anon_email
        user.first_name = "Deleted"
        user.last_name = "User"
        user.deleted_at = now

        if user.settings:
            user.settings.notify_comments = False
            user.settings.notify_updates = False
            user.settings.notify_marketing = False

        self.db.commit()


def get_user_repository(db: Session = Depends(get_db)) -> SqlAlchemyUserRepository:
    """Inyector de dependencias para el repositorio de usuarios."""
    return SqlAlchemyUserRepository(db)
