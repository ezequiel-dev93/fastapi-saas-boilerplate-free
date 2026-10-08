from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.modules.billing.models import StripeCustomer, SubscriptionPlan
from api.modules.billing.stripe_service import sync_access
from api.modules.users.models import UserProfile, UserSettings


def test_list_subscription_plans_public(client: TestClient, db_session):
    """Listing plans is public and filters only active plans."""
    plan1 = SubscriptionPlan(name="Starter", slug="starter", price=10.0, interval="monthly", is_active=True)
    plan2 = SubscriptionPlan(name="Hidden", slug="hidden", price=99.0, interval="monthly", is_active=False)
    db_session.add_all([plan1, plan2])
    db_session.commit()

    response = client.get("/api/v1/billing/plans")
    assert response.status_code == 200
    plans = response.json()
    slugs = [p["slug"] for p in plans]
    assert "starter" in slugs
    assert "hidden" not in slugs


def test_sync_access_status_mapping(db_session):
    """STATUS_MAP correctly maps Stripe statuses to local access states."""
    user = UserProfile(cognito_sub="sync-sub-1", email="sync@example.com")
    db_session.add(user)
    db_session.commit()

    # Active
    settings = sync_access(db_session, user, "active")
    assert settings.subscription_status == "active"
    assert settings.subscription_start_date is not None

    # past_due stays active to prevent premature lockout
    settings = sync_access(db_session, user, "past_due")
    assert settings.subscription_status == "active"

    # canceled
    settings = sync_access(db_session, user, "canceled")
    assert settings.subscription_status == "cancelled"

    # unpaid
    settings = sync_access(db_session, user, "unpaid")
    assert settings.subscription_status == "inactive"


