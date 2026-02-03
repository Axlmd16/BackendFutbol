"""
Tests de interoperabilidad para el servicio de correo SMTP.

Verifica:
- Envío de correos funciona correctamente
- Errores de SMTP retornan mensajes amigables
- SMTP no configurado no hace crashear la app
"""

import smtplib

import pytest

from app.core.config import settings
from app.utils.email_client import send_credentials_email, send_reset_email
from app.utils.exceptions import EmailServiceException


class FakeSMTP:
    """Fake SMTP para simular conexiones exitosas."""

    def __init__(self, host, port, timeout=None):
        self.logged_in = False
        self.sent_messages = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        pass

    def login(self, user, password):
        self.logged_in = True

    def send_message(self, message):
        self.sent_messages.append(message)


class FakeSMTPError:
    """Fake SMTP que simula error de conexión."""

    def __init__(self, host, port, timeout=None):
        raise smtplib.SMTPConnectError(421, "Connection refused")


@pytest.mark.interoperability
class TestSMTPEmailSending:
    """Tests para envío de correos."""

    def test_send_reset_email_success(self, monkeypatch):
        """Verifica que se envía el correo de reset correctamente."""
        created = []

        def _smtp_ssl(host, port, timeout=None):
            client = FakeSMTP(host, port, timeout)
            created.append(client)
            return client

        monkeypatch.setattr("app.utils.email_client.smtplib.SMTP_SSL", _smtp_ssl)
        monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
        monkeypatch.setattr(settings, "SMTP_PORT", 465)
        monkeypatch.setattr(settings, "SMTP_USER", "user@test.com")
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "secret")
        monkeypatch.setattr(settings, "SMTP_FROM", "from@test.com")
        monkeypatch.setattr(settings, "SMTP_SSL", True)
        monkeypatch.setattr(settings, "FRONTEND_URL", "http://frontend.test")

        send_reset_email("dest@test.com", "Test User", "token123")

        assert len(created) == 1
        assert created[0].logged_in is True
        assert len(created[0].sent_messages) == 1

    def test_smtp_not_configured_does_not_crash(self, monkeypatch):
        """Verifica que si SMTP no está configurado, no crashea."""
        monkeypatch.setattr(settings, "SMTP_HOST", None)
        monkeypatch.setattr(settings, "SMTP_PORT", 0)
        monkeypatch.setattr(settings, "SMTP_USER", None)
        monkeypatch.setattr(settings, "SMTP_PASSWORD", None)
        monkeypatch.setattr(settings, "SMTP_FROM", None)
        monkeypatch.setattr(settings, "SMTP_SSL", False)

        # No debe lanzar excepción
        send_credentials_email("dest@test.com", "Test User", "Temp123!")
        send_reset_email("dest@test.com", "Test User", "token123")


@pytest.mark.interoperability
class TestSMTPErrorHandling:
    """Tests para manejo de errores SMTP."""

    def test_connection_error_raises_friendly_exception(self, monkeypatch):
        """Verifica que errores de conexión retornan EmailServiceException."""
        monkeypatch.setattr("app.utils.email_client.smtplib.SMTP", FakeSMTPError)
        monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
        monkeypatch.setattr(settings, "SMTP_PORT", 587)
        monkeypatch.setattr(settings, "SMTP_USER", "user@test.com")
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "secret")
        monkeypatch.setattr(settings, "SMTP_FROM", "from@test.com")
        monkeypatch.setattr(settings, "SMTP_SSL", False)

        with pytest.raises(EmailServiceException) as exc_info:
            send_credentials_email("dest@test.com", "Test User", "Temp123!")

        # El mensaje debe ser amigable, no técnico
        message = exc_info.value.message.lower()
        assert "smtpconnecterror" not in message
        assert "421" not in message
        assert "intente" in message or "disponible" in message

    def test_email_exception_has_503_status(self, monkeypatch):
        """Verifica que EmailServiceException tiene status 503."""
        monkeypatch.setattr("app.utils.email_client.smtplib.SMTP", FakeSMTPError)
        monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
        monkeypatch.setattr(settings, "SMTP_PORT", 587)
        monkeypatch.setattr(settings, "SMTP_USER", "user@test.com")
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "secret")
        monkeypatch.setattr(settings, "SMTP_FROM", "from@test.com")
        monkeypatch.setattr(settings, "SMTP_SSL", False)

        with pytest.raises(EmailServiceException) as exc_info:
            send_credentials_email("dest@test.com", "Test User", "Temp123!")

        assert exc_info.value.status_code == 503


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
