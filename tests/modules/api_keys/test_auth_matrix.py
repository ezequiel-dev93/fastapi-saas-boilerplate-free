"""Matriz de seguridad de la autenticación dual (JWT + API Key de organización).

Estos tests se escriben ANTES de la implementación (TDD): fallan hasta que
``api/core/security.py`` exponga:

    get_auth_context        -> AuthContext
    get_api_key_validator   -> dependencia placeholder (se sobreescribe en main.py / tests)
    get_jwt_authenticator   -> dependencia placeholder (idem)
    require_scope(scope)    -> guard de scope (+ coincidencia de org si hay {org_id} en la ruta)
    require_jwt             -> guard que solo acepta JWT
    get_current_user        -> wrapper existente; ahora exige kind == "jwt"

Supuestos a adaptar a tu repo: ``settings.ENVIRONMENT`` en ``api.core.config``
y el nombre de ``get_current_user``.
"""

import logging

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from api.core.auth_context import AuthContext, Scope
from api.core.config import settings
from api.core.database import get_db
from api.core.protocols import (
    get_api_key_validator,
    get_jwt_authenticator,
    reset_api_key_validator,
    reset_jwt_authenticator,
    set_api_key_validator,
    set_jwt_authenticator,
)
from api.core.security import (
    get_auth_context,
    get_current_user,
    require_jwt,
    require_scope,
)
from tests.fakes import (
    FakeApiKeyValidator,
    FakeJwtAuthenticator,
    FakeUser,
    make_raw_key,
)

