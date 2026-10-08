from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from api.core.database import get_db
from api.core.email import send_trial_started_email
from api.core.limiter import limiter
from api.core.security import get_current_user
from api.modules.users.models import UserProfile
from api.modules.users.privacy_schemas import (
    AccountDeletionResponse,
    UserDataExport,
)
from api.modules.users.privacy_service import PrivacyService, get_privacy_service
from api.modules.users.schemas import (
    UserMeResponse,
    UserProfileRead,
    UserProfileUpdate,
    UserSettingsRead,
    UserSettingsUpdate,
)
from api.modules.users.services import UserService, get_user_service

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/me", response_model=UserMeResponse)
async def get_user_me(current_user: UserProfile = Depends(get_current_user)):
    """Obtiene el perfil completo y configuración del usuario autenticado actual."""
    return UserMeResponse(
        profile=current_user,
        settings=current_user.settings,
    )


@router.get("/me/export", response_model=UserDataExport)
async def export_user_data(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
    privacy_service: PrivacyService = Depends(get_privacy_service),
):
    """Exporta todos los datos personales asociados al usuario (GDPR Art. 15 y 20)."""
    return privacy_service.export_user_data(db=db, user=current_user)


@router.delete("/me/account", response_model=AccountDeletionResponse)
async def delete_user_account(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
    privacy_service: PrivacyService = Depends(get_privacy_service),
):
    """
    Suprime la cuenta del usuario cumpliendo con el Derecho al Olvido (GDPR Art. 17).
    Valida precondiciones (suscripciones activas, organizaciones), anonimiza el perfil,
    preserva las API keys para no romper integraciones de las organizaciones, y encola la baja en el IdP.
    """
    return await privacy_service.delete_user_account(db=db, user=current_user)


@router.patch("/me", response_model=UserProfileRead)
async def update_user_profile(
    update_data: UserProfileUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
):
    """Actualiza la información del perfil (nombre y apellido)."""
    return user_service.update_profile(
        db=db,
        user=current_user,
        first_name=update_data.first_name,
        last_name=update_data.last_name,
    )


@router.get("/settings", response_model=UserSettingsRead)
async def get_user_settings(current_user: UserProfile = Depends(get_current_user)):
    """Obtiene las preferencias de notificación y estado de suscripción del usuario."""
    return current_user.settings


@router.patch("/settings", response_model=UserSettingsRead)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
):
    """Actualiza las preferencias de notificaciones."""
    return user_service.update_settings(
        db=db,
        user=current_user,
        notify_comments=settings_data.notify_comments,
        notify_updates=settings_data.notify_updates,
        notify_marketing=settings_data.notify_marketing,
    )


@router.post("/trial")
@limiter.limit("5/minute")
async def start_trial(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
):
    """Inicia un período de prueba gratuito de 14 días verificando que no haya sido consumido."""
    trial_end = user_service.start_trial(db=db, user=current_user)
    user_name = f"{current_user.first_name} {current_user.last_name}".strip() or current_user.email.split("@")[0]
    background_tasks.add_task(send_trial_started_email, current_user.email, user_name=user_name)
    return {
        "status": "trial",
        "trial_end_date": trial_end,
        "message": "Período de prueba iniciado con éxito (14 días).",
    }
