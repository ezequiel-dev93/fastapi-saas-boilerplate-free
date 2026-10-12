[English](README.md) | [Español](README.es.md)

# FastAPI SaaS Boilerplate - Web Application (Free Edition)

Modern frontend for **FastAPI SaaS Boilerplate (Free Edition)** built with **Next.js 16 (App Router + Turbopack)**, **React 19**, **Tailwind CSS v4**, and **TanStack React Query v5**. It features end-to-end type safety with **OpenAPI TypeScript**, native bilingual internationalization (English/Spanish), and full support for dark and light modes.

---

## ⚡ Tech Stack

| Category | Technology |
|---|---|
| **Framework** | [Next.js 16.4](https://nextjs.org) (App Router, Turbopack, Server & Client Components) |
| **Core** | [React 19](https://react.dev), [TypeScript 5](https://www.typescriptlang.org) |
| **Styling** | [Tailwind CSS v4](https://tailwindcss.com) with `@tailwindcss/turbopack` |
| **Data Fetching & State** | [TanStack React Query v5](https://tanstack.com/query) |
| **API Client** | [openapi-fetch](https://openapi-ts.dev/openapi-fetch) with compile-time schema types |
| **Authentication** | [oidc-client-ts](https://authts.github.io/oidc-client-ts/) for AWS Cognito + 1-Click Local Dev Auth |
| **Form Management** | [React Hook Form](https://react-hook-form.com) + [Zod](https://zod.dev) validation |
| **UI Components & Icons** | [Lucide React](https://lucide.dev), [Sonner](https://sonner.emilkowal.ski) Toasts, [next-themes](https://github.com/pacocoursey/next-themes) |
| **Package Manager** | [pnpm](https://pnpm.io) (v9+) |

---

## 🚀 Features Included

- **Showcase Landing Page (`/`)**: Feature matrix, technical highlights, and comparison between Free and Pro editions.
- **Dual Authentication (`/login`, `/auth/callback`)**:
  - **Local Development**: Instant one-click login bypassing cloud dependencies (pre-seeded `admin@example.com` and `member@example.com`).
  - **Production**: Full PKCE OAuth2 flow integrated with AWS Cognito User Pools.
- **Dashboard Hub (`/dashboard`)**: Responsive layout with collapsible sidebar, dynamic header, breadcrumbs, and live user state.
- **User Profile Management (`/dashboard/profile`)**: Manage personal details (full name, avatar URL, bio) and account preferences.
- **GDPR Privacy Center (`/dashboard/privacy`)**:
  - **Right of Access & Portability (Art. 15 & 20)**: One-click export of personal profile and preferences in structured JSON.
  - **Right to Erasure (Art. 17)**: Self-service account deletion with confirmation dialog, automated anonymization, and session termination.
- **Internationalization (i18n)**: Instant runtime toggle between English and Spanish across all views.
- **Dark & Light Mode**: Theme switching with persistent preference storage and zero layout flicker.

---

## 📂 Project Structure

```text
web/
├── src/
│   ├── app/                     # Next.js 16 App Router
│   │   ├── (auth)/              # Auth route group (login, Cognito callback)
│   │   ├── (dashboard)/         # Authenticated route group (dashboard, profile, privacy)
│   │   ├── globals.css          # Tailwind CSS v4 styling rules
│   │   ├── layout.tsx           # Root HTML layout with providers (Query, Theme, Auth, i18n)
│   │   └── page.tsx             # Public landing page
│   │
│   ├── components/              # Reusable UI & Layout Components
│   │   ├── layout/              # AppSidebar, Header, LanguageToggle, ThemeToggle
│   │   ├── ui/                  # Atomic primitives: Button, Card, Dialog, Input, Badge, etc.
│   │   └── providers.tsx        # React Context Providers aggregator
│   │
│   ├── core/                    # Core Infrastructure & Cross-cutting logic
│   │   ├── api/                 # openapi-fetch client and schema.d.ts definitions
│   │   ├── auth/                # AuthContext, Token persistence, and Cognito client
│   │   ├── config/              # Validated environment settings (Zod schema)
│   │   ├── i18n/                # Language context and translations (EN/ES)
│   │   └── query/               # TanStack QueryClient configuration
│   │
│   ├── features/                # Domain-Driven View Components
│   │   ├── overview/            # Dashboard main view
│   │   ├── privacy/             # GDPR export and deletion views
│   │   └── profile/             # Profile editing form
│   │
│   └── lib/                     # Utility helpers (cn, clsx, tailwind-merge)
├── package.json                 # Dependencies and scripts
└── tsconfig.json                # TypeScript configuration
```

---

## 🛠️ Getting Started

### 1. Prerequisites
- **Node.js**: `v20.x` or higher
- **pnpm**: `v9.x` or higher (`npm install -g pnpm`)
- **Backend API**: FastAPI backend running (default: `http://localhost:8000`)

### 2. Install Dependencies
```bash
pnpm install
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

Default local configuration:
```ini
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

### 4. Run Development Server
```bash
pnpm dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🔄 Synchronizing Backend OpenAPI Types

When backend endpoints, DTOs, or schemas change in FastAPI, synchronize types end-to-end:

1. From the repository root, export the schema:
   ```bash
   python scripts/export_openapi.py
   ```
2. In the `web/` directory, regenerate TypeScript definitions:
   ```bash
   pnpm generate-types
   ```
This updates `src/core/api/schema.d.ts` with complete compile-time type safety for all API requests and responses.

---

## 📦 Production Build & Quality Checks

```bash
# Typecheck and production bundle build
pnpm build

# Start production server
pnpm start

# Run ESLint validation
pnpm lint
```
