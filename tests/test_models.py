from datetime import datetime, timedelta, timezone

from api.modules.users.models import UserProfile, UserSettings


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
