# CLAUDE.md - FastAPI SaaS Boilerplate (Free/Lite Edition) Development Guide

## Project Overview
Production-ready FastAPI SaaS boilerplate (Free / Open-Source Edition). Built with strict adherence to **SOLID principles**, **Object-Oriented Programming (OOP)**, and **Design Patterns** (Repository, Strategy, Null Object, Domain Exceptions).

Features in this edition:
- User profile & preferences management (`api/modules/users`)
- Trial lifecycle management with domain integrity validation
- GDPR technical compliance: Right to Data Portability (Export JSON) & Right to Erasure (Soft-deletion & anonymization)
- Unified Authentication: AWS Cognito JWT authentication + Local Dev Auth Bypass
- Pluggable API Key validation via Null Object Pattern (`NullApiKeyValidator`)
- Transactional Emails via Strategy Pattern (Console, SMTP, AWS SES)
- Background job processing with ARQ & Redis fallback
- Modern Next.js 16 frontend with TypeScript & OpenAPI type synchronization

**Stack**: FastAPI 0.115+, Python 3.12, SQLAlchemy 2.0 (Mapped/mapped_column), SQLite/PostgreSQL, Alembic, Redis/ARQ, Next.js 16 (App Router + Turbopack).

---

## Architecture Rules & SOLID Enforcement

### 1. Screaming Modular Architecture
- Domain logic is structured by business domain:
  - `api/modules/users/`: Profile, settings, trials, privacy (GDPR)
  - `api/modules/auth/`: Dev authentication routes, tokens, login bypass
  - `api/core/`: Cross-cutting concerns (database, security, protocols, email strategies, domain exceptions)
- Each module contains: `models.py`, `schemas.py`, `services.py`, `repository.py`, `routes.py`

### 2. SOLID Implementation
| Principle | Implementation |
|---|---|
| **SRP (Single Responsibility)** | Routes handle HTTP and request parsing. Services encapsulate business rules. Repositories handle database persistence. Exception handlers map domain errors to HTTP. |
| **OCP (Open/Closed)** | Email strategies (`EmailSenderProtocol`) and API key validators (`ApiKeyValidatorProtocol`) allow extending functionality without touching core services. |
| **LSP (Liskov Substitution)** | `ConsoleEmailSender`, `SmtpEmailSender`, and `SesEmailSender` are drop-in interchangeable implementations of `EmailSenderProtocol`. `NullApiKeyValidator` safely substitutes any active validator. |
| **ISP (Interface Segregation)** | Focused protocols: `EmailSenderProtocol`, `ApiKeyValidatorProtocol`, `UserRepositoryProtocol`. Clients depend only on what they need. |
| **DIP (Dependency Inversion)** | Services depend on abstractions (`UserRepositoryProtocol`, `EmailSenderProtocol`), injected via factory functions or constructors. |

### 3. Layer Boundaries
```text
routes.py  →  services.py  →  repository.py (UserRepositoryProtocol)  →  models.py (SQLAlchemy 2.0)
                   ↓
             protocols.py  ←  strategies / providers (EmailSenderProtocol, ApiKeyValidatorProtocol)
```
- **Routes** do not execute direct SQL queries; they delegate to Services.
- **Services** do not import `HTTPException`, `Request`, or `Response`. They raise domain exceptions (`DomainError`, `UserValidationError`, `ActiveTrialExistsError`, `TrialAlreadyUsedError`).
- **Repositories** encapsulate SQLAlchemy queries and session state.

---

## Key Patterns Implemented

### 1. Repository Pattern (`api/modules/users/repository.py`)
Decouples domain services from SQLAlchemy ORM operations:
```python
from api.modules.users.repository import UserRepositoryProtocol, get_user_repository

@router.get("/me")
async def get_my_profile(
    user: UserProfile = Depends(get_current_user),
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
):
    ...
```

### 2. Strategy Pattern for Email Delivery (`api/core/email.py`)
Interchangeable email senders depending on environment:
- `ConsoleEmailSender`: Terminal logging for zero-config development
- `SmtpEmailSender`: Mailpit or standard SMTP servers
- `SesEmailSender`: Production AWS SES delivery
```python
from api.core.email import get_email_service

email_service = get_email_service()
await email_service.send_email(
    to_email="user@example.com",
    subject="Welcome",
    html_content="<p>Welcome!</p>",
)
```

### 3. Null Object Pattern for API Key Validation (`api/core/protocols/api_key_provider.py`)
When no external API key validator is registered, the system uses `NullApiKeyValidator` to cleanly reject API key attempts with 401 Unauthorized rather than throwing an unhandled exception or 500 error.

### 4. Custom Domain Exceptions & Global Handlers (`api/core/exceptions.py`)
Services raise strongly typed domain exceptions:
- `UserValidationError` → HTTP 422
- `ActiveTrialExistsError` / `TrialAlreadyUsedError` → HTTP 400
- `EntityNotFoundError` → HTTP 404
Global handler registered in `api/main.py` translates `DomainError` into standard JSON responses automatically.

### 5. GDPR Privacy & Account Erasure (`api/modules/users/privacy_service.py`)
- **Right to Access / Portability (GDPR Art. 15 & 20)**: `GET /api/v1/users/me/export` returns all user data in structured JSON format.
- **Right to Erasure (GDPR Art. 17)**: `DELETE /api/v1/users/me/account` performs soft-anonymization (`deleted_at`), scrubs PII, and cascades user settings deletion.

---

## Common Development Commands

### Backend Commands (Run from workspace root)
```bash
# Run API dev server
uvicorn api.main:app --reload

# Run full test suite (44 tests, 100% green)
pytest -v

# Run database migrations
alembic upgrade head

# Seed initial demo users
python seed.py

# Export OpenAPI schema for frontend code generation
python scripts/export_openapi.py
```

### Frontend Commands (Run from `web/` directory)
```bash
# Install dependencies
pnpm install

# Run frontend dev server (Next.js 16 + Turbopack)
pnpm dev

# Build frontend for production
pnpm build

# Regenerate TypeScript types from openapi.json
pnpm openapi
```

### Testing Strategy
- Tests in `tests/` cover dev auth, health checks, emails, user profile/trial management, GDPR compliance, rate limiting, worker fallbacks, and design patterns.
- Tests are 100% offline and do not require external databases or cloud credentials.