# FastAPI SaaS Boilerplate (Lite Edition) 🚀

This is the **Lite/Open Source version** of the FastAPI SaaS Boilerplate. It provides a solid, production-ready foundation to start building modern web applications using Python and React.

> **Looking for the PRO version?**
> Save +40 hours of development time with the **[FastAPI SaaS PRO Edition](https://your-lemonsqueezy-link.com)**. It includes everything you need to launch a profitable AI SaaS this weekend:
> - 💳 **Stripe & LemonSqueezy Integration** (Subscriptions, Webhooks, Portals)
> - 🤖 **Anthropic Claude 3.5 & OpenAI Integration** (Streaming, Usage limits)
> - 🏢 **Multi-tenant Organizations & Teams** (RBAC, Invitations)
> - 🔑 **Bring Your Own Key (BYOK) System** for your users
> - 🎨 **Premium Next.js Dashboard UI** with advanced metrics
> - 🧪 **183 Automated Tests** (100% Coverage)
> 
> 👉 **[Get the PRO Edition Here](https://your-lemonsqueezy-link.com)**

---

## 🛠️ What's included in this Lite Edition?

### Backend (FastAPI)
- **FastAPI** with Python 3.12+
- **SQLAlchemy 2.0** (Async) with PostgreSQL
- **Alembic** for Database Migrations
- **JWT Authentication** (Login, Register)
- **Dev Auth System** for fast local development without cloud providers

### Frontend (Next.js)
- **Next.js 15** (App Router)
- **Tailwind CSS** + Radix UI components
- **React Query** for data fetching
- **Zod + React Hook Form** for validation
- **Clean Architecture** (Separation of Core, Features, and UI)

---

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd api
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
alembic upgrade head

# Start the server
make run
```

### 2. Frontend Setup
```bash
cd web
pnpm install

# Setup environment
cp .env.example .env.local

# Start the development server
pnpm dev
```

---

## 📜 License
This Lite Edition is open-source and available under the MIT License.
