from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ExportUserProfile(BaseModel):
    id: int
    cognito_sub: str
    email: EmailStr
    first_name: str
    last_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExportUserSettings(BaseModel):
    subscription_status: str
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    notify_comments: bool = False
    notify_updates: bool = False
    notify_marketing: bool = False

    model_config = ConfigDict(from_attributes=True)


class ExportOrganizationMembership(BaseModel):
    organization_id: int
    organization_name: str
    organization_slug: str
    role: str
    joined_at: datetime


class ExportStripeCustomer(BaseModel):
    stripe_customer_id: str
    subscription_status: Optional[str] = None
    stripe_subscription_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ExportApiKey(BaseModel):
    id: int
    organization_id: int
    name: str
    key_prefix: str
    scopes: List[str]
    created_at: datetime
    last_used_at: Optional[datetime] = None


class ExportAiUsageEvent(BaseModel):
    request_id: str
    organization_id: int
    provider: str
    model: str
    status: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDataExport(BaseModel):
    """Estructura completa de exportación de datos del usuario bajo GDPR (Derecho de Acceso y Portabilidad)."""
    user: ExportUserProfile
    settings: Optional[ExportUserSettings] = None
    memberships: List[ExportOrganizationMembership] = Field(default_factory=list)
    stripe_customer: Optional[ExportStripeCustomer] = None
    created_api_keys: List[ExportApiKey] = Field(default_factory=list)
    ai_usage_events: List[ExportAiUsageEvent] = Field(default_factory=list)
    exported_at: datetime


class AccountDeletionResponse(BaseModel):
    """Confirmación de supresión y anonimización de cuenta bajo GDPR (Derecho al Olvido)."""
    message: str = "Tu cuenta y datos personales han sido anonimizados de acuerdo a GDPR."
    status: str = "anonymized"
    deleted_at: datetime
