from __future__ import annotations

from pydantic import BaseModel


class DevUserRead(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    cognito_sub: str


class DevLoginRequest(BaseModel):
    email: str


class DevLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: DevUserRead
