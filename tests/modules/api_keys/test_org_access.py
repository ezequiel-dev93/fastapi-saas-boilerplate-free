"""Tests de los guards de organización (deny-by-default para API keys).

Verificados con modelos mínimos y SQLite en memoria. Para tu repo hay que
adaptar SOLO el fixture ``db`` (y los imports de engine/SessionLocal): crear
tus Organization / OrganizationMember / SubscriptionPlan reales con los campos
obligatorios que tengan. El resto de los tests no cambia.
"""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from api.core.auth_context import Scope
from api.core.config import settings
from api.core.database import Base, SessionLocal, engine
from api.core.protocols import get_api_key_validator, get_jwt_authenticator
from api.modules.billing.models import SubscriptionPlan
from api.modules.organizations.dependencies import (
    get_active_organization,
    get_current_org_membership,
    require_active_org,
    require_feature,
    require_org_access,
    require_org_role,
)
from api.modules.organizations.models import Organization, OrganizationMember
from api.modules.users.models import UserProfile
from tests.fakes.auth import FakeApiKeyValidator, FakeJwtAuthenticator, FakeUser, make_raw_key

JWT = ".".join(["eyJhbGciOiJSUzI1NiJ9", "e" * 300, "s" * 342])


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")


@pytest.fixture
def db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    s = SessionLocal()
    u1 = UserProfile(id=1, cognito_sub="sub-1", email="u1@example.com")
    u2 = UserProfile(id=2, cognito_sub="sub-2", email="u2@example.com")
    u3 = UserProfile(id=3, cognito_sub="sub-3", email="u3@example.com")
    s.add_all([u1, u2, u3])
    pro = SubscriptionPlan(id=1, name="Pro", slug="pro", features=["advanced_analytics"])
    free = SubscriptionPlan(id=2, name="Free", slug="free", features=[])
    s.add_all([pro, free])
    s.add_all(
        [
            Organization(
                id=1, name="A", slug="org-a", owner_id=1, subscription_status="active", subscription_plan_id=1
            ),
            Organization(
                id=2, name="B", slug="org-b", owner_id=1, subscription_status="active", subscription_plan_id=2
            ),
            Organization(
                id=3, name="C", slug="org-c", owner_id=1, subscription_status="canceled", subscription_plan_id=1
            ),
        ]
    )
    s.add_all(
        [
            OrganizationMember(organization_id=1, user_id=1, role="admin"),
            OrganizationMember(organization_id=1, user_id=2, role="member"),
            OrganizationMember(organization_id=1, user_id=3, role="owner"),
            OrganizationMember(organization_id=2, user_id=1, role="admin"),
        ]
    )
    s.commit()
    s.close()
    yield
    s = SessionLocal()
    s.rollback()
    s.close()


@pytest.fixture
def validator():
    return FakeApiKeyValidator()


@pytest.fixture
def client(db, validator):
    jwt = FakeJwtAuthenticator()
    jwt.add(JWT, FakeUser(id=1))  # admin de la org 1 y 2
    app = FastAPI()

    @app.post("/orgs/{org_id}/members")
    async def invite(org_id: int, a=Depends(require_org_access(roles=["owner", "admin"], scope=Scope.MEMBERS_WRITE))):
        return {"role": a.role, "user_id": a.user_id, "kind": type(a).__name__}

    @app.delete("/orgs/{org_id}")
    async def delete_org(org_id: int, a=Depends(require_org_access(roles=["owner"]))):
        return {"ok": True}

    @app.get("/orgs/{org_id}/analytics")
    async def analytics(
        org_id: int,
        a=Depends(
            require_org_access(roles=["admin", "member"], scope=Scope.BILLING_READ, feature="advanced_analytics")
        ),
    ):
        return {"ok": True}

    @app.get("/orgs/{org_id}/legacy-membership")
    async def legacy_membership(org_id: int, m=Depends(get_current_org_membership)):
        return {"ok": True}

    @app.get("/orgs/{org_id}/legacy-role")
    async def legacy_role(org_id: int, m=Depends(require_org_role(["admin"]))):
        return {"ok": True}

    @app.get("/orgs/{org_id}/legacy-feature")
    async def legacy_feature(org_id: int, m=Depends(require_feature("advanced_analytics"))):
        return {"ok": True}

    @app.get("/active")
    async def active(o=Depends(get_active_organization)):
        return {"org": o.id}

    @app.get("/active-scoped")
    async def active_scoped(o=Depends(require_active_org(Scope.USERS_READ))):
        return {"org": o.id}

    app.dependency_overrides[get_api_key_validator] = lambda: validator
    app.dependency_overrides[get_jwt_authenticator] = lambda: jwt
    return TestClient(app)


