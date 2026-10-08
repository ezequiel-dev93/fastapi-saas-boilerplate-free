from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.core.auth_context import Scope
from api.core.protocols.ai import (
    ProviderAuthError,
    ProviderChatRequest,
    ProviderMessage,
    ProviderRateLimited,
    TextDelta,
    UsageReport,
)
from api.modules.ai.models import AiUsageEvent
from api.modules.ai.providers.claude import ClaudeProvider
from api.modules.ai.providers.factory import get_ai_provider
from api.modules.ai.providers.gemini import GeminiProvider
from api.modules.ai.providers.mock import MockAiProvider
from api.modules.ai.providers.openai import OpenAiProvider
from api.modules.ai.schemas import ChatMessage, ChatStreamRequest
from api.modules.ai.sse import format_sse, format_sse_ping
from api.modules.billing.models import SubscriptionPlan
from api.modules.organizations.api_key_service import get_api_key_service
from api.modules.organizations.models import Organization, OrganizationMember
from api.modules.usage.services import get_usage_service
from api.modules.users.models import UserProfile

# ──────────────────────────────────────────────────────────────────────────
# 1. Tests de Validación de Esquemas y Controles de Costo (D-10)
# ──────────────────────────────────────────────────────────────────────────


def test_chat_stream_request_validation():
    """Valida restricciones de entrada: límites de caracteres, mensajes y lista blanca de modelos."""
    # 1. Contenido vacío rechazado
    with pytest.raises(ValueError):
        ChatMessage(role="user", content="   ")

    # 2. Último mensaje debe ser del rol 'user'
    with pytest.raises(ValueError, match="rol 'user'"):
        ChatStreamRequest(
            messages=[
                ChatMessage(role="user", content="Hola"),
                ChatMessage(role="assistant", content="Cómo estás?"),
            ]
        )

    # 3. Modelo no permitido rechazado
    with pytest.raises(ValueError, match="no está permitido"):
        ChatStreamRequest(
            messages=[ChatMessage(role="user", content="Hola")],
            model="unauthorized-super-expensive-model",
        )

    # 4. Exceder límite de caracteres rechazado
    huge_text = "a" * 17000
    with pytest.raises(ValueError, match="excede el límite permitido"):
        ChatStreamRequest(
            messages=[ChatMessage(role="user", content=huge_text)],
        )

    # 5. Petición válida aceptada
    valid_req = ChatStreamRequest(
        messages=[
            ChatMessage(role="system", content="Eres un asistente útil."),
            ChatMessage(role="user", content="Cuál es la capital de Francia?"),
        ],
        model="gpt-4o-mini",
        temperature=0.5,
    )
    assert valid_req.model == "gpt-4o-mini"
    assert valid_req.temperature == 0.5


# ──────────────────────────────────────────────────────────────────────────
# 2. Tests del Proveedor Mock (D-01, D-02, D-11)
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mock_ai_provider_lifecycle():
    """Verifica que MockAiProvider emita deltas deterministas y UsageReport."""
    provider = MockAiProvider()
    req = ProviderChatRequest(
        messages=[ProviderMessage(role="user", content="Test prompt")],
        model="mock-chat",
    )

    events = [event async for event in provider.stream_chat(req)]
    assert len(events) > 1

    deltas = [e for e in events if isinstance(e, TextDelta)]
    usage_reports = [e for e in events if isinstance(e, UsageReport)]

    assert len(deltas) > 0
    assert len(usage_reports) == 1
    assert usage_reports[0].output_tokens == len(deltas)
    assert usage_reports[0].total_tokens > 0

    full_text = "".join(d.text for d in deltas)
    assert "mock-chat" in full_text


def test_mock_ai_provider_forbidden_in_production():
    """Verifica que MockAiProvider lance error si ENVIRONMENT='production' (D-02)."""
    with patch("api.modules.ai.providers.mock.settings.ENVIRONMENT", "production"):
        with pytest.raises(ValueError, match="estrictamente prohibido en producción"):
            MockAiProvider()


# ──────────────────────────────────────────────────────────────────────────
# 3. Tests del Endpoint de Streaming SSE con JWT y API Keys
# ──────────────────────────────────────────────────────────────────────────


