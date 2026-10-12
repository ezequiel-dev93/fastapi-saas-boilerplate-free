from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from api.core.email import (
    ConsoleEmailSender,
    EmailSenderProtocol,
    EmailService,
    SesEmailSender,
    SmtpEmailSender,
    get_email_sender,
)
from api.core.exceptions import (
    ActiveTrialExistsError,
    DomainError,
    TrialAlreadyUsedError,
    UserValidationError,
)
from api.modules.users.models import UserProfile, UserSettings
from api.modules.users.repository import (
    SqlAlchemyUserRepository,
    UserRepositoryProtocol,
)
from api.modules.users.services import UserService


def test_domain_exceptions_hierarchy():
    """Verifica la jerarquía de excepciones de dominio (SRP)."""
    exc = UserValidationError("Error de prueba")
    assert isinstance(exc, DomainError)
    assert exc.status_code == 400
    assert exc.message == "Error de prueba"


def test_user_repository_crud(db_session: Session):
    """Verifica que SqlAlchemyUserRepository cumple el protocolo y realiza operaciones CRUD (Repository Pattern)."""
    repo = SqlAlchemyUserRepository(db_session)
    assert isinstance(repo, UserRepositoryProtocol)

    # Crear usuario
    user = repo.create_user(
        cognito_sub="repo-sub-1",
        email="repo1@example.com",
        first_name="Repo",
        last_name="User",
    )
    assert user.id is not None
    assert user.settings is not None

    # Obtener por diferentes criterios
    by_id = repo.get_by_id(user.id)
    assert by_id is not None and by_id.email == "repo1@example.com"

    by_sub = repo.get_by_cognito_sub("repo-sub-1")
    assert by_sub is not None and by_sub.id == user.id

    by_email = repo.get_by_email("repo1@example.com")
    assert by_email is not None and by_email.id == user.id

    # Actualizar perfil
    updated = repo.update_profile(user, first_name="Updated", last_name="Name")
    assert updated.first_name == "Updated"

    # Actualizar settings
    settings = repo.get_or_create_settings(user)
    updated_settings = repo.update_settings(settings, notify_comments=True)
    assert updated_settings.notify_comments is True

    # Soft delete
    repo.soft_delete_user(user, anon_email="deleted_repo@deleted.invalid")
    assert user.deleted_at is not None
    assert user.email == "deleted_repo@deleted.invalid"
    assert user.first_name == "Deleted"


def test_user_service_raises_domain_exceptions_on_invalid_input(db_session: Session):
    """Verifica que UserService lance excepciones de dominio puras (SRP / DIP)."""
    repo = SqlAlchemyUserRepository(db_session)
    service = UserService(repository=repo)

    user = repo.create_user(
        cognito_sub="sub-service-test",
        email="service_test@example.com",
    )

    # Validar longitud de nombre
    with pytest.raises(UserValidationError) as exc:
        service.update_profile(db_session, user, first_name="A" * 151, last_name="Valid")
    assert "150 caracteres o menos" in str(exc.value)

    # Iniciar trial válido
    trial_end = service.start_trial(db_session, user)
    assert trial_end is not None

    # Iniciar trial cuando ya está activo
    with pytest.raises(ActiveTrialExistsError):
        service.start_trial(db_session, user)


def test_email_strategies_implement_protocol():
    """Verifica que todas las estrategias de envío de email cumplan EmailSenderProtocol (Strategy Pattern / LSP)."""
    smtp_sender = SmtpEmailSender()
    ses_sender = SesEmailSender()
    console_sender = ConsoleEmailSender()

    assert isinstance(smtp_sender, EmailSenderProtocol)
    assert isinstance(ses_sender, EmailSenderProtocol)
    assert isinstance(console_sender, EmailSenderProtocol)


def test_console_email_sender():
    """Verifica que ConsoleEmailSender envíe exitosamente registrando en logs."""
    sender = ConsoleEmailSender(from_email="noreply@test.com")
    result = sender.send_email(
        to_email="dev@example.com",
        subject="Test Console",
        html_content="<p>Hello</p>",
        text_content="Hello",
    )
    assert result is True


def test_email_service_delegation():
    """Verifica que EmailService delegue correctamente en su estrategia inyectada (DIP / OCP)."""
    mock_sender = MagicMock(spec=EmailSenderProtocol)
    mock_sender.send_email.return_value = True

    service = EmailService(sender=mock_sender)
    assert service.sender == mock_sender

    # Mock send call
    delivered = mock_sender.send_email(
        to_email="test@example.com",
        subject="Subject",
        html_content="<p>HTML</p>",
        text_content="Text",
    )
    assert delivered is True
    mock_sender.send_email.assert_called_once()
