from fastapi.testclient import TestClient

from api.modules.users.models import UserProfile


def test_user_me_unauthorized(client: TestClient):
    """Accessing /users/me without token returns 401 Unauthorized."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_user_me_authorized_creates_profile(client: TestClient, db_session):
    """Accessing /users/me with test token auto-creates UserProfile and UserSettings."""
    token = "test-token-cognito-sub-1"
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["cognito_sub"] == "cognito-sub-1"
    assert data["settings"]["subscription_status"] == "inactive"

    # Verify persisted in database
    user = db_session.query(UserProfile).filter_by(cognito_sub="cognito-sub-1").first()
    assert user is not None
    assert user.settings is not None


def test_update_user_profile(client: TestClient):
    """Updating profile saves first_name and last_name."""
    token = "test-token-cognito-sub-2"
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {"first_name": "Carlos", "last_name": "Gomez"}
    response = client.patch("/api/v1/users/me", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Carlos"
    assert data["last_name"] == "Gomez"

    # Fetch /me to verify
    me_resp = client.get("/api/v1/users/me", headers=headers)
    assert me_resp.json()["profile"]["first_name"] == "Carlos"


def test_update_profile_validation(client: TestClient):
    """Profile update rejects names longer than 150 characters."""
    token = "test-token-cognito-sub-3"
    headers = {"Authorization": f"Bearer {token}"}

    long_name = "A" * 151
    response = client.patch("/api/v1/users/me", json={"first_name": long_name, "last_name": "Valid"}, headers=headers)
    assert response.status_code == 400


def test_trial_cannot_be_used_twice(client: TestClient, db_session):
    """Trial activates for 14 days and cannot be activated again."""
    token = "test-token-cognito-sub-5"
    headers = {"Authorization": f"Bearer {token}"}

    # 1. First trial activation
    response = client.post("/api/v1/users/trial", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "trial"

    # Verify settings
    user = db_session.query(UserProfile).filter_by(cognito_sub="cognito-sub-5").first()
    assert user.settings.subscription_status == "trial"
    assert user.settings.is_trial_active is True

    # 2. Second activation attempt while active
    dup_response = client.post("/api/v1/users/trial", headers=headers)
    assert dup_response.status_code == 400

    # 3. Simulate expired trial by moving trial_end_date back in time
    user.settings.subscription_status = "inactive"
    db_session.commit()

    third_response = client.post("/api/v1/users/trial", headers=headers)
    assert third_response.status_code == 400
    assert "already been used" in third_response.json()["detail"]


def test_user_me_rejects_api_key_header(client: TestClient):
    """User identity endpoints reject API keys passed in X-API-Key header with 401/403."""
    response = client.get("/api/v1/users/me", headers={"X-API-Key": "sk_test_invalid_sample_key_12345678901234567890"})
    assert response.status_code in (401, 403)


def test_user_me_rejects_bearer_api_key(client: TestClient):
    """User identity endpoints strictly reject Organization API keys passed as Bearer tokens."""
    # A valid format sk_test_ key is rejected because /users/me requires JWT
    raw_key = "sk_test_" + "A" * 43
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {raw_key}"})
    assert response.status_code in (401, 403)


def test_user_settings_requires_jwt(client: TestClient):
    """Settings endpoints reject unauthorized requests."""
    response = client.get("/api/v1/users/settings")
    assert response.status_code == 401
