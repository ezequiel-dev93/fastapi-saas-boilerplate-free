from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.core.auth_context import Scope
from api.main import app
from api.modules.billing.models import StripeCustomer, SubscriptionPlan
from api.modules.organizations.api_key_service import get_api_key_service
from api.modules.organizations.models import Organization, OrganizationMember
from api.modules.usage.dependencies import consume_quota
from api.modules.usage.services import UsageService, get_usage_service, utcnow
from api.modules.users.models import UserProfile, UserSettings

# Router de prueba para verificar la dependencia consume_quota
dummy_quota_router = APIRouter()


@dummy_quota_router.post("/api/v1/test-quota/consume/{org_id}")
async def dummy_quota_endpoint(
    org_id: int,
    quota=Depends(consume_quota("ai_messages", 1)),
):
    return {"message": "Consumo exitoso", "used": quota.used}


app.include_router(dummy_quota_router)


def test_usage_period_calendar_and_stripe(db_session: Session):
    """Verifica el cálculo del ciclo de facturación (fallback calendario UTC vs Stripe)."""
    usage_service = UsageService()

    owner = UserProfile(cognito_sub="period-owner", email="period@example.com", first_name="Period", last_name="Test")
    db_session.add(owner)
    db_session.flush()

    # 1. Fallback: sin fechas de Stripe -> mes calendario en UTC (D-06)
    org_fallback = Organization(
        name="Calendar Org",
        slug="cal-org",
        owner_id=owner.id,
        subscription_status="active",
    )
    db_session.add(org_fallback)
    db_session.commit()

    start, end = usage_service.current_period(org_fallback)
    now = utcnow()
    assert start.year == now.year
    assert start.month == now.month
    assert start.day == 1
    assert start.tzinfo == timezone.utc
    assert end.tzinfo == timezone.utc
    assert end > start

    # 2. Organización con ciclo de Stripe vigente
    stripe_start = now - timedelta(days=5)
    stripe_end = now + timedelta(days=25)
    org_stripe = Organization(
        name="Stripe Org",
        slug="stripe-org",
        owner_id=owner.id,
        subscription_status="active",
        current_period_start=stripe_start,
        current_period_end=stripe_end,
    )
    db_session.add(org_stripe)
    db_session.commit()

    s_start, s_end = usage_service.current_period(org_stripe)
    assert s_start == stripe_start
    assert s_end == stripe_end


def test_usage_get_limit(db_session: Session):
    """Verifica resolución de límites (numérico, null=ilimitado, ausente=0)."""
    usage_service = UsageService()

    plan = SubscriptionPlan(
        name="Pro Plan",
        slug="pro-plan-limits",
        price=49.00,
        limits={
            "ai_messages": 500,
            "members": None,  # null = ilimitado (D-07)
        },
    )
    db_session.add(plan)
    db_session.flush()

    owner = UserProfile(cognito_sub="lim-owner", email="lim@example.com", first_name="Lim", last_name="Test")
    db_session.add(owner)
    db_session.flush()

    org = Organization(
        name="Limits Org",
        slug="limits-org",
        owner_id=owner.id,
        subscription_plan_id=plan.id,
        subscription_status="active",
    )
    db_session.add(org)
    db_session.commit()

    # Métrica configurada con número
    assert usage_service.get_limit(db_session, org, "ai_messages") == 500
    # Métrica configurada con None (ilimitado)
    assert usage_service.get_limit(db_session, org, "members") is None
    # Clave ausente -> 0 (falla cerrado, D-07)
    assert usage_service.get_limit(db_session, org, "unknown_feature") == 0


