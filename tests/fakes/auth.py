"""Fakes en memoria para testear la autenticación sin base de datos ni Cognito."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any, Iterable, Literal

from api.core.auth_context import Scope
from api.core.protocols.api_key import ValidatedApiKey


def make_raw_key(env: Literal["live", "test"] = "test", random_part: str | None = None) -> str:
    """Genera una key con el formato real: ``sk_<env>_<token_urlsafe(32)>``.

    ``secrets.token_urlsafe(32)`` produce siempre 43 caracteres.
    """
    return f"sk_{env}_{random_part or secrets.token_urlsafe(32)}"


@dataclass(frozen=True)
class FakeUser:
    id: int = 1
    email: str = "user@example.com"
    first_name: str = "Test"
    last_name: str = "User"
    cognito_sub: str = "test-sub"
    deleted_at: Any = None


class FakeApiKeyValidator:
    """Implementa ``ApiKeyValidatorProtocol``. ``calls`` permite afirmar que NO se consultó."""

    def __init__(self) -> None:
        self._keys: dict[str, ValidatedApiKey] = {}
        self.calls: list[str] = []

    def add(
        self,
        raw_key: str,
        *,
        org_id: int,
        scopes: Iterable[Scope],
        key_id: int = 1,
        created_by_id: int | None = None,
    ) -> ValidatedApiKey:
        validated = ValidatedApiKey(
            key_id=key_id,
            org_id=org_id,
            scopes=frozenset(scopes),
            created_by_id=created_by_id,
        )
        self._keys[raw_key] = validated
        return validated

    async def validate(self, raw_key: str) -> ValidatedApiKey | None:
        self.calls.append(raw_key)
        return self._keys.get(raw_key)


class FakeJwtAuthenticator:
    """Implementa ``JwtAuthenticatorProtocol``."""

    def __init__(self) -> None:
        self._tokens: dict[str, Any] = {}
        self.calls: list[str] = []

    def add(self, token: str, user: Any | None = None) -> None:
        self._tokens[token] = user or FakeUser()

    async def authenticate(self, token: str) -> Any | None:
        self.calls.append(token)
        return self._tokens.get(token)