def test_ai_chat_stream_with_jwt_success(client: TestClient, db_session: Session):
    """
    Verifica streaming exitoso vía JWT:
    - Retorna status 200 con text/event-stream.
    - Emite eventos meta, delta, usage y done.
    - Descuenta 1 mensaje de la cuota de la organización.
    - Registra AiUsageEvent sin almacenar contenido del prompt/respuesta (D-03).
    """
    plan = SubscriptionPlan(
        name="AI Pro",
        slug="ai-pro-plan",
        price=49.00,
        limits={"ai_messages": 100},
    )
    db_session.add(plan)
    db_session.flush()

    user = UserProfile(cognito_sub="ai-jwt-user", email="aiuser@example.com", first_name="AI", last_name="User")
    db_session.add(user)
    db_session.flush()

    org = Organization(
        name="AI Workspace",
        slug="ai-workspace",
        owner_id=user.id,
        subscription_plan_id=plan.id,
        subscription_status="active",
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=user.id, role="owner")
    db_session.add(member)
    db_session.commit()

    headers = {
        "Authorization": "Bearer test-token-ai-jwt-user",
        "X-Organization-ID": str(org.id),
    }
    payload = {
        "messages": [{"role": "user", "content": "Hola mundo"}],
        "model": "mock-chat",
    }

    response = client.post("/api/v1/ai/chat/stream", json=payload, headers=headers)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    assert response.headers.get("cache-control") == "no-cache"

    content = response.text
    assert "event: meta" in content
    assert "event: delta" in content
    assert "event: usage" in content
    assert "event: done" in content

    # 1. Verificar que se consumió 1 mensaje de la cuota
    usage_service = get_usage_service()
    summary = usage_service.summary(db_session, org.id)
    ai_stat = next(m for m in summary.metrics if m.metric == "ai_messages")
    assert ai_stat.used == 1
    assert ai_stat.remaining == 99

    # 2. Verificar auditoría de metadatos (D-03)
    event_row = db_session.query(AiUsageEvent).filter_by(organization_id=org.id).first()
    assert event_row is not None
    assert event_row.user_id == user.id
    assert event_row.provider == "mock"
    assert event_row.model == "mock-chat"
    assert event_row.status == "completed"
    assert event_row.output_tokens > 0


