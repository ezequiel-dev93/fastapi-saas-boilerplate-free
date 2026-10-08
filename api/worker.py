import asyncio
import logging
from typing import Any, Dict, Optional

from arq.connections import RedisSettings, create_pool

from api.core.config import settings
from api.core.email import send_email, send_organization_invitation_email

logger = logging.getLogger(__name__)


async def task_send_email(
    ctx: Dict[str, Any],
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
):
    """Tarea de worker ARQ para envío asíncrono de emails transaccionales."""
    logger.info("[ARQ Worker] Procesando envío de email para %s | Asunto: %s", to_email, subject)
    send_email(to_email=to_email, subject=subject, body_text=body_text, body_html=body_html)


async def task_send_invitation_email(
    ctx: Dict[str, Any],
    to_email: str,
    org_name: str,
    inviter_name: str,
    token: str,
    role: str = "member",
):
    """Tarea de worker ARQ para entrega de invitaciones a organizaciones."""
    logger.info("[ARQ Worker] Procesando invitación para %s a la organización '%s'", to_email, org_name)
    send_organization_invitation_email(
        to_email=to_email,
        org_name=org_name,
        inviter_name=inviter_name,
        token=token,
        role=role,
    )


async def task_finalize_account_deletion(
    ctx: Dict[str, Any],
    cognito_sub: str,
):
    """Tarea de worker ARQ para eliminar al usuario en AWS Cognito en segundo plano (GDPR, D-15)."""
    logger.info("[ARQ Worker] Finalizando eliminación de cuenta en Cognito para sub: %s", cognito_sub)
    from api.core.protocols.identity import get_identity_provider

    provider = get_identity_provider()
    await provider.delete_user(cognito_sub)


class WorkerSettings:
    """Configuración del worker de ARQ.
    Para ejecutar: arq api.worker.WorkerSettings
    """

    functions = [task_send_email, task_send_invitation_email, task_finalize_account_deletion]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 60


async def enqueue_job(task_name: str, *args, **kwargs) -> bool:
    """Encola un trabajo en segundo plano en Redis a través de ARQ.
    Si Redis no está accesible (ej. desarrollo local sin Redis levantado o tests unitarios),
    ejecuta la función directamente garantizando resiliencia total sin interrumpir la API.
    """
    try:
        redis_pool = await asyncio.wait_for(
            create_pool(RedisSettings.from_dsn(settings.REDIS_URL)),
            timeout=0.5,
        )
        await redis_pool.enqueue_job(task_name, *args, **kwargs)
        await redis_pool.close()
        logger.info("[ARQ] Trabajo '%s' encolado exitosamente en Redis.", task_name)
        return True
    except Exception as exc:
        logger.debug("[ARQ Fallback] Redis no disponible (%s). Ejecutando tarea directamente: %s", task_name, exc)
        if task_name == "task_send_email":
            send_email(*args, **kwargs)
        elif task_name == "task_send_invitation_email":
            send_organization_invitation_email(*args, **kwargs)
        elif task_name == "task_finalize_account_deletion":
            await task_finalize_account_deletion({}, *args, **kwargs)
        return False