def key(validator, org_id, scopes, kid=1):
    raw = make_raw_key("test")
    validator.add(raw, org_id=org_id, scopes=set(scopes), key_id=kid)
    return {"X-API-Key": raw}


J = {"Authorization": f"Bearer {JWT}"}


class TestJwtUnchanged:
    def test_admin_invites(self, client):
        r = client.post("/orgs/1/members", headers=J)
        assert r.status_code == 200 and r.json()["kind"] == "OrganizationMember"

    def test_member_role_rejected(self, client, validator):
        # user 1 es admin en org 1; en org 2 también admin. Ruta owner-only:
        assert client.delete("/orgs/1", headers=J).status_code == 403

    def test_not_a_member_rejected(self, client):
        assert client.post("/orgs/3/members", headers=J).status_code == 403

    def test_active_org_defaults_to_first(self, client):
        assert client.get("/active", headers=J).json() == {"org": 1}

    def test_active_org_header_requires_membership(self, client):
        assert client.get("/active", headers={**J, "X-Organization-ID": "3"}).status_code == 403

    def test_legacy_guards_work_for_jwt(self, client):
        assert client.get("/orgs/1/legacy-membership", headers=J).status_code == 200
        assert client.get("/orgs/1/legacy-role", headers=J).status_code == 200
        assert client.get("/orgs/1/legacy-feature", headers=J).status_code == 200
        assert client.get("/orgs/2/legacy-feature", headers=J).status_code == 403  # plan Free


class TestApiKeyAccess:
    def test_key_with_scope_and_org_is_allowed_without_fake_user_id(self, client, validator):
        r = client.post("/orgs/1/members", headers=key(validator, 1, {Scope.MEMBERS_WRITE}))
        assert r.status_code == 200
        assert r.json() == {"role": "api_key", "user_id": None, "kind": "ApiKeyOrgAccess"}

    def test_missing_scope(self, client, validator):
        assert client.post("/orgs/1/members", headers=key(validator, 1, {Scope.MEMBERS_READ})).status_code == 403

    def test_other_org(self, client, validator):
        assert client.post("/orgs/2/members", headers=key(validator, 1, set(Scope))).status_code == 403

    def test_owner_only_route_is_never_reachable_with_a_key(self, client, validator):
        assert client.delete("/orgs/1", headers=key(validator, 1, set(Scope))).status_code == 403

    @pytest.mark.parametrize("path", ["legacy-membership", "legacy-role", "legacy-feature"])
    def test_legacy_guards_are_deny_by_default_for_keys(self, client, validator, path):
        assert client.get(f"/orgs/1/{path}", headers=key(validator, 1, set(Scope))).status_code == 403

    def test_inactive_subscription_is_rejected(self, client, validator):
        assert client.post("/orgs/3/members", headers=key(validator, 3, {Scope.MEMBERS_WRITE})).status_code == 403

    def test_plan_feature_is_enforced_for_keys(self, client, validator):
        # org 1 (Pro) incluye el feature; org 2 (Free) no, aunque la key tenga el scope.
        assert client.get("/orgs/1/analytics", headers=key(validator, 1, {Scope.BILLING_READ})).status_code == 200
        assert client.get("/orgs/2/analytics", headers=key(validator, 2, {Scope.BILLING_READ})).status_code == 403

    def test_feature_route_still_needs_the_scope(self, client, validator):
        assert client.get("/orgs/1/analytics", headers=key(validator, 1, {Scope.USERS_READ})).status_code == 403

    def test_active_org_is_deny_by_default_for_keys(self, client, validator):
        assert client.get("/active", headers=key(validator, 1, set(Scope))).status_code == 403

    def test_scoped_active_org(self, client, validator):
        h = key(validator, 1, {Scope.USERS_READ})
        assert client.get("/active-scoped", headers=h).json() == {"org": 1}
        assert client.get("/active-scoped", headers={**h, "X-Organization-ID": "2"}).status_code == 403
        assert client.get("/active-scoped", headers=key(validator, 1, {Scope.USERS_WRITE})).status_code == 403