def test_ai_chat_stream_with_api_key_success(client: TestClient, db_session: Session):
    """Verifica streaming exitoso vía API Key con scope 'ai:generate'."""
    plan = SubscriptionPlan(
        name="B2B AI Plan",
        slug="b2b-ai-plan",
        price=99.00,
        limits={"ai_messages": 50},
    )
    db_session.add(plan)
    db_session.flush()

    owner = UserProfile(cognito_sub="b2b-owner", email="b2b@example.com", first_name="B2B", last_name="Owner")
    db_session.add(owner)
    db_session.flush()

    org = Organization(
        name="B2B Org",
        slug="b2b-org",
        owner_id=owner.id,
        subscription_plan_id=plan.id,
        subscription_status="active",
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner")
    db_session.add(member)
    db_session.commit()

    key_service = get_api_key_service()
    _, raw_key = key_service.create_api_key(
        db_session,
        org.id,
        owner,
        "owner",
        "AI Automation Key",
        [Scope.AI_GENERATE],
    )

    headers = {"X-API-Key": raw_key}
    payload = {
        "messages": [{"role": "user", "content": "Generar reporte B2B"}],
        "model": "mock-chat",
    }

    response = client.post("/api/v1/ai/chat/stream", json=payload, headers=headers)
    assert response.status_code == 200
    assert "event: done" in response.text

    # Verificar que el evento de auditoría tiene api_key_id y user_id es None
    event_row = db_session.query(AiUsageEvent).filter_by(organization_id=org.id).first()
    assert event_row is not None
    assert event_row.api_key_id is not None
    assert event_row.user_id is None
    assert event_row.status == "completed"


def test_ai_chat_stream_forbidden_without_ai_scope(client: TestClient, db_session: Session):
    """API Key sin scope 'ai:generate' es denegada con 403 y no consume cuota."""
    plan = SubscriptionPlan(
        name="Restricted Plan",
        slug="restr-plan",
        price=10.00,
        limits={"ai_messages": 20},
    )
    db_session.add(plan)
    db_session.flush()

    owner = UserProfile(cognito_sub="restr-owner", email="restr@example.com", first_name="R", last_name="Owner")
    db_session.add(owner)
    db_session.flush()

    org = Organization(
        name="Restr Org",
        slug="restr-org",
        owner_id=owner.id,
        subscription_plan_id=plan.id,
        subscription_status="active",
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner")
    db_session.add(member)
    db_session.commit()

    key_service = get_api_key_service()
    _, raw_key = key_service.create_api_key(
        db_session,
        org.id,
        owner,
        "owner",
        "Users Only Key",
        [Scope.USERS_READ],  # Sin Scope.AI_GENERATE
    )

    headers = {"X-API-Key": raw_key}
    payload = {"messages": [{"role": "user", "content": "Test"}]}

    response = client.post("/api/v1/ai/chat/stream", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Missing required scope" in response.json()["detail"]

    # Cuota intacta
    usage_service = get_usage_service()
    assert usage_service.summary(db_session, org.id).metrics[0].used == 0


def test_ai_chat_stream_quota_exhausted_returns_402(client: TestClient, db_session: Session):
    """Agotar el cupo mensual de mensajes de IA retorna HTTP 402 antes del stream (D-04)."""
    plan = SubscriptionPlan(
        name="1 Message Plan",
        slug="one-msg-plan",
        price=5.00,
        limits={"ai_messages": 1},  # Solo 1 mensaje
    )
    db_session.add(plan)
    db_session.flush()

    owner = UserProfile(cognito_sub="one-owner", email="one@example.com", first_name="One", last_name="Owner")
    db_session.add(owner)
    db_session.flush()

    org = Organization(
        name="One Org", slug="one-org", owner_id=owner.id, subscription_plan_id=plan.id, subscription_status="active"
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner")
    db_session.add(member)
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-one-owner", "X-Organization-ID": str(org.id)}
    payload = {"messages": [{"role": "user", "content": "Mensaje 1"}]}

    # 1. Primer mensaje consume el cupo (1/1) -> 200 OK
    resp1 = client.post("/api/v1/ai/chat/stream", json=payload, headers=headers)
    assert resp1.status_code == 200

    # 2. Segundo mensaje excede la cuota -> 402 Payment Required
    resp2 = client.post("/api/v1/ai/chat/stream", json=payload, headers=headers)
    assert resp2.status_code == 402
    body = resp2.json()
    assert body["code"] == "quota_exceeded"
    assert body["metric"] == "ai_messages"
    assert body["limit"] == 1
    assert body["used"] == 1


def test_ai_chat_stream_refund_on_failure_before_first_token(client: TestClient, db_session: Session):
    """
    Si el proveedor de IA falla antes de emitir el primer token (D-08):
    - Emite evento SSE 'error'.
    - Reembolsa automáticamente la unidad de cuota consumida.
    - Registra el evento de uso con status 'refunded'.
    """
    plan = SubscriptionPlan(
        name="Refund Plan",
        slug="refund-plan",
        price=15.00,
        limits={"ai_messages": 10},
    )
    db_session.add(plan)
    db_session.flush()

    owner = UserProfile(cognito_sub="ref-owner", email="ref@example.com", first_name="Ref", last_name="Owner")
    db_session.add(owner)
    db_session.flush()

    org = Organization(
        name="Ref Org", slug="ref-org", owner_id=owner.id, subscription_plan_id=plan.id, subscription_status="active"
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner")
    db_session.add(member)
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-ref-owner", "X-Organization-ID": str(org.id)}
    payload = {
        "messages": [{"role": "user", "content": "SIMULATE_ERROR_BEFORE_TOKEN"}],
    }

    response = client.post("/api/v1/ai/chat/stream", json=payload, headers=headers)
    assert response.status_code == 200
    content = response.text
    assert "event: error" in content
    assert "Simulated upstream connection failure" in content

    # 1. Verificar reembolso en la cuota (contador vuelve a 0)
    usage_service = get_usage_service()
    summary = usage_service.summary(db_session, org.id)
    ai_stat = next(m for m in summary.metrics if m.metric == "ai_messages")
    assert ai_stat.used == 0

    # 2. Verificar estado en auditoría
    event_row = db_session.query(AiUsageEvent).filter_by(organization_id=org.id).first()
    assert event_row is not None
    assert event_row.status == "refunded"


def test_ai_chat_stream_mid_stream_failure_does_not_refund(client: TestClient, db_session: Session):
    """
    Si el proveedor falla a mitad del stream (ya entregó tokens):
    - Emite evento SSE 'error'.
    - NO reembolsa la cuota (los tokens fueron consumidos/entregados).
    - Registra el evento con status 'failed'.
    """
    plan = SubscriptionPlan(
        name="Mid Fail Plan",
        slug="mid-fail-plan",
        price=20.00,
        limits={"ai_messages": 10},
    )
    db_session.add(plan)
    db_session.flush()

    owner = UserProfile(cognito_sub="mid-owner", email="mid@example.com", first_name="Mid", last_name="Owner")
    db_session.add(owner)
    db_session.flush()

    org = Organization(
        name="Mid Org", slug="mid-org", owner_id=owner.id, subscription_plan_id=plan.id, subscription_status="active"
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=owner.id, role="owner")
    db_session.add(member)
    db_session.commit()

    headers = {"Authorization": "Bearer test-token-mid-owner", "X-Organization-ID": str(org.id)}
    payload = {
        "messages": [{"role": "user", "content": "SIMULATE_ERROR_MID_STREAM"}],
    }

    response = client.post("/api/v1/ai/chat/stream", json=payload, headers=headers)
    assert response.status_code == 200
    content = response.text
    assert "event: delta" in content
    assert "event: error" in content

    # Cuota permanece consumida (used = 1, NO reembolsada)
    usage_service = get_usage_service()
    summary = usage_service.summary(db_session, org.id)
    ai_stat = next(m for m in summary.metrics if m.metric == "ai_messages")
    assert ai_stat.used == 1

    event_row = db_session.query(AiUsageEvent).filter_by(organization_id=org.id).first()
    assert event_row.status == "failed"


# ──────────────────────────────────────────────────────────────────────────
# 4. Tests de Adaptadores Reales con Fakes / Mock HTTP (OpenAI y Gemini)
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_openai_provider_sse_parsing():
    """Verifica que OpenAiProvider procese correctamente respuestas SSE simuladas."""
    mock_sse_lines = [
        b'data: {"choices": [{"delta": {"content": "Hola"}}]}\n\n',
        b'data: {"choices": [{"delta": {"content": " mundo"}}]}\n\n',
        b'data: {"usage": {"prompt_tokens": 12, "completion_tokens": 4}}\n\n',
        b"data: [DONE]\n\n",
    ]

    async def mock_aiter_lines():
        for line in mock_sse_lines:
            yield line.decode("utf-8")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.aiter_lines = mock_aiter_lines

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.stream.return_value.__aenter__.return_value = mock_resp

    provider = OpenAiProvider(api_key="sk-test-fake-key", client=mock_client)
    req = ProviderChatRequest(
        messages=[ProviderMessage(role="user", content="Test")],
        model="gpt-4o",
    )

    events = [event async for event in provider.stream_chat(req)]
    deltas = [e.text for e in events if isinstance(e, TextDelta)]
    reports = [e for e in events if isinstance(e, UsageReport)]

    assert deltas == ["Hola", " mundo"]
    assert len(reports) == 1
    assert reports[0].input_tokens == 12
    assert reports[0].output_tokens == 4


@pytest.mark.asyncio
async def test_openai_provider_handles_auth_and_rate_limit_errors():
    """Verifica mapeo de errores HTTP 401 y 429 a excepciones de dominio."""
    # 1. Falta de API key -> ProviderAuthError
    provider_no_key = OpenAiProvider(api_key=None)
    with patch("api.modules.ai.providers.openai.settings.OPENAI_API_KEY", None):
        provider_no_key.api_key = None
        with pytest.raises(ProviderAuthError):
            req = ProviderChatRequest(messages=[ProviderMessage(role="user", content="Hi")], model="gpt-4o")
            async for _ in provider_no_key.stream_chat(req):
                pass

    # 2. HTTP 429 -> ProviderRateLimited
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.stream.return_value.__aenter__.return_value = mock_resp_429

    provider_rate_limited = OpenAiProvider(api_key="sk-fake", client=mock_client)
    with pytest.raises(ProviderRateLimited):
        req = ProviderChatRequest(messages=[ProviderMessage(role="user", content="Hi")], model="gpt-4o")
        async for _ in provider_rate_limited.stream_chat(req):
            pass


@pytest.mark.asyncio
async def test_gemini_provider_sse_parsing():
    """Verifica que GeminiProvider procese respuestas SSE de Google Gemini."""
    mock_sse_lines = [
        b'data: {"candidates": [{"content": {"parts": [{"text": "Buenos"}]}}]}\n\n',
        b'data: {"candidates": [{"content": {"parts": [{"text": " d\xc3\xadas"}]}}]}\n\n',
        b'data: {"usageMetadata": {"promptTokenCount": 8, "candidatesTokenCount": 2}}\n\n',
    ]

    async def mock_aiter_lines():
        for line in mock_sse_lines:
            yield line.decode("utf-8")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.aiter_lines = mock_aiter_lines

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.stream.return_value.__aenter__.return_value = mock_resp

    provider = GeminiProvider(api_key="fake-gemini-key", client=mock_client)
    req = ProviderChatRequest(
        messages=[ProviderMessage(role="user", content="Test")],
        model="gemini-1.5-flash",
    )

    events = [event async for event in provider.stream_chat(req)]
    deltas = [e.text for e in events if isinstance(e, TextDelta)]
    reports = [e for e in events if isinstance(e, UsageReport)]

    assert "".join(deltas) == "Buenos días"
    assert len(reports) == 1
    assert reports[0].input_tokens == 8
    assert reports[0].output_tokens == 2


@pytest.mark.asyncio
async def test_claude_provider_sse_parsing():
    """Verifica que ClaudeProvider procese respuestas SSE de Anthropic Claude."""
    mock_sse_lines = [
        b'data: {"type": "message_start", "message": {"usage": {"input_tokens": 15, "output_tokens": 1}}}\n\n',
        b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hola desde"}}\n\n',
        b'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": " Claude"}}\n\n',
        b'data: {"type": "message_delta", "usage": {"output_tokens": 5}}\n\n',
        b'data: {"type": "message_stop"}\n\n',
    ]

    async def mock_aiter_lines():
        for line in mock_sse_lines:
            yield line.decode("utf-8")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.aiter_lines = mock_aiter_lines

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.stream.return_value.__aenter__.return_value = mock_resp

    provider = ClaudeProvider(api_key="sk-ant-test-fake-key", client=mock_client)
    req = ProviderChatRequest(
        messages=[
            ProviderMessage(role="system", content="Sos un asistente"),
            ProviderMessage(role="user", content="Hola"),
        ],
        model="claude-3-5-sonnet",
    )

    events = [event async for event in provider.stream_chat(req)]
    deltas = [e.text for e in events if isinstance(e, TextDelta)]
    reports = [e for e in events if isinstance(e, UsageReport)]

    assert "".join(deltas) == "Hola desde Claude"
    assert len(reports) == 1
    assert reports[0].input_tokens == 15
    assert reports[0].output_tokens == 5


@pytest.mark.asyncio
async def test_claude_provider_handles_errors():
    """Verifica excepciones de ClaudeProvider por falta de API key y 429."""
    # 1. Sin API key
    provider_no_key = ClaudeProvider(api_key=None)
    with patch("api.modules.ai.providers.claude.settings.ANTHROPIC_API_KEY", None):
        provider_no_key.api_key = None
        with pytest.raises(ProviderAuthError):
            req = ProviderChatRequest(messages=[ProviderMessage(role="user", content="Hi")], model="claude-3-5-sonnet")
            async for _ in provider_no_key.stream_chat(req):
                pass


    # 2. HTTP 429
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.stream.return_value.__aenter__.return_value = mock_resp_429

    provider_429 = ClaudeProvider(api_key="sk-ant-fake", client=mock_client)
    with pytest.raises(ProviderRateLimited):
        req = ProviderChatRequest(messages=[ProviderMessage(role="user", content="Hi")], model="claude-3-5-sonnet")
        async for _ in provider_429.stream_chat(req):
            pass


def test_claude_factory_resolution():
    """Verifica resolución de ClaudeProvider a través de get_ai_provider."""
    provider = get_ai_provider("claude")
    assert isinstance(provider, ClaudeProvider)
    assert provider.name == "claude"

    provider_anthropic = get_ai_provider("anthropic")
    assert isinstance(provider_anthropic, ClaudeProvider)


# ──────────────────────────────────────────────────────────────────────────
# 5. Tests de Keepalive SSE
# ──────────────────────────────────────────────────────────────────────────



def test_sse_formatting():
    """Verifica formato estándar SSE y ping keepalive."""
    ping = format_sse_ping()
    assert ping == ": ping\n\n"

    msg = format_sse("test", {"hello": "world"})
    assert msg.startswith("event: test\ndata: ")
    assert msg.endswith("\n\n")
    assert '"hello": "world"' in msg
