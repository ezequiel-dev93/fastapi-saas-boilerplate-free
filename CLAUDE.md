# CLAUDE.md - FastAPI SaaS Boilerplate Development Guide

## Project Overview
Production-ready FastAPI SaaS boilerplate with unified dual authentication (AWS Cognito + Organization API Keys), multi-tenancy (organizations/workspaces with RBAC), AI-ready engine with SSE streaming, atomic usage metering & quotas per plan, GDPR technical compliance, Stripe billing, background workers (ARQ/Redis), and transactional emails.

**Stack**: FastAPI 0.115+, Python 3.12, PostgreSQL/SQLite, SQLAlchemy 2.0, Alembic, Stripe, AWS Cognito, Redis/ARQ, AWS SES/Mailpit, OpenAI/Gemini

## Architecture Rules (Strict)

### 1. Screaming Modular Monolith
- Code organization **screams the business domain** (`users`, `billing`, `organizations`, `usage`, `ai`)
- Each module is self-contained: `models.py`, `schemas.py`, `services.py`, `routes.py`
- Shared cross-cutting infrastructure in `api/core/` (security, protocols, database, logging)

### 2. SOLID Enforcement
| Principle | Implementation |
|---|---|
| **SRP** | Routes = HTTP only. Services = Business logic. Gateways/Providers = External APIs. |
| **OCP** | New AI/Payment providers = new protocol implementation (`AiProviderProtocol`, `PaymentGatewayProtocol`). |
| **LSP** | Any provider implementation cleanly substitutes another (`MockAiProvider`, `OpenAiProvider`, `GeminiProvider`). |
| **ISP** | Focused protocols: `AiProviderProtocol`, `IdentityProviderProtocol`, `PaymentGatewayProtocol`, `EmailSenderProtocol`. |
| **DIP** | Domain services depend on protocols and dependency injection, never concrete SDK clients. |

### 3. Layer Boundaries (Never Cross)
```text
routes.py  →  services.py  →  models.py (ORM)
                    ↓
              protocols.py  ←  gateway.py / providers/ (Stripe, OpenAI, Gemini, SES, Cognito)
```
- **Routes** never import third-party SDKs (`stripe`, `boto3`, `openai`, `google-genai`) directly
- **Services** never handle HTTP (no `Request`, `Response`, `HTTPException` imports in core domain classes)
- **Gateways & Providers** implement protocols and contain external SDK calls

---

## Key Patterns to Follow

### 1. Dual Authentication & Unified AuthContext
Authentication entrypoint is `get_auth_context` in `api/core/security.py`:
```python
from api.core.auth_context import AuthContext, Scope
from api.core.security import get_auth_context, get_current_user, require_jwt, require_scope

# 1. Human user endpoint (Cognito JWT only, 403 for API keys):
@router.get("/me")
async def get_me(user: UserProfile = Depends(get_current_user)):
    return user

# 2. Dual endpoint (JWT or Org API Key with scope):
@router.post("/chat/stream")
async def stream_chat(
    ctx: AuthContext = Depends(require_scope(Scope.AI_GENERATE)),
):
    # ctx.org_id is guaranteed whether calling via JWT or API Key
    return ...
```

### 2. Organization API Keys (Tenant-Scoped)
Keys are scoped exclusively to organizations (`OrganizationApiKey`) with environment prefixes (`sk_live_...` or `sk_test_...`):
```python
from api.modules.organizations.api_key_service import get_api_key_service

key_service = get_api_key_service()
api_key, raw_key = key_service.create_api_key(
    db=db,
    org_id=org.id,
    creator=current_user,
    creator_role="owner",
    name="Production Agent",
    scopes=[Scope.AI_GENERATE],
)
```

### 3. Atomic Usage Metering & Quotas (D-04, D-08, D-09)
Enforce plan limits with atomic SQL increments:
```python
from api.modules.usage.dependencies import consume_quota

# Reusable dependency: atomically validates and increments usage before controller executes
@router.post("/organizations/{org_id}/heavy-action")
async def run_action(
    org_id: int,
    quota=Depends(consume_quota("ai_messages", amount=1)),
):
    # If quota was exhausted, QuotaExceededException automatically returns HTTP 402 Payment Required
    return {"status": "ok", "remaining": quota.remaining}
```

### 4. AI Streaming Module with SSE (D-01, D-03, D-10)
Stream text deltas via Server-Sent Events with keepalives and auto-refund:
```python
from api.modules.ai.services import get_ai_chat_service

chat_service = get_ai_chat_service()
return await chat_service.stream_chat(
    request=chat_request,
    org_id=ctx.org_id,
    user_id=ctx.user.id if ctx.user else None,
    api_key_id=ctx.api_key_id,
)
```

### 5. GDPR Privacy & Account Erasure (D-12, D-13, D-14, D-15)
Handle Right of Access and Right to Erasure without breaking B2B accounting or integrations:
```python
from api.modules.users.privacy_service import get_privacy_service

privacy_service = get_privacy_service()

# 1. Export structured JSON (GDPR Art. 15/20):
export_data = privacy_service.export_user_data(db=db, user=current_user)

# 2. Erasure with soft-anonymization & B2B key preservation (GDPR Art. 17):
deletion = await privacy_service.delete_user_account(db=db, user=current_user)
```

---

## Common Tasks Reference

### Run Locally
```bash
# Full stack (API + Postgres + Redis + Mailpit)
make docker-up

# Or run API directly with SQLite (no Docker needed)
make run        # uvicorn api.main:app --reload

# ARQ background worker
make worker

# Run the complete test suite (172 tests, 100% green)
python scripts/test_summary.py --html
# or
make test       # pytest -v
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Seed initial subscription plans
python seed.py
```

### Export OpenAPI for Frontend
```bash
make openapi    # Generates openapi.json for TypeScript type generation
```

### Testing Strategy
- **Unit / Mock Tests**: 100% offline, zero network, zero real Stripe/OpenAI/Cognito credentials needed.
- **Full Verification**: Run `python scripts/test_summary.py --html` which exports an interactive verification badge and breakdown to `docs/test_summary_widget.html`.