# Guía de Despliegue en Producción

Esta guía describe cómo empaquetar, configurar y desplegar `fastapi-saas-boilerplate` en entornos de producción cloud como **Render**, **Railway**, **Fly.io** o **AWS ECS / App Runner**.

---

## 1. Lista de Verificación para Producción (Production Readiness)

Antes de desplegar en vivo, verifica los siguientes puntos clave:

- [ ] **Base de Datos**: Utilizar **PostgreSQL** administrado (RDS, Supabase, Neon, Railway Postgres). Reemplazar `sqlite:///./saas.db` por `postgresql+psycopg://user:password@host:5432/dbname`.
- [ ] **Redis**: Instancia de Redis 7+ para rate limiting distribuido y colas de background workers.
- [ ] **Entorno**: Configurar `ENVIRONMENT=production` y `DEBUG=False` para activar logs JSON estructurados.
- [ ] **CORS**: Definir `ALLOWED_ORIGINS` con la URL real de tu frontend (ej. `https://app.tudominio.com`).
- [ ] **Migraciones**: Ejecutar `alembic upgrade head` durante la fase de *Release* antes del arranque del tráfico.
- [ ] **Health Check**: Configurar el balanceador para sondear `GET /health` cada 15-30 segundos.

---

## 2. Variables de Entorno Mínimas en Producción

Configura estas variables en tu panel de hosting:

```ini
# Configuración del Sistema
PROJECT_NAME="Mi SaaS Production"
ENVIRONMENT=production
DEBUG=False
ALLOWED_ORIGINS=https://app.tudominio.com

# Base de Datos y Cache
DATABASE_URL=postgresql+psycopg://postgres:secret@db.host.internal:5432/saas_prod
REDIS_URL=redis://default:token@redis.host.internal:6379/0

# AWS Cognito
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_xxxxxxxxx
COGNITO_APP_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...

# Emails Transaccionales (AWS SES)
USE_DEV_SMTP=False
SES_FROM_EMAIL=notificaciones@tudominio.com

# Rate Limiting
ENABLE_RATE_LIMIT=True
RATE_LIMIT_DEFAULT="100/minute"
```

---

## 3. Despliegue con Docker

El proyecto incluye un [`Dockerfile`](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-boilerplate/Dockerfile) optimizado para producción con Python 3.12:

### Construir la imagen localmente:
```bash
docker build -t fastapi-saas-boilerplate:latest .
```

### Ejecutar el contenedor:
```bash
docker run -d \
  -p 8000:8000 \
  --env-file .env.production \
  --name saas-api \
  fastapi-saas-boilerplate:latest
```

---

## 4. Despliegue en Plataformas Cloud

### Opción A: Render (Recomendado para inicio rápido)

1. Conecta tu repositorio de GitHub en [Render](https://render.com/).
2. Crea una **PostgreSQL Database** y un **Redis Instance**.
3. Crea un **Web Service**:
   - **Runtime**: `Docker`
   - **Plan**: Starter o superior.
   - **Release Command** (ejecuta migraciones automáticamente):
     ```bash
     alembic upgrade head
     ```
   - **Start Command**:
     ```bash
     uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
     ```
   - **Health Check Path**: `/health`
4. Crea un **Background Worker** para procesar tareas asíncronas:
   - **Start Command**:
     ```bash
     arq api.worker.WorkerSettings
     ```

---

### Opción B: Railway

1. En [Railway](https://railway.app/), crea un nuevo proyecto e importa tu repositorio.
2. Añade los plugins de **PostgreSQL** y **Redis**.
3. En la configuración del servicio API:
   - Configura el comando de arranque:
     ```bash
     alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 4
     ```
   - Añade las variables de entorno vinculando `${{Postgres.DATABASE_URL}}` y `${{Redis.REDIS_URL}}`.
   - Healthcheck Path: `/health`.

---

### Opción C: Fly.io

1. Instala el CLI de Fly (`flyctl`).
2. Inicializa la app en el directorio del proyecto:
   ```bash
   fly launch
   ```
3. En tu archivo `fly.toml`, define el comando de lanzamiento y health checks:
   ```toml
   app = "mi-saas-api"
   primary_region = "iad"

   [deploy]
     release_command = "alembic upgrade head"

   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = false
     auto_start_machines = true
     min_machines_running = 1

     [http_service.checks]
       [http_service.checks.health]
         grace_period = "10s"
         interval = "30s"
         method = "GET"
         path = "/health"
         timeout = "5s"
   ```
4. Despliega con:
   ```bash
   fly deploy
   ```

---

### Opción D: AWS ECS / AWS App Runner

Para despliegues empresariales en Amazon Web Services:
1. Publica tu imagen Docker en **Amazon ECR (Elastic Container Registry)**.
2. Utiliza **AWS App Runner** (la forma más sencilla de ejecutar contenedores en AWS con balanceo y escalado automático) o **AWS ECS Fargate**.
3. En la configuración de red de App Runner o ECS, apunta a tu base de datos **Amazon RDS PostgreSQL** y **Amazon ElastiCache Redis**.
4. Health check URL: `/health` (espera código 200).

---

## 5. Estrategia de Migraciones con Alembic

En producción, **nunca ejecutes migraciones manuales en contenedores en ejecución**. La práctica estándar es:
1. **Fase de Release**: Se ejecuta `alembic upgrade head` en un contenedor efímero antes de reemplazar los contenedores de la versión anterior.
2. Si la migración falla, el despliegue se cancela automáticamente y los contenedores antiguos continúan sirviendo tráfico sin interrupción.

---

## 6. Monitoreo y Alertas

1. **Health Check (`/health`)**:
   - Responde HTTP 200 con `{"status": "ok", "database": "connected"}` si la base de datos responde.
   - Responde HTTP 503 con `{"detail": "Database connection failed: ..."}` si la conexión con PostgreSQL cae.
2. **Logs Estructurados**:
   - Con `ENVIRONMENT=production`, cada petición y error se formatea en JSON puro. Puedes enviar los logs directamente a Datadog, Grafana Cloud o AWS CloudWatch Logs Insights para consultar latencias, errores 500 y rastrear solicitudes mediante el campo `request_id`.
