"""
Contexto de autenticación unificado.

Una request autenticada es SIEMPRE un ``AuthContext``, venga de un JWT de
Cognito o de una API Key de organización. Las rutas y los guards trabajan
contra este objeto y nunca contra el ORM.

Este módulo vive en ``core/`` y no debe importar nada de ``modules/``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

from frozendict import frozendict


class Scope(StrEnum):
    """Permisos que puede tener una API Key. Formato ``recurso:acción``.

    No existe un scope ``admin`` a propósito: una key no puede administrar
    keys (crear, listar, modificar o revocar). Eso es solo para JWT, así una
    key con permisos limitados no puede escalarse a sí misma.
    """

    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    MEMBERS_READ = "members:read"
    MEMBERS_WRITE = "members:write"
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"
    AI_GENERATE = "ai:generate"


# Conjuntos predefinidos de scopes permitidos según el rol del creador
# El servicio valida que los scopes pedidos no superen estos límites (anti-escalada)
DEFAULT_SCOPES_BY_ROLE: frozendict[str, frozenset[Scope]] = frozendict(
    {
        "owner": frozenset(Scope),  # Todos los permisos, incluyendo mutations financieras y generación de IA
        "admin": frozenset(
            {
                Scope.USERS_READ,
                Scope.USERS_WRITE,
                Scope.MEMBERS_READ,
                Scope.MEMBERS_WRITE,
                Scope.BILLING_READ,  # admin puede auditar facturación, pero NO mutarla
                Scope.AI_GENERATE,
            }
        ),
        "member": frozenset(),  # members no pueden crear API keys
    }
)


AuthKind = Literal["jwt", "api_key"]


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Quién (o qué) está haciendo la request y con qué alcance.

    - ``kind="jwt"``: actúa una persona. ``user`` viene informado; la
      organización se resuelve por la URL y la membership, y los permisos
      por rol. ``scopes`` es siempre ``None``.
    - ``kind="api_key"``: actúa una key. Está fijada a UNA organización
      (``org_id``) y a un conjunto explícito de ``scopes``. No hay ``user``:
      la key NO hereda lo que pueda hacer quien la creó.

    Semántica de ``scopes`` (importante, es fácil confundirla):
    ``None`` significa "los permisos los define el rol", NO "sin permisos"
    ni "todos los permisos". Por eso ``has_scope`` falla cerrado: para un
    JWT devuelve ``False`` y es el guard quien decide cómo tratar cada tipo.
    """

    kind: AuthKind
    user: Any | None = None
    org_id: int | None = None
    scopes: frozenset[Scope] | None = None
    api_key_id: int | None = None

    def __post_init__(self) -> None:
        # Invariantes: impiden construir contextos a medias que luego abran
        # una ruta por accidente (p. ej. una "api_key" sin org_id).
        if self.kind == "jwt":
            if self.user is None:
                raise ValueError("Un contexto jwt requiere user")
            if self.org_id is not None or self.scopes is not None or self.api_key_id is not None:
                raise ValueError("Un contexto jwt no puede tener org_id, scopes ni api_key_id")
        elif self.kind == "api_key":
            if self.user is not None:
                raise ValueError("Un contexto api_key no puede tener user")
            if self.org_id is None or self.scopes is None or self.api_key_id is None:
                raise ValueError("Un contexto api_key requiere org_id, scopes y api_key_id")
        else:  # pragma: no cover - protegido por el tipo Literal
            raise ValueError(f"kind inválido: {self.kind!r}")

    @property
    def is_api_key(self) -> bool:
        return self.kind == "api_key"

    @property
    def is_jwt(self) -> bool:
        return self.kind == "jwt"

    def has_scope(self, scope: Scope) -> bool:
        """True solo si es una API Key que tiene ese scope (falla cerrado)."""
        return self.scopes is not None and scope in self.scopes
