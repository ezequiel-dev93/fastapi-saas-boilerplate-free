from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.core.database import Base, get_db
from api.core.protocols import get_api_key_validator, get_jwt_authenticator
from api.main import app

# Use an in-memory SQLite database with StaticPool for fast, isolated tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all database tables for test session and clean up after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator:
    """Provide a clean transactional database session per test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session) -> Generator[TestClient, None, None]:
    """TestClient fixture with overridden database dependency."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override JWT authenticator for tests (uses mock token format with db persistence)
    class TestJwtAuthenticator:
        async def authenticate(self, token: str):
            from api.core.config import settings

            if settings.DEBUG and token.startswith("test-token-"):
                sub = token.replace("test-token-", "")
                from api.modules.users.models import UserProfile, UserSettings

                user = db_session.query(UserProfile).filter(UserProfile.cognito_sub == sub).first()
                if user and user.deleted_at is not None:
                    return None
                if not user:
                    user = UserProfile(
                        cognito_sub=sub,
                        email=f"{sub}@example.com",
                        first_name="Test",
                        last_name=sub.capitalize(),
                    )
                    db_session.add(user)
                    db_session.flush()
                    if not user.settings:
                        user_settings = UserSettings(user_id=user.id, subscription_status="inactive")
                        db_session.add(user_settings)
                    db_session.commit()
                    db_session.refresh(user)
                return user
            return None

    class NonClosingSession:
        def __init__(self, s):
            self._s = s

        def __getattr__(self, name):
            return getattr(self._s, name)

        def close(self):
            pass

    from api.core.protocols.identity import MockIdentityProvider, reset_identity_provider, set_identity_provider
    from api.modules.ai.services import AiChatService, get_ai_chat_service
    from api.modules.organizations.api_key_service import ApiKeyService, get_api_key_service

    test_key_service = ApiKeyService(session_factory=lambda: NonClosingSession(db_session))
    test_ai_service = AiChatService(session_factory=lambda: NonClosingSession(db_session))
    test_idp = MockIdentityProvider()
    set_identity_provider(test_idp, force=True)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_jwt_authenticator] = lambda: TestJwtAuthenticator()
    app.dependency_overrides[get_api_key_validator] = lambda: test_key_service
    app.dependency_overrides[get_api_key_service] = lambda: test_key_service
    app.dependency_overrides[get_ai_chat_service] = lambda: test_ai_service

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    reset_identity_provider()
