import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from jinja2 import Environment, FileSystemLoader, select_autoescape

from api.core.config import settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "xml"]))


def render_email_template(template_name: str, **context) -> str:
    """Render an HTML email template with given context variables."""
    context.setdefault("project_name", settings.PROJECT_NAME)
    template = jinja_env.get_template(template_name)
    return template.render(**context)


def send_via_smtp(to_email: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
    """Attempt to deliver email via local SMTP (e.g. Mailpit). Returns True if successful."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SES_FROM_EMAIL
    msg["To"] = to_email

    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    if body_html:
        msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=2) as server:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SES_FROM_EMAIL, [to_email], msg.as_string())
        logger.info("[DEV SMTP/Mailpit] Email sent to %s | Subject: %s", to_email, subject)
        return True
    except Exception as exc:
        logger.debug("Could not deliver to local SMTP (%s:%s): %s", settings.SMTP_HOST, settings.SMTP_PORT, exc)
        return False


def send_email(to_email: str, subject: str, body_text: str, body_html: Optional[str] = None):
    """Send an email using local SMTP/Mailpit in development, or AWS SES in production.
    Falls back gracefully to logging if dev SMTP server is not active or in DEBUG mode.
    """
    if settings.DEBUG:
        if settings.USE_DEV_SMTP:
            delivered = send_via_smtp(to_email, subject, body_text, body_html)
            if delivered:
                return

        if not settings.SES_FROM_EMAIL.endswith(".com"):
            logger.info("[DEV EMAIL] To: %s | Subject: %s | Body: %s", to_email, subject, body_text)
            return

    try:
        client = boto3.client("ses", region_name=settings.AWS_REGION)
        message_body = {"Text": {"Data": body_text, "Charset": "UTF-8"}}
        if body_html:
            message_body["Html"] = {"Data": body_html, "Charset": "UTF-8"}

        response = client.send_email(
            Source=settings.SES_FROM_EMAIL,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": message_body,
            },
        )
        logger.info("SES email sent to %s. MessageId: %s", to_email, response.get("MessageId"))
    except (BotoCoreError, ClientError) as e:
        logger.error("Failed to send SES email to %s: %s", to_email, e)


def send_subscription_confirmation_email(user_email: str, plan_name: str = "Pro", user_name: Optional[str] = None):
    """Send confirmation email upon successful subscription."""
    body_html = render_email_template("subscription_confirmed.html", plan_name=plan_name, user_name=user_name)
    send_email(
        to_email=user_email,
        subject=f"Subscription Confirmed - {plan_name}",
        body_text=f"Your subscription to the {plan_name} plan has been confirmed. Thank you for joining!",
        body_html=body_html,
    )


def send_subscription_cancellation_email(user_email: str, user_name: Optional[str] = None):
    """Send confirmation email when a user cancels their subscription."""
    body_html = render_email_template("subscription_cancelled.html", user_name=user_name)
    send_email(
        to_email=user_email,
        subject="Subscription Cancelled",
        body_text="Your subscription has been cancelled. You retain full access until the end of your billing cycle.",
        body_html=body_html,
    )


def send_trial_started_email(user_email: str, user_name: Optional[str] = None):
    """Send welcome email when a user starts their 14-day free trial."""
    body_html = render_email_template("trial_started.html", user_name=user_name)
    send_email(
        to_email=user_email,
        subject="Welcome to Your Free Trial!",
        body_text="Your 14-day free trial has started. Explore all premium features!",
        body_html=body_html,
    )


def send_organization_invitation_email(
    to_email: str,
    org_name: str,
    inviter_name: str,
    token: str,
    role: str = "member",
    recipient_name: Optional[str] = None,
    dashboard_base_url: str = "http://localhost:3000",
):
    """Send invitation email with secure one-time token to join an organization."""
    invite_url = f"{dashboard_base_url.rstrip('/')}/invite/{token}"
    body_html = render_email_template(
        "organization_invitation.html",
        org_name=org_name,
        inviter_name=inviter_name,
        role=role,
        invite_url=invite_url,
        recipient_name=recipient_name,
    )
    send_email(
        to_email=to_email,
        subject=f"Invitación para unirte a {org_name}",
        body_text=f"{inviter_name} te ha invitado a unirte a {org_name} con rol {role}. Para aceptar la invitación ingresa a: {invite_url}",
        body_html=body_html,
    )


def send_payment_failed_email(
    to_email: str,
    user_name: Optional[str] = None,
    amount_due: Optional[str] = None,
    portal_url: Optional[str] = None,
):
    """Envía email de notificación y recuperación tras el fallo de un cobro de Stripe (Dunning)."""
    body_html = render_email_template(
        "payment_failed.html",
        user_name=user_name,
        amount_due=amount_due,
        portal_url=portal_url or "http://localhost:3000/dashboard/billing",
    )
    send_email(
        to_email=to_email,
        subject="Acción requerida: No pudimos procesar tu pago",
        body_text="Intentamos procesar el cobro de tu suscripción pero fue rechazado. Por favor actualiza tu tarjeta para evitar interrupciones de servicio.",
        body_html=body_html,
    )
