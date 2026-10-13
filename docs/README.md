# 📚 FastAPI SaaS Boilerplate (Free Lite Edition) — Documentación

Bienvenido a la documentación oficial de **FastAPI SaaS Boilerplate (Free Lite Edition)**. Este repositorio provee una arquitectura backend robusta con FastAPI 0.115+, tipado estricto con Pydantic v2, autenticación dual (AWS Cognito + Dev Auth local), cumplimiento GDPR, tareas asíncronas con ARQ y un frontend moderno en Next.js 16 con soporte para modo claro y oscuro.

---

## 🗺️ Mapa de Documentación

### 🏛️ Arquitectura y Diseño
- [ARCHITECTURE.md](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-free/ARCHITECTURE.md): English reference for Screaming Architecture, Domain Layer, Services, Protocols and SOLID patterns.
- [ARCHITECTURE.es.md](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-free/ARCHITECTURE.es.md): Especificación arquitectónica completa en español.
- [FREE_VS_PRO.md](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-free/docs/FREE_VS_PRO.md): Matriz comparativa entre la versión Free (Lite) y las características planificadas para la versión Pro (Enterprise).

### 🚀 Guías de Configuración y Despliegue
- [Guía de Configuración: AWS Cognito](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-free/docs/guides/aws-cognito-setup.md): Creación de User Pool, App Client público sin secretos, configuración de OAuth y validación asíncrona de firmas JWKS (RS256).
- [Guía de Despliegue en Producción](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-free/docs/guides/production-deployment.md): Empaquetado Docker multi-stage, variables de entorno seguras, migraciones con Alembic y despliegues en Render, Railway, Fly.io y AWS App Runner / ECS.

### 🧪 Suite de Pruebas y Monitoreo
- [Widget de Tests (HTML)](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-free/docs/test_summary_widget.html): Componente visual de terminal que resume los **44 tests automatizados (100% pasando)** con la paleta de colores de marca.

---

## ⚡ Inicio Rápido (Quickstart)

### Backend
```bash
# 1. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Aplicar migraciones de base de datos
alembic upgrade head

# 4. Iniciar servidor de desarrollo
uvicorn api.main:app --reload --port 8000
```
- **Documentación Interactiva Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Documentación ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Galería de Emails Transaccionales**: [http://localhost:8000/dev/emails](http://localhost:8000/dev/emails) (solo en modo `DEBUG=True`)

### Frontend (Dashboard Next.js)
```bash
cd web
pnpm install
pnpm dev
```
- **Dashboard Web**: [http://localhost:3000](http://localhost:3000)

---

## 🛡️ Características Principales de la Versión Free

| Módulo | Descripción |
| :--- | :--- |
| **Autenticación Dual** | Tokens JWT de AWS Cognito para producción y Dev Auth sin fricción para desarrollo local con auto-provisión Just-In-Time (JIT). |
| **Privacidad & GDPR** | Endpoints nativos para el Derecho de Acceso/Portabilidad (`GET /api/v1/users/me/export`) y Derecho al Olvido (`DELETE /api/v1/users/me/account`) con anonimización suave. |
| **Emails Transaccionales** | Plantillas Jinja2 responsivas con galería de previsualización en vivo (`/dev/emails`), soporte local con Mailpit y envío cloud con AWS SES. |
| **Rate Limiting Distribuido** | Protección SlowAPI contra abusos y fuerza bruta, con respaldo en memoria o Redis. |
| **Background Worker** | Encolamiento asíncrono con ARQ y Redis con fallback síncrono para desarrollo local. |
| **Frontend Dashboard** | Next.js 16 (App Router), Tailwind CSS v4, i18n (Español / Inglés) y temas Dark / Light sincronizados con el backend. |
