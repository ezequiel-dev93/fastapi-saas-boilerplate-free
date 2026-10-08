> 🇪🇸 **¿Buscas la versión en Español?** Revisa [README.es.md](README.es.md).
> 
> ---

# ⚡ FastAPI SaaS Boilerplate (Enterprise Edition)

[![CI Pipeline](https://img.shields.io/badge/CI-passing-10b981.svg)](.github/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-183%20passed-success.svg)](tests/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/license-Commercial%20(EULA)-purple.svg)](LICENSE)

The production-ready, batteries-included backend starter kit designed to launch scalable, AI-ready B2B SaaS applications in days, not months. Built with **FastAPI**, **AWS Cognito**, **Stripe**, **PostgreSQL**, **Redis**, and **AWS SES**.

---

## 🚀 Key Features

- 🤖 **Multi-Provider AI-Ready Engine with SSE Streaming**:
  - Provider-agnostic streaming protocol (`AiProviderProtocol`) with swappable native adapters:
    - **Anthropic Claude**: `claude-3-5-sonnet`, `claude-3-5-haiku`, `claude-3-opus`.
    - **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `o3-mini`.
    - **Google Gemini**: `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`.
    - **Mock**: Offline/CI testing with zero API keys or external network costs.
  - Standardized Server-Sent Events (SSE): structured `meta`, `delta`, `usage`, `done`, and `error` events.
  - Heartbeat `: ping` keepalive frames every 15 seconds to prevent proxy and gateway timeouts.
  - **Atomic Quota Pre-Checks & Auto-Refund**: Message quota is reserved before connection opens; automatically refunded if the AI provider fails before delivering the first text token.
  - **GDPR-Safe Metadata Audit**: Logs request timestamps, token counts, and models in `ai_usage_events`. **Never** stores user prompts or model responses.


- 📊 **Atomic Usage Metering & Plan Quotas**:
  - High-concurrency atomic SQL counter updates (`UPDATE organization_usage SET used = used + :n WHERE used + :n <= :limit`). Zero race conditions and zero overages.
  - Clear **`HTTP 402 Payment Required`** response on quota exhaustion with structured upgrade metadata (`metric`, `limit`, `used`, `upgrade_url`), preventing wasteful retry storms caused by generic 429 throttling.
  - **Billing Cycle Synchronization**: Automatically synced with Stripe subscription periods (`current_period_start/end`), with UTC calendar month fallback for free or inactive plans.
  - **Member Limits**: Automatically enforces maximum seat count on team invitations based on `SubscriptionPlan.limits["members"]`.

- 🛡️ **GDPR Technical Privacy & Account Erasure**:
  - **Right of Access & Data Portability (Art. 15 & 20)**: `GET /api/v1/users/me/export` delivers a complete, structured JSON export of profile, settings, team memberships, Stripe references, created API keys (metadata only), and AI audit events.
  - **Right to Erasure / "Right to be Forgotten" (Art. 17)**: `DELETE /api/v1/users/me/account` with strict safety preconditions (`409 Conflict` if an active Stripe subscription exists or user is sole owner of a multi-member organization).
  - **Soft-Anonymization**: Replaces personal email with `deleted_<uuid>@deleted.invalid` (RFC 2606), scrubs names to `Deleted User`, disables notifications, and marks `deleted_at`.
  - **B2B Integration Preservation**: Unlinks API keys created by the deleted user (`created_by_id = NULL`) so existing client integrations for surviving organizations continue uninterrupted.
  - **Async Identity Provider Deletion**: Enqueues physical deletion in AWS Cognito (`admin_delete_user`) via ARQ/Redis with immediate `401 Unauthorized` invalidation for all active tokens.

- 🔑 **Tenant-Scoped Organization API Keys**:
  - Replaces user-level keys with dedicated B2B organization keys (`OrganizationApiKey`).
  - Strict environment-prefixed format (`sk_live_...` for production, `sk_test_...` for dev/staging) validated before touching infrastructure.
  - Only stored as SHA-256 hashes with safe 16-character public prefixes for auditing and support.
  - **Granular Scopes**: Fine-grained permissions (`billing:read`, `org:admin`, `ai:generate`) with anti-privilege escalation checks based on the creator's role.
  - Survives employee offboarding: keys belong to the organization and keep working even if the creator leaves.

- 🏢 **B2B Multi-Tenancy & Workspaces**:
  - Organization creation with unique slug generation and designated owner.
  - **Role-Based Access Control (RBAC)**: `owner`, `admin`, and `member` roles enforced via reusable FastAPI dependencies (`require_org_role`).
  - **Secure Email Invitations**: 7-day cryptographically secure one-time tokens with responsive HTML email templates.
  - **Feature Gating**: Reusable `require_feature` dependency to restrict premium routes based on `SubscriptionPlan.features`.

- 🔐 **Hybrid Authentication Architecture**:
  - Unified `AuthContext` separating human users (JWT) from machine integrations (API Keys).
  - **AWS Cognito**: Cryptographic RS256 JWT verification against public JWKS with JIT user profile provisioning in production.
  - **Zero-AWS Local Dev Authentication**: Instant 1-click login with `DevJwtAuthenticator` and endpoints `/auth/dev-users` and `/auth/dev-login` utilizing seeded users. Strictly disabled (404/403) in production environments.
  - **Organization API Keys**: Developer API authentication via `X-API-Key` or `Authorization: Bearer` with Deny-by-Default guards protecting personal endpoints.

- 💳 **Complete Stripe Billing & Subscription Engine**:
  - Modern Payment Methods API.
  - Pinned Stripe API version (`2026-08-26.dahlia`) to eliminate SDK breaking changes.
  - Subscriptions with automatic idempotency keys (prevents accidental double billing).
  - Cryptographically verified webhooks with an **idempotency & deduplication ledger** (`StripeWebhookEvent`) that prevents duplicate webhook processing.
  - Native **Stripe Customer Portal** integration for self-serve card updates and invoice downloads.
  - Honest cancellation (`cancel_at_period_end=True`): customers retain full access until their paid billing cycle finishes.
  - Unified access sync (`sync_access`) ensuring local DB access and Stripe billing state never drift.

- ⚡ **Background Worker with Redis & ARQ**:
  - Non-blocking, distributed background task processing for transactional emails, heavy workloads, and Cognito account deletion.
  - Automatic, transparent synchronous fallback for local development and unit tests without requiring a running Redis instance.

- 🛡️ **Distributed Rate Limiting (SlowAPI)**:
  - Active brute-force and DDoS protection on sensitive endpoints (`/checkout`, `/invitations`, `/ai/chat/stream`).
  - Configurable limits by client IP address or authenticated API Key.

- 🎨 **Developer Experience (DX) & Rich Logging**:
  - Dual logging engine: syntax-highlighted, color-coded console logs with `rich` in development/testing; structured JSON lines in production with `X-Request-ID` correlation tracing.
  - Live interactive email preview gallery at `http://localhost:8000/dev/emails`.

- 📧 **Transactional Emails (Jinja2 + Dual Mode)**:
  - 4 responsive HTML email templates (Trial welcome, Team invitation, Subscription confirmation, Honest cancellation).
  - **Mailpit** support for interactive local inspection at `http://localhost:8025` and **AWS SES** for production delivery.

- 🧪 **183 Automated Tests (100% Green)**:
  - Exhaustive test suite covering dual auth, AI streaming (OpenAI, Gemini, Claude), quotas, GDPR privacy, billing, webhooks, multi-tenancy, RBAC, background worker, and rate limiting with Pytest.

- 📦 **Container Ready & Production Deployable**:
  - Multi-stage `Dockerfile`, `docker-compose.yml`, GitHub Actions CI pipeline, and step-by-step production guides for **Render**, **Fly.io**, **Railway**, and **AWS ECS**.

- 🌐 **100% Frontend Agnostic**:
  - Built-in `make openapi` command exports a clean static `openapi.json` contract for instant TypeScript type generation in **Next.js**, **Astro**, **React**, or mobile clients.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI 0.115+ (Python 3.12) with ASGI Uvicorn |
| **Authentication** | AWS Cognito (RS256 JWT) + Dev JWT Local + Org API Keys (`X-API-Key: sk_live_...`) |
| **AI Engine** | SSE Streaming + Multi-Provider (Mock, OpenAI, Google Gemini, Anthropic Claude) |
| **Usage & Quotas** | Atomic SQL Metering + Stripe Period Sync + HTTP 402 Responses |
| **GDPR Compliance** | Data Export JSON (Art. 15/20) + Soft-Anonymization Deletion (Art. 17) |
| **Multi-Tenancy** | Workspaces/Organizations, RBAC (`owner`, `admin`, `member`), Email Invites |
| **Payments & Billing** | Stripe (Payment Methods + Customer Portal + Idempotent Webhooks) |
| **Database** | PostgreSQL 16 (Production) / SQLite (Local Dev & Unit Tests) |
| **ORM & Migraciones** | SQLAlchemy 2.0 (Modern 2.0 syntax) + Alembic |
| **Task Queue (Worker)** | Redis 7 + ARQ (Native AsyncIO worker + sync fallback) |
| **Rate Limiting** | SlowAPI (Distributed IP and API Key limits) |
| **Transactional Emails** | AWS SES (Production) + Mailpit (Local) + Jinja2 HTML templates |
| **Automated Testing** | Pytest + TestClient (**183 automated tests, 100% passing**) |
| **Containers & DevOps** | Docker + Docker Compose + GitHub Actions CI |


---

## 📁 Directory Structure (Screaming Architecture)

```text
.
├── ARCHITECTURE.md                  # C4 model, SOLID design rules, and ADRs
├── docs/
│   ├── guides/
│   │   ├── stripe-setup.md          # Step-by-step Stripe dashboard, webhook & portal guide
│   │   ├── aws-cognito-setup.md     # User Pool, App Client & OAuth scopes setup
│   │   ├── production-deployment.md # Multi-stage Docker deployment (Render, Fly.io, ECS)
│   │   └── COMMERCIAL_LAUNCH_GUIDE.md # Sales kit for LemonSqueezy / Gumroad ($149-$249)
│   ├── UPGRADING.md                 # Migration guides for v2 (Org API Keys) & v3 (AI & GDPR)
│   └── test_summary_widget.html     # Live visual verification widget for landing page
├── api/
│   ├── main.py                     # App factory, middlewares, lifespan dependencies & routing
│   ├── worker.py                   # Async ARQ background worker (+ local sync fallback)
│   ├── core/                       # Shared cross-cutting infrastructure
│   │   ├── config.py               # Typed settings with pydantic-settings (.env)
│   │   ├── database.py             # SQLAlchemy async engine, SessionLocal & get_db
│   │   ├── auth_context.py         # Unified AuthContext & Scope enumeration
│   │   ├── security.py             # Unified auth entrypoint, deny-by-default wrappers & guards
│   │   ├── limiter.py              # Distributed rate limiting (SlowAPI)
│   │   ├── email.py                # Transactional email dispatcher (SES / Mailpit)
│   │   ├── dev_emails.py           # Live interactive email preview gallery (/dev/emails)
│   │   ├── logging/                # Dual logger (Rich in dev, JSON in production)
│   │   └── protocols/              # Abstract contracts (Payment, Email, AI, Identity)
│   ├── modules/                    # Business Domains (Screaming Feature Modules)
│   │   ├── users/
│   │   │   ├── models.py           # UserProfile & UserSettings ORM models
│   │   │   ├── services.py         # Use cases (profile, trial logic)
│   │   │   ├── privacy_service.py  # GDPR data export & soft-anonymization erasure
│   │   │   ├── privacy_schemas.py  # GDPR export & deletion DTOs
│   │   │   ├── routes.py           # Thin HTTP controller (/me, /export, /account)
│   │   │   └── schemas.py          # Pydantic v2 DTO schemas
│   │   ├── billing/
│   │   │   ├── models.py           # SubscriptionPlan, StripeCustomer, WebhookEvent models
│   │   │   ├── gateway.py          # StripePaymentGateway adapter implementing protocol
│   │   │   ├── services.py         # Use cases (checkout, idempotency, portal sessions)
│   │   │   ├── routes.py           # Thin HTTP controller
│   │   │   └── schemas.py          # Pydantic v2 DTO schemas
│   │   ├── organizations/
│   │   │   ├── models.py           # Organization, Member, Invitation, OrganizationApiKey
│   │   │   ├── api_key_service.py  # Org API key generation, hashing & throttled validation
│   │   │   ├── dependencies.py     # RBAC guards (require_org_role, require_feature)
│   │   │   ├── services.py         # Workspaces, members, invite tokens
│   │   │   ├── routes.py           # Organization & API key management endpoints
│   │   │   └── schemas.py          # Pydantic v2 DTO schemas
│   │   ├── usage/
│   │   │   ├── models.py           # OrganizationUsage table (atomic tracking)
│   │   │   ├── services.py         # Atomic SQL increments, period resolution, summaries
│   │   │   ├── dependencies.py     # Reusable consume_quota dependency & 402 exception handler
│   │   │   └── schemas.py          # QuotaExceededResponse & usage summary DTOs
│   │   └── ai/
│   │       ├── models.py           # AiUsageEvent table (metadata-only audit)
│   │       ├── providers/          # MockAiProvider, OpenAiProvider, GeminiProvider
│   │       ├── sse.py              # Server-Sent Events formatting & keepalive generator
│   │       ├── services.py         # AiChatService (quota gating, auto-refund, streaming)
│   │       ├── routes.py           # Streaming endpoint (/api/v1/ai/chat/stream)
│   │       └── schemas.py          # ChatMessage, ChatStreamRequest DTOs
│   └── templates/emails/           # Responsive Jinja2 HTML email templates
├── alembic/                        # Versioned database migrations
├── tests/                          # 172 automated tests (100% passing)
├── scripts/                        # Utility scripts (test_summary.py, export_openapi.py)
├── Dockerfile                      # Production-ready multi-stage Dockerfile
├── docker-compose.yml              # Local stack (FastAPI + PostgreSQL + Redis + Mailpit)
├── Makefile                        # DX terminal shortcuts
└── pyproject.toml                  # Linter and tool configurations (Ruff)
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.12+
- Git

### 2. Create and Activate Virtual Environment

On **Windows (PowerShell)**:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

On **Linux / macOS**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
cp .env.example .env       # On Linux/macOS
copy .env.example .env     # On Windows
```

### 5. Apply Migrations & Seed Initial Plans
```bash
alembic upgrade head
python seed.py
```

### 6. Run the Development Server
```bash
make run
# or
uvicorn api.main:app --reload --port 8000
```

Open your browser:
- **Interactive Swagger / OpenAPI UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Email Preview Gallery:** [http://localhost:8000/dev/emails](http://localhost:8000/dev/emails)
- **Health Check (`SELECT 1` DB probe):** [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Running Automated Tests

Run the full verification suite with detailed domain breakdown:

```bash
python scripts/test_summary.py --html
```

Or run directly with Pytest:

```bash
pytest -v
```

Expected result (**100% Green / 183 tests passing**):
```text
==========================================================================
       FASTAPI SAAS BOILERPLATE - TEST SUITE VERIFICATION
==========================================================================
 Domain / Feature Module                       Tests      Status      
 ----------------------------------------------------------------------
   Authentication & User Profiles              8 passed   [ PASS 8/8 ]
   Organizations & RBAC Multi-Tenancy          8 passed   [ PASS 8/8 ]
   Stripe Billing & Webhook Idempotency        8 passed   [ PASS 8/8 ]
   API Keys: Core Authentication & Hashing     33 passed  [ PASS 33/33 ]
   API Keys: Auth Matrix & Scopes              30 passed  [ PASS 30/30 ]
   API Keys: Tenant Access & RBAC Guards       18 passed  [ PASS 18/18 ]
   API Keys: Management CRUD & Service         14 passed  [ PASS 14/14 ]
   Transactional Emails & SES / SMTP           6 passed   [ PASS 6/6 ]
   Health Checks & Distributed Tracing         5 passed   [ PASS 5/5 ]
   SQLAlchemy 2.0 Models & Cascade Logic       4 passed   [ PASS 4/4 ]
   Background Worker & Task Queues (ARQ)       3 passed   [ PASS 3/3 ]
   Rate Limiting & Redis Protection            1 passed   [ PASS 1/1 ]
   AI-Ready SaaS: M0 Core Foundations          3 passed   [ PASS 3/3 ]
   Usage Metering & Atomic Quotas              9 passed   [ PASS 9/9 ]
   AI Engine: Streaming SSE & Providers        16 passed  [ PASS 16/16 ]
   GDPR Privacy & Account Erasure              9 passed   [ PASS 9/9 ]
   Local Dev Authentication                    8 passed   [ PASS 8/8 ]
 ----------------------------------------------------------------------
 Total: 183 tests executed in 28.73s  ->  100% GREEN (ALL 183 TESTS PASSING)
==========================================================================
```

---

## 📡 API Endpoints Overview

### Health & Root
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | Public | Active health check testing live database connectivity (`SELECT 1`) |
| `GET` | `/` | Public | Welcome message with links to documentation |

### Local Dev Authentication (Frictionless Login)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/auth/dev-users` | Public (Dev) | Lists seeded demo users and orgs for 1-click login (404 in prod) |
| `POST` | `/api/v1/auth/dev-login` | Public (Dev) | Issues instant dev JWT token for quick testing without Cognito (404 in prod) |


### Users & GDPR Privacy
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/users/me` | JWT | Returns current authenticated user profile & settings |
| `PATCH` | `/api/v1/users/me` | JWT | Updates user first and last name |
| `GET` | `/api/v1/users/settings` | JWT | Retrieves notification & subscription settings |
| `PATCH` | `/api/v1/users/settings` | JWT | Updates notification preferences |
| `POST` | `/api/v1/users/trial` | JWT | Activates a 14-day free trial (anti-abuse protected) |
| `GET` | `/api/v1/users/me/export` | JWT | **GDPR Art. 15/20**: Exports all personal data in structured JSON |
| `DELETE`| `/api/v1/users/me/account` | JWT | **GDPR Art. 17**: Soft-anonymizes account, preserves B2B keys & enqueues Cognito deletion |

### AI Engine (Streaming SSE)
| Method | Endpoint | Auth | Min Scope | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/ai/chat/stream` | JWT or Org API Key | `ai:generate` | Streams chat completion via SSE (`meta`, `delta`, `usage`, `done`, `error`) |

### Billing & Subscriptions (Stripe)
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/billing/plans` | Public | Lists active subscription plans, limits, and pricing |
| `POST` | `/api/v1/billing/checkout` | JWT | Creates Stripe subscription using a PaymentMethod ID |
| `GET` | `/api/v1/billing/subscription`| JWT | Retrieves detailed subscription status |
| `POST` | `/api/v1/billing/cancel` | JWT | Schedules cancellation at end of paid billing cycle |
| `POST` | `/api/v1/billing/portal` | JWT | Creates a session URL for the Stripe Customer Portal |
| `POST` | `/api/v1/billing/webhook` | Stripe Signature | Idempotently processes and deduplicates Stripe events |

### Organizations & Workspaces (B2B Multi-Tenancy)
| Method | Endpoint | Auth | Min Role | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/organizations` | JWT | User | Creates workspace and sets current user as `owner` |
| `GET` | `/api/v1/organizations` | JWT | Member | Lists all organizations the authenticated user belongs to |
| `GET` | `/api/v1/organizations/{org_id}` | JWT / API Key | Member | Retrieves organization details |
| `PATCH` | `/api/v1/organizations/{org_id}` | JWT | Admin/Owner | Updates organization name or slug |
| `GET` | `/api/v1/organizations/{org_id}/members` | JWT / API Key | Member | Lists organization members with profiles and roles |
| `PATCH` | `/api/v1/organizations/{org_id}/members/{user_id}` | JWT | Admin/Owner | Updates member role (`admin` or `member`) |
| `DELETE` | `/api/v1/organizations/{org_id}/members/{user_id}` | JWT | Admin/Owner | Removes member (`owner` cannot be deleted) |
| `POST` | `/api/v1/organizations/{org_id}/invitations` | JWT | Admin/Owner | Invites user via email (gated by plan seat limits) |
| `GET` | `/api/v1/organizations/{org_id}/invitations` | JWT | Admin/Owner | Lists pending invitations |
| `DELETE` | `/api/v1/organizations/{org_id}/invitations/{id}` | JWT | Admin/Owner | Revokes pending invitation |
| `POST` | `/api/v1/organizations/invitations/{token}/accept` | JWT | User | Accepts invitation and grants workspace membership |
| `GET` | `/api/v1/organizations/{org_id}/usage` | JWT / API Key | Member | Returns current billing period usage summary vs plan limits |

### Organization API Keys (Tenant-Scoped)
| Method | Endpoint | Auth | Min Role | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/organizations/{org_id}/api-keys` | JWT | Admin/Owner | Generates an API Key with scoped permissions (`Cache-Control: no-store`) |
| `GET` | `/api/v1/organizations/{org_id}/api-keys` | JWT | Admin/Owner | Lists organization API keys (masked with 16-char prefix) |
| `GET` | `/api/v1/organizations/{org_id}/api-keys/{key_id}` | JWT | Admin/Owner | Retrieves metadata for a specific key |
| `DELETE`| `/api/v1/organizations/{org_id}/api-keys/{key_id}` | JWT | Admin/Owner | Immediately revokes API key |

---

## 🖥️ Modern Next.js SaaS Dashboard (`/web`)

The repository includes a production-grade, enterprise-ready dashboard application inside `/web`, decoupled and structured for both **Free** and **Pro** tiers:

- **Framework**: Next.js 16 (App Router, Turbopack, React 19) + TypeScript + Tailwind CSS v4.
- **UI Components**: Hand-crafted accessible components based on **shadcn/ui** patterns (Radix Primitives, Lucide icons, Sonner notifications).
- **Dual Authentication**: 
  - **Local Development**: Instant 1-click dev switcher consuming `/api/v1/auth/dev-users` and `/auth/dev-login`.
  - **Production**: Full OpenID Connect integration with AWS Cognito via `oidc-client-ts`.
- **End-to-End Type Safety**: 100% synchronized TypeScript types generated directly from backend OpenAPI schemas via `openapi-typescript` and `openapi-fetch`.
- **Intelligent Server State**: TanStack Query (React Query) configured to distinguish between `402 Payment Required` (quota exhausted, immediate upgrade prompt without retry) and `429 Too Many Requests` (transient rate limiting with exponential backoff).
- **AI Streaming Interface**: Real-time Server-Sent Events (SSE) chat client consuming `POST /api/v1/ai/chat/stream` via native `fetch` and `ReadableStreamDefaultReader` with auto-scroll and quota pre-check warnings.
- **Workspace & Team Management**: Multi-organization switcher with active workspace header (`X-Organization-ID`), role management (`owner`, `admin`, `member`), and cryptographic email invitation links.
- **Developer API Key Management**: Self-service organization API key generator with scoped privileges and secure one-time secret reveal modal.
- **Stripe Billing & Subscriptions**: Interactive subscription plan comparison cards, live trial / plan badge, and direct redirection to Stripe Customer Portal.
- **GDPR Privacy Center**: Machine-readable JSON data export (Art. 15/20) and irreversible account erasure workflow (Art. 17).
- **Internationalization (i18n)**: English by default for global commerce readiness (Lemon Squeezy), with instant in-app Spanish translation toggle.
- **Screaming Modular Architecture**: Segregated under `src/features/` (`auth/`, `overview/`, `ai-chat/`, `teams/`, `usage/`, `api-keys/`, `billing/`, `profile/`, `privacy/`), allowing trivial creation of the Free tier by pruning Pro feature folders and entries from `src/core/features/registry.ts`.

### Running the Dashboard
```bash
# 1. Install frontend dependencies (inside /web)
cd web
pnpm install

# 2. Run the Next.js development server
pnpm dev
# (or from the project root: make web-dev)
```
Open [http://localhost:3000](http://localhost:3000) to view the landing page and dashboard.

---

## 💻 Makefile Shortcuts

| Command | Action |
|---|---|
| `make run` | Starts FastAPI development server with hot-reload (`http://localhost:8000`) |
| `make web-dev` | Starts Next.js development server with Turbopack (`http://localhost:3000`) |
| `make web-build` | Builds production-optimized Next.js bundle |
| `make web-types` | Re-exports `openapi.json` and updates TypeScript definitions |
| `make worker` | Starts the ARQ background worker process (Redis) |
| `make openapi` | Exports static `openapi.json` contract for TypeScript generation |
| `make test` | Runs the full verification suite (`pytest -v`) |
| `make migrate` | Applies Alembic migrations to the database |
| `make seed` | Populates initial demo subscription plans |
| `make docker-up` | Boots the full local stack (API + Postgres + Redis + Mailpit) |
| `make docker-down` | Shuts down local Docker containers |

---

## 👨‍💻 Author & Contact

Crafted with dedication by **Ezequiel** — Full Stack & Backend Engineer.

- 🌐 **Portfolio:** [ezequielsuarez-dev.com](https://www.ezequielsuarez-dev.com/)
- 💼 **LinkedIn:** [linkedin.com/in/ezequiel-suarez-dev](https://www.linkedin.com/in/ezequiel-suarez-dev/)
- 🐙 **GitHub:** [ezequiel-dev93](https://github.com/ezequiel-dev93)
- ✉️ **Contact:** [ezequielsuarez.dev@gmail.com](mailto:ezequielsuarez.dev@gmail.com)

---

## 📄 Commercial License

This project is a commercial digital software product distributed under an **End-User License Agreement (EULA)**:

- ✅ **Allowed**: You are granted a perpetual, non-exclusive license to use, modify, and integrate this Software into an unlimited number of your own commercial applications, SaaS products, and client projects.
- 🔄 **Updates & Support**: Your purchase includes **1 year of repository updates** (new features, bug fixes, security patches) and **direct email support** for integration questions.
- ❌ **Prohibited**: You may not resell, redistribute, sub-license, or publicly share the source code (on public GitHub repositories or elsewhere) as a boilerplate, starter kit, or competing template.

For the full legal terms, see the [`LICENSE`](LICENSE) file.
