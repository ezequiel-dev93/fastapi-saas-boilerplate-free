from __future__ import annotations

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
from api.core.protocols.email import EmailSenderProtocol

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "xml"]))


def render_email_template(template_name: str, **context) -> str:
    """Renderiza una plantilla Jinja2 HTML de email con variables de contexto."""
    context.setdefault("project_name", settings.PROJECT_NAME)
    template = jinja_env.get_template(template_name)
    return template.render(**context)


# ──────────────────────────────────────────────────────────────────────────
# Estrategias Concretas de Envío (Strategy Pattern / OCP / LSP)
# ──────────────────────────────────────────────────────────────────────────


class SmtpEmailSender(EmailSenderProtocol):
    """Estrategia de envío mediante SMTP local (ej. Mailpit) para desarrollo."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
    ):
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.user = user or settings.SMTP_USER
        self.password = password or settings.SMTP_PASSWORD
        self.from_email = from_email or settings.SES_FROM_EMAIL

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = to_email

        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        if html_content:
            msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=2) as server:
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(self.from_email, [to_email], msg.as_string())
            logger.info("[DEV SMTP/Mailpit] Email sent to %s | Subject: %s", to_email, subject)
            return True
        except Exception as exc:
            logger.debug("Could not deliver to local SMTP (%s:%s): %s", self.host, self.port, exc)
            return False


class SesEmailSender(EmailSenderProtocol):
    """Estrategia de envío mediante AWS SES para producción."""

    def __init__(self, region_name: Optional[str] = None, from_email: Optional[str] = None):
        self.region_name = region_name or settings.AWS_REGION
        self.from_email = from_email or settings.SES_FROM_EMAIL

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        try:
            client = boto3.client("ses", region_name=self.region_name)
            message_body: dict[str, dict[str, str]] = {}
            if text_content:
                message_body["Text"] = {"Data": text_content, "Charset": "UTF-8"}
            if html_content:
                message_body["Html"] = {"Data": html_content, "Charset": "UTF-8"}

            response = client.send_email(
                Source=self.from_email,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": message_body,
                },
            )
            logger.info("SES email sent to %s. MessageId: %s", to_email, response.get("MessageId"))
            return True
        except (BotoCoreError, ClientError) as e:
            logger.error("Failed to send SES email to %s: %s", to_email, e)
            return False


class ConsoleEmailSender(EmailSenderProtocol):
    """Estrategia de fallback para pruebas o desarrollo sin servidor SMTP activo."""

    def __init__(self, from_email: Optional[str] = None):
        self.from_email = from_email or settings.SES_FROM_EMAIL

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        logger.info("[DEV EMAIL] To: %s | Subject: %s | Body: %s", to_email, subject, text_content or html_content)
        return True


# ──────────────────────────────────────────────────────────────────────────
# Factory y Servicio de Alto Nivel (DIP / OCP)
# ──────────────────────────────────────────────────────────────────────────


def get_email_sender() -> EmailSenderProtocol:
    """Factory que instancia la estrategia de envío adecuada según el entorno."""
    if settings.DEBUG:
        if settings.USE_DEV_SMTP:
            return SmtpEmailSender()
        return ConsoleEmailSender()
    return SesEmailSender()


class EmailService:
    """Servicio de dominio para renderizado y orquestación de emails."""

    def __init__(self, sender: Optional[EmailSenderProtocol] = None):
        self._sender = sender

    @property
    def sender(self) -> EmailSenderProtocol:
        return self._sender or get_email_sender()

    def send(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> bool:
        if settings.DEBUG:
            if settings.USE_DEV_SMTP:
                smtp_sender = SmtpEmailSender()
                delivered = smtp_sender.send_email(
                    to_email=to_email,
                    subject=subject,
                    html_content=body_html or "",
                    text_content=body_text,
                )
                if delivered:
                    return True

            if not settings.SES_FROM_EMAIL.endswith(".com"):
                console_sender = ConsoleEmailSender()
                return console_sender.send_email(
                    to_email=to_email,
                    subject=subject,
                    html_content=body_html or "",
                    text_content=body_text,
                )

        return SesEmailSender().send_email(
            to_email=to_email,
            subject=subject,
            html_content=body_html or "",
            text_content=body_text,
        )


_email_service = EmailService()


def get_email_service() -> EmailService:
    """Inyector de dependencias para FastAPI."""
    return _email_service


# ──────────────────────────────────────────────────────────────────────────
# Helpers de Compatibilidad Retroactiva
# ──────────────────────────────────────────────────────────────────────────


def send_via_smtp(to_email: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
    """Envía email vía SMTP local."""
    sender = SmtpEmailSender()
    return sender.send_email(to_email, subject, html_content=body_html or "", text_content=body_text)


def send_email(to_email: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
    """Punto de entrada compatible para envío de correos."""
    return _email_service.send(to_email=to_email, subject=subject, body_text=body_text, body_html=body_html)


def send_trial_started_email(user_email: str, user_name: Optional[str] = None):
    """Envía email de bienvenida al iniciar período de prueba de 14 días."""
    body_html = render_email_template("trial_started.html", user_name=user_name)
    send_email(
        to_email=user_email,
        subject="Welcome to Your Free Trial!",
        body_text="Your 14-day free trial has started. Explore all premium features!",
        body_html=body_html,
    )


def send_subscription_confirmation_email(user_email: str, plan_name: str = "Pro", user_name: Optional[str] = None):
    """Envía confirmación de suscripción."""
    body_html = render_email_template("subscription_confirmed.html", plan_name=plan_name, user_name=user_name)
    send_email(
        to_email=user_email,
        subject=f"Subscription Confirmed - {plan_name}",
        body_text=f"Your subscription to the {plan_name} plan has been confirmed. Thank you for joining!",
        body_html=body_html,
    )


def send_subscription_cancellation_email(user_email: str, user_name: Optional[str] = None):
    """Envía confirmación de cancelación de suscripción."""
    body_html = render_email_template("subscription_cancelled.html", user_name=user_name)
    send_email(
        to_email=user_email,
        subject="Subscription Cancelled",
        body_text="Your subscription has been cancelled. You retain full access until the end of your billing cycle.",
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
    """Envía email de invitación a organización."""
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
    """Envía email tras fallo de cobro."""
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
