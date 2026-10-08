# Guía de Configuración: Stripe

Esta guía explica paso a paso cómo configurar tu cuenta de Stripe, crear productos y precios, activar el Customer Portal y configurar los webhooks tanto en desarrollo local como en producción.

---

## 1. Obtener las Claves de API

1. Inicia sesión en tu [Dashboard de Stripe](https://dashboard.stripe.com/).
2. Asegúrate de estar en **Modo de Prueba (Test Mode)** activando el interruptor en la esquina superior derecha.
3. Dirígete a **Desarrolladores > Claves de API (Developers > API Keys)**.
4. Copia tu **Clave secreta (Secret Key)** (comienza con `sk_test_...`).
5. Copia tu **Clave publicable (Publishable Key)** (comienza con `pk_test_...`) para configurarla en tu aplicación frontend.

---

## 2. Crear Productos y Precios

1. Ve a **Catálogo de productos > Productos (Product Catalog > Products)** y haz clic en **+ Añadir producto**.
2. Completa los detalles:
   - **Nombre**: Ej. *Plan Pro*.
   - **Descripción**: *Acceso completo a funcionalidades avanzadas*.
3. En la sección **Información de precios**:
   - **Modelo de precios**: *Precio estándar*.
   - **Precio**: Ej. *29.00 USD*.
   - **Facturación**: *Periódica (Recurring)*.
   - **Período de facturación**: *Mensual (Monthly)*.
4. Guarda el producto y copia el identificador del precio generado (**Price ID**, comienza con `price_...`).

---

## 3. Configurar el Stripe Customer Portal

El Customer Portal permite a tus clientes autogestionar sus tarjetas de crédito, descargar facturas en PDF y cancelar sus suscripciones sin necesidad de que construyas interfaces complejas:

1. En el Dashboard de Stripe, ve a **Configuración > Facturación > Portal de clientes (Settings > Billing > Customer Portal)**.
2. Activa las siguientes opciones:
   - **Permitir a los clientes cancelar suscripciones**: Selecciona *"Al final del período de facturación actual"*.
   - **Permitir a los clientes actualizar sus métodos de pago**: Activar.
   - **Historial de facturación**: Activar descarga de facturas en PDF.
3. En **Términos del servicio y política de privacidad**, añade las URLs de tu aplicación.
4. Haz clic en **Guardar cambios**.

---

## 4. Configurar Webhooks

Los webhooks notifican al boilerplate sobre renovaciones, cancelaciones y pagos fallidos de manera asíncrona.

### Opción A: Desarrollo Local con Stripe CLI (Recomendado)

1. Descarga e instala la herramienta oficial [Stripe CLI](https://stripe.com/docs/stripe-cli):
   ```powershell
   # En Windows usando Scoop o Chocolatey:
   scoop install stripe
   # o
   choco install stripe-cli
   ```
2. Inicia sesión en tu cuenta de Stripe desde la terminal:
   ```bash
   stripe login
   ```
3. Reenvía los eventos de Stripe hacia tu servidor local de FastAPI:
   ```bash
   stripe listen --forward-to localhost:8000/api/v1/billing/webhook
   ```
4. La terminal de Stripe CLI mostrará un secreto de webhook para pruebas:
   ```text
   > Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
5. Copia ese secreto y colócalo en tu archivo `.env` como `STRIPE_WEBHOOK_SECRET`.

### Opción B: Entorno de Producción

1. En el Dashboard de Stripe, dirígete a **Desarrolladores > Webhooks (Developers > Webhooks)**.
2. Haz clic en **+ Añadir un endpoint**.
3. **URL del endpoint**: `https://api.tudominio.com/api/v1/billing/webhook`
4. **Eventos a escuchar**: Selecciona los siguientes eventos esenciales:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Haz clic en **Añadir endpoint**.
6. En la sección **Secreto para firmar (Signing secret)**, haz clic en **Revelar** y copia el valor `whsec_...`.

---

## 5. Variables de Entorno en el Boilerplate

Configura las variables correspondientes en tu archivo `.env`:

```ini
# Configuración de Stripe
STRIPE_SECRET_KEY=sk_test_51...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
STRIPE_API_VERSION=2026-08-26.dahlia
```

---

## 6. Verificación del Flujo

1. Inicia el backend con `make run` o `uvicorn api.main:app --reload`.
2. Realiza un checkout de prueba usando los datos de prueba de Stripe (tarjeta `4242 4242 4242 4242`, cualquier fecha futura y cualquier CVC).
3. Verifica que la tabla `stripe_customers` guarde el `stripe_customer_id` y `stripe_subscription_id`.
4. Comprueba en `/health` y en los logs enriquecidos con `rich` que el evento fue procesado con éxito.
