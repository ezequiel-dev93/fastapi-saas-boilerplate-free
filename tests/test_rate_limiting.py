from fastapi.testclient import TestClient

from api.core.limiter import limiter


def test_rate_limiting_triggers_429(client: TestClient):
    """Exceeding endpoint rate limit returns 429 Too Many Requests."""
    limiter.reset()
    token = "test-token-rate-limit-user"
    headers = {"Authorization": f"Bearer {token}"}

    responses = []
    # Endpoint /users/trial has a limit of 5/minute
    for _ in range(6):
        res = client.post("/api/v1/users/trial", headers=headers)
        responses.append(res.status_code)

    # First 5 are processed (200 or 400 for duplicate trial), the 6th must return 429 Too Many Requests
    assert all(code != 429 for code in responses[:5])
    assert responses[5] == 429

    # Clean up limiter state for subsequent tests
    limiter.reset()
