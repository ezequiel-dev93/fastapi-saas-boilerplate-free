from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse

from api.core.config import settings
from api.core.email import render_email_template

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
        "color": "#10b981",
    },
    {
        "id": "organization_invitation",
        "title": "Invitación a Espacio de Trabajo / Organización",
        "trigger": "Al invitar a un colaborador en /api/v1/organizations/{id}/invitations",
        "badge": "B2B Multi-tenancy",
        "color": "#6366f1",
    },
    {
        "id": "subscription_confirmed",
        "title": "Confirmación de Suscripción / Pago Exitoso",
        "trigger": "Al completar checkout en Stripe o recibir webhook de pago exitoso",
        "badge": "Facturación",
        "color": "#3b82f6",
    },
    {
        "id": "subscription_cancelled",
        "title": "Cancelación de Suscripción (Honest Churn)",
        "trigger": "Al cancelar suscripción al final del ciclo facturado",
        "badge": "Facturación",
        "color": "#f59e0b",
    },
    {
        "id": "payment_failed",
        "title": "Recuperación de Pago Fallido (Dunning / Stripe)",
        "trigger": "Al recibir webhook invoice.payment_failed cuando la tarjeta rechaza el cobro",
        "badge": "Dunning / Retención",
        "color": "#ef4444",
    },
]


@router.get("", response_model=None, response_class=HTMLResponse)
async def list_email_templates():
    """Galería interactiva para previsualizar todas las plantillas de correo en desarrollo."""
    cards_html = ""
    for tmpl in TEMPLATE_METADATA:
        cards_html += f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="background: {tmpl["color"]}15; color: {tmpl["color"]}; font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.05em;">
                        {tmpl["badge"]}
                    </span>
                    <span style="color: #94a3b8; font-size: 13px; font-mono;">{tmpl["id"]}.html</span>
                </div>
                <h3 style="margin: 0 0 8px 0; color: #0f172a; font-size: 18px; font-weight: 600;">{tmpl["title"]}</h3>
                <p style="margin: 0 0 20px 0; color: #64748b; font-size: 14px; line-height: 1.5;"><strong>Disparador:</strong> {tmpl["trigger"]}</p>
            </div>
            <div style="display: flex; gap: 10px;">
                <a href="/dev/emails/preview/{tmpl["id"]}" target="_blank" style="flex: 1; text-align: center; background: #0f172a; color: #ffffff; text-decoration: none; padding: 10px 16px; border-radius: 8px; font-size: 14px; font-weight: 600; transition: background 0.2s;">
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
                background-color: #f8fafc;
                margin: 0;
                padding: 40px 20px;
                color: #0f172a;
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
                font-size: 30px;
                margin: 0 0 10px 0;
                letter-spacing: -0.02em;
            }}
            .header p {{
                color: #64748b;
                font-size: 16px;
                margin: 0;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
                gap: 24px;
            }}
            .badge-env {{
                background: #e0e7ff;
                color: #4338ca;
                padding: 4px 12px;
                border-radius: 9999px;
                font-size: 13px;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <span class="badge-env">Entorno de Desarrollo (DEBUG=True)</span>
                <h1>🎨 Galería de Emails Transaccionales</h1>
                <p>Previsualiza en tiempo real las plantillas Jinja2 renderizadas con datos de prueba realistas.</p>
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
