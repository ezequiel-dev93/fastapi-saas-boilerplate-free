from unittest.mock import patch

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from api.main import app
from api.modules.billing.models import SubscriptionPlan
from api.modules.organizations.dependencies import require_feature
from api.modules.organizations.models import (
    Organization,
    OrganizationMember,
)
from api.modules.users.models import UserProfile

# Router auxiliar de prueba para Feature Gating
dummy_feature_router = APIRouter()


@dummy_feature_router.get("/api/v1/test-org/{org_id}/analytics")
async def test_analytics_endpoint(
    membership=Depends(require_feature("advanced_analytics")),
):
    return {"message": "Access granted to advanced analytics"}


app.include_router(dummy_feature_router)


def test_create_organization_assigns_owner(client: TestClient, db_session):
    """Creating an organization automatically sets current_user as owner."""
    headers = {"Authorization": "Bearer test-token-org-owner"}
    payload = {"name": "Acme Inc.", "slug": "acme-inc"}

    response = client.post("/api/v1/organizations", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Inc."
    assert data["slug"] == "acme-inc"

    # Verify membership in DB
    user = db_session.query(UserProfile).filter_by(cognito_sub="org-owner").first()
    assert user is not None

    membership = db_session.query(OrganizationMember).filter_by(organization_id=data["id"], user_id=user.id).first()
    assert membership is not None
    assert membership.role == "owner"


def test_list_user_organizations(client: TestClient):
    """User only sees organizations they belong to."""
    headers_a = {"Authorization": "Bearer test-token-user-a"}
    headers_b = {"Authorization": "Bearer test-token-user-b"}

    # User A creates 2 orgs
    client.post("/api/v1/organizations", json={"name": "Org A1"}, headers=headers_a)
    client.post("/api/v1/organizations", json={"name": "Org A2"}, headers=headers_a)

    # User B creates 1 org
    client.post("/api/v1/organizations", json={"name": "Org B1"}, headers=headers_b)

    # Check User A's orgs
    resp_a = client.get("/api/v1/organizations", headers=headers_a)
    assert resp_a.status_code == 200
    names_a = [o["name"] for o in resp_a.json()]
    assert "Org A1" in names_a
    assert "Org A2" in names_a
    assert "Org B1" not in names_a


def test_get_organization_access_control(client: TestClient):
    """Only members can view organization details."""
    headers_owner = {"Authorization": "Bearer test-token-owner-view"}
    headers_stranger = {"Authorization": "Bearer test-token-stranger"}

    create_resp = client.post("/api/v1/organizations", json={"name": "Private Org"}, headers=headers_owner)
    org_id = create_resp.json()["id"]

    # Owner can access
    resp_ok = client.get(f"/api/v1/organizations/{org_id}", headers=headers_owner)
    assert resp_ok.status_code == 200
    assert resp_ok.json()["name"] == "Private Org"

    # Non-member is forbidden
    resp_forbidden = client.get(f"/api/v1/organizations/{org_id}", headers=headers_stranger)
    assert resp_forbidden.status_code == 403


def test_update_organization_rbac(client: TestClient, db_session):
    """Admins/owners can update org; normal members cannot."""
    headers_owner = {"Authorization": "Bearer test-token-owner-edit"}
    headers_member = {"Authorization": "Bearer test-token-member-edit"}

    create_resp = client.post("/api/v1/organizations", json={"name": "Initial Name"}, headers=headers_owner)
    org_id = create_resp.json()["id"]

    # Add member user to the org as 'member'
    client.get("/api/v1/users/me", headers=headers_member)  # Ensures profile exists
    user_member = db_session.query(UserProfile).filter_by(cognito_sub="member-edit").first()

    member_record = OrganizationMember(organization_id=org_id, user_id=user_member.id, role="member")
    db_session.add(member_record)
    db_session.commit()

    # Normal member tries to update -> 403
    resp_fail = client.patch(
        f"/api/v1/organizations/{org_id}",
        json={"name": "Hacked Name"},
        headers=headers_member,
    )
    assert resp_fail.status_code == 403

    # Owner updates -> 200
    resp_ok = client.patch(
        f"/api/v1/organizations/{org_id}",
        json={"name": "Updated Org Name"},
        headers=headers_owner,
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json()["name"] == "Updated Org Name"


def test_member_role_update_and_removal(client: TestClient, db_session):
    """Owner can change member role and remove members, but cannot remove owner."""
    headers_owner = {"Authorization": "Bearer test-token-owner-manage"}
    headers_admin = {"Authorization": "Bearer test-token-admin-manage"}

    create_resp = client.post("/api/v1/organizations", json={"name": "Team Org"}, headers=headers_owner)
    org_id = create_resp.json()["id"]

    # Pre-create admin profile and membership
    client.get("/api/v1/users/me", headers=headers_admin)
    admin_user = db_session.query(UserProfile).filter_by(cognito_sub="admin-manage").first()

    admin_record = OrganizationMember(organization_id=org_id, user_id=admin_user.id, role="member")
    db_session.add(admin_record)
    db_session.commit()

    # Owner promotes member to admin
    role_resp = client.patch(
        f"/api/v1/organizations/{org_id}/members/{admin_user.id}",
        json={"role": "admin"},
        headers=headers_owner,
    )
    assert role_resp.status_code == 200
    assert role_resp.json()["role"] == "admin"

    # Admin tries to remove owner -> 400
    owner_user = db_session.query(UserProfile).filter_by(cognito_sub="owner-manage").first()
    bad_remove = client.delete(
        f"/api/v1/organizations/{org_id}/members/{owner_user.id}",
        headers=headers_admin,
    )
    assert bad_remove.status_code == 400

    # Owner removes admin member -> 200
    remove_resp = client.delete(
        f"/api/v1/organizations/{org_id}/members/{admin_user.id}",
        headers=headers_owner,
    )
    assert remove_resp.status_code == 200


@patch("api.modules.organizations.routes.send_organization_invitation_email")
def test_invitation_flow_and_acceptance(mock_send_email, client: TestClient, db_session):
    """Full invitation lifecycle: create invite, accept invite, access org."""
    headers_owner = {"Authorization": "Bearer test-token-inviter"}
    headers_invitee = {"Authorization": "Bearer test-token-invitee"}

    create_resp = client.post("/api/v1/organizations", json={"name": "Collab Space"}, headers=headers_owner)
    org_id = create_resp.json()["id"]

    # 1. Create invitation
    invite_resp = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "colleague@example.com", "role": "member"},
        headers=headers_owner,
    )
    assert invite_resp.status_code == 201
    invite_data = invite_resp.json()
    token = invite_data["token"]
    assert invite_data["status"] == "pending"

    # Verify email task was queued
    mock_send_email.assert_called_once()

    # 2. Invitee accepts invitation
    accept_resp = client.post(
        f"/api/v1/organizations/invitations/{token}/accept",
        headers=headers_invitee,
    )
    assert accept_resp.status_code == 200
    assert "con éxito" in accept_resp.json()["message"]

    # 3. Invitee now has access to the organization
    view_resp = client.get(f"/api/v1/organizations/{org_id}", headers=headers_invitee)
    assert view_resp.status_code == 200

    # 4. Trying to reuse the same accepted token fails
    dup_accept = client.post(
        f"/api/v1/organizations/invitations/{token}/accept",
        headers=headers_invitee,
    )
    assert dup_accept.status_code == 400


