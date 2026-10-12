"""Excepciones de dominio puras desacopladas del protocolo HTTP."""

class DomainError(Exception):
    """Excepción base para todos los errores de la capa de dominio."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UserValidationError(DomainError):
    """Lanzada cuando los datos del perfil de usuario no cumplen las reglas de negocio."""
    def __init__(self, message: str = "Los nombres deben contener 150 caracteres o menos."):
        super().__init__(message=message, status_code=400)


class ActiveTrialExistsError(DomainError):
    """Lanzada cuando un usuario ya tiene una suscripción o período de prueba activo."""
    def __init__(self, message: str = "Ya posees una suscripción o período de prueba activo."):
        super().__init__(message=message, status_code=400)


class TrialAlreadyUsedError(DomainError):
    """Lanzada cuando el período de prueba ya fue consumido previamente."""
    def __init__(self, message: str = "Tu período de prueba gratuito ya ha sido utilizado (already been used)."):
        super().__init__(message=message, status_code=400)


class UserNotFoundError(DomainError):
    """Lanzada cuando un usuario no existe en el sistema."""
    def __init__(self, message: str = "Usuario no encontrado."):
        super().__init__(message=message, status_code=404)


class AccountAlreadyDeletedError(DomainError):
    """Lanzada cuando una cuenta ya fue suprimida/anonimizada."""
    def __init__(self, message: str = "Esta cuenta ha sido eliminada."):
        super().__init__(message=message, status_code=400)