def test_usage_consume_and_refund(db_session: Session):
    """Verifica consumo atómico secuencial, bloqueo al alcanzar el límite y reembolsos."""
    usage_service = UsageService()

    plan = SubscriptionPlan(
        name="Mini Plan",
        slug="mini-plan",
        price=10.00,
        limits={"ai_messages": 5},
    )
    db_session.add(plan)
    db_session.flush()

    owner = UserProfile(cognito_sub="mini-owner", email="mini@example.com", first_name="Mini", last_name="Owner")
    db_session.add(owner)
    db_session.flush()

    org = Organization(
        name="Mini Org",
        slug="mini-org",
        owner_id=owner.id,
        subscription_plan_id=plan.id,
        subscription_status="active",
    )
    db_session.add(org)
    db_session.commit()

    # 1. Consumir 3 de 5 -> OK
    res1 = usage_service.consume(db_session, org.id, "ai_messages", amount=3)
    assert res1.allowed is True
    assert res1.used == 3
    assert res1.limit == 5

    # 2. Consumir 2 restantes de 5 -> OK, llega al límite (5/5)
    res2 = usage_service.consume(db_session, org.id, "ai_messages", amount=2)
    assert res2.allowed is True
    assert res2.used == 5

    # 3. Consumir 1 adicional -> Bloqueado (allowed=False, used permanece en 5)
    res3 = usage_service.consume(db_session, org.id, "ai_messages", amount=1)
    assert res3.allowed is False
    assert res3.used == 5
    assert res3.limit == 5

    # 4. Reembolsar 2 unidades (ej: fallo de red del proveedor antes de emitir tokens, D-08)
    usage_service.refund(db_session, org.id, "ai_messages", amount=2)

    # 5. Consumir 1 unidad nuevamente -> OK
    res4 = usage_service.consume(db_session, org.id, "ai_messages", amount=1)
    assert res4.allowed is True
    assert res4.used == 4

    # 6. Reembolsar más de lo consumido no debe generar valores negativos
    usage_service.refund(db_session, org.id, "ai_messages", amount=10)
    res5 = usage_service.consume(db_session, org.id, "ai_messages", amount=1)
    assert res5.allowed is True
    assert res5.used == 1


def test_usage_unlimited_and_zero_limits(db_session: Session):
    """Verifica métricas ilimitadas (None) y métricas con cupo 0."""
    usage_service = UsageService()

    plan = SubscriptionPlan(
        name="Custom Plan",
        slug="custom-plan",
        price=99.00,
        limits={
            "ai_messages": None,  # ilimitado
            "restricted_op": 0,  # sin cupo
        },
    )
    db_session.add(plan)
    db_session.flush()

    owner = UserProfile(cognito_sub="cust-owner", email="cust@example.com", first_name="Cust", last_name="Owner")
    db_session.add(owner)
    db_session.flush()

    org = Organization(
        name="Custom Org",
        slug="custom-org",
        owner_id=owner.id,
        subscription_plan_id=plan.id,
        subscription_status="active",
    )
    db_session.add(org)
    db_session.commit()

    # Consumo en métrica ilimitada
    res_unlimited = usage_service.consume(db_session, org.id, "ai_messages", amount=100)
    assert res_unlimited.allowed is True
    assert res_unlimited.limit is None
    assert res_unlimited.used == 100

    # Consumo en métrica con cupo 0 -> rechaza de inmediato sin escribir en BD
    res_zero = usage_service.consume(db_session, org.id, "restricted_op", amount=1)
    assert res_zero.allowed is False
    assert res_zero.limit == 0
    assert res_zero.used == 0


def test_usage_high_concurrency():
    """
    Verifica atomicidad bajo alta concurrencia (D-09):
    10 hilos intentan consumir simultáneamente 1 unidad con cupo máximo de 5.
    Exactamente 5 deben tener éxito y 5 deben ser rechazados.
    El contador final en BD no debe exceder 5 bajo ninguna circunstancia.
    """
    import os
    import tempfile

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from api.core.database import Base

    usage_service = UsageService()

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    tmp_engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"timeout": 30, "check_same_thread": False},
    )
    try:
        Base.metadata.create_all(bind=tmp_engine)
        TmpSessionLocal = sessionmaker(bind=tmp_engine)

        setup_session = TmpSessionLocal()
        plan = SubscriptionPlan(
            name="Concurrent Plan",
            slug="concurrent-plan",
            price=20.00,
            limits={"ai_messages": 5},
        )
        setup_session.add(plan)
        setup_session.flush()

        owner = UserProfile(cognito_sub="conc-owner", email="conc@example.com", first_name="Conc", last_name="Owner")
        setup_session.add(owner)
        setup_session.flush()

        org = Organization(
            name="Conc Org",
            slug="conc-org",
            owner_id=owner.id,
            subscription_plan_id=plan.id,
            subscription_status="active",
        )
        setup_session.add(org)
        setup_session.commit()
        org_id = org.id
        setup_session.close()

        def worker_consume():
            session = TmpSessionLocal()
            try:
                res = usage_service.consume(session, org_id, "ai_messages", amount=1)
                return res.allowed
            finally:
                session.close()

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: worker_consume(), range(10)))

        successes = sum(1 for r in results if r is True)
        rejections = sum(1 for r in results if r is False)

        assert successes == 5
        assert rejections == 5

        # Verificación consolidada en la base de datos
        verify_session = TmpSessionLocal()
        summary = usage_service.summary(verify_session, org_id)
        metric_stat = next(m for m in summary.metrics if m.metric == "ai_messages")
        assert metric_stat.used == 5
        assert metric_stat.limit == 5
        assert metric_stat.remaining == 0
        verify_session.close()
    finally:
        tmp_engine.dispose()
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