def test_feature_gating_dependency(client: TestClient, db_session):
    """Route protected by require_feature blocks or allows access based on plan features."""
    headers_owner = {"Authorization": "Bearer test-token-feature-owner"}

    create_resp = client.post("/api/v1/organizations", json={"name": "SaaS Startup"}, headers=headers_owner)
    org_id = create_resp.json()["id"]

    # 1. Org has no plan -> 403
    resp_no_plan = client.get(f"/api/v1/test-org/{org_id}/analytics", headers=headers_owner)
    assert resp_no_plan.status_code == 403
    assert "requiere una suscripción activa" in resp_no_plan.json()["detail"]

    # 2. Org has basic plan WITHOUT 'advanced_analytics' -> 403
    basic_plan = SubscriptionPlan(
        name="Basic Plan",
        slug="basic-test-plan",
        price=19.00,
        features=["basic_reports", "email_support"],
    )
    db_session.add(basic_plan)
    db_session.flush()

    org = db_session.query(Organization).filter_by(id=org_id).first()
    org.subscription_plan_id = basic_plan.id
    org.subscription_status = "active"
    db_session.commit()

    resp_basic = client.get(f"/api/v1/test-org/{org_id}/analytics", headers=headers_owner)
    assert resp_basic.status_code == 403
    assert "no incluye la funcionalidad" in resp_basic.json()["detail"]

    # 3. Org has enterprise plan WITH 'advanced_analytics' -> 200
    enterprise_plan = SubscriptionPlan(
        name="Enterprise Plan",
        slug="enterprise-test-plan",
        price=99.00,
        features=["advanced_analytics", "priority_support"],
    )
    db_session.add(enterprise_plan)
    db_session.flush()

    org.subscription_plan_id = enterprise_plan.id
    db_session.commit()

    resp_enterprise = client.get(f"/api/v1/test-org/{org_id}/analytics", headers=headers_owner)
    assert resp_enterprise.status_code == 200
    assert resp_enterprise.json()["message"] == "Access granted to advanced analytics"
