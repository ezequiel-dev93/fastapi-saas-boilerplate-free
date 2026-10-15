from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserProfile(Base):
    """Modelo ORM para perfiles de usuario (SQLAlchemy 2.0)."""
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cognito_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(150), default="", nullable=False)
    last_name: Mapped[str] = mapped_column(String(150), default="", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    settings: Mapped[Optional[UserSettings]] = relationship(
        "UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<UserProfile(id={self.id}, email='{self.email}', sub='{self.cognito_sub}')>"


class UserSettings(Base):
    """Modelo ORM para configuraciones y preferencias de usuario (SQLAlchemy 2.0)."""
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Notification preferences
    notify_comments: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_updates: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_marketing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Subscription settings
    subscription_plan_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    subscription_status: Mapped[str] = mapped_column(String(20), default="inactive", nullable=False)  # active, inactive, cancelled, trial
    subscription_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    subscription_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    user: Mapped[UserProfile] = relationship("UserProfile", back_populates="settings")

    @property
    def is_subscription_active(self) -> bool:
        """Return True if user has an active, non-expired subscription."""
        if self.subscription_status != "active":
            return False
        if self.subscription_end_date:
            end_date = self.subscription_end_date
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            if end_date < utcnow():
                return False
        return True

    @property
    def is_trial_active(self) -> bool:
        """Return True if user currently has an active, non-expired trial."""
        if self.subscription_status != "trial":
            return False
        if self.trial_end_date:
            end_date = self.trial_end_date
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            if end_date < utcnow():
                return False
        return True

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id}, status='{self.subscription_status}')>"
