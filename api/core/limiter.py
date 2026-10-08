import logging

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.core.config import settings

logger = logging.getLogger(__name__)


def rate_limit_key_func(request: Request) -> str:
    """Extrae la clave para el rate limiting:
    1. Si se envía el header X-API-Key, aplica el límite por clave de API.
    2. En caso contrario, aplica el límite por dirección IP del cliente.
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key[:16]}"
    return get_remote_address(request)


# Almacenamiento en memoria para desarrollo/tests o Redis en producción
storage_uri = "memory://"
if not settings.DEBUG and settings.REDIS_URL:
    storage_uri = settings.REDIS_URL

limiter = Limiter(
    key_func=rate_limit_key_func,
    default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.ENABLE_RATE_LIMIT else [],
    enabled=settings.ENABLE_RATE_LIMIT,
    storage_uri=storage_uri,
)
