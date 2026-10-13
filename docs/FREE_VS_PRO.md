# ⚖️ Comparativa: Free Lite Edition vs. Pro Enterprise Edition

Este documento detalla las diferencias técnicas y funcionales entre la versión de código abierto **Free Lite Edition** y la versión avanzada **Pro Enterprise Edition**.

---

## 📊 Matriz Comparativa de Funcionalidades

| Funcionalidad / Módulo | 🟢 Free Lite Edition (Este Repo) | 🚀 Pro Enterprise Edition |
| :--- | :---: | :---: |
| **Framework Base** | FastAPI 0.115+ / Python 3.12 | FastAPI 0.115+ / Python 3.12 |
| **Tipado y Validación** | Pydantic v2 estricto | Pydantic v2 estricto |
| **Autenticación Personas** | AWS Cognito JWT (RS256) | AWS Cognito JWT (RS256) |
| **Modo Desarrollo (Dev Auth)** | Auto-provisión JIT (`/dev/auth`) | Auto-provisión JIT (`/dev/auth`) |
| **Gestión de Perfiles & Settings** | ✅ Incluido | ✅ Incluido |
| **GDPR Art. 15 & 20 (Export)** | ✅ Exportación JSON de usuario | ✅ Exportación con historial B2B e IA |
| **GDPR Art. 17 (Olvido / Supresión)** | ✅ Soft-anonymization de usuario | ✅ Soft-anonymization con preservación de API Keys de empresa |
| **Rate Limiting Distribuido** | ✅ SlowAPI (Memoria / Redis) | ✅ SlowAPI (Redis cluster con tiers por plan) |
| **Worker Asíncrono** | ✅ ARQ + Redis (con fallback síncrono) | ✅ ARQ + Redis (con retries, dead letters y jobs programados) |
| **Emails Transaccionales** | ✅ 4 plantillas Jinja2 + galería `/dev/emails` | ✅ 8+ plantillas Jinja2 (Stripe, Dunning, Invitaciones B2B) |
| **Observabilidad** | ✅ Logs estructurados JSON + Request ID | ✅ Logs JSON + OpenTelemetry + Métricas Prometheus |
| **Frontend Dashboard** | ✅ Next.js 16 + Tailwind v4 + Dark/Light | ✅ Next.js 16 + Billing UI + Org Switcher + AI Playground |
| **Pruebas Automatizadas** | ✅ **44 Tests (100% pasando)** | ✅ **183+ Tests (100% pasando)** |
| **Multi-Tenancy B2B & Workspaces** | ❌ (Uso individual B2C / MVP) | ✅ Organizaciones, slugs, roles (Owner, Admin, Member), invitaciones |
| **API Keys por Tenant** | ❌ (Solo tokens JWT) | ✅ `OrganizationApiKey` (`sk_live_...`), scopes granulares y SHA-256 |
| **Facturación Recurrente (Stripe)** | ❌ (Solo contrato `PaymentGatewayProtocol`) | ✅ Checkout sessions, Customer Portal, Webhooks con deduplicación estricta |
| **Motor de IA con Streaming SSE** | ❌ (No incluido) | ✅ Protocolo agnóstico (`AiProviderProtocol`), adaptadores OpenAI & Gemini, keepalive 15s y auto-reembolso |
| **Medición & Cuotas Atómicas** | ❌ (No incluido) | ✅ Control de cuotas en SQL atómico (`UPDATE ... WHERE used <= limit`), respuesta `HTTP 402` y sync con Stripe |

---

## 🟢 ¿Qué puedes construir con la Free Lite Edition?

La versión **Free Lite** es ideal para:
1. **MVPs y Proyectos B2C**: Lanzar productos con autenticación de usuarios individuales sin necesidad de multi-empresa.
2. **Prototipos y Startups en Fase Semilla**: Probar rápidamente una idea de negocio con una arquitectura limpia, sólida y desacoplada siguiendo los principios SOLID y Screaming Architecture.
3. **Aplicaciones con pasarelas locales o personalizadas**: Implementar tu propio procesador de pagos (MercadoPago, LemonSqueezy, PayU, etc.) extendiendo [`api/core/protocols/payment.py`](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-free/api/core/protocols/payment.py).
4. **Despliegues económicos**: Funciona con un contenedor único en plataformas como Render, Railway o Fly.io, utilizando SQLite para prototipos o PostgreSQL para producción.

---

## 🚀 ¿Cuándo dar el salto a la Pro Enterprise Edition?

La versión **Pro Enterprise** está pensada para productos que requieren:
- **Modelo de Negocio B2B**: Venta a equipos y empresas donde múltiples colaboradores comparten un espacio de trabajo con facturación centralizada.
- **Productos con IA Generativa**: Si tu producto consume LLMs (OpenAI o Google Gemini) y necesitas entregar respuestas en streaming al frontend sin que se corte la conexión y garantizando que ningún usuario sobrepase su cuota contratada.
- **Integraciones vía API para tus clientes**: Permitir que los clientes de tu SaaS creen sus propias API Keys con prefijo seguro y permisos específicos para automatizar procesos desde sus propios servidores.
- **Cobros recurrentes automatizados**: Suscripciones con Stripe listas para usar, con control de impagos (dunning) y portal de clientes de autoservicio.

---

## 🔗 Recursos Relacionados
- [Índice de Documentación](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-free/docs/README.md)
- [Arquitectura del Sistema (ARCHITECTURE.md)](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-free/ARCHITECTURE.md)
- [Guía de Configuración de AWS Cognito](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-free/docs/guides/aws-cognito-setup.md)
- [Guía de Despliegue en Producción](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-free/docs/guides/production-deployment.md)
