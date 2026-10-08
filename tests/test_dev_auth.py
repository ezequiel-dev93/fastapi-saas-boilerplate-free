from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from api.core.config import settings
from api.core.security import create_dev_access_token, verify_jwt_token
from api.main import CognitoJwtAuthenticator
from api.modules.organizations.models import Organization, OrganizationMember
from api.modules.users.models import UserProfile


def test_dev_token_creation_and_verification(db_session):
    user = UserProfile(
        cognito_sub="sub-dev-unit-1",
        email="testdev@example.com",
        first_name="Carlos",
        last_name="Tester",
    )
    db_session.add(user)
    db_session.commit()

    token = create_dev_access_token(user)
    assert isinstance(token, str)

    claims = verify_jwt_token(token)
    assert claims["sub"] == "sub-dev-unit-1"
    assert claims["email"] == "testdev@example.com"
    assert claims["given_name"] == "Carlos"
    assert claims["family_name"] == "Tester"
    assert claims["iss"] == "fastapi-saas-dev"


def test_dev_token_forbidden_in_production(db_session, monkeypatch):
    user = UserProfile(
        cognito_sub="sub-dev-unit-2",
        email="prodtest@example.com",
        first_name="Prod",
        last_name="Test",
    )
    db_session.add(user)
    db_session.commit()

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with pytest.raises(HTTPException) as exc_info:
        create_dev_access_token(user)
    assert exc_info.value.status_code == 403


def test_list_dev_users_success(client, db_session):
    # Setup test users
    user1 = UserProfile(
        cognito_sub="dev-sub-1",
        email="dev1@example.com",
        first_name="Dev",
        last_name="One",
    )
    user2 = UserProfile(
        cognito_sub="dev-sub-2",
        email="dev2@example.com",
        first_name="Dev",
        last_name="Two",
    )
    db_session.add_all([user1, user2])
    db_session.flush()

    org = Organization(name="Dev Org", slug="dev-org-test", owner_id=user1.id)
    db_session.add(org)
    db_session.flush()

    membership = OrganizationMember(organization_id=org.id, user_id=user1.id, role="owner")
    db_session.add(membership)
    db_session.commit()

    resp = client.get("/api/v1/auth/dev-users")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    emails = [u["email"] for u in data]
    assert "dev1@example.com" in emails
    assert "dev2@example.com" in emails

    u1_entry = next(u for u in data if u["email"] == "dev1@example.com")
    assert len(u1_entry["organizations"]) >= 1
    assert u1_entry["organizations"][0]["slug"] == "dev-org-test"
    assert u1_entry["organizations"][0]["role"] == "owner"


def test_dev_login_existing_user(client, db_session):
    user = UserProfile(
        cognito_sub="dev-sub-existing",
        email="existing@example.com",
        first_name="Ana",
        last_name="Dev",
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post("/api/v1/auth/dev-login", json={"email": "existing@example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "existing@example.com"
    assert data["user"]["first_name"] == "Ana"


def test_dev_login_auto_provisions_new_user(client, db_session):
    email = "fresh-new-dev@example.com"
    resp = client.post("/api/v1/auth/dev-login", json={"email": email})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == email

    # Verify user exists in database with settings
    user = db_session.query(UserProfile).filter_by(email=email).first()
    assert user is not None
    assert user.settings is not None


def test_dev_login_deleted_user_returns_400(client, db_session):
    user = UserProfile(
        cognito_sub="dev-sub-deleted",
        email="deleted@example.com",
        deleted_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post("/api/v1/auth/dev-login", json={"email": "deleted@example.com"})
    assert resp.status_code == 400
    assert "eliminada" in resp.json()["detail"]


def test_dev_endpoints_return_404_in_production(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    resp_get = client.get("/api/v1/auth/dev-users")
    assert resp_get.status_code == 404

    resp_post = client.post("/api/v1/auth/dev-login", json={"email": "any@example.com"})
    assert resp_post.status_code == 404


@pytest.mark.asyncio
async def test_cognito_jwt_authenticator_accepts_dev_token_in_dev(db_session):
    user = UserProfile(
        cognito_sub="sub-dev-auth-flow",
        email="flow@example.com",
        first_name="Flow",
        last_name="Tester",
    )
    db_session.add(user)
    db_session.commit()

    token = create_dev_access_token(user)
    authenticator = CognitoJwtAuthenticator()

    authenticated_user = await authenticator.authenticate(token)
    assert authenticated_user is not None
    assert authenticated_user.email == "flow@example.com"
    assert authenticated_user.cognito_sub == "sub-dev-auth-flow"
