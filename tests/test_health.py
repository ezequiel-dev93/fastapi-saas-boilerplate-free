from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Verify that the health check endpoint returns 200, status ok, and database connected."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "project" in data


def test_health_check_database_failure():
    """Verify that 503 is returned when database connection fails."""
    from unittest.mock import MagicMock

    from api.core.database import get_db
    from api.main import app

    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("DB Connection Refused")

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with TestClient(app) as test_client:
            response = test_client.get("/health")
            assert response.status_code == 503
            assert "Database connection failed" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_root_endpoint(client: TestClient):
    """Verify that the root endpoint returns API information and documentation link."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs" in data
    assert "health" in data
    assert data["version"] == "1.0.0"


def test_request_id_middleware_generates_header(client: TestClient):
    """Verify that API responses automatically include an X-Request-ID header."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_request_id_middleware_preserves_custom_header(client: TestClient):
    """Verify that an incoming X-Request-ID header is propagated to the response."""
    custom_trace_id = "trace-custom-uuid-123456"
    response = client.get("/health", headers={"X-Request-ID": custom_trace_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_trace_id
