from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.core.auth_context import Scope
from api.core.protocols.identity import get_identity_provider
from api.modules.ai.models import AiUsageEvent
from api.modules.billing.models import StripeCustomer
from api.modules.organizations.api_key_service import get_api_key_service
from api.modules.organizations.models import Organization, OrganizationApiKey, OrganizationMember
from api.modules.users.models import UserProfile, UserSettings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ──────────────────────────────────────────────────────────────────────────
# 1. Tests de Derecho de Acceso y Portabilidad (GDPR Art. 15 y 20)
# ──────────────────────────────────────────────────────────────────────────


def test_gdpr_export_user_data(client: TestClient, db_session: Session):
    """Verifica que el usuario pueda exportar la totalidad de sus datos en formato estructurado JSON."""
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

    # Organización de la que es owner
    org = Organization(
        name="Carla Tech",
        slug="carla-tech",
        owner_id=user.id,
        subscription_status="inactive",
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role="owner",
    )
    db_session.add(member)

    # API key creada por la usuaria
    key_service = get_api_key_service()
    api_key, raw_key = key_service.create_api_key(
        db=db_session,
        org_id=org.id,
        creator=user,
        creator_role="owner",
        name="Production Key",
        scopes=[Scope.AI_GENERATE],
    )

    # Evento de uso de IA registrado
    ai_event = AiUsageEvent(
        request_id="ai-req-export-001",
        organization_id=org.id,
        user_id=user.id,
        api_key_id=api_key.id,
        provider="mock",
        model="gpt-4o-mini",
        status="completed",
        input_tokens=15,
        output_tokens=30,
    )
    db_session.add(ai_event)
    db_session.commit()

    # Petición con autenticación JWT
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

    # Validar configuración
    assert data["settings"]["notify_comments"] is True
    assert data["settings"]["notify_updates"] is False
    assert data["settings"]["notify_marketing"] is True

    # Validar membresías
    assert len(data["memberships"]) == 1
    assert data["memberships"][0]["organization_name"] == "Carla Tech"
    assert data["memberships"][0]["role"] == "owner"

    # Validar API keys creadas (metadatos sin secreto crudo)
    assert len(data["created_api_keys"]) == 1
    assert data["created_api_keys"][0]["name"] == "Production Key"
    assert "sk_test_" in data["created_api_keys"][0]["key_prefix"]
    assert raw_key not in str(data)  # Nunca se exporta el raw_key

    # Validar eventos de IA (metadatos de uso, nunca prompts/respuestas)
    assert len(data["ai_usage_events"]) == 1
    assert data["ai_usage_events"][0]["request_id"] == "ai-req-export-001"
    assert data["ai_usage_events"][0]["provider"] == "mock"
    assert data["ai_usage_events"][0]["input_tokens"] == 15
    assert data["ai_usage_events"][0]["output_tokens"] == 30

    assert data["exported_at"] is not None


def test_gdpr_export_rejected_for_api_key(client: TestClient, db_session: Session):
    """Verifica que las API keys de organización no puedan acceder al endpoint de exportación personal (403 Forbidden)."""
    user = UserProfile(
        cognito_sub="key-creator-export",
        email="creator_exp@example.com",
    )
    db_session.add(user)
    db_session.flush()

    org = Organization(
        name="Key Org Export",
        slug="key-org-export",
        owner_id=user.id,
    )
    db_session.add(org)
    db_session.flush()

    key_service = get_api_key_service()
    _, raw_key = key_service.create_api_key(
        db=db_session,
        org_id=org.id,
        creator=user,
        creator_role="owner",
        name="Test Export Key",
        scopes=[Scope.AI_GENERATE],
    )
    db_session.commit()

    response = client.get(
        "/api/v1/users/me/export",
        headers={"X-API-Key": raw_key},
    )
    assert response.status_code == 403
    assert "Organization API keys cannot access user-level endpoints" in response.json()["detail"]


# ──────────────────────────────────────────────────────────────────────────
# 2. Precondiciones de Supresión (HTTP 409 Conflict, D-13)
# ──────────────────────────────────────────────────────────────────────────


def test_gdpr_delete_rejected_if_sole_owner_with_other_members(client: TestClient, db_session: Session):
    """Rechaza supresión (HTTP 409) si el usuario es el único propietario de una organización con otros miembros."""
    alice = UserProfile(
        cognito_sub="alice-sole-owner",
        email="alice_sole@example.com",
    )
    bob = UserProfile(
        cognito_sub="bob-member",
        email="bob_member@example.com",
    )
    db_session.add_all([alice, bob])
    db_session.flush()

    org = Organization(
        name="Shared Venture",
        slug="shared-venture",
        owner_id=alice.id,
    )
    db_session.add(org)
    db_session.flush()

    db_session.add_all([
        OrganizationMember(organization_id=org.id, user_id=alice.id, role="owner"),
        OrganizationMember(organization_id=org.id, user_id=bob.id, role="member"),
    ])
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-alice-sole-owner"}
    response = client.delete("/api/v1/users/me/account", headers=headers)

    assert response.status_code == 409
    assert "único propietario" in response.json()["detail"]
    assert "Shared Venture" in response.json()["detail"]