JWT_TOKEN = "header.payload.signature"
ORG_ID = 1
OTHER_ORG_ID = 2


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def development_env(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")


@pytest.fixture(autouse=True)
def override_validators(validator, jwt_auth):
    """Configura los validadores globales para tests (usando force=True para permitir reconfiguración)."""
    set_api_key_validator(validator, force=True)
    set_jwt_authenticator(jwt_auth, force=True)
    yield
    reset_api_key_validator()
    reset_jwt_authenticator()


@pytest.fixture
def validator() -> FakeApiKeyValidator:
    return FakeApiKeyValidator()


@pytest.fixture
def jwt_auth() -> FakeJwtAuthenticator:
    fake = FakeJwtAuthenticator()
    fake.add(JWT_TOKEN, FakeUser())
    return fake


@pytest.fixture
def app(validator, jwt_auth) -> FastAPI:
    """Create test app with all dependencies overridden."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Create tables
    from api.core.database import Base

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_api_key_validator] = lambda: validator
    app.dependency_overrides[get_jwt_authenticator] = lambda: jwt_auth

    @app.get("/whoami")
    async def whoami(ctx: AuthContext = Depends(get_auth_context)):
        return {
            "kind": ctx.kind,
            "org_id": ctx.org_id,
            "api_key_id": ctx.api_key_id,
            "scopes": sorted(s.value for s in ctx.scopes) if ctx.scopes is not None else None,
        }

    @app.get("/state")
    async def state(request: Request, ctx: AuthContext = Depends(get_auth_context)):
        # El rate limiter y las quotas leen estos valores sin ir a la base.
        return {
            "api_key_id": getattr(request.state, "api_key_id", None),
            "org_id": getattr(request.state, "org_id", None),
        }

    @app.get("/orgs/{org_id}/members")
    async def read_members(org_id: int, ctx: AuthContext = Depends(require_scope(Scope.MEMBERS_READ))):
        return {"ok": True}

    @app.post("/orgs/{org_id}/members")
    async def write_members(org_id: int, ctx: AuthContext = Depends(require_scope(Scope.MEMBERS_WRITE))):
        return {"ok": True}

    @app.get("/orgs/{org_id}/api-keys")
    async def list_api_keys(org_id: int, ctx: AuthContext = Depends(require_jwt)):
        return {"ok": True}

    @app.get("/legacy")
    async def legacy(user=Depends(get_current_user)):
        return {"ok": True}

    return app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.fixture
def raw_key(validator) -> str:
    """Key válida de la org 1, solo con members:read (key_id=10)."""
    key = make_raw_key("test")
    validator.add(key, org_id=ORG_ID, scopes={Scope.MEMBERS_READ}, key_id=10)
    return key


def api_key_header(key: str) -> dict:
    return {"X-API-Key": key}


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------- #
# Extracción y decisión de credencial
# --------------------------------------------------------------------------- #
class TestCredentialExtraction:
    def test_missing_credentials_returns_401(self, client):
        assert client.get("/whoami").status_code == 401

    def test_valid_jwt_returns_jwt_context(self, client):
        response = client.get("/whoami", headers=bearer(JWT_TOKEN))
        assert response.status_code == 200
        assert response.json() == {"kind": "jwt", "org_id": None, "api_key_id": None, "scopes": None}

    def test_invalid_jwt_returns_401(self, client):
        assert client.get("/whoami", headers=bearer("not.a.valid-jwt")).status_code == 401

    def test_api_key_via_x_api_key_header(self, client, raw_key):
        response = client.get("/whoami", headers=api_key_header(raw_key))
        assert response.status_code == 200
        assert response.json() == {
            "kind": "api_key",
            "org_id": ORG_ID,
            "api_key_id": 10,
            "scopes": ["members:read"],
        }

    def test_api_key_via_bearer_header(self, client, raw_key):
        response = client.get("/whoami", headers=bearer(raw_key))
        assert response.status_code == 200
        assert response.json()["kind"] == "api_key"

    def test_both_credentials_at_once_returns_400(self, client, raw_key, validator, jwt_auth):
        headers = {**api_key_header(raw_key), **bearer(JWT_TOKEN)}
        assert client.get("/whoami", headers=headers).status_code == 400
        assert validator.calls == [] and jwt_auth.calls == []

    def test_sk_prefixed_bearer_is_never_tried_as_jwt(self, client, raw_key, jwt_auth):
        client.get("/whoami", headers=bearer(raw_key))
        assert jwt_auth.calls == []

    def test_non_api_key_value_in_x_api_key_is_rejected_and_not_tried_as_jwt(self, client, jwt_auth):
        response = client.get("/whoami", headers=api_key_header(JWT_TOKEN))
        assert response.status_code == 401
        assert jwt_auth.calls == []


# --------------------------------------------------------------------------- #
# Fallos de API Key: uniformes y baratos
# --------------------------------------------------------------------------- #
MALFORMED_KEYS = [
    "sk_test_",  # sin parte aleatoria
    "sk_test_short",  # demasiado corta
    "sk_prod_" + "A" * 43,  # entorno desconocido
    "sk_test_" + "A" * 42 + "!",  # carácter fuera del alfabeto urlsafe
    "sk_test_" + "A" * 44,  # demasiado larga
]


class TestApiKeyFailures:
    def test_unknown_key_returns_401(self, client, validator):
        response = client.get("/whoami", headers=api_key_header(make_raw_key("test")))
        assert response.status_code == 401
        assert len(validator.calls) == 1

    @pytest.mark.parametrize("key", MALFORMED_KEYS)
    def test_malformed_key_returns_401_without_touching_the_validator(self, client, validator, key):
        response = client.get("/whoami", headers=api_key_header(key))
        assert response.status_code == 401
        assert validator.calls == []

    def test_all_key_failures_look_identical(self, client):
        unknown = client.get("/whoami", headers=api_key_header(make_raw_key("test")))
        malformed = client.get("/whoami", headers=api_key_header("sk_test_short"))
        assert unknown.status_code == malformed.status_code == 401
        assert unknown.json() == malformed.json()
        assert unknown.headers.get("www-authenticate") == malformed.headers.get("www-authenticate")

    @pytest.mark.parametrize(
        ("environment", "key_env"),
        [("production", "test"), ("development", "live"), ("staging", "live")],
    )
    def test_environment_mismatch_returns_401_without_touching_the_validator(
        self, client, validator, monkeypatch, environment, key_env
    ):
        monkeypatch.setattr(settings, "ENVIRONMENT", environment)
        key = make_raw_key(key_env)
        validator.add(key, org_id=ORG_ID, scopes={Scope.MEMBERS_READ})  # existe y es válida
        response = client.get("/whoami", headers=api_key_header(key))
        assert response.status_code == 401
        assert validator.calls == []

    def test_live_key_works_in_production(self, client, validator, monkeypatch):
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")
        key = make_raw_key("live")
        validator.add(key, org_id=ORG_ID, scopes={Scope.MEMBERS_READ})
        assert client.get("/whoami", headers=api_key_header(key)).status_code == 200

    def test_raw_key_is_never_logged(self, client, caplog):
        # Nota: si tu logger tiene propagate=False, caplog no lo ve y este
        # test pasaría en falso; en ese caso adjuntá el handler de caplog.
        key = make_raw_key("test")
        with caplog.at_level(logging.DEBUG):
            client.get("/whoami", headers=api_key_header(key))
        assert key not in caplog.text


# --------------------------------------------------------------------------- #
# Scopes, organización y rutas solo-JWT
# --------------------------------------------------------------------------- #
class TestScopesAndOrganization:
    def test_key_with_required_scope_and_same_org_is_allowed(self, client, raw_key):
        response = client.get(f"/orgs/{ORG_ID}/members", headers=api_key_header(raw_key))
        assert response.status_code == 200

    def test_key_without_required_scope_gets_403(self, client, raw_key):
        response = client.post(f"/orgs/{ORG_ID}/members", headers=api_key_header(raw_key))
        assert response.status_code == 403

    def test_key_from_another_org_gets_403(self, client, raw_key):
        response = client.get(f"/orgs/{OTHER_ORG_ID}/members", headers=api_key_header(raw_key))
        assert response.status_code == 403

    def test_jwt_is_not_restricted_by_scopes(self, client):
        # Para JWT los permisos los resuelve el rol (require_org_role), no los scopes.
        response = client.get(f"/orgs/{ORG_ID}/members", headers=bearer(JWT_TOKEN))
        assert response.status_code == 200

    def test_jwt_only_route_rejects_api_keys(self, client, validator):
        key = make_raw_key("test")
        validator.add(key, org_id=ORG_ID, scopes=set(Scope))  # incluso con todos los scopes
        response = client.get(f"/orgs/{ORG_ID}/api-keys", headers=api_key_header(key))
        assert response.status_code == 403

    def test_jwt_only_route_accepts_jwt(self, client):
        assert client.get(f"/orgs/{ORG_ID}/api-keys", headers=bearer(JWT_TOKEN)).status_code == 200

    def test_legacy_get_current_user_is_deny_by_default_for_api_keys(self, client, raw_key):
        # Las rutas existentes siguen siendo solo-JWT salvo que declaren require_scope.
        assert client.get("/legacy", headers=api_key_header(raw_key)).status_code == 403

    def test_legacy_get_current_user_still_works_with_jwt(self, client):
        assert client.get("/legacy", headers=bearer(JWT_TOKEN)).status_code == 200


# --------------------------------------------------------------------------- #
# Datos para rate limiting y quotas
# --------------------------------------------------------------------------- #
class TestRequestState:
    def test_api_key_populates_request_state(self, client, raw_key):
        response = client.get("/state", headers=api_key_header(raw_key))
        assert response.json() == {"api_key_id": 10, "org_id": ORG_ID}

    def test_jwt_leaves_api_key_state_empty(self, client):
        response = client.get("/state", headers=bearer(JWT_TOKEN))
        assert response.json() == {"api_key_id": None, "org_id": None}
