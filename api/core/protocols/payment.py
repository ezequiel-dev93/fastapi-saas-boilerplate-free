from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class PaymentGatewayProtocol(Protocol):
    """Contrato abstracto para pasarelas de pago (Stripe, LemonSqueezy, MercadoPago, etc.)."""

    def create_checkout_session(
        self,
        customer_email: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Crea una sesión de checkout y retorna la URL de redirección."""
        ...

    def construct_webhook_event(
        self,
        payload: bytes,
        sig_header: str,
    ) -> Dict[str, Any]:
        """Verifica la firma criptográfica del webhook y retorna el evento deserializado."""
        ...
