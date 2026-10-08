import asyncio
import hashlib
import os
import tempfile
from datetime import timedelta, timezone

from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from alembic import command
from api.core.auth_context import Scope
from api.modules.organizations.api_key_service import ApiKeyService, utcnow
from api.modules.organizations.models import Organization, OrganizationApiKey, OrganizationMember
from api.modules.users.models import UserProfile


def test_create_organization_api_key(client: TestClient, db_session: Session):
    """Owner can create an organization API key and receives raw secret only once."""
    owner = UserProfile(cognito_sub="org-owner-1", email="owner1@example.com", first_name="Owner", last_name="One")
    db_session.add(owner)
    db_session.flush()

    org = Organization(name="Acme Corp", slug="acme-corp", owner_id=owner.id, subscription_status="active")
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner")
    db_session.add(member)
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-org-owner-1"}
    payload = {
        "name": "Production CI/CD",
        "scopes": ["users:read", "billing:read"],
        "expires_in_days": 30,
    }

    response = client.post(f"/api/v1/organizations/{org.id}/api-keys", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.headers.get("Cache-Control") == "no-store"
    data = response.json()

    assert data["name"] == "Production CI/CD"
    assert data["key_prefix"].startswith("sk_test_")
    assert "raw_key" in data
    assert data["raw_key"].startswith(data["key_prefix"])
    assert data["scopes"] == ["users:read", "billing:read"]
    assert data["is_active"] is True

    # Verify database has hash, not the raw key
    db_key = db_session.query(OrganizationApiKey).filter_by(id=data["id"]).first()
    assert db_key is not None
    assert db_key.hashed_key == hashlib.sha256(data["raw_key"].encode("utf-8")).hexdigest()
    assert db_key.hashed_key != data["raw_key"]


def test_list_organization_api_keys_masks_secret(client: TestClient, db_session: Session):
    """Listing API keys returns active metadata but never exposes raw secret."""
    owner = UserProfile(cognito_sub="org-owner-2", email="owner2@example.com")
    db_session.add(owner)
    db_session.flush()

    org = Organization(name="Beta Labs", slug="beta-labs", owner_id=owner.id, subscription_status="active")
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner")
    db_session.add(member)
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-org-owner-2"}

    # Create 2 keys
    client.post(
        f"/api/v1/organizations/{org.id}/api-keys", json={"name": "Key 1", "scopes": ["users:read"]}, headers=headers
    )
    client.post(
        f"/api/v1/organizations/{org.id}/api-keys", json={"name": "Key 2", "scopes": ["billing:read"]}, headers=headers
    )

    # List
    response = client.get(f"/api/v1/organizations/{org.id}/api-keys", headers=headers)
    assert response.status_code == 200
    keys = response.json()
    assert len(keys) == 2
    for k in keys:
        assert "raw_key" not in k
        assert "hashed_key" not in k
        assert k["key_prefix"].startswith("sk_test_")


def test_revoke_organization_api_key(client: TestClient, db_session: Session):
    """Revoking an API key sets revoked_at and marks is_active as false."""
    owner = UserProfile(cognito_sub="org-owner-3", email="owner3@example.com")
    db_session.add(owner)
    db_session.flush()

    org = Organization(name="Gamma Inc", slug="gamma-inc", owner_id=owner.id, subscription_status="active")
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner")
    db_session.add(member)
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-org-owner-3"}
    create_resp = client.post(
        f"/api/v1/organizations/{org.id}/api-keys", json={"name": "Temp Key", "scopes": ["users:read"]}, headers=headers
    )
    key_id = create_resp.json()["id"]

    # Revoke
    del_resp = client.delete(f"/api/v1/organizations/{org.id}/api-keys/{key_id}", headers=headers)
    assert del_resp.status_code == 200
    assert "revocada" in del_resp.json()["message"]

    # List shows revoked
    list_resp = client.get(f"/api/v1/organizations/{org.id}/api-keys", headers=headers)
    assert list_resp.json()[0]["is_active"] is False
    assert list_resp.json()[0]["revoked_at"] is not None


def test_member_role_cannot_manage_api_keys(client: TestClient, db_session: Session):
    """Users with member role cannot create or view API keys (403 Forbidden)."""
    owner = UserProfile(cognito_sub="org-owner-4", email="owner4@example.com")
    member_user = UserProfile(cognito_sub="org-member-4", email="member4@example.com")
    db_session.add_all([owner, member_user])
    db_session.flush()

    org = Organization(name="Delta Co", slug="delta-co", owner_id=owner.id, subscription_status="active")
    db_session.add(org)
    db_session.flush()

    db_session.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner"))
    db_session.add(OrganizationMember(organization_id=org.id, user_id=member_user.id, role="member"))
    db_session.commit()

    # Member role attempt
    member_headers = {"Authorization": "Bearer test-token-org-member-4"}
    resp = client.post(
        f"/api/v1/organizations/{org.id}/api-keys",
        json={"name": "Forbidden", "scopes": ["users:read"]},
        headers=member_headers,
    )
    assert resp.status_code == 403


def test_api_key_service_validate_direct(db_session: Session):
    """ApiKeyService directly validates hash and rejects revoked keys."""
    owner = UserProfile(cognito_sub="org-owner-5", email="owner5@example.com")
    db_session.add(owner)
    db_session.flush()

    org = Organization(name="Epsilon LLC", slug="epsilon-llc", owner_id=owner.id, subscription_status="active")
    db_session.add(org)
    db_session.flush()

    service = ApiKeyService()
    key_obj, raw_key = service.create_api_key(
        db=db_session,
        org_id=org.id,
        creator=owner,
        creator_role="owner",
        name="Direct Test",
        scopes=[Scope.USERS_READ, Scope.BILLING_READ],
    )

    validated = asyncio.run(service.validate(raw_key, db=db_session))
    assert validated is not None
    assert validated.org_id == org.id
    assert Scope.USERS_READ in validated.scopes
    assert Scope.BILLING_READ in validated.scopes

    # Revoked key returns None
    service.revoke_api_key(db_session, org.id, key_obj.id)
    assert asyncio.run(service.validate(raw_key, db=db_session)) is None


def test_admin_cannot_escalate_billing_write_scope(client: TestClient, db_session: Session):
    """Admin cannot grant billing:write (anti-escalation, returns 400)."""
    owner = UserProfile(cognito_sub="org-owner-6", email="owner6@example.com")
    admin_user = UserProfile(cognito_sub="org-admin-6", email="admin6@example.com")
    db_session.add_all([owner, admin_user])
    db_session.flush()

    org = Organization(name="Zeta Security", slug="zeta-sec", owner_id=owner.id, subscription_status="active")
    db_session.add(org)
    db_session.flush()

    db_session.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner"))
    db_session.add(OrganizationMember(organization_id=org.id, user_id=admin_user.id, role="admin"))
    db_session.commit()

    admin_headers = {"Authorization": "Bearer test-token-org-admin-6"}

    # Attempt to grant billing:write
    escalate_resp = client.post(
        f"/api/v1/organizations/{org.id}/api-keys",
        json={"name": "Illegal Key", "scopes": ["billing:write"]},
        headers=admin_headers,
    )
    assert escalate_resp.status_code == 400
    assert "billing:write" in escalate_resp.json()["detail"]

    # Allowed scopes succeed
    allowed_resp = client.post(
        f"/api/v1/organizations/{org.id}/api-keys",
        json={"name": "Legal Key", "scopes": ["users:read", "members:write"]},
        headers=admin_headers,
    )
    assert allowed_resp.status_code == 201


def test_get_and_delete_other_org_api_key_returns_404_idor(client: TestClient, db_session: Session):
    """Accessing or deleting a key belonging to another organization returns 404 (anti-IDOR)."""
    owner_a = UserProfile(cognito_sub="org-owner-7a", email="owner7a@example.com")
    owner_b = UserProfile(cognito_sub="org-owner-7b", email="owner7b@example.com")
    db_session.add_all([owner_a, owner_b])
    db_session.flush()

    org_a = Organization(name="Org A", slug="org-a", owner_id=owner_a.id, subscription_status="active")
    org_b = Organization(name="Org B", slug="org-b", owner_id=owner_b.id, subscription_status="active")
    db_session.add_all([org_a, org_b])
    db_session.flush()

    db_session.add(OrganizationMember(organization_id=org_a.id, user_id=owner_a.id, role="owner"))
    db_session.add(OrganizationMember(organization_id=org_b.id, user_id=owner_b.id, role="owner"))
    db_session.commit()

    headers_a = {"Authorization": "Bearer test-token-org-owner-7a"}
    headers_b = {"Authorization": "Bearer test-token-org-owner-7b"}

    # Create key in Org A
    create_resp = client.post(
        f"/api/v1/organizations/{org_a.id}/api-keys",
        json={"name": "Key A", "scopes": ["users:read"]},
        headers=headers_a,
    )
    assert create_resp.status_code == 201
    key_a_id = create_resp.json()["id"]

    # Owner A can read own key metadata
    get_a_resp = client.get(f"/api/v1/organizations/{org_a.id}/api-keys/{key_a_id}", headers=headers_a)
    assert get_a_resp.status_code == 200
    assert "raw_key" not in get_a_resp.json()

    # Owner B attempts to GET Key A through Org B url -> 404
    get_resp = client.get(f"/api/v1/organizations/{org_b.id}/api-keys/{key_a_id}", headers=headers_b)
    assert get_resp.status_code == 404

    # Owner B attempts to DELETE Key A through Org B url -> 404
    del_resp = client.delete(f"/api/v1/organizations/{org_b.id}/api-keys/{key_a_id}", headers=headers_b)
    assert del_resp.status_code == 404


def test_api_key_calling_api_keys_management_returns_403(client: TestClient, db_session: Session):
    """An API key cannot manage organization API keys (CRUD requires human JWT)."""
    owner = UserProfile(cognito_sub="org-owner-8", email="owner8@example.com")
    db_session.add(owner)
    db_session.flush()

    org = Organization(name="Theta Shield", slug="theta-shield", owner_id=owner.id, subscription_status="active")
    db_session.add(org)
    db_session.flush()

    db_session.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner"))
    db_session.commit()

    service = ApiKeyService()
    key_obj, raw_key = service.create_api_key(
        db=db_session,
        org_id=org.id,
        creator=owner,
        creator_role="owner",
        name="Automation Key",
        scopes=[Scope.USERS_READ, Scope.MEMBERS_READ],
    )

    api_key_headers = {"X-API-Key": raw_key}

    # API key calling POST /api-keys
    post_resp = client.post(
        f"/api/v1/organizations/{org.id}/api-keys",
        json={"name": "Sub Key", "scopes": ["users:read"]},
        headers=api_key_headers,
    )
    assert post_resp.status_code == 403

    # API key calling GET /api-keys
    list_resp = client.get(f"/api/v1/organizations/{org.id}/api-keys", headers=api_key_headers)
    assert list_resp.status_code == 403

    # API key calling GET /api-keys/{id}
    get_resp = client.get(f"/api/v1/organizations/{org.id}/api-keys/{key_obj.id}", headers=api_key_headers)
    assert get_resp.status_code == 403

    # API key calling DELETE /api-keys/{id}
    del_resp = client.delete(f"/api/v1/organizations/{org.id}/api-keys/{key_obj.id}", headers=api_key_headers)
    assert del_resp.status_code == 403


def test_key_survives_creator_deletion(db_session: Session):
    """Deleting the user who created an API key unlinks creator (SET NULL) but key remains valid."""
    owner = UserProfile(cognito_sub="org-owner-9", email="owner9@example.com")
    admin_creator = UserProfile(cognito_sub="org-admin-9", email="admin9@example.com")
    db_session.add_all([owner, admin_creator])
    db_session.flush()

    org = Organization(name="Iota Corp", slug="iota-corp", owner_id=owner.id, subscription_status="active")
    db_session.add(org)
    db_session.flush()

    db_session.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner"))
    db_session.add(OrganizationMember(organization_id=org.id, user_id=admin_creator.id, role="admin"))
    db_session.commit()

    service = ApiKeyService()
    key_obj, raw_key = service.create_api_key(
        db=db_session,
        org_id=org.id,
        creator=admin_creator,
        creator_role="admin",
        name="Survivor Key",
        scopes=[Scope.USERS_READ],
    )
    assert key_obj.created_by_id == admin_creator.id

    # Delete creator (admin_creator departs / account removed)
    db_session.delete(admin_creator)
    db_session.commit()

    # Verify created_by_id is now None (SET NULL)
    refreshed_key = db_session.query(OrganizationApiKey).filter_by(id=key_obj.id).first()
    assert refreshed_key is not None
    assert refreshed_key.created_by_id is None

    # Key still validates successfully
    validated = asyncio.run(service.validate(raw_key, db=db_session))
    assert validated is not None
    assert validated.org_id == org.id
    assert validated.created_by_id is None


def test_expired_key_returns_401(client: TestClient, db_session: Session):
    """An expired API key returns 401 Unauthorized."""
    owner = UserProfile(cognito_sub="org-owner-10", email="owner10@example.com")
    db_session.add(owner)
    db_session.flush()

    org = Organization(name="Kappa Tech", slug="kappa-tech", owner_id=owner.id, subscription_status="active")
    db_session.add(org)
    db_session.flush()

    service = ApiKeyService()
    key_obj, raw_key = service.create_api_key(
        db=db_session,
        org_id=org.id,
        creator=owner,
        creator_role="owner",
        name="Expired Key",
        scopes=[Scope.MEMBERS_READ],
    )

    # Manually expire the key
    key_obj.expires_at = utcnow() - timedelta(days=2)
    db_session.commit()

    # Direct validation returns None
    assert asyncio.run(service.validate(raw_key, db=db_session)) is None

    # HTTP call with expired key returns 401
    resp = client.get(f"/api/v1/organizations/{org.id}/members", headers={"X-API-Key": raw_key})
    assert resp.status_code == 401


def test_inactive_org_subscription_blocks_api_key(client: TestClient, db_session: Session):
    """API key of an organization with inactive subscription receives 403 Forbidden."""
    owner = UserProfile(cognito_sub="org-owner-11", email="owner11@example.com")
    db_session.add(owner)
    db_session.flush()

    org = Organization(name="Lambda Soft", slug="lambda-soft", owner_id=owner.id, subscription_status="canceled")
    db_session.add(org)
    db_session.flush()

    service = ApiKeyService()
    _, raw_key = service.create_api_key(
        db=db_session,
        org_id=org.id,
        creator=owner,
        creator_role="owner",
        name="Canceled Org Key",
        scopes=[Scope.MEMBERS_READ],
    )

    resp = client.get(f"/api/v1/organizations/{org.id}/members", headers={"X-API-Key": raw_key})
    assert resp.status_code == 403
    assert "subscription is not active" in resp.json()["detail"].lower()


def test_last_used_at_throttling(db_session: Session):
    """last_used_at is updated on first use and throttled against repeated writes within 5 minutes."""
    owner = UserProfile(cognito_sub="org-owner-12", email="owner12@example.com")
    db_session.add(owner)
    db_session.flush()

    org = Organization(name="Mu Networks", slug="mu-networks", owner_id=owner.id, subscription_status="active")
    db_session.add(org)
    db_session.flush()

    service = ApiKeyService()
    key_obj, raw_key = service.create_api_key(
        db=db_session,
        org_id=org.id,
        creator=owner,
        creator_role="owner",
        name="Throttle Test",
        scopes=[Scope.USERS_READ],
    )
    assert key_obj.last_used_at is None

    # First validation sets last_used_at
    asyncio.run(service.validate(raw_key, db=db_session))
    db_session.refresh(key_obj)
    first_used_at = key_obj.last_used_at
    assert first_used_at is not None

    # Immediate second validation does not rewrite last_used_at
    asyncio.run(service.validate(raw_key, db=db_session))
    db_session.refresh(key_obj)
    assert key_obj.last_used_at == first_used_at

    # Simulate 6 minutes passed
    older_time = utcnow() - timedelta(minutes=6)
    key_obj.last_used_at = older_time
    db_session.commit()

    # Third validation updates last_used_at
    asyncio.run(service.validate(raw_key, db=db_session))
    db_session.refresh(key_obj)
    last_used = key_obj.last_used_at
    if last_used.tzinfo is None:
        last_used = last_used.replace(tzinfo=timezone.utc)
    assert last_used > older_time


def test_cascade_delete_organization_deletes_api_keys(db_session: Session):
    """Deleting an organization cascades and removes its API keys."""
    owner = UserProfile(cognito_sub="org-owner-13", email="owner13@example.com")
    db_session.add(owner)
    db_session.flush()

    org = Organization(name="Nu Systems", slug="nu-systems", owner_id=owner.id, subscription_status="active")
    db_session.add(org)
    db_session.flush()

    service = ApiKeyService()
    key_obj, _ = service.create_api_key(
        db=db_session,
        org_id=org.id,
        creator=owner,
        creator_role="owner",
        name="Cascade Test",
        scopes=[Scope.USERS_READ],
    )

    # Delete Org
    db_session.delete(org)
    db_session.commit()

    remaining_key = db_session.query(OrganizationApiKey).filter_by(id=key_obj.id).first()
    assert remaining_key is None


def test_alembic_migration_upgrade_downgrade_cycle():
    """Verify Alembic upgrade -> downgrade -> upgrade cycle on a clean database."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_cycle.db").replace("\\", "/")

    try:
        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

        # 1. Upgrade to head
        command.upgrade(cfg, "head")

        # 2. Downgrade to previous revision
        command.downgrade(cfg, "e6cacfecc701")

        # 3. Upgrade back to head
        command.upgrade(cfg, "head")
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
