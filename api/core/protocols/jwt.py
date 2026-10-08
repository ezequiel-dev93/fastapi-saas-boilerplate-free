"""Contrato para autenticar un JWT (Cognito en producción).

Por qué existe: ``get_auth_context`` no puede declarar ``Depends(get_current_user)``
directamente, porque FastAPI resolvería esa dependencia SIEMPRE y fallaría con
401 en las requests que vienen con API Key. El JWT se verifica de forma
perezosa, solo si la credencial no es una API Key, y por eso se inyecta como
un colaborador más.

La implementación real envuelve la verificación RS256/JWKS que ya existe.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class JwtAuthenticatorProtocol(Protocol):
    async def authenticate(self, token: str) -> Any | None:
        """Devuelve el usuario (``UserProfile``) o ``None`` si el token no es válido."""
        ...
