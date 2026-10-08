# Guía de Configuración: AWS Cognito

Esta guía detalla cómo crear y configurar un **User Pool** de AWS Cognito para la autenticación de usuarios en tu SaaS, y cómo integrarlo con el boilerplate para la validación de tokens JWT (RS256).

---

## 1. Crear un User Pool en AWS Cognito

1. Inicia sesión en la consola de [AWS Management Console](https://console.aws.amazon.com/cognito).
2. Selecciona tu región deseada (ej. `us-east-1`).
3. En el servicio **Amazon Cognito**, haz clic en **Crear grupo de usuarios (Create user pool)**.

### Paso 1: Configurar experiencia de inicio de sesión
- **Proveedores de inicio de sesión**: Selecciona **Grupo de usuarios de Cognito (Cognito user pool)**.
- **Opciones de inicio de sesión de usuarios**: Marca **Correo electrónico (Email)**.

### Paso 2: Configurar requisitos de seguridad
- **Directiva de contraseñas**: Deja los valores predeterminados o ajusta la longitud mínima.
- **Autenticación multifactor (MFA / 2FA)**:
  - **MFA Opcional** (*Optional MFA*): Recomendado para permitir que cada usuario active o desactive 2FA desde su perfil.
  - **MFA Obligatorio** (*Required MFA*): Para aplicaciones B2B con altos estándares de cumplimiento.
  - **Métodos MFA soportados**:
    - **Software Token MFA (TOTP)**: Google Authenticator, Authy, 1Password (Recomendado, sin costo por SMS).
    - **SMS message**: Mensajes de texto SMS vía Amazon SNS.
- **Recuperación de cuentas de usuario**: Marca *Habilitar recuperación automática de mensajes* con entrega por correo electrónico.

### Paso 3: Configurar experiencia de registro
- **Habilitar autoregistro**: Sí.
- **Atributos estándar requeridos**:
  - `email` (obligatorio por defecto)
  - `given_name` (Nombre, opcional o requerido según tu diseño)
  - `family_name` (Apellido, opcional o requerido)

### Paso 4: Configurar entrega de mensajes
- **Correo electrónico**: Para pruebas iniciales, selecciona *Enviar correo electrónico con Cognito* (límite de 50 emails diarios de prueba). Para producción, selecciona *Enviar correo electrónico con Amazon SES*.

---

## 2. Configurar el Cliente de Aplicación (App Client)

El backend y el frontend se comunican con Cognito mediante un App Client:

1. Asigna un nombre al grupo (ej. `saas-user-pool-production`).
2. En la sección **Clientes de aplicaciones (App Clients)**:
   - **Tipo de cliente**: Selecciona **Cliente público (Public client)**.
   - **Nombre del cliente**: `saas-web-frontend`.
   - ⚠️ **IMPORTANTE**: **NO** generes un secreto de cliente (*Do not generate a client secret*). Los clientes públicos (SPAs como React, Next.js o aplicaciones móviles) no pueden mantener secretos seguros.

---

## 3. Configurar Scopes y Dominio de Cognito

1. En la pestaña **Experiencia de inicio de sesión (App integration)** del User Pool:
2. **Dominio de Cognito**: Asigna un prefijo único para tu dominio alojado (ej. `mi-saas-app.auth.us-east-1.amazoncognito.com`).
3. En la configuración de tu cliente de aplicación:
   - **Tipos de concesión de OAuth 2.0 (OAuth Grant Types)**: *Código de autorización (Authorization code grant)* e *Implícito (Implicit)* para pruebas locales.
   - **Ámbitos de OpenID Connect (OpenID Connect Scopes)**: Marca `openid`, `email`, `profile`.
   - **URL de retrollamada permitida (Allowed callback URLs)**:
     - `http://localhost:3000/api/auth/callback/cognito`
     - `https://tudominio.com/api/auth/callback/cognito`

---

## 4. Obtener las Variables de Entorno

Desde la consola de Cognito:
1. Copia el **ID del grupo de usuarios (User Pool ID)** (ej. `us-east-1_AbC123XyZ`).
2. Entra en tu App Client y copia el **ID de cliente de aplicación (App Client ID)** (ej. `7abcdefgh1234567890ijklmn`).
3. Anota la **Región de AWS** (ej. `us-east-1`).

---

## 5. Configuración en el Boilerplate

Coloca los valores en tu archivo `.env`:

```ini
# Configuración de AWS Cognito
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_AbC123XyZ
COGNITO_APP_CLIENT_ID=7abcdefgh1234567890ijklmn
```

---

## 6. ¿Cómo Valida los Tokens el Backend?

El boilerplate implementa validación sin estado y de alto rendimiento en [`api/core/security.py`](file:///c:/Users/ezequ/Documents/software-projects/fastapi-saas-boilerplate/api/core/security.py):

1. **Descarga y Caché de Claves JWKS**: Consulta automáticamente el endpoint público:
   ```text
   https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json
   ```
2. **Verificación Criptográfica (RS256)**: Valida la firma del token JWT recibido en el header `Authorization: Bearer <token>`, verificando:
   - Caducidad (`exp`).
   - Audiencia (`aud` coincidente con `COGNITO_APP_CLIENT_ID`).
   - Emisor (`iss` coincidente con el User Pool).
3. **Mapeo Automático de Usuario**: Al validar el token, extrae el identificador único `sub`, busca el usuario en la base de datos local y, si es la primera vez que ingresa, crea su registro en `UserProfile` y `UserSettings` de forma transparente.
