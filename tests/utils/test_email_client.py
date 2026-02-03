"""Tests adicionales para email_client."""

from email.message import EmailMessage
from unittest.mock import MagicMock, patch

import pytest

from app.utils.email_client import _send_email, send_credentials_email, send_reset_email
from app.utils.exceptions import EmailServiceException


class TestSendEmail:
    """Tests para _send_email."""

    @patch("app.utils.email_client.smtplib")
    def test_send_email_success_with_ssl(self, mock_smtp):
        """Envía email exitosamente con SSL."""
        mock_server = MagicMock()
        mock_smtp.SMTP_SSL.return_value.__enter__.return_value = mock_server

        msg = EmailMessage()
        msg["Subject"] = "Test"
        msg["From"] = "from@test.com"
        msg["To"] = "to@test.com"
        msg.set_content("Test content")

        _send_email(
            message=msg,
            smtp_host="smtp.test.com",
            smtp_port=465,
            smtp_user="user@test.com",
            smtp_password="password",
            use_ssl=True,
            to_email="to@test.com",
            log_success_message="Email sent",
        )

        mock_smtp.SMTP_SSL.assert_called_once_with("smtp.test.com", 465, timeout=15)
        mock_server.login.assert_called_once_with("user@test.com", "password")
        mock_server.send_message.assert_called_once()

    @patch("app.utils.email_client.smtplib")
    def test_send_email_success_with_starttls(self, mock_smtp):
        """Envía email exitosamente con STARTTLS."""
        mock_server = MagicMock()
        mock_smtp.SMTP.return_value.__enter__.return_value = mock_server

        msg = EmailMessage()
        msg["Subject"] = "Test"
        msg["From"] = "from@test.com"
        msg["To"] = "to@test.com"

        _send_email(
            message=msg,
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="user@test.com",
            smtp_password="password",
            use_ssl=False,
            to_email="to@test.com",
            log_success_message="Email sent",
        )

        mock_smtp.SMTP.assert_called_once_with("smtp.test.com", 587, timeout=15)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()

    @patch("app.utils.email_client.smtplib")
    def test_send_email_without_auth(self, mock_smtp):
        """Envía email sin autenticación."""
        mock_server = MagicMock()
        mock_smtp.SMTP.return_value.__enter__.return_value = mock_server

        msg = EmailMessage()
        msg["Subject"] = "Test"

        _send_email(
            message=msg,
            smtp_host="smtp.test.com",
            smtp_port=25,
            smtp_user=None,
            smtp_password=None,
            use_ssl=False,
            to_email="to@test.com",
            log_success_message="Email sent",
        )

        # No debe llamar a login si no hay credenciales
        mock_server.login.assert_not_called()

    def test_send_email_smtp_exception(self):
        """Maneja excepción SMTP."""

        msg = EmailMessage()

        # Usar un host inválido que cause excepción
        with pytest.raises(EmailServiceException):
            _send_email(
                message=msg,
                smtp_host="invalid.host.that.does.not.exist.test",
                smtp_port=465,
                smtp_user="user",
                smtp_password="pass",
                use_ssl=True,
                to_email="to@test.com",
                log_success_message="Email sent",
            )


class TestSendCredentialsEmail:
    """Tests para send_credentials_email."""

    @patch("app.utils.email_client._send_email")
    def test_send_credentials_email(self, mock_send):
        """Envía email de credenciales."""
        send_credentials_email(
            to_email="user@test.com", full_name="Test User", temp_password="temp123"
        )

        # Verifica que se llamó a _send_email
        mock_send.assert_called_once()


class TestSendResetEmail:
    """Tests para send_reset_email."""

    @patch("app.utils.email_client._send_email")
    def test_send_reset_email(self, mock_send):
        """Envía email de reset de password."""
        send_reset_email(
            to_email="user@test.com", full_name="Test User", reset_token="abc123token"
        )

        # Verifica que se llamó a _send_email
        mock_send.assert_called_once()


class TestEmailModule:
    """Tests para el módulo de email."""

    def test_email_module_exists(self):
        """Verifica que el módulo existe."""
        from app.utils import email_client

        assert hasattr(email_client, "send_credentials_email")
        assert hasattr(email_client, "send_reset_email")
        assert hasattr(email_client, "_send_email")
