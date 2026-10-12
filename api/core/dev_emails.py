from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse

from api.core.config import settings
from api.core.email import render_email_template
from api.core.theme import DARK_PALETTE, LIGHT_PALETTE

router = APIRouter(prefix="/dev/emails", tags=["Herramientas de Desarrollo"])

SAMPLE_CONTEXTS: Dict[str, Dict[str, Any]] = {
    "trial_started": {
        "project_name": settings.PROJECT_NAME,
        "user_name": "Ezequiel",
        "dashboard_url": "http://localhost:3000/dashboard",
        "trial_days": 14,
        "trial_end_date": "21 de Septiembre, 2026",
    },
    "organization_invitation": {
        "project_name": settings.PROJECT_NAME,
        "recipient_name": "Valeria",
        "org_name": "Acme Dynamics Corp",
        "inviter_name": "Ezequiel Suarez",
        "role": "Administrador",
        "invite_url": "http://localhost:3000/invitations/accept?token=sample_cryptographic_token_xyz",
    },
    "subscription_confirmed": {
        "project_name": settings.PROJECT_NAME,
        "user_name": "Ezequiel",
        "plan_name": "Pro Anual",
        "amount": "$190.00 USD / año",
        "dashboard_url": "http://localhost:3000/dashboard",
    },
    "subscription_cancelled": {
        "project_name": settings.PROJECT_NAME,
        "user_name": "Ezequiel",
        "dashboard_url": "http://localhost:3000/dashboard/billing",
        "period_end_date": "30 de Septiembre, 2026",
    },
    "payment_failed": {
        "project_name": settings.PROJECT_NAME,
        "user_name": "Ezequiel",
        "amount_due": "$49.00 USD",
        "portal_url": "http://localhost:3000/dashboard/billing/portal",
    },
}

TEMPLATE_METADATA = [
    {
        "id": "trial_started",
        "title": "Bienvenida a Período de Prueba (14 Días)",
        "trigger": "Al registrarse o activar el trial desde /api/v1/users/trial",
        "badge": "Onboarding",
        "color": DARK_PALETTE["acid_yellow"],
        "bg": "#1e2205",
    },
    {
        "id": "organization_invitation",
        "title": "Invitación a Espacio de Trabajo / Organización",
        "trigger": "Al invitar a un colaborador en /api/v1/organizations/{id}/invitations",
        "badge": "B2B Multi-tenancy",
        "color": LIGHT_PALETTE["smoke_gray"],
        "bg": "#1c2014",
    },
    {
        "id": "subscription_confirmed",
        "title": "Confirmación de Suscripción / Pago Exitoso",
        "trigger": "Al completar checkout en Stripe o recibir webhook de pago exitoso",
        "badge": "Facturación",
        "color": LIGHT_PALETTE["neon_lime"],
        "bg": "#162405",
    },
    {
        "id": "subscription_cancelled",
        "title": "Cancelación de Suscripción (Honest Churn)",
        "trigger": "Al cancelar suscripción al final del ciclo facturado",
        "badge": "Facturación",
        "color": DARK_PALETTE["hot_orange"],
        "bg": "#2b1404",
    },
    {
        "id": "payment_failed",
        "title": "Recuperación de Pago Fallido (Dunning / Stripe)",
        "trigger": "Al recibir webhook invoice.payment_failed cuando la tarjeta rechaza el cobro",
        "badge": "Dunning / Retención",
        "color": DARK_PALETTE["hot_orange"],
        "bg": "#2b1404",
    },
]


@router.get("", response_model=None, response_class=HTMLResponse)
async def list_email_templates():
    """Galería interactiva para previsualizar todas las plantillas de correo en desarrollo."""
    cards_html = ""
    for tmpl in TEMPLATE_METADATA:
        cards_html += f"""
        <div style="background: #181818; border: 1px solid #2e2e2e; border-radius: 14px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                    <span style="background: {tmpl["bg"]}; color: {tmpl["color"]}; border: 1px solid {tmpl["color"]}40; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.05em;">
                        {tmpl["badge"]}
                    </span>
                    <span style="color: {DARK_PALETTE["concrete_gray"]}; font-size: 13px; font-family: monospace;">{tmpl["id"]}.html</span>
                </div>
                <h3 style="margin: 0 0 8px 0; color: #FFFFFF; font-size: 18px; font-weight: 700;">{tmpl["title"]}</h3>
                <p style="margin: 0 0 20px 0; color: #a0a0a0; font-size: 14px; line-height: 1.5;"><strong>Disparador:</strong> {tmpl["trigger"]}</p>
            </div>
            <div style="display: flex; gap: 10px;">
                <a href="/dev/emails/preview/{tmpl["id"]}" target="_blank" style="flex: 1; text-align: center; background: {DARK_PALETTE["acid_yellow"]}; color: {DARK_PALETTE["postes_black"]}; text-decoration: none; padding: 12px 16px; border-radius: 10px; font-size: 14px; font-weight: 700; transition: opacity 0.2s;">
                    Abrir en Pantalla Completa ↗
                </a>
            </div>
        </div>
        """

    page_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Galería de Plantillas de Email - {settings.PROJECT_NAME}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background-color: {DARK_PALETTE["postes_black"]};
                margin: 0;
                padding: 40px 20px;
                color: #FFFFFF;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
            }}
            .header {{
                margin-bottom: 36px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 32px;
                margin: 0 0 10px 0;
                letter-spacing: -0.02em;
                color: {DARK_PALETTE["flash_white"]};
            }}
            .header p {{
                color: {DARK_PALETTE["concrete_gray"]};
                font-size: 16px;
                margin: 0;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
                gap: 24px;
            }}
            .badge-env {{
                background: #1f2405;
                color: {DARK_PALETTE["acid_yellow"]};
                border: 1px solid {DARK_PALETTE["acid_yellow"]}40;
                padding: 5px 14px;
                border-radius: 9999px;
                font-size: 12px;
                font-weight: 700;
                display: inline-block;
                margin-bottom: 14px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span class="badge-env">⚡ Entorno de Desarrollo (DEBUG=True)</span>
                <h1>Galería de Emails Transaccionales</h1>
                <p>Previsualiza en tiempo real las plantillas Jinja2 con la paleta oficial del sistema de diseño.</p>
            </div>
            <div class="grid">
                {cards_html}
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=page_html)


@router.get("/preview/{template_name}", response_model=None, response_class=HTMLResponse)
async def preview_email(template_name: str):
    """Renderiza una plantilla de correo específica con datos de prueba."""
    clean_name = template_name.replace(".html", "")
    if clean_name not in SAMPLE_CONTEXTS:
        available = ", ".join(SAMPLE_CONTEXTS.keys())
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plantilla '{template_name}' no encontrada. Disponibles: {available}",
        )

    context = SAMPLE_CONTEXTS[clean_name]
    html_content = render_email_template(f"{clean_name}.html", **context)
    return HTMLResponse(content=html_content)
