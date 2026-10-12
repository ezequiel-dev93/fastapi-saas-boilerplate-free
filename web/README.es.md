[English](README.md) | [Español](README.es.md)

# FastAPI SaaS Boilerplate - Aplicación Web (Free Edition)

Frontend moderno para **FastAPI SaaS Boilerplate (Free Edition)** construido con **Next.js 16 (App Router + Turbopack)**, **React 19**, **Tailwind CSS v4** y **TanStack React Query v5**. Cuenta con seguridad de tipos de extremo a extremo mediante **OpenAPI TypeScript**, internacionalización bilingüe nativa (inglés/español) y soporte completo para modo oscuro y claro.

---

## ⚡ Stack Tecnológico

| Categoría | Tecnología |
|---|---|
| **Framework** | [Next.js 16.4](https://nextjs.org) (App Router, Turbopack, Server & Client Components) |
| **Núcleo** | [React 19](https://react.dev), [TypeScript 5](https://www.typescriptlang.org) |
| **Estilos** | [Tailwind CSS v4](https://tailwindcss.com) con `@tailwindcss/turbopack` |
| **Data Fetching y Estado** | [TanStack React Query v5](https://tanstack.com/query) |
| **Cliente de API** | [openapi-fetch](https://openapi-ts.dev/openapi-fetch) con tipado en tiempo de compilación |
| **Autenticación** | [oidc-client-ts](https://authts.github.io/oidc-client-ts/) para AWS Cognito + Login de Desarrollo en 1 Clic |
| **Gestión de Formularios** | [React Hook Form](https://react-hook-form.com) + validaciones con [Zod](https://zod.dev) |
| **Componentes de UI e Íconos** | [Lucide React](https://lucide.dev), Toasts con [Sonner](https://sonner.emilkowal.ski), [next-themes](https://github.com/pacocoursey/next-themes) |
| **Gestor de Paquetes** | [pnpm](https://pnpm.io) (v9+) |

---

## 🚀 Características Incluidas

- **Página de Inicio / Showcase (`/`)**: Matriz de características, destacados técnicos y comparativa entre la edición Free y Pro.
- **Autenticación Dual (`/login`, `/auth/callback`)**:
  - **Desarrollo Local**: Inicio de sesión instantáneo en un clic sin dependencias cloud (usuarios preconfigurados `admin@example.com` y `member@example.com`).
  - **Producción**: Flujo OAuth2 PKCE completo integrado con AWS Cognito User Pools.
- **Panel de Control / Dashboard (`/dashboard`)**: Layout responsivo con barra lateral colapsable, encabezado dinámico, migas de pan y estado de usuario en tiempo real.
- **Gestión de Perfil de Usuario (`/dashboard/profile`)**: Modificación de datos personales (nombre, avatar URL, bio) y configuración de notificaciones/preferencias.
- **Centro de Privacidad GDPR (`/dashboard/privacy`)**:
  - **Derecho de Acceso y Portabilidad (Art. 15 y 20)**: Exportación en un clic del perfil y configuraciones en formato JSON estructurado.
  - **Derecho al Olvido (Art. 17)**: Eliminación de cuenta autoservicio con diálogo de confirmación, anonimización automática y cierre de sesión.
- **Internacionalización (i18n)**: Selector instantáneo entre inglés y español en todas las pantallas.
- **Modo Oscuro y Claro**: Cambio de tema con persistencia de preferencias y sin parpadeo de pantalla.

---

## 📂 Estructura del Proyecto

```text
web/
├── src/
│   ├── app/                     # Next.js 16 App Router
│   │   ├── (auth)/              # Grupo de rutas de autenticación (login, callback Cognito)
│   │   ├── (dashboard)/         # Grupo de rutas autenticadas (dashboard, perfil, privacidad)
│   │   ├── globals.css          # Reglas de estilo de Tailwind CSS v4
│   │   ├── layout.tsx           # Layout HTML raíz con proveedores (Query, Tema, Auth, i18n)
│   │   └── page.tsx             # Landing page pública
│   │
│   ├── components/              # Componentes de UI y Maquetación Reutilizables
│   │   ├── layout/              # AppSidebar, Header, LanguageToggle, ThemeToggle
│   │   ├── ui/                  # Primitivas atómicas: Button, Card, Dialog, Input, Badge, etc.
│   │   └── providers.tsx        # Agregador de Providers de React Context
│   │
│   ├── core/                    # Infraestructura Transversal y Lógica Central
│   │   ├── api/                 # Cliente openapi-fetch y definiciones en schema.d.ts
│   │   ├── auth/                # AuthContext, persistencia de tokens y cliente Cognito
│   │   ├── config/              # Configuración de variables de entorno validadas con Zod
│   │   ├── i18n/                # Contexto de idioma y diccionarios de traducción (EN/ES)
│   │   └── query/               # Configuración de QueryClient de TanStack
│   │
│   ├── features/                # Vistas orientadas al Dominio del Negocio
│   │   ├── overview/            # Vista principal del Dashboard
│   │   ├── privacy/             # Vistas de exportación y eliminación GDPR
│   │   └── profile/             # Formulario de edición de perfil
│   │
│   └── lib/                     # Helpers de utilidad (cn, clsx, tailwind-merge)
├── package.json                 # Dependencias y scripts
└── tsconfig.json                # Configuración de TypeScript
```

---

## 🛠️ Primeros Pasos

### 1. Requisitos Previos
- **Node.js**: `v20.x` o superior
- **pnpm**: `v9.x` o superior (`npm install -g pnpm`)
- **Backend API**: Backend FastAPI ejecutándose (por defecto: `http://localhost:8000`)

### 2. Instalar Dependencias
```bash
pnpm install
```

### 3. Configurar Variables de Entorno
Copia el archivo `.env.example` como `.env.local`:
```bash
cp .env.example .env.local
```

Configuración local por defecto:
```ini
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

### 4. Iniciar el Servidor de Desarrollo
```bash
pnpm dev
```
Abre [http://localhost:3000](http://localhost:3000) en tu navegador.

---

## 🔄 Sincronización de Tipos OpenAPI del Backend

Cuando se modifican endpoints, esquemas o DTOs en FastAPI, sincroniza los tipos de extremo a extremo:

1. Desde la raíz del repositorio, exporta el esquema:
   ```bash
   python scripts/export_openapi.py
   ```
2. En la carpeta `web/`, regenera las definiciones de TypeScript:
   ```bash
   pnpm generate-types
   ```
Esto actualiza `src/core/api/schema.d.ts` garantizando seguridad de tipos en tiempo de compilación.

---

## 📦 Construcción para Producción

```bash
# Comprobación de tipos y empaquetado para producción
pnpm build

# Iniciar servidor de producción
pnpm start

# Validación con ESLint
pnpm lint
```
