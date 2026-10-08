import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.core.auth_context import DEFAULT_SCOPES_BY_ROLE, Scope
from api.core.config import Settings
from api.modules.billing.models import SubscriptionPlan
from api.modules.organizations.models import Organization
from api.modules.users.models import UserProfile, utcnow


def test_scope_ai_generate_definitions():
    """Verify Scope.AI_GENERATE and role permissions."""
    assert Scope.AI_GENERATE.value == "ai:generate"
    assert Scope.AI_GENERATE in DEFAULT_SCOPES_BY_ROLE["owner"]
    assert Scope.AI_GENERATE in DEFAULT_SCOPES_BY_ROLE["admin"]
    assert Scope.AI_GENERATE not in DEFAULT_SCOPES_BY_ROLE["member"]


def test_ai_settings_validation():
    """Verify AI configuration defaults and environment validation."""
    # Default is mock in development
    s = Settings()
    assert s.AI_PROVIDER == "mock"
    assert "gpt-4o" in s.AI_ALLOWED_MODELS
    assert s.AI_MAX_MESSAGES == 50
    assert s.AI_MAX_INPUT_CHARS == 16000

    # Invalid provider raises error
    with pytest.raises(ValidationError):
        Settings(AI_PROVIDER="unknown_provider")

    # Mock in production is forbidden (D-02)
    with pytest.raises(ValidationError) as exc_info:
        Settings(ENVIRONMENT="production", AI_PROVIDER="mock")
    assert "está estrictamente prohibido en producción" in str(exc_info.value)

    # Real provider in production is allowed
    prod_s = Settings(ENVIRONMENT="production", AI_PROVIDER="openai")
    assert prod_s.AI_PROVIDER == "openai"


def test_m0_models_columns(db_session: Session):
    """Verify limits, organization periods, and user deleted_at columns."""
    user = UserProfile(
        cognito_sub="test-m0-user",
        email="m0@example.com",
        first_name="Foundation",
        last_name="Test",
    )
    db_session.add(user)
    db_session.flush()

    assert user.deleted_at is None
    now = utcnow()
    user.deleted_at = now
    db_session.commit()

    queried_user = db_session.query(UserProfile).filter_by(id=user.id).first()
    assert queried_user.deleted_at is not None

    plan = SubscriptionPlan(
        name="AI Pro",
        slug="ai-pro",
        price=49.00,
        limits={"ai_messages": 500, "members": 10},
    )
    db_session.add(plan)
    db_session.commit()

    queried_plan = db_session.query(SubscriptionPlan).filter_by(slug="ai-pro").first()
    assert queried_plan.limits == {"ai_messages": 500, "members": 10}

    org = Organization(
        name="AI Startup",
        slug="ai-startup",
        owner_id=user.id,
        subscription_plan_id=plan.id,
        subscription_status="active",
        current_period_start=now,
        current_period_end=now,
    )
    db_session.add(org)
    db_session.commit()

    queried_org = db_session.query(Organization).filter_by(slug="ai-startup").first()
    assert queried_org.current_period_start is not None
    assert queried_org.current_period_end is not None
