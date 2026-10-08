from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserSettingsBase(BaseModel):
    notify_comments: bool = False
    notify_updates: bool = False
    notify_marketing: bool = False


class UserSettingsUpdate(UserSettingsBase):
    pass


class UserSettingsRead(UserSettingsBase):
    model_config = ConfigDict(from_attributes=True)

    subscription_status: str
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    is_subscription_active: bool
    is_trial_active: bool


class UserProfileBase(BaseModel):
    first_name: str = ""
    last_name: str = ""


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileRead(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cognito_sub: str
    email: EmailStr
    created_at: datetime


class UserMeResponse(BaseModel):
    profile: UserProfileRead
    settings: Optional[UserSettingsRead] = None
