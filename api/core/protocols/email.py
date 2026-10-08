from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class EmailSenderProtocol(Protocol):
    """Contrato abstracto para proveedores de envío de email (SES, Mailpit/SMTP, Resend, SendGrid)."""

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Envía un email al destinatario especificado."""
        ...
