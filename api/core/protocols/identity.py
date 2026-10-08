from __future__ import annotations

import logging
from typing import Optional, Protocol, runtime_checkable

from api.core.config import settings

logger = logging.getLogger(__name__)


@runtime_checkable
class IdentityProviderProtocol(Protocol):
    """Protocolo formal para gestión del ciclo de vida en el proveedor de identidad (Cognito/Auth0)."""

    async def delete_user(self, cognito_sub: str) -> bool:
        """Elimina de forma permanente al usuario del directorio de identidad."""
        ...


class CognitoIdentityProvider(IdentityProviderProtocol):
    """Implementación real para AWS Cognito User Pools mediante boto3."""

    def __init__(self, user_pool_id: Optional[str] = None, region_name: Optional[str] = None):
        self.user_pool_id = user_pool_id or settings.COGNITO_USER_POOL_ID
        self.region_name = region_name or settings.AWS_REGION

    async def delete_user(self, cognito_sub: str) -> bool:
        if not self.user_pool_id:
            logger.warning("COGNITO_USER_POOL_ID no configurado; omitiendo borrado en AWS Cognito.")
            return True

        try:
            import boto3
            client = boto3.client("cognito-idp", region_name=self.region_name)
            client.admin_delete_user(
                UserPoolId=self.user_pool_id,
                Username=cognito_sub,
            )
            logger.info("Usuario %s eliminado con éxito en Cognito User Pool %s", cognito_sub, self.user_pool_id)
            return True
        except Exception as exc:
            # Si el usuario ya no existe en Cognito, se considera completado
            if "UserNotFoundException" in str(exc):
                logger.info("Usuario %s ya no existía en Cognito.", cognito_sub)
                return True
            logger.error("Error al eliminar usuario %s en Cognito: %s", cognito_sub, exc)
            raise


class MockIdentityProvider(IdentityProviderProtocol):
    """Proveedor simulado para pruebas automáticas y entornos de CI sin AWS."""

    def __init__(self):
        self.deleted_users: list[str] = []

    async def delete_user(self, cognito_sub: str) -> bool:
        self.deleted_users.append(cognito_sub)
        logger.info("[Mock Identity] Usuario %s registrado como eliminado.", cognito_sub)
        return True


_identity_provider_instance: Optional[IdentityProviderProtocol] = None


def set_identity_provider(provider: IdentityProviderProtocol, force: bool = False) -> None:
    """Configura la instancia del proveedor de identidad (usado en lifespan y tests)."""
    global _identity_provider_instance
    if _identity_provider_instance is not None and not force:
        raise RuntimeError("El IdentityProvider ya fue configurado. Usa force=True para sobrescribirlo.")
    _identity_provider_instance = provider


def reset_identity_provider() -> None:
    """Restablece la instancia del proveedor de identidad."""
    global _identity_provider_instance
    _identity_provider_instance = None


def get_identity_provider() -> IdentityProviderProtocol:
    """Retorna la instancia del proveedor de identidad configurado."""
    global _identity_provider_instance
    if _identity_provider_instance is None:
        if settings.ENVIRONMENT in ("development", "test") or not settings.COGNITO_USER_POOL_ID:
            _identity_provider_instance = MockIdentityProvider()
        else:
            _identity_provider_instance = CognitoIdentityProvider()
    return _identity_provider_instance