def test_gdpr_delete_rejected_if_active_stripe_subscription(client: TestClient, db_session: Session):
    """Rechaza supresión (HTTP 409) si el usuario tiene una suscripción de Stripe activa."""
    user = UserProfile(
        cognito_sub="stripe-active-user",
        email="stripe_active@example.com",
    )
    db_session.add(user)
    db_session.flush()

    customer = StripeCustomer(
        user_id=user.id,
        stripe_customer_id="cus_active_123",
        subscription_status="active",
        stripe_subscription_id="sub_active_123",
    )
    db_session.add(customer)
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-stripe-active-user"}
    response = client.delete("/api/v1/users/me/account", headers=headers)

    assert response.status_code == 409
    assert "suscripción activa de Stripe" in response.json()["detail"]


def test_gdpr_delete_rejected_if_owned_org_has_active_subscription(client: TestClient, db_session: Session):
    """Rechaza supresión (HTTP 409) si la organización que posee tiene suscripción activa."""
    user = UserProfile(
        cognito_sub="org-active-sub-user",
        email="org_sub_user@example.com",
    )
    db_session.add(user)
    db_session.flush()

    org = Organization(
        name="Subscribed Org",
        slug="subscribed-org",
        owner_id=user.id,
        subscription_status="active",
    )
    db_session.add(org)
    db_session.flush()

    db_session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="owner"))
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-org-active-sub-user"}
    response = client.delete("/api/v1/users/me/account", headers=headers)

    assert response.status_code == 409
    assert "suscripción activa de Stripe" in response.json()["detail"]


# ──────────────────────────────────────────────────────────────────────────
# 3. Flujo Exitoso de Supresión (GDPR Soft-Anonymization, D-12, D-14, D-15)
# ──────────────────────────────────────────────────────────────────────────


