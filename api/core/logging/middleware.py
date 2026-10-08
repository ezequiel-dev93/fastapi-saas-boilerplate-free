import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from api.core.logging.logger import get_logger

logger = get_logger("api.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para trazabilidad de peticiones con X-Request-ID y registro estructurado de accesos."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            process_time_ms = (time.perf_counter() - start_time) * 1000

            # Registrar acceso HTTP
            logger.info(
                f"[bold cyan]{request.method}[/] {request.url.path} "
                f"-> [bold green]{response.status_code}[/] "
                f"({process_time_ms:.2f}ms) [dim][id={request_id}][/]"
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            process_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[bold red]FAIL[/] {request.method} {request.url.path} "
                f"({process_time_ms:.2f}ms) [id={request_id}]: {str(exc)}"
            )
            raise exc
