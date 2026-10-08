# Guía de Lanzamiento Comercial: Cómo Vender este Boilerplate

Esta guía contiene la estrategia de monetización, el texto de venta (copywriting de alta conversión), la estructura de precios y la configuración técnica paso a paso para vender este boilerplate en **LemonSqueezy** o **Gumroad**.

---

## 1. Texto de Venta Listo para Copiar y Pegar (Copywriting)

Puedes usar este texto directamente en la descripción de tu producto en **LemonSqueezy** o **Gumroad**:

```markdown
# ⚡ FastAPI SaaS Boilerplate (AI-Ready Enterprise Edition)
### Construye y lanza tu SaaS B2B con IA en días, no meses. Backend listo para producción con FastAPI 0.115+, Motor de IA con Streaming SSE, Cuotas de Uso Atómicas, Cumplimiento GDPR, Stripe Billing y 172 tests automatizados (100% en verde).

---

¿Cansado de perder semanas configurando autenticación, streaming de IA con SSE, webhooks de Stripe que fallan, control de cuotas de uso concurrentes, exportaciones GDPR y roles de equipo cada vez que inicias un proyecto SaaS?

Este starter kit backend te ahorra **más de 180 horas de desarrollo complejo** y te entrega una arquitectura de grado empresarial lista para escalar y facturar desde el primer día.

---

### 🚀 ¿Qué incluye este Boilerplate?

- 🤖 **Motor de IA con Streaming SSE (AI-Ready)**:
  - Protocolo agnóstico del proveedor con adaptadores listos para **OpenAI** (`gpt-4o`, `gpt-4o-mini`), **Google Gemini** (`gemini-1.5-flash`, `gemini-1.5-pro`) y **Mock** (para tests offline sin costo).
  - Eventos estandarizados en SSE (`meta`, `delta`, `usage`, `done`, `error`) con keepalive frames (`: ping`) cada 15 segundos.
  - **Control Atómico de Costos y Auto-Reembolso**: Gating preventivo de saldo y reembolso automático si el proveedor falla antes de entregar el primer token.
  - Auditoría inmutable en base de datos (`ai_usage_events`) solo con metadatos (tokens, modelo, timestamps). Nunca persiste prompts ni respuestas (GDPR-safe).

- 📊 **Medición y Cuotas de Uso Atómicas por Plan**:
  - Control de consumo concurrente en SQL atómico (`UPDATE organization_usage SET used = used + :n WHERE used + :n <= :limit`). Cero condiciones de carrera.
  - Respuesta clara **`HTTP 402 Payment Required`** al agotar la cuota mensual con payload estructurado (`metric`, `limit`, `used`, `upgrade_url`), evitando reintentos infinitos causados por el código 429.
  - Sincronización automática con el ciclo de facturación de Stripe (`current_period_start/end`) o mes calendario UTC para planes gratuitos.
  - Límites de miembros por plan aplicados automáticamente en el flujo de invitaciones.

- 🛡️ **Privacidad Técnica y Cumplimiento GDPR**:
  - **Derecho de Acceso y Portabilidad (Art. 15 y 20)**: `GET /api/v1/users/me/export` exporta en formato JSON estructurado todo el perfil, configuración, organizaciones, cliente Stripe, metadatos de API keys y eventos de IA.
  - **Derecho a la Supresión y Olvido (Art. 17)**: `DELETE /api/v1/users/me/account` con precondiciones estrictas (`HTTP 409 Conflict` si tiene suscripción activa o es el único owner de una organización con otros miembros).
  - **Anonimización Suave (Soft-Anonymization)**: Email a `deleted_<uuid>@deleted.invalid`, nombres neutros, preferencias apagadas y fecha `deleted_at`.
  - **Preservación B2B de API Keys**: Desvincula el creador (`created_by_id = NULL`) para que las integraciones empresariales no se rompan ante la salida de empleados.
  - Encolamiento asíncrono con ARQ para borrado físico en AWS Cognito con invalidación inmediata de tokens (`401 Unauthorized`).

- 🔑 **API Keys de Organización por Tenant**:
  - API Keys vinculadas a la entidad empresarial (`OrganizationApiKey`), eliminando las keys personales ambiguas.
  - Formato estricto por entorno (`sk_live_...` y `sk_test_...`) validado antes de consultar la infraestructura.
  - Hasheadas exclusivamente con SHA-256, mostrando el secreto una única vez (`Cache-Control: no-store`) con prefijo público de 16 caracteres para soporte.
  - **Scopes Granulares**: Mínimo privilegio (`billing:read`, `org:admin`, `ai:generate`) con verificación anti-escalada.

- 🏢 **Multi-Tenancy B2B & Workspaces**: Organizaciones completas, slugs únicos, roles RBAC (`owner`, `admin`, `member`), invitaciones temporales por email con token criptográfico (7 días) y feature gating por plan.
- 🔐 **Autenticación Dual Unificada**: `AuthContext` limpio que separa personas (JWT de **AWS Cognito** con auto-provisión JIT) de integraciones automáticas (API Keys de organización con guards Deny-by-Default).
- 💳 **Pagos Recurrentes con Stripe**: Suscripciones con Payment Methods, **Stripe Customer Portal** para autogestión de facturas y tarjetas, y **webhooks con deduplicación e idempotencia estricta** (tabla `StripeWebhookEvent` que previene cobros duplicados).
- ⚡ **Worker Asíncrono con Redis & ARQ**: Procesamiento pesado en segundo plano y entrega de correos, con fallback síncrono automático para desarrollo local sin Redis.
- 🛡️ **Rate Limiting Distribuido (SlowAPI)**: Protección activa contra ataques de fuerza bruta en endpoints sensibles (`/checkout`, `/invitations`, `/ai/chat/stream`).
- 🎨 **Observabilidad & Rich Logging**: Consola enriquecida con `rich` y tracebacks interactivos en desarrollo; formato JSON estructurado automático en producción con trazabilidad mediante `X-Request-ID`.
- 📧 **Emails Transaccionales con Plantillas HTML**: 4 plantillas responsivas Jinja2 con **galería interactiva en vivo (`/dev/emails`)** y previsualización local en **Mailpit** o envío por **AWS SES**.
- 🏛️ **Screaming Architecture & Principios SOLID**: Código desacoplado en Thin Controllers, Use Case Services y Gateways abstractos con `typing.Protocol`.
- 🧪 **172 Tests Automatizados (100% Pasando en Verde)**: Cobertura exhaustiva de autenticación, IA streaming, cuotas atómicas, GDPR, facturación, RBAC, modelos, workers y rate limits con Pytest.
- 📦 **Listo para Desplegar**: Dockerfile multi-stage, `docker-compose.yml`, pipeline de GitHub Actions (CI/CD) y guías paso a paso para **Render**, **Fly.io**, **Railway** y **AWS ECS**.
- 🌐 **100% Agnóstico al Frontend**: Exportador `make openapi` para generar tipos de TypeScript instantáneos para **Next.js**, **Astro**, React o Flutter.

---

### 🎁 Lo que recibes al comprar:
1. **Acceso al repositorio privado de GitHub por 1 año** con actualizaciones (nuevas features, adaptadores de IA, parches de seguridad).
2. **Soporte directo por email** durante 1 año para dudas de integración y configuración.
3. Descarga directa en archivo `.zip` con el código fuente y migraciones reversibles de Alembic.
4. Documentación completa (`ARCHITECTURE.md`, Guía de Stripe, Guía de Cognito, Guía de Despliegue y Guía de Actualización `UPGRADING.md`).
5. Licencia comercial perpetua para crear proyectos y productos SaaS ilimitados.
```