def test_gdpr_delete_account_success_and_api_keys_preservation(client: TestClient, db_session: Session):
    """
    Supresión exitosa:
    - Soft-anonymization del perfil (email deleted_<uuid>@deleted.invalid, nombres neutros).
    - Preserva las API keys (created_by_id = NULL) y la key sigue funcionando (D-14).
    - Encola la baja en Cognito (MockIdentityProvider registra el cognito_sub) (D-15).
    - La organización compartida sobrevive con el otro propietario.
    """
    alice = UserProfile(
        cognito_sub="alice-delete-success",
        email="alice_del@example.com",
        first_name="Alice",
        last_name="Johnson",
    )
    bob = UserProfile(
        cognito_sub="bob-coowner",
        email="bob_coowner@example.com",
        first_name="Bob",
        last_name="Williams",
    )
    db_session.add_all([alice, bob])
    db_session.flush()

    alice_settings = UserSettings(
        user_id=alice.id,
        subscription_status="inactive",
        notify_comments=True,
        notify_updates=True,
    )
    db_session.add(alice_settings)

    # Organización con dos propietarios (Alice y Bob)
    org = Organization(
        name="Dual Owner Org",
        slug="dual-owner-org",
        owner_id=bob.id,  # Bob es el primary owner
        subscription_status="inactive",
    )
    db_session.add(org)
    db_session.flush()

    db_session.add_all([
        OrganizationMember(organization_id=org.id, user_id=alice.id, role="owner"),
        OrganizationMember(organization_id=org.id, user_id=bob.id, role="owner"),
    ])

    # Alice crea una API key para la organización
    key_service = get_api_key_service()
    api_key, raw_key = key_service.create_api_key(
        db=db_session,
        org_id=org.id,
        creator=alice,
        creator_role="owner",
        name="Key Created By Alice",
        scopes=[Scope.AI_GENERATE],
    )
    db_session.commit()

    api_key_id = api_key.id
    alice_id = alice.id

    # Alice ejecuta la eliminación de su cuenta
    headers = {"Authorization": "Bearer test-token-alice-delete-success"}
    response = client.delete("/api/v1/users/me/account", headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["deleted_at"] is not None

    # Verificar estado en la base de datos
    db_session.expire_all()
    alice_db = db_session.query(UserProfile).filter_by(id=alice_id).first()
    assert alice_db is not None
    assert alice_db.email.startswith("deleted_")
    assert alice_db.email.endswith("@deleted.invalid")
    assert alice_db.first_name == "Deleted"
    assert alice_db.last_name == "User"
    assert alice_db.deleted_at is not None

    # Notificaciones limpiadas
    assert alice_db.settings.notify_comments is False
    assert alice_db.settings.notify_updates is False

    # Membresía de Alice removida
    alice_membership = db_session.query(OrganizationMember).filter_by(user_id=alice_id).first()
    assert alice_membership is None

    # Organización de Bob sigue intacta
    org_db = db_session.query(Organization).filter_by(id=org.id).first()
    assert org_db is not None

    # D-14: La API Key fue desvinculada (created_by_id = NULL) pero sigue viva y activa
    refreshed_key = db_session.query(OrganizationApiKey).filter_by(id=api_key_id).first()
    assert refreshed_key is not None
    assert refreshed_key.created_by_id is None
    assert refreshed_key.is_active is True

    # Validar que la API key funciona y valida correctamente tras la baja de Alice
    validated = key_service._sync_validate(raw_key, db=db_session)
    assert validated is not None
    assert validated.key_id == api_key_id

    # D-15: MockIdentityProvider registró la baja del cognito_sub
    idp = get_identity_provider()
    assert "alice-delete-success" in idp.deleted_users


def test_gdpr_deleted_user_token_rejected_immediately(client: TestClient, db_session: Session):
    """
    Verifica que inmediatamente tras la eliminación, el token JWT previo del usuario
    sea rechazado con HTTP 401 Unauthorized (D-15).
    """
    user = UserProfile(
        cognito_sub="user-to-be-deleted-401",
        email="instant_401@example.com",
        first_name="Instant",
        last_name="Test",
    )
    db_session.add(user)
    db_session.flush()

    user_settings = UserSettings(user_id=user.id, subscription_status="inactive")
    db_session.add(user_settings)
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-user-to-be-deleted-401"}

    # 1. Petición previa funciona
    resp_before = client.get("/api/v1/users/me", headers=headers)
    assert resp_before.status_code == 200

    # 2. Eliminar cuenta
    resp_delete = client.delete("/api/v1/users/me/account", headers=headers)
    assert resp_delete.status_code == 200

    # 3. Petición posterior con el mismo token es inmediatamente rechazada con 401
    resp_after = client.get("/api/v1/users/me", headers=headers)
    assert resp_after.status_code == 401
    assert "Invalid or expired token" in resp_after.json()["detail"] or "eliminada" in resp_after.json()["detail"]


def test_gdpr_delete_sole_member_org_cleaned_up(client: TestClient, db_session: Session):
    """
    Si el usuario es dueño de una organización donde es el ÚNICO miembro y no tiene suscripción activa,
    la organización personal se elimina limpiamente junto con el usuario.
    """
    user = UserProfile(
        cognito_sub="solo-owner-cleanup",
        email="solo_cleanup@example.com",
    )
    db_session.add(user)
    db_session.flush()

    org = Organization(
        name="Solo Project",
        slug="solo-project",
        owner_id=user.id,
        subscription_status="inactive",
    )
    db_session.add(org)
    db_session.flush()

    db_session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="owner"))
    db_session.commit()

    org_id = org.id

    headers = {"Authorization": "Bearer test-token-solo-owner-cleanup"}
    response = client.delete("/api/v1/users/me/account", headers=headers)
    assert response.status_code == 200

    db_session.expire_all()
    # La organización vacía debe haber sido eliminada
    deleted_org = db_session.query(Organization).filter_by(id=org_id).first()
    assert deleted_org is None


def test_gdpr_delete_regular_member_leaves_org_intact(client: TestClient, db_session: Session):
    """
    Si el usuario es un miembro regular (role='member') en una organización ajena,
    su eliminación no afecta la organización ni al resto de los miembros.
    """
    owner = UserProfile(
        cognito_sub="org-boss",
        email="boss@example.com",
    )
    member_user = UserProfile(
        cognito_sub="org-regular-employee",
        email="employee@example.com",
    )
    db_session.add_all([owner, member_user])
    db_session.flush()

    org = Organization(
        name="Big Enterprise",
        slug="big-enterprise",
        owner_id=owner.id,
        subscription_status="inactive",
    )
    db_session.add(org)
    db_session.flush()

    db_session.add_all([
        OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner"),
        OrganizationMember(organization_id=org.id, user_id=member_user.id, role="member"),
    ])
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-org-regular-employee"}
    response = client.delete("/api/v1/users/me/account", headers=headers)
    assert response.status_code == 200

    db_session.expire_all()
    # La organización sigue existiendo con su dueño
    org_db = db_session.query(Organization).filter_by(id=org.id).first()
    assert org_db is not None
    assert len(org_db.members) == 1
    assert org_db.members[0].user_id == owner.id
