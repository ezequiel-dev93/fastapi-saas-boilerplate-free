"""Core configuration, database, and security modules."""

from api.core.auth_context import DEFAULT_SCOPES_BY_ROLE, AuthContext, Scope

__all__ = ["AuthContext", "Scope", "DEFAULT_SCOPES_BY_ROLE"]
