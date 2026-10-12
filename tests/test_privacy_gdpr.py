from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.modules.users.models import UserProfile, UserSettings


def test_gdpr_export_user_data(client: TestClient, db_session: Session):
    """Verifica que el usuario pueda exportar la totalidad de sus datos personales en formato JSON (GDPR Art. 15 y 20)."""
    user = UserProfile(
        cognito_sub="gdpr-export-user",
        email="export_user@example.com",
        first_name="Carla",
        last_name="Gomez",
    )
    db_session.add(user)
    db_session.flush()

    settings = UserSettings(
        user_id=user.id,
        subscription_status="inactive",
        notify_comments=True,
        notify_updates=False,
        notify_marketing=True,
    )
    db_session.add(settings)
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-gdpr-export-user"}
    response = client.get("/api/v1/users/me/export", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Validar sección usuario
    assert data["user"]["id"] == user.id
    assert data["user"]["cognito_sub"] == "gdpr-export-user"
    assert data["user"]["email"] == "export_user@example.com"
    assert data["user"]["first_name"] == "Carla"
    assert data["user"]["last_name"] == "Gomez"

    # Validar sección settings
    assert data["settings"]["notify_comments"] is True
    assert data["settings"]["notify_updates"] is False
    assert data["settings"]["notify_marketing"] is True

    # Validar listas vacías en edición Lite
    assert data["memberships"] == []
    assert data["stripe_customer"] is None
    assert data["created_api_keys"] == []
    assert data["ai_usage_events"] == []
    assert data["exported_at"] is not None


def test_gdpr_export_rejected_without_auth(client: TestClient):
    """Acceso a /users/me/export sin token retorna 401 Unauthorized."""
    response = client.get("/api/v1/users/me/export")
    assert response.status_code == 401


def test_gdpr_export_rejected_for_api_key(client: TestClient):
    """Verifica que credenciales de tipo API key no puedan acceder al endpoint de exportación personal (401/403)."""
    response = client.get(
        "/api/v1/users/me/export",
        headers={"X-API-Key": "sk_test_" + "A" * 43},
    )
    assert response.status_code in (401, 403)


def test_gdpr_delete_user_account(client: TestClient, db_session: Session):
    """Verifica la anonimización y supresión de cuenta bajo GDPR Art. 17 (Derecho al Olvido)."""
    user = UserProfile(
        cognito_sub="gdpr-delete-user",
        email="delete_me@example.com",
        first_name="Marco",
        last_name="Rossi",
    )
    db_session.add(user)
    db_session.flush()

    settings = UserSettings(
        user_id=user.id,
        subscription_status="inactive",
        notify_comments=True,
        notify_updates=True,
        notify_marketing=True,
    )
    db_session.add(settings)
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-gdpr-delete-user"}
    response = client.delete("/api/v1/users/me/account", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "anonymized"
    assert "anonimizados" in data["message"]
    assert data["deleted_at"] is not None

    # Verificar anonimización en la base de datos
    db_session.expire_all()
    queried = db_session.query(UserProfile).filter_by(cognito_sub="gdpr-delete-user").first()
    assert queried is not None
    assert queried.deleted_at is not None
    assert queried.first_name == "Deleted"
    assert queried.last_name == "User"
    assert queried.email.startswith("deleted_")
    assert queried.email.endswith("@deleted.invalid")

    # Notificaciones reseteadas a False
    assert queried.settings.notify_comments is False
    assert queried.settings.notify_updates is False
    assert queried.settings.notify_marketing is False


def test_deleted_user_cannot_access_me_endpoint(client: TestClient, db_session: Session):
    """Un usuario con deleted_at no puede acceder a /users/me."""
    user = UserProfile(
        cognito_sub="already-deleted-user",
        email="deleted_xyz@deleted.invalid",
        first_name="Deleted",
        last_name="User",
    )
    db_session.add(user)
    db_session.flush()

    from datetime import datetime, timezone
    user.deleted_at = datetime.now(timezone.utc)
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-already-deleted-user"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401