def test_consume_quota_dependency_http_402(client: TestClient, db_session: Session):
    """Verifica que agotar el cupo vía dependencia HTTP retorne 402 con payload estructurado (D-04)."""
    plan = SubscriptionPlan(
        name="HTTP Quota Plan",
        slug="http-quota-plan",
        price=15.00,
        limits={"ai_messages": 2},
    )
    db_session.add(plan)
    db_session.flush()

    owner = UserProfile(cognito_sub="http-quota-owner", email="httpq@example.com", first_name="HQ", last_name="Owner")
    db_session.add(owner)
    db_session.flush()

    org = Organization(
        name="HTTP Quota Org",
        slug="http-quota-org",
        owner_id=owner.id,
        subscription_plan_id=plan.id,
        subscription_status="active",
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner")
    db_session.add(member)
    db_session.commit()

    headers = {
        "Authorization": "Bearer test-token-http-quota-owner",
        "X-Organization-ID": str(org.id),
    }

    # Request 1: 1/2 -> 200 OK
    resp1 = client.post(f"/api/v1/test-quota/consume/{org.id}", headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["used"] == 1

    # Request 2: 2/2 -> 200 OK
    resp2 = client.post(f"/api/v1/test-quota/consume/{org.id}", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["used"] == 2

    # Request 3: 3/2 -> 402 Payment Required con payload estructurado
    resp3 = client.post(f"/api/v1/test-quota/consume/{org.id}", headers=headers)
    assert resp3.status_code == 402
    body = resp3.json()
    assert body["code"] == "quota_exceeded"
    assert body["metric"] == "ai_messages"
    assert body["limit"] == 2
    assert body["used"] == 2
    assert "resets_at" in body
    assert "Has alcanzado el límite mensual" in body["message"]


def test_get_organization_usage_endpoint(client: TestClient, db_session: Session):
    """Verifica el endpoint GET /organizations/{org_id}/usage para JWT y API Key."""
    plan = SubscriptionPlan(
        name="Usage Plan",
        slug="usage-plan",
        price=30.00,
        limits={"ai_messages": 100, "members": 5},
    )
    db_session.add(plan)
    db_session.flush()

    owner = UserProfile(cognito_sub="usage-owner", email="uowner@example.com", first_name="U", last_name="Owner")
    db_session.add(owner)
    db_session.flush()

    org = Organization(
        name="Usage Org",
        slug="usage-org",
        owner_id=owner.id,
        subscription_plan_id=plan.id,
        subscription_status="active",
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner")
    db_session.add(member)
    db_session.commit()

    # 1. Consumir algo de uso
    usage_service = get_usage_service()
    usage_service.consume(db_session, org.id, "ai_messages", amount=15)

    # 2. Acceso vía JWT (Owner)
    jwt_headers = {"Authorization": "Bearer test-token-usage-owner"}
    resp_jwt = client.get(f"/api/v1/organizations/{org.id}/usage", headers=jwt_headers)
    assert resp_jwt.status_code == 200
    data_jwt = resp_jwt.json()
    assert data_jwt["organization_id"] == org.id
    assert "period_start" in data_jwt
    assert "period_end" in data_jwt

    ai_metric = next(m for m in data_jwt["metrics"] if m["metric"] == "ai_messages")
    assert ai_metric["used"] == 15
    assert ai_metric["limit"] == 100
    assert ai_metric["remaining"] == 85

    members_metric = next(m for m in data_jwt["metrics"] if m["metric"] == "members")
    assert members_metric["used"] == 1  # Solo el owner
    assert members_metric["limit"] == 5
    assert members_metric["remaining"] == 4

    # 3. Acceso vía API Key con scope members:read
    key_service = get_api_key_service()
    _, raw_key = key_service.create_api_key(
        db_session,
        org.id,
        owner,
        "owner",
        "Usage Audit Key",
        [Scope.MEMBERS_READ],
    )
    key_headers = {"X-API-Key": raw_key}
    resp_key = client.get(f"/api/v1/organizations/{org.id}/usage", headers=key_headers)
    assert resp_key.status_code == 200
    assert resp_key.json()["organization_id"] == org.id

    # 4. Acceso denegado con API Key sin scope members:read
    _, no_scope_key = key_service.create_api_key(
        db_session,
        org.id,
        owner,
        "owner",
        "AI Only Key",
        [Scope.AI_GENERATE],
    )
    resp_no_scope = client.get(f"/api/v1/organizations/{org.id}/usage", headers={"X-API-Key": no_scope_key})
    assert resp_no_scope.status_code == 403


def test_member_quota_gating_invitations(client: TestClient, db_session: Session):
    """Verifica que invitar miembros bloquee con HTTP 402 cuando se alcanza el límite del plan (D-04, D-05)."""
    plan = SubscriptionPlan(
        name="Small Team Plan",
        slug="small-team",
        price=19.00,
        limits={"members": 2},  # Límite: 2 miembros en total
    )
    db_session.add(plan)
    db_session.flush()

    owner = UserProfile(cognito_sub="team-owner", email="teamowner@example.com", first_name="Team", last_name="Owner")
    db_session.add(owner)
    db_session.flush()

    org = Organization(
        name="Team Org",
        slug="team-org",
        owner_id=owner.id,
        subscription_plan_id=plan.id,
        subscription_status="active",
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner")
    db_session.add(member)
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-team-owner"}

    with patch("api.modules.organizations.routes.send_organization_invitation_email"):
        # Invitación 1: 1 activo + 1 pendiente = 2/2 -> Éxito (201 Created)
        resp1 = client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={"email": "member1@example.com", "role": "member"},
            headers=headers,
        )
        assert resp1.status_code == 201

        # Invitación 2: 1 activo + 1 pendiente = 2 >= 2 -> HTTP 402 Quota Exceeded!
        resp2 = client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            json={"email": "member2@example.com", "role": "member"},
            headers=headers,
        )
        assert resp2.status_code == 402
        body = resp2.json()
        assert body["code"] == "quota_exceeded"
        assert body["metric"] == "members"
        assert body["limit"] == 2
        assert body["used"] == 2


def test_stripe_webhook_syncs_billing_period(client: TestClient, db_session: Session):
    """Verifica que los webhooks de Stripe sincronicen current_period_start y end en la organización (D-06)."""
    owner = UserProfile(cognito_sub="wh-owner", email="wh@example.com", first_name="WH", last_name="Owner")
    db_session.add(owner)
    db_session.flush()

    settings_row = UserSettings(user_id=owner.id, subscription_status="active")
    db_session.add(settings_row)

    customer = StripeCustomer(
        user_id=owner.id,
        stripe_customer_id="cus_test_sync_123",
        stripe_subscription_id="sub_test_sync_123",
        subscription_status="active",
    )
    db_session.add(customer)

    org = Organization(
        name="Sync Org",
        slug="sync-org",
        owner_id=owner.id,
        subscription_status="active",
    )
    db_session.add(org)
    db_session.commit()

    period_start_ts = int(datetime(2026, 10, 15, 0, 0, 0, tzinfo=timezone.utc).timestamp())
    period_end_ts = int(datetime(2026, 11, 15, 0, 0, 0, tzinfo=timezone.utc).timestamp())

    fake_event = {
        "id": "evt_test_period_sync",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test_sync_123",
                "customer": "cus_test_sync_123",
                "status": "active",
                "current_period_start": period_start_ts,
                "current_period_end": period_end_ts,
                "metadata": {
                    "organization_id": str(org.id),
                },
            }
        },
    }

    with patch("stripe.Webhook.construct_event", return_value=fake_event):
        response = client.post(
            "/api/v1/billing/webhook",
            content=b"{}",
            headers={"Stripe-Signature": "test-signature"},
        )
        assert response.status_code == 200

    # Verificar que el modelo Organization se actualizó
    db_session.refresh(org)
    assert org.current_period_start is not None
    assert org.current_period_end is not None

    start = org.current_period_start
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    end = org.current_period_end
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    assert int(start.timestamp()) == period_start_ts
    assert int(end.timestamp()) == period_end_ts
