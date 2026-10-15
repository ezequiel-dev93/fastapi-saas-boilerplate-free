# FastAPI SaaS Boilerplate (Edición Lite) 🚀

Esta es la **versión Lite / Open Source** del Boilerplate para SaaS en FastAPI. Te proporciona una base sólida y lista para producción para empezar a construir aplicaciones web modernas usando Python y React.

> **¿Buscas la versión PRO?**
> Ahórrate más de 40 horas de desarrollo con la **[Edición PRO de FastAPI SaaS](https://ezequiel-suarez-dev.lemonsqueezy.com)**. Incluye todo lo necesario para lanzar un SaaS de IA rentable este mismo fin de semana:
> - 💳 **Integración con Stripe y LemonSqueezy** (Suscripciones, Webhooks, Portales)
> - 🤖 **Integración con Anthropic Claude 3.5 y OpenAI** (Streaming, Límites de uso)
> - 🏢 **Organizaciones Multi-tenant y Equipos** (Roles RBAC, Invitaciones)
> - 🔑 **Sistema BYOK (Trae Tu Propia API Key)** para tus clientes
> - 🎨 **Dashboard Premium en Next.js** con métricas avanzadas
> - 🧪 **183 Tests Automatizados** (100% de Cobertura)
> 
> 👉 **[Consigue la Edición PRO Aquí](https://ezequiel-suarez-dev.lemonsqueezy.com)**

---

## 🛠️ ¿Qué incluye esta Edición Lite?

### Backend (FastAPI)
- **FastAPI** con Python 3.12+
- **SQLAlchemy 2.0** (Asíncrono) con PostgreSQL
- **Alembic** para Migraciones de Base de Datos
- **Autenticación JWT** (Login, Registro)
- **Sistema Dev Auth** para desarrollo local rápido sin proveedores en la nube

### Frontend (Next.js)
- **Next.js 15** (App Router)
- **Tailwind CSS** + Componentes Radix UI
- **React Query** para consumo de APIs
- **Zod + React Hook Form** para validación
- **Arquitectura Limpia** (Separación de Core, Funcionalidades y UI)

---

## 🚀 Inicio Rápido

### 1. Configuración del Backend
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configurar entorno
cp .env.example .env
# Edita .env con las credenciales de tu base de datos

# Ejecutar migraciones
alembic upgrade head

# Sembrar datos de desarrollo
python seed.py

# Iniciar servidor
make run
```

### 2. Configuración del Frontend
```bash
cd web
pnpm install

# Configurar entorno
cp .env.example .env.local

# Iniciar el servidor de desarrollo
pnpm dev
```

---

## 📜 Licencia
Esta Edición Lite es de código abierto y está disponible bajo la Licencia MIT.

---

## 👨‍💻 Autor y Contacto

Creado por **Ezequiel** — Full Stack & Backend Engineer.

- 🌐 **Portfolio:** [ezequielsuarez-dev.com](https://www.ezequielsuarez-dev.com/)
- 💼 **LinkedIn:** [linkedin.com/in/ezequiel-suarez-dev](https://www.linkedin.com/in/ezequiel-suarez-dev/)
- 🐙 **GitHub:** [ezequiel-dev93](https://github.com/ezequiel-dev93)
- ✉️ **Contacto:** [ezequielsuarez.dev@gmail.com](mailto:ezequielsuarez.dev@gmail.com)
