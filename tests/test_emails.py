from unittest.mock import ANY, MagicMock, patch

from api.core.email import (
    render_email_template,
    send_email,
    send_subscription_cancellation_email,
    send_subscription_confirmation_email,
    send_trial_started_email,
)


def test_render_email_templates():
    """Verify that Jinja2 renders email templates properly with context."""
    html = render_email_template("subscription_confirmed.html", plan_name="Enterprise")
    assert "Enterprise" in html
    assert "FastAPI SaaS Boilerplate" in html
    assert "<!DOCTYPE html>" in html

    trial_html = render_email_template("trial_started.html")
    assert "14 días" in trial_html

    cancel_html = render_email_template("subscription_cancelled.html")
    assert "cancelada" in cancel_html


@patch("boto3.client")
def test_send_email_calls_ses(mock_boto_client):
    """Test that send_email constructs and calls SES send_email with text and html."""
    mock_ses = MagicMock()
    mock_boto_client.return_value = mock_ses

    with patch("api.core.config.settings.DEBUG", False):
        with patch("api.core.config.settings.SES_FROM_EMAIL", "noreply@mydomain.com"):
            send_email(
                to_email="customer@example.com",
                subject="Test Subject",
                body_text="Hello customer!",
                body_html="<p>Hello customer!</p>",
            )

            mock_ses.send_email.assert_called_once()
            call_kwargs = mock_ses.send_email.call_args[1]
            assert call_kwargs["Source"] == "noreply@mydomain.com"
            assert call_kwargs["Destination"]["ToAddresses"] == ["customer@example.com"]
            assert call_kwargs["Message"]["Subject"]["Data"] == "Test Subject"
            assert call_kwargs["Message"]["Body"]["Text"]["Data"] == "Hello customer!"
            assert call_kwargs["Message"]["Body"]["Html"]["Data"] == "<p>Hello customer!</p>"


@patch("api.core.email.send_email")
def test_email_helpers_pass_correct_parameters(mock_send):
    """Test helper functions send appropriate subjects, bodies and html templates."""
    send_subscription_confirmation_email("user1@example.com", plan_name="Enterprise")
    mock_send.assert_called_with(
        to_email="user1@example.com",
        subject="Subscription Confirmed - Enterprise",
        body_text="Your subscription to the Enterprise plan has been confirmed. Thank you for joining!",
        body_html=ANY,
    )

    send_subscription_cancellation_email("user2@example.com")
    mock_send.assert_called_with(
        to_email="user2@example.com",
        subject="Subscription Cancelled",
        body_text="Your subscription has been cancelled. You retain full access until the end of your billing cycle.",
        body_html=ANY,
    )

    send_trial_started_email("user3@example.com")
    mock_send.assert_called_with(
        to_email="user3@example.com",
        subject="Welcome to Your Free Trial!",
        body_text="Your 14-day free trial has started. Explore all premium features!",
        body_html=ANY,
    )


@patch("smtplib.SMTP")
def test_send_email_via_smtp_in_dev(mock_smtp_class):
    """Test that in dev mode with USE_DEV_SMTP=True, SMTP/Mailpit is invoked."""
    mock_server = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_server

    with patch("api.core.config.settings.DEBUG", True):
        with patch("api.core.config.settings.USE_DEV_SMTP", True):
            send_email(
                to_email="dev@example.com",
                subject="Local Dev Email",
                body_text="Plain dev body",
                body_html="<p>HTML dev body</p>",
            )

            mock_server.sendmail.assert_called_once()
            args = mock_server.sendmail.call_args[0]
            assert args[1] == ["dev@example.com"]
            assert "Subject: Local Dev Email" in args[2]


def test_dev_emails_gallery_endpoint(client):
    """Verify that /dev/emails renders the email gallery in DEBUG mode."""
    response = client.get("/dev/emails")
    assert response.status_code == 200
    assert "Galería de Emails Transaccionales" in response.text
    assert "trial_started" in response.text


def test_dev_emails_preview_endpoint(client):
    """Verify that /dev/emails/preview/{template} renders the selected email template."""
    response = client.get("/dev/emails/preview/organization_invitation")
    assert response.status_code == 200
    assert "Acme Dynamics Corp" in response.text
    assert "Ezequiel Suarez" in response.text

    # Invalid template returns 404
    bad_resp = client.get("/dev/emails/preview/unknown_template")
    assert bad_resp.status_code == 404
