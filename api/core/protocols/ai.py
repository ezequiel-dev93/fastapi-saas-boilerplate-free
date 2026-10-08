from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Optional, Protocol, Union


@dataclass(frozen=True, slots=True)
class TextDelta:
    """Fragmento de texto emitido durante el streaming del modelo de IA."""

    text: str


@dataclass(frozen=True, slots=True)
class UsageReport:
    """Metadatos de consumo de tokens reportados al finalizar el stream."""

    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


AiStreamEvent = Union[TextDelta, UsageReport]


class AiProviderError(Exception):
    """Excepción base para errores originados por un proveedor de IA."""

    def __init__(self, message: str, code: str = "provider_error"):
        super().__init__(message)
        self.message = message
        self.code = code


class ProviderAuthError(AiProviderError):
    """Error de credenciales o configuración interna del proveedor (HTTP 503 al cliente)."""

    def __init__(self, message: str = "Credenciales del proveedor de IA no configuradas o inválidas."):
        super().__init__(message, code="provider_auth_error")


class ProviderRateLimited(AiProviderError):
    """El proveedor aguas arriba aplicó throttling o agotó su cuota (HTTP 429)."""

    def __init__(self, message: str = "El proveedor de IA ha rechazado temporalmente la solicitud por límite de tasa."):
        super().__init__(message, code="provider_rate_limited")


class ProviderUnavailable(AiProviderError):
    """El proveedor está temporalmente caído o la llamada superó el tiempo de espera (timeout)."""

    def __init__(self, message: str = "El servicio de IA no se encuentra disponible temporalmente."):
        super().__init__(message, code="provider_unavailable")


class ProviderBadRequest(AiProviderError):
    """El proveedor rechazó la solicitud por parámetros inválidos o bloqueo de políticas de contenido."""

    def __init__(self, message: str = "Parámetros de generación o contenido rechazados por el proveedor."):
        super().__init__(message, code="provider_bad_request")


@dataclass(frozen=True, slots=True)
class ProviderMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class ProviderChatRequest:
    messages: list[ProviderMessage]
    model: str
    temperature: Optional[float] = 0.7
    max_output_tokens: Optional[int] = None


class AiProviderProtocol(Protocol):
    """
    Protocolo formal para adaptadores de proveedores de IA (DIP).
    Permite desacoplar el core del SaaS de SDKs concretos (OpenAI, Gemini, Anthropic, Mock).
    """

    @property
    def name(self) -> str:
        """Nombre identificador del proveedor (ej: 'mock', 'openai', 'gemini')."""
        ...

    async def stream_chat(
        self,
        request: ProviderChatRequest,
    ) -> AsyncIterator[AiStreamEvent]:
        """
        Emite un flujo asíncrono de eventos normalizados (TextDelta y UsageReport).
        """
        ...