---

## 2. Estrategia de Precios Recomendada

| Nivel | Precio | Público Objetivo | Beneficios |
| :--- | :--- | :--- | :--- |
| **Standard / Indie License** | **$149 USD** | Desarrolladores individuales e Indie Hackers | Proyectos comerciales ilimitados, código completo con IA y GDPR, **1 año de actualizaciones + soporte por email**. |
| **Team / Agency Enterprise License** | **$249 USD** | Startups y Agencias de Software | Hasta 5 miembros del equipo con acceso al repo privado, proyectos de clientes ilimitados, **1 año de actualizaciones + soporte prioritario**. |

> 💡 *Tip de lanzamiento*: Ofrece un descuento de lanzamiento durante las primeras 48 horas (ej. 30% con el cupón `LAUNCH30`) para generar las primeras ventas y testimonios iniciales.

---

## 3. Configuración en LemonSqueezy (Paso a Paso)

LemonSqueezy es la plataforma recomendada porque actúa como *Merchant of Record* (ellos gestionan los impuestos globales, IVA y facturas de tus clientes):

1. Regístrate en [LemonSqueezy.com](https://www.lemonsqueezy.com/).
2. Ve a **Store > Products > New Product**.
3. **Nombre del Producto**: `FastAPI SaaS Boilerplate (AI-Ready Enterprise Edition)`.
4. **Tipo**: *Digital File* o *Single payment*.
5. **Precio**: `$149.00 USD` (o `$249.00 USD` para licencias de agencia).
6. En la pestaña **Files**:
   - Comprime tu proyecto en un archivo `.zip` (excluyendo `.venv/`, `.pytest_cache/`, `saas.db`).
   - Sube el archivo `fastapi-saas-boilerplate-enterprise-v3.0.zip`.
7. **Integración con GitHub (Invitación Automática)**:
   - Ve a **Settings > Integrations > GitHub**.
   - Conecta tu cuenta de GitHub y selecciona el repositorio privado `fastapi-saas-boilerplate`.
   - Marca la opción para invitar automáticamente al comprador tras completar el pago.

---

## 4. Preguntas Frecuentes para Clientes (FAQ)

#### ¿Por qué elegir FastAPI en lugar de Node.js / Next.js API Routes?
FastAPI ofrece tipado estricto en tiempo de ejecución con Pydantic v2, rendimiento ASGI asíncrono cercano a Go, documentación OpenAPI automática nativa y es el estándar de facto absoluto para integrar modelos de Inteligencia Artificial (OpenAI, Anthropic, Gemini, LangChain, PyTorch).

#### ¿Cómo funciona el módulo de streaming de IA?
Utiliza Server-Sent Events (SSE) con adaptadores asíncronos desacoplados (`AiProviderProtocol`). Viene listo para OpenAI y Google Gemini, y cuenta con un adaptador Mock para ejecutar pruebas sin gastar saldo. Además, incorpora heartbeats cada 15 segundos y reembolso automático de créditos si el proveedor falla antes del primer token.

#### ¿Cómo protege el boilerplate el consumo de cuotas contra ataques o abusos?
Implementa incrementos atómicos en base de datos (`UPDATE ... WHERE used + n <= limit`), evitando condiciones de carrera bajo concurrencia. Cuando se agota el cupo, devuelve `HTTP 402 Payment Required` con payload estructurado para que el frontend invite al usuario a actualizar su plan.

#### ¿El boilerplate cumple con el GDPR?
Sí. Cuenta con endpoints técnicos listos para producción para el Derecho de Acceso y Portabilidad (`GET /api/v1/users/me/export`, Art. 15 y 20) y el Derecho a la Supresión (`DELETE /api/v1/users/me/account`, Art. 17). Además, en la eliminación preserva las API keys empresariales (`created_by_id = NULL`) para no interrumpir integraciones B2B activas.

#### ¿Con qué frontends puedo utilizarlo?
Con cualquiera. El backend es 100% agnóstico. Solo necesitas ejecutar `make openapi` para generar el archivo `openapi.json` y usar herramientas como `openapi-typescript` para tener autocompletado en Next.js, Astro, Vue, React o Flutter.

#### ¿Puedo usarlo para proyectos de clientes?
Sí. La licencia comercial te permite crear proyectos propios y para clientes sin pagar regalías adicionales. Lo único que prohíbe es revender el boilerplate en sí como plantilla competidora.
