from __future__ import annotations

from dataclasses import dataclass

from api.core.auth_context import Scope
from api.core.protocols.api_key import ApiKeyValidatorProtocol, ValidatedApiKey


@dataclass
class _StoredKey:
    """API key almacenada en memoria para testing."""

    key_id: int
    raw_key: str
    org_id: int
    scopes: frozenset[Scope]
    created_by_id: int | None
    revoked: bool = False
    expired: bool = False
    org_active: bool = True


class FakeApiKeyValidator(ApiKeyValidatorProtocol):
    """
    Validador falso en memoria para tests.

    Simula el comportamiento del validador real sin base de datos:
    - Valida formato y entorno (sk_live_ vs sk_test_)
    - Busca por hash (simulado con dict por raw_key)
    - Respeta revocación, expiración y estado de la org
    - Devuelve ValidatedApiKey o None (nunca lanza excepciones)
    """

    def __init__(self, environment: str = "development"):
        self._keys: dict[str, _StoredKey] = {}  # raw_key -> _StoredKey
        self._next_key_id = 1
        self.environment = environment
        self.expected_prefix = "sk_live_" if environment == "production" else "sk_test_"

    def add_key(
        self,
        raw_key: str,
        org_id: int,
        scopes: set[Scope] | frozenset[Scope],
        created_by_id: int | None = None,
        revoked: bool = False,
        expired: bool = False,
        org_active: bool = True,
    ) -> int:
        """Agrega una key al almacén para testing."""
        key_id = self._next_key_id
        self._next_key_id += 1

        self._keys[raw_key] = _StoredKey(
            key_id=key_id,
            raw_key=raw_key,
            org_id=org_id,
            scopes=frozenset(scopes),
            created_by_id=created_by_id,
            revoked=revoked,
            expired=expired,
            org_active=org_active,
        )
        return key_id

    def revoke_key(self, raw_key: str) -> bool:
        """Revoca una key existente."""
        if raw_key in self._keys:
            self._keys[raw_key].revoked = True
            return True
        return False

    def set_org_active(self, org_id: int, active: bool) -> None:
        """Cambia el estado activo de todas las keys de una org."""
        for key in self._keys.values():
            if key.org_id == org_id:
                key.org_active = active

    async def validate(self, raw_key: str) -> ValidatedApiKey | None:
        """
        Valida una key siguiendo las mismas reglas que la implementación real.

        Orden de comprobaciones (barato → caro):
        1. Formato: debe empezar con prefijo esperado
        2. Entorno: sk_live_ solo en production, sk_test_ solo en development
        3. Existencia en almacén
        4. Revocada
        5. Expirada
        6. Org activa
        """
        # 1. Formato básico
        if not raw_key or not raw_key.startswith(("sk_live_", "sk_test_")):
            return None

        # 2. Entorno: validar prefijo coincide con entorno
        if not raw_key.startswith(self.expected_prefix):
            return None

        # 3. Existencia
        stored = self._keys.get(raw_key)
        if not stored:
            return None

        # 4. Revocada
        if stored.revoked:
            return None

        # 5. Expirada
        if stored.expired:
            return None

        # 6. Org activa
        if not stored.org_active:
            return None

        # Todo OK → devolver datos para AuthContext
        return ValidatedApiKey(
            key_id=stored.key_id,
            org_id=stored.org_id,
            scopes=stored.scopes,
            created_by_id=stored.created_by_id,
        )

    def clear(self) -> None:
        """Limpia el almacén (útil entre tests)."""
        self._keys.clear()
        self._next_key_id = 1
