import json
import logging
import sys
from typing import Any, Dict

from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

from api.core.config import settings


class JSONFormatter(logging.Formatter):
    """Formateador de logs en formato JSON estructurado para producción (CloudWatch, Datadog, etc.)."""

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        return json.dumps(log_record, ensure_ascii=False)


def setup_logging() -> None:
    """Configura el sistema global de logging según el entorno de ejecución."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    if settings.ENVIRONMENT.lower() in ("development", "test", "testing"):
        install_rich_traceback(show_locals=False, width=120)
        handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
            markup=True,
            log_time_format="[%X]",
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())

    handler.setLevel(log_level)
    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)


def get_logger(name: str = "api") -> logging.Logger:
    """Obtiene un logger configurado con el nombre especificado."""
    return logging.getLogger(name)
