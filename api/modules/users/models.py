from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from api.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    cognito_sub = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(150), default="", nullable=False)
    last_name = Column(String(150), default="", nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    stripe_customer = relationship("StripeCustomer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserProfile(id={self.id}, email='{self.email}', sub='{self.cognito_sub}')>"


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Notification preferences
    notify_comments = Column(Boolean, default=False, nullable=False)
    notify_updates = Column(Boolean, default=False, nullable=False)
    notify_marketing = Column(Boolean, default=False, nullable=False)

    # Subscription settings
    subscription_plan_id = Column(Integer, ForeignKey("subscription_plans.id", ondelete="SET NULL"), nullable=True)
    subscription_status = Column(String(20), default="inactive", nullable=False)  # active, inactive, cancelled, trial
    subscription_start_date = Column(DateTime(timezone=True), nullable=True)
    subscription_end_date = Column(DateTime(timezone=True), nullable=True)
    trial_end_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    user = relationship("UserProfile", back_populates="settings")
    subscription_plan = relationship("SubscriptionPlan", back_populates="subscribers")

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

    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, status='{self.subscription_status}')>"
