from datetime import datetime, timedelta, timezone

from api.modules.billing.models import StripeCustomer, SubscriptionPlan
from api.modules.users.models import UserProfile, UserSettings


def test_create_subscription_plan(db_session):
    """Test creating and querying a subscription plan with JSON features."""
    plan = SubscriptionPlan(
        name="Pro Plan",
        slug="pro-monthly",
        description="Best for growing teams",
        price=29.99,
        interval="monthly",
        features=["Unlimited Projects", "Priority Support", "Analytics"],
        is_active=True,
    )
    db_session.add(plan)
    db_session.commit()

    saved = db_session.query(SubscriptionPlan).filter_by(slug="pro-monthly").first()
    assert saved is not None
    assert saved.name == "Pro Plan"
    assert float(saved.price) == 29.99
    assert len(saved.features) == 3
    assert "Priority Support" in saved.features


def test_user_profile_and_settings_relationship(db_session):
    """Test UserProfile and 1-to-1 UserSettings creation and relationship."""
    user = UserProfile(cognito_sub="sub-12345", email="developer@example.com", first_name="Jane", last_name="Doe")
    db_session.add(user)
    db_session.commit()

    settings = UserSettings(user_id=user.id, notify_comments=True, notify_updates=False, subscription_status="inactive")
    db_session.add(settings)
    db_session.commit()

    queried_user = db_session.query(UserProfile).filter_by(email="developer@example.com").first()
    assert queried_user.settings is not None
    assert queried_user.settings.notify_comments is True
    assert queried_user.settings.is_subscription_active is False


def test_subscription_active_property(db_session):
    """Test is_subscription_active calculation based on status and dates."""
    now = datetime.now(timezone.utc)
    user = UserProfile(cognito_sub="sub-active", email="active@example.com")
    db_session.add(user)
    db_session.commit()

    # Active subscription in future
    settings = UserSettings(
        user_id=user.id,
        subscription_status="active",
        subscription_start_date=now - timedelta(days=10),
        subscription_end_date=now + timedelta(days=20),
    )
    db_session.add(settings)
    db_session.commit()
    assert settings.is_subscription_active is True

    # Expired subscription
    settings.subscription_end_date = now - timedelta(days=1)
    db_session.commit()
    assert settings.is_subscription_active is False

    # Inactive status
    settings.subscription_status = "inactive"
    settings.subscription_end_date = now + timedelta(days=20)
    db_session.commit()
    assert settings.is_subscription_active is False


def test_stripe_customer_and_cascade_deletion(db_session):
    """Test StripeCustomer creation and cascade deletion with UserProfile."""
    user = UserProfile(cognito_sub="sub-stripe", email="stripe@example.com")
    db_session.add(user)
    db_session.commit()

    customer = StripeCustomer(
        user_id=user.id,
        stripe_customer_id="cus_test_123",
        stripe_subscription_id="sub_test_456",
        subscription_status="active",
    )
    db_session.add(customer)
    db_session.commit()

    assert user.stripe_customer.stripe_customer_id == "cus_test_123"

    # Cascade delete
    db_session.delete(user)
    db_session.commit()

    remaining_customer = db_session.query(StripeCustomer).filter_by(stripe_customer_id="cus_test_123").first()
    assert remaining_customer is None