@patch("stripe.Customer.create")
@patch("stripe.PaymentMethod.attach")
@patch("stripe.Customer.modify")
@patch("stripe.Subscription.create")
def test_checkout_creates_subscription_and_syncs(
    mock_sub_create, mock_cust_modify, mock_pm_attach, mock_cust_create, client: TestClient, db_session
):
    """Checkout attaches payment method, creates subscription, and syncs user access."""
    token = "test-token-stripe-user-1"
    headers = {"Authorization": f"Bearer {token}"}

    # Setup mocks
    mock_cust_create.return_value = MagicMock(id="cus_mock_999")
    mock_subscription = MagicMock(
        id="sub_mock_888",
        status="active",
        items=MagicMock(data=[MagicMock(current_period_end=1800000000)]),
        latest_invoice=MagicMock(confirmation_secret=MagicMock(client_secret="secret_abc123")),
    )
    mock_sub_create.return_value = mock_subscription

    payload = {"payment_method_id": "pm_mock_card", "price_id": "price_pro_monthly"}

    response = client.post("/api/v1/billing/checkout", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["subscription_id"] == "sub_mock_888"
    assert data["client_secret"] == "secret_abc123"
    assert data["status"] == "active"

    # Verify database synchronization
    user = db_session.query(UserProfile).filter_by(cognito_sub="stripe-user-1").first()
    assert user.stripe_customer.stripe_customer_id == "cus_mock_999"
    assert user.stripe_customer.stripe_subscription_id == "sub_mock_888"
    assert user.settings.subscription_status == "active"
    assert user.settings.is_subscription_active is True


@patch("stripe.Subscription.modify")
def test_cancel_subscription_at_period_end(mock_sub_modify, client: TestClient, db_session):
    """Cancelling a subscription marks cancel_at_period_end on Stripe."""
    token = "test-token-stripe-user-2"
    headers = {"Authorization": f"Bearer {token}"}

    # Pre-create user with Stripe customer
    user = UserProfile(cognito_sub="stripe-user-2", email="user2@example.com")
    db_session.add(user)
    db_session.flush()

    customer = StripeCustomer(
        user_id=user.id,
        stripe_customer_id="cus_user2",
        stripe_subscription_id="sub_user2",
        subscription_status="active",
    )
    db_session.add(customer)
    db_session.commit()

    response = client.post("/api/v1/billing/cancel", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled_at_period_end"

    mock_sub_modify.assert_called_once_with("sub_user2", cancel_at_period_end=True)


@patch("stripe.billing_portal.Session.create")
def test_create_customer_portal_url(mock_portal_create, client: TestClient, db_session):
    """Creating customer portal returns temporary Stripe portal session URL."""
    token = "test-token-stripe-user-3"
    headers = {"Authorization": f"Bearer {token}"}

    user = UserProfile(cognito_sub="stripe-user-3", email="user3@example.com")
    db_session.add(user)
    db_session.flush()

    customer = StripeCustomer(
        user_id=user.id,
        stripe_customer_id="cus_user3",
        stripe_subscription_id="sub_user3",
        subscription_status="active",
    )
    db_session.add(customer)
    db_session.commit()

    mock_portal_create.return_value = MagicMock(url="https://billing.stripe.com/p/session_mock")

    response = client.post("/api/v1/billing/portal", json={}, headers=headers)
    assert response.status_code == 200
    assert response.json()["url"] == "https://billing.stripe.com/p/session_mock"


def test_webhook_rejects_invalid_signature(client: TestClient):
    """Webhook rejects calls with invalid or missing signature."""
    response = client.post("/api/v1/billing/webhook", content=b"{}", headers={"stripe-signature": "bad_sig"})
    assert response.status_code == 400


@patch("stripe.Webhook.construct_event")
def test_webhook_updates_subscription_and_access(mock_construct_event, client: TestClient, db_session):
    """Webhook receives subscription update from Stripe and syncs local UserSettings."""
    # Pre-create user and Stripe customer
    user = UserProfile(cognito_sub="webhook-user", email="webhook@example.com")
    db_session.add(user)
    db_session.flush()

    settings = UserSettings(user_id=user.id, subscription_status="active")
    customer = StripeCustomer(
        user_id=user.id, stripe_customer_id="cus_wh_1", stripe_subscription_id="sub_wh_1", subscription_status="active"
    )
    db_session.add_all([settings, customer])
    db_session.commit()

    # Mock incoming Stripe webhook event: canceled
    mock_construct_event.return_value = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_wh_1", "status": "canceled"}},
    }

    response = client.post(
        "/api/v1/billing/webhook", content=b'{"mock": "payload"}', headers={"stripe-signature": "valid_signature"}
    )
    assert response.status_code == 200

    # Verify customer and user settings were updated
    db_session.refresh(customer)
    db_session.refresh(settings)
    assert customer.subscription_status == "canceled"
    assert settings.subscription_status == "cancelled"
    assert settings.is_subscription_active is False


@patch("stripe.Webhook.construct_event")
def test_webhook_idempotency_prevents_duplicate_processing(mock_construct_event, client: TestClient, db_session):
    """Sending the same Stripe webhook event twice is handled idempotently without re-processing."""
    from api.modules.billing.models import StripeWebhookEvent

    user = UserProfile(cognito_sub="webhook-idemp-user", email="webhook_idemp@example.com")
    db_session.add(user)
    db_session.flush()

    settings = UserSettings(user_id=user.id, subscription_status="inactive")
    customer = StripeCustomer(
        user_id=user.id,
        stripe_customer_id="cus_idemp_1",
        stripe_subscription_id="sub_idemp_1",
        subscription_status="inactive",
    )
    db_session.add_all([settings, customer])
    db_session.commit()

    event_id = "evt_test_idempotency_123"
    mock_construct_event.return_value = {
        "id": event_id,
        "type": "customer.subscription.updated",
        "data": {"object": {"id": "sub_idemp_1", "status": "active"}},
    }

    # First call: processes and records StripeWebhookEvent
    resp1 = client.post(
        "/api/v1/billing/webhook", content=b'{"mock": "payload"}', headers={"stripe-signature": "valid_sig"}
    )
    assert resp1.status_code == 200

    saved_event = db_session.query(StripeWebhookEvent).filter_by(event_id=event_id).first()
    assert saved_event is not None
    assert saved_event.event_type == "customer.subscription.updated"

    # Second call with the same event_id: returns already_processed
    resp2 = client.post(
        "/api/v1/billing/webhook", content=b'{"mock": "payload"}', headers={"stripe-signature": "valid_sig"}
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "already_processed"
    assert resp2.json()["event_id"] == event_id

    # Verify no duplicate records created
    count = db_session.query(StripeWebhookEvent).filter_by(event_id=event_id).count()
    assert count == 1
