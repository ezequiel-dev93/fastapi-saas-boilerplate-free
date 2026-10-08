# Guía de Actualización (Upgrading Guide)

Esta guía documenta los cambios arquitectónicos y pasos de migración para actualizar instalaciones anteriores a las versiones modernas de **FastAPI SaaS Boilerplate**.

---

## 🚀 Versión 3.0.0 - AI-Ready SaaS, Cuotas Atómicas & Privacidad GDPR

### Resumen de la Versión
La versión 3.0.0 expande el boilerplate con capacidades empresariales avanzadas para productos impulsados por Inteligencia Artificial:
1. **Motor de IA Agnóstico con Streaming SSE**: Protocolo `AiProviderProtocol` con adaptadores para OpenAI, Gemini y Mock, heartbeats periódicos de 15s y auto-reembolso de créditos ante fallos de inicio.
2. **Medición Atómica y Cuotas de Uso Mensuales**: Tabla `organization_usage`, límite de miembros en invitaciones, sincronización con el ciclo de Stripe y respuesta estructurada `HTTP 402 Payment Required`.
3. **Privacidad Técnica GDPR (Art. 15, 17 y 20)**: Endpoint de exportación de datos estructurados en JSON (`/api/v1/users/me/export`) y eliminación con anonimización suave (`/api/v1/users/me/account`), preservación B2B de API keys y baja asíncrona en AWS Cognito.

### Pasos de Migración

#### 1. Ejecutar Migraciones de Base de Datos
Aplica las tres migraciones de Alembic introducidas en la Fase 3:
```bash
alembic upgrade head
```
- `42993e819a6f`: Añade `SubscriptionPlan.limits` (JSON), `Organization.current_period_start/end` y `UserProfile.deleted_at`.
- `cafa7e63a60e`: Crea la tabla `organization_usage` con índice único por `(organization_id, metric, period_start)` y chequeo de no-negatividad.
- `b817e452a10d`: Crea la tabla inmutable `ai_usage_events` para auditoría de IA (sin almacenar prompts ni respuestas).

#### 2. Configurar Variables de Entorno de IA
Si deseas habilitar proveedores de IA reales, añade en tu archivo `.env`:
```ini
AI_PROVIDER=openai       # o 'gemini' (o 'mock' exclusivamente en desarrollo/testing)
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
GEMINI_API_KEY=AIza...
GEMINI_CHAT_MODEL=gemini-1.5-flash
```

#### 3. Actualizar Endpoints y Consumo de IA
- **Endpoint**: `POST /api/v1/ai/chat/stream`
- **Consumo frontend recomendado**: Utilizar `fetch` con lector de streams asíncrono (`ReadableStreamDefaultReader`) en lugar de `EventSource` nativo para permitir envío de headers (`Authorization` o `X-API-Key`) y payload JSON en método POST.

---

## 🚀 Versión 2.0.0 - Migración a Organization API Keys

### Resumen del Cambio
A partir de la versión 2.0.0, **FastAPI SaaS Boilerplate** adopta un modelo canónico de seguridad enterprise:
- **Identidad Humana (Personas)**: Autenticadas exclusivamente mediante tokens JWT de AWS Cognito. Acceden a perfiles de usuario y gestión de cuentas personales.
- **Identidad de Servicio (Integraciones B2B)**: Autenticadas mediante API Keys vinculadas a una Organización (`OrganizationApiKey`). Soportan prefijo por entorno (`sk_live_` y `sk_test_`), scopes granulares (`Scope.USERS_READ`, `Scope.BILLING_WRITE`, `Scope.AI_GENERATE`, etc.) y sobreviven a cambios de personal en la organización.
- **Deprecación**: Se eliminan las API keys a nivel de usuario (`user_settings.api_key_hash`) para garantizar cero ambigüedad, evitar ataques de escalada de privilegios y simplificar la auditoría.

---

### Pasos de Migración

#### 1. Ejecutar Migraciones de Base de Datos
La migración de Alembic `6504e82721c0_add_organization_api_keys_and_drop_` crea automáticamente la tabla `organization_api_keys` y elimina las columnas legacy de `user_settings`.

```bash
alembic upgrade head
```

#### 2. Regeneración de API Keys (Breaking Change en Integraciones)
Debido a que el nuevo estándar de seguridad requiere prefijos estrictos de entorno (`sk_live_` y `sk_test_`) validados por formato antes de consultar la infraestructura, las API keys legacy de la v1 (sin prefijo, vinculadas al usuario personal) no son compatibles con el validador estricto.

Los administradores (`owner` o `admin`) deben generar nuevas API keys desde el panel de la organización (`/api/v1/organizations/{org_id}/api-keys`) y suministrarlas a sus servicios e integraciones externas con los scopes mínimos necesarios.

#### 3. Actualización de Clientes API
Cualquier integración externa debe actualizarse para utilizar las nuevas API keys generadas:
- **Header recomendado**: `X-API-Key: sk_live_...` (o `sk_test_...` en desarrollo/staging)
- **Header alternativo**: `Authorization: Bearer sk_live_...`

---

### Endpoints Nuevos de Organización
| Método | Endpoint | Descripción | Rol Requerido |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/organizations/{org_id}/api-keys` | Crear API key con scopes específicos (devuelve secreto con `Cache-Control: no-store`) | `owner` o `admin` |
| `GET` | `/api/v1/organizations/{org_id}/api-keys` | Listar todas las keys (con prefijo seguro enmascarado) | `owner` o `admin` |
| `GET` | `/api/v1/organizations/{org_id}/api-keys/{key_id}` | Obtener metadata de una API key específica (aislado por org) | `owner` o `admin` |
| `DELETE` | `/api/v1/organizations/{org_id}/api-keys/{key_id}` | Revocar API key inmediatamente (pasa a `revoked_at != null`) | `owner` o `admin` |
