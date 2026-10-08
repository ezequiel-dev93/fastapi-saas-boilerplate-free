> 🇺🇸 **Looking for the English version?** Check out [README.md](README.md).
> 
> ---

# ⚡ FastAPI SaaS Boilerplate (Edición Enterprise Pro)

[![CI Pipeline](https://img.shields.io/badge/CI-passing-10b981.svg)](.github/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-183%20passed-success.svg)](tests/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/license-Commercial%20(EULA)-purple.svg)](LICENSE)

El starter kit de grado de producción, listo para desplegar y diseñado para lanzar aplicaciones SaaS B2B modernas y listas para IA en días, no meses. Desarrollado con **FastAPI**, **AWS Cognito**, **Stripe**, **PostgreSQL**, **Redis** y **AWS SES**.

---

## 🚀 Características Principales

- 🤖 **Motor de IA con Streaming SSE Multi-Proveedor**:
  - Protocolo agnóstico del proveedor (`AiProviderProtocol`) con adaptadores nativos intercambiables:
    - **Anthropic Claude**: `claude-3-5-sonnet`, `claude-3-5-haiku`, `claude-3-opus`.
    - **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `o3-mini`.
    - **Google Gemini**: `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`.
    - **Mock**: Para pruebas locales y CI/CD sin consumir saldo ni requerir conexión externa.
  - Eventos estandarizados en Server-Sent Events (SSE): `meta`, `delta`, `usage`, `done` y `error`.
  - Pings keepalive periódicos `: ping` cada 15 segundos para evitar cortes por timeouts de proxies o firewalls.
  - **Verificación Atómica de Cuota y Reembolso Automático**: La cuota de mensajes se descuenta antes de abrir la conexión; si el proveedor falla antes del primer token, se reembolsa automáticamente el crédito.
  - **Auditoría Inmutable Compatible con GDPR**: Registro de metadatos (timestamps, tokens, modelo) en `ai_usage_events`. **Nunca** almacena prompts ni respuestas de los usuarios.


- 📊 **Medición y Cuotas de Uso Atómicas por Plan**:
  - Actualizaciones atómicas en SQL (`UPDATE organization_usage SET used = used + :n WHERE used + :n <= :limit`). Sin condiciones de carrera ni sobrecostos imprevistos.
  - Respuesta estructurada **`HTTP 402 Payment Required`** al agotar la cuota mensual con metadata de actualización (`metric`, `limit`, `used`, `upgrade_url`), evitando reintentos infinitos provocados por el código 429.
  - **Sincronización con el Ciclo de Facturación**: Fechas alineadas con el período de Stripe (`current_period_start/end`), con fallback automático a mes calendario UTC para planes gratuitos.
  - **Límites de Miembros**: Validación automática del límite de asientos al invitar miembros según `SubscriptionPlan.limits["members"]`.

- 🛡️ **Privacidad y Cumplimiento Técnico GDPR**:
  - **Derecho de Acceso y Portabilidad (Art. 15 y 20)**: `GET /api/v1/users/me/export` exporta en JSON estructurado el perfil, configuraciones, membresías, cliente Stripe, metadatos de API keys y eventos de IA.
  - **Derecho al Olvido / Supresión de Cuenta (Art. 17)**: `DELETE /api/v1/users/me/account` con precondiciones estrictas (`409 Conflict` si existe suscripción activa de Stripe o si es el único dueño de una organización con otros miembros).
  - **Anonimización Suave (Soft-Anonymization)**: Sustituye el email por `deleted_<uuid>@deleted.invalid` (RFC 2606), neutraliza nombres a `Deleted User`, desactiva notificaciones y asigna `deleted_at`.
  - **Preservación B2B de API Keys**: Desvincula el creador de las API keys (`created_by_id = NULL`) para que las integraciones empresariales de la organización sigan funcionando ininterrumpidamente.
  - **Baja Asíncrona en el Proveedor de Identidad**: Encola la eliminación física en AWS Cognito (`admin_delete_user`) vía ARQ/Redis e invalida inmediatamente cualquier token previo con `401 Unauthorized`.

- 🔑 **API Keys de Organización por Tenant**:
  - Keys aisladas a nivel de organización (`OrganizationApiKey`), eliminando las keys personales ambiguas.
  - Prefijos estrictos por entorno (`sk_live_...` para producción, `sk_test_...` para desarrollo/staging) con validación previa a la base de datos.
  - Almacenadas exclusivamente mediante hash criptográfico SHA-256 con prefijo público de 16 caracteres para auditoría.
  - **Scopes Granulares**: Permisos de mínimo privilegio (`billing:read`, `org:admin`, `ai:generate`) con protección anti-escalada.
  - Sobreviven a la salida del empleado: pertenecen a la entidad empresarial.

- 🏢 **Multi-Tenancy y Gestión de Equipos (Workspaces B2B)**:
  - Creación de organizaciones con slugs únicos y propietarios asignados automáticamente.
  - **Control de Acceso Basado en Roles (RBAC)**: `owner`, `admin` y `member` con dependencias reutilizables (`require_org_role`).
  - **Invitaciones Seguras por Correo**: Tokens de un solo uso válidos por 7 días con plantilla HTML responsiva.
  - **Feature Gating**: Dependencia `require_feature` para restringir endpoints según las capacidades contratadas en el plan (`SubscriptionPlan.features`).

- 🔐 **Arquitectura de Autenticación Híbrida**:
  - `AuthContext` unificado que distingue usuarios humanos (JWT) de integraciones automáticas (API Keys).
  - **AWS Cognito**: Verificación de tokens JWT RS256 contra JWKS públicas con auto-provisión JIT de perfil local en producción.
  - **Autenticación Local Sin Dependencias de AWS**: Modo de desarrollo con `DevJwtAuthenticator` y endpoints `/auth/dev-users` y `/auth/dev-login` para inicio de sesión en 1 clic con usuarios del `seed.py`. Totalmente bloqueado (404/403) en producción.
  - **API Keys**: Autenticación vía header `X-API-Key` o `Authorization: Bearer` con guards Deny-by-Default que protegen rutas personales.

- 💳 **Flujo Completo de Pagos y Suscripciones (Stripe)**:
  - API moderna de *Payment Methods*.
  - Versión de API de Stripe fijada (`2026-08-26.dahlia`) para blindar contra cambios retrocompatibles.
  - Creación de suscripciones con clave de idempotencia automática.
  - Webhooks firmados y verificados con **tabla de deduplicación e idempotencia** (`StripeWebhookEvent`).
  - Integración nativa con **Stripe Customer Portal** para autogestión de tarjetas y facturas.
  - Cancelación honesta (`cancel_at_period_end=True`): acceso total hasta el fin del ciclo ya abonado.

- ⚡ **Worker Asíncrono con Redis & ARQ**:
  - Procesamiento en segundo plano no bloqueante para correos, tareas pesadas y bajas de cuentas en Cognito.
  - Fallback automático y transparente para desarrollo local o tests sin necesidad de levantar Redis.

- 🛡️ **Rate Limiting Distribuido (SlowAPI)**:
  - Protección activa contra fuerza bruta y DDoS en endpoints sensibles (`/checkout`, `/invitations`, `/ai/chat/stream`).

- 🎨 **Observabilidad & Rich Logging**:
  - Doble motor de logs: consola interactiva con `rich` en desarrollo y JSON estructurado con trazabilidad `X-Request-ID` en producción.
  - Galería interactiva en `/dev/emails` para previsualizar emails en el navegador.

- 🧪 **183 Tests Automatizados (100% Pasando)**:
  - Cobertura exhaustiva de autenticación dual, IA multi-proveedor, cuotas, GDPR, facturación, webhooks, multi-tenancy, workers y rate limits.

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|---|---|
| **Backend** | FastAPI 0.115+ (Python 3.12) con ASGI Uvicorn |
| **Autenticación** | AWS Cognito (RS256) + Dev JWT Local + Claves de Org (`X-API-Key: sk_live_...`) |
| **Motor de IA** | Streaming SSE + Multi-Proveedor (Mock, OpenAI, Google Gemini, Anthropic Claude) |
| **Cuotas y Medición** | Contadores Atómicos SQL + Sync Período Stripe + Respuestas HTTP 402 |
| **Privacidad GDPR** | Exportación JSON (Art. 15/20) + Anonimización y Baja (Art. 17) |
| **Multi-Tenancy** | Workspaces/Organizaciones, RBAC (`owner`, `admin`, `member`) e Invitaciones |
| **Pagos y Facturación** | Stripe (Payment Methods API + Customer Portal + Webhooks Idempotentes) |
| **Base de Datos** | PostgreSQL 16 (Producción) / SQLite (Desarrollo Local y Tests) |
| **ORM & Migraciones** | SQLAlchemy 2.0 (Sintaxis 2.0 moderna) + Alembic |
| **Worker / Cola** | Redis 7 + ARQ (Worker nativo AsyncIO con fallback síncrono) |
| **Rate Limiting** | SlowAPI (Límites por IP o API Key) |
| **Emails Transaccionales** | AWS SES (Producción) + Mailpit (Local) + Plantillas Jinja2 HTML |
| **Tests Automatizados** | Pytest + TestClient (**183 tests automatizados, 100% pasando**) |
| **Contenedores y CI/CD** | Docker + Docker Compose + GitHub Actions CI |

---

## 🧪 Ejecución de Tests Automatizados

Ejecuta la suite completa de verificación con desglose por dominios:

```bash
python scripts/test_summary.py --html
```

O directamente mediante Pytest:

```bash
pytest -v
```

Resultado esperado (**100% Verde / 183 tests pasando**):
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

## 📡 Resumen de Endpoints de la API

### Salud y Raíz
| Método | Endpoint | Autenticación | Descripción |
|---|---|---|---|
| `GET` | `/health` | Pública | Chequeo de salud activo con base de datos (`SELECT 1`) |
| `GET` | `/` | Pública | Bienvenida con enlaces a documentación |

### Autenticación en Desarrollo Local (Dev Login)
| Método | Endpoint | Autenticación | Descripción |
|---|---|---|---|
| `GET` | `/api/v1/auth/dev-users` | Pública (Dev) | Lista usuarios del seed con sus organizaciones para login en 1 clic (404 en prod) |
| `POST` | `/api/v1/auth/dev-login` | Pública (Dev) | Genera JWT dev instantáneo para pruebas rápidas sin Cognito (404 en prod) |


### Usuarios y Privacidad GDPR
| Método | Endpoint | Autenticación | Descripción |
|---|---|---|---|
| `GET` | `/api/v1/users/me` | JWT | Retorna el perfil y configuración del usuario autenticado |
| `PATCH` | `/api/v1/users/me` | JWT | Actualiza nombre y apellido |
| `GET` | `/api/v1/users/settings` | JWT | Obtiene preferencias de notificación y suscripción |
| `PATCH` | `/api/v1/users/settings` | JWT | Actualiza preferencias de notificación |
| `POST` | `/api/v1/users/trial` | JWT | Inicia período de prueba de 14 días (protegido contra abusos) |
| `GET` | `/api/v1/users/me/export` | JWT | **GDPR Art. 15/20**: Exporta todos los datos personales en formato JSON |
| `DELETE`| `/api/v1/users/me/account` | JWT | **GDPR Art. 17**: Anonimiza cuenta, preserva keys B2B y encola baja en Cognito |

### Motor de IA (Streaming SSE)
| Método | Endpoint | Autenticación | Scope Mínimo | Descripción |
|---|---|---|---|---|
| `POST` | `/api/v1/ai/chat/stream` | JWT o Org API Key | `ai:generate` | Streaming SSE de chat (`meta`, `delta`, `usage`, `done`, `error`) con auto-refund |

### Facturación y Suscripciones (Stripe)
| Método | Endpoint | Autenticación | Descripción |
|---|---|---|---|
| `GET` | `/api/v1/billing/plans` | Pública | Lista planes de suscripción, límites y precios |
| `POST` | `/api/v1/billing/checkout` | JWT | Crea suscripción de Stripe usando un PaymentMethod ID |
| `GET` | `/api/v1/billing/subscription`| JWT | Consulta estado detallado de la suscripción |
| `POST` | `/api/v1/billing/cancel` | JWT | Programa cancelación al finalizar el ciclo abonado |
| `POST` | `/api/v1/billing/portal` | JWT | Genera URL de sesión para el Stripe Customer Portal |
| `POST` | `/api/v1/billing/webhook` | Firma Stripe | Procesa y deduplica eventos de webhook de forma idempotente |

### Organizaciones y Workspaces (Multi-Tenancy B2B)
| Método | Endpoint | Autenticación | Rol Mínimo | Descripción |
|---|---|---|---|---|
| `POST` | `/api/v1/organizations` | JWT | User | Crea organización y asigna al usuario como `owner` |
| `GET` | `/api/v1/organizations` | JWT | Member | Lista las organizaciones a las que pertenece el usuario |
| `GET` | `/api/v1/organizations/{org_id}` | JWT / API Key | Member | Obtiene información de la organización |
| `PATCH` | `/api/v1/organizations/{org_id}` | JWT | Admin/Owner | Actualiza nombre o slug de la organización |
| `GET` | `/api/v1/organizations/{org_id}/members` | JWT / API Key | Member | Lista miembros y roles |
| `PATCH` | `/api/v1/organizations/{org_id}/members/{user_id}` | JWT | Admin/Owner | Modifica el rol de un miembro (`admin` o `member`) |
| `DELETE` | `/api/v1/organizations/{org_id}/members/{user_id}` | JWT | Admin/Owner | Remueve miembro (`owner` no puede ser eliminado) |
| `POST` | `/api/v1/organizations/{org_id}/invitations` | JWT | Admin/Owner | Invita usuario por email (limitado por cupo de miembros) |
| `GET` | `/api/v1/organizations/{org_id}/invitations` | JWT | Admin/Owner | Lista invitaciones pendientes |
| `DELETE` | `/api/v1/organizations/{org_id}/invitations/{id}` | JWT | Admin/Owner | Revoca invitación pendiente |
| `POST` | `/api/v1/organizations/invitations/{token}/accept` | JWT | User | Acepta invitación y une al usuario a la organización |
| `GET` | `/api/v1/organizations/{org_id}/usage` | JWT / API Key | Member | Resumen de consumo del período actual vs límites del plan |

### API Keys de Organización (Por Tenant)
| Método | Endpoint | Autenticación | Rol Mínimo | Descripción |
|---|---|---|---|---|
| `POST` | `/api/v1/organizations/{org_id}/api-keys` | JWT | Admin/Owner | Genera API Key con scopes (`Cache-Control: no-store`) |
| `GET` | `/api/v1/organizations/{org_id}/api-keys` | JWT | Admin/Owner | Lista API keys (enmascaradas con prefijo de 16 caracteres) |
| `GET` | `/api/v1/organizations/{org_id}/api-keys/{key_id}` | JWT | Admin/Owner | Obtiene metadatos de una key específica |
| `DELETE`| `/api/v1/organizations/{org_id}/api-keys/{key_id}` | JWT | Admin/Owner | Revoca inmediatamente la API key |

---

## 🖥️ Dashboard Frontend en Next.js (`/web`)

El repositorio incluye un dashboard enterprise desacoplado y completo dentro de la carpeta `/web`, preparado tanto para la versión **Free** como para la versión **Pro**:

- **Framework**: Next.js 16 (App Router, Turbopack, React 19) + TypeScript + Tailwind CSS v4.
- **Componentes UI**: Componentes accesibles basados en patrones **shadcn/ui** (Radix Primitives, íconos Lucide, notificaciones Sonner).
- **Autenticación Dual**:
  - **Desarrollo Local**: Selector rápido de 1-click consumiendo `/api/v1/auth/dev-users` y `/auth/dev-login`.
  - **Producción**: Integración completa OpenID Connect con AWS Cognito mediante `oidc-client-ts`.
- **Tipado Seguro Extremo a Extremo**: Tipos TypeScript 100% sincronizados generados directamente del esquema OpenAPI del backend con `openapi-typescript` y `openapi-fetch`.
- **Estado de Servidor Inteligente**: TanStack Query (React Query) configurado para distinguir entre `402 Payment Required` (cuota agotada, aviso inmediato de upgrade sin reintentos) y `429 Too Many Requests` (límite transitorio con reintentos exponenciales).
- **Chat de IA con Streaming SSE**: Cliente de chat en tiempo real consumiendo `POST /api/v1/ai/chat/stream` vía `fetch` nativo y `ReadableStreamDefaultReader` con auto-scroll y alerta preventiva de cuota.
- **Gestión de Equipos y Workspaces**: Switcher de organizaciones con header de contexto activo (`X-Organization-ID`), administración de roles (`owner`, `admin`, `member`) e invitaciones por correo electrónico firmadas criptográficamente.
- **Gestión de API Keys**: Generador autoservicio de llaves de organización con permisos granulares (scopes) y modal seguro de revelación única del secreto.
- **Facturación y Suscripciones Stripe**: Tarjetas comparativas de planes, badge en tiempo real del estado de prueba/suscripción y redirección directa al Stripe Customer Portal.
- **Centro de Privacidad GDPR**: Exportación de datos en formato JSON legible por máquina (Art. 15/20) y flujo de supresión de cuenta (Art. 17).
- **Internacionalización (i18n)**: Inglés por defecto para venta global (Lemon Squeezy), con selector instantáneo para traducir a Español.
- **Arquitectura Modular Desacoplada**: Organizado por módulos independientes en `src/features/` (`auth/`, `overview/`, `ai-chat/`, `teams/`, `usage/`, `api-keys/`, `billing/`, `profile/`, `privacy/`). La versión Free se crea simplemente eliminando las carpetas Pro y sus entradas en `src/core/features/registry.ts`.

### Cómo ejecutar el Dashboard
```bash
# 1. Instalar dependencias en /web (usando pnpm)
cd web
pnpm install

# 2. Iniciar el servidor de desarrollo
pnpm dev
# (o desde la raíz del proyecto: make web-dev)
```
Abrí [http://localhost:3000](http://localhost:3000) para ver la landing page y el dashboard.

---

## 💻 Comandos del Makefile

| Comando | Acción |
|---|---|
| `make run` | Inicia el servidor backend FastAPI con recarga automática (`http://localhost:8000`) |
| `make web-dev` | Inicia el dashboard Next.js con Turbopack (`http://localhost:3000`) |
| `make web-build` | Compila el bundle de producción optimizado de Next.js |
| `make web-types` | Regenera el archivo `openapi.json` y actualiza los tipos TypeScript en `/web` |
| `make worker` | Inicia el worker asíncrono ARQ (Redis) |
| `make openapi` | Exporta el contrato estático `openapi.json` |
| `make test` | Ejecuta la suite completa de tests automatizados (`pytest -v`) |
| `make migrate` | Aplica las migraciones de Alembic a la base de datos |
| `make seed` | Puebla los planes iniciales de suscripción |
| `make docker-up` | Levanta todo el stack local (API + Postgres + Redis + Mailpit) |
| `make docker-down` | Detiene y apaga los contenedores Docker locales |

---

## 👨‍💻 Autor y Contacto

Creado con dedicación por **Ezequiel** — Full Stack & Backend Engineer.

- 🌐 **Portfolio:** [ezequielsuarez-dev.com](https://www.ezequielsuarez-dev.com/)
- 💼 **LinkedIn:** [linkedin.com/in/ezequiel-suarez-dev](https://www.linkedin.com/in/ezequiel-suarez-dev/)
- 🐙 **GitHub:** [ezequiel-dev93](https://github.com/ezequiel-dev93)
- ✉️ **Contacto:** [ezequielsuarez.dev@gmail.com](mailto:ezequielsuarez.dev@gmail.com)
