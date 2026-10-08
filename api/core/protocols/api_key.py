"""Contrato para validar API Keys de organización.

``core/security.py`` depende de este protocolo y no del modelo ORM. La
implementación real (``ApiKeyService``) vive en el módulo de dominio y se
conecta en ``main.py`` (composition root). En tests se usa un fake.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from api.core.auth_context import Scope


@dataclass(frozen=True, slots=True)
class ValidatedApiKey:
    """Resultado inmutable de una validación exitosa.

    Es un dataclass y no un objeto ORM a propósito: evita sesiones cerradas,
    lazy loading inesperado y que ``core`` conozca los modelos.
    """

    key_id: int
    org_id: int
    scopes: frozenset[Scope]
    created_by_id: int | None = None


@runtime_checkable
class ApiKeyValidatorProtocol(Protocol):
    async def validate(self, raw_key: str) -> ValidatedApiKey | None:
        """Devuelve la key validada, o ``None`` ante CUALQUIER fallo.

        No distingue el motivo (inexistente, revocada, inactiva, expirada,
        org inactiva, creador fuera de la org...). Quien llama responde
        siempre el mismo 401; el motivo real se registra en el log de la
        implementación, nunca con la key completa.
        """
        ...
