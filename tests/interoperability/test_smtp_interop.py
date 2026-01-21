import pytest

from app.core.config import settings
from app.utils.email_client import send_credentials_email, send_reset_email


class FakeSMTP:
    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.logged_in = False
        self.starttls_called = False
        self.sent_messages = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        self.starttls_called = True

    def login(self, user, password):
        self.logged_in = True

    def send_message(self, message):
        self.sent_messages.append(message)


@pytest.mark.interoperability
def test_send_reset_email_uses_ssl_and_sends_message(monkeypatch):
    created = []

    def _smtp_ssl(host, port, timeout=None):
        client = FakeSMTP(host, port, timeout=timeout)
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
    client = created[0]
    assert client.logged_in is True
    assert len(client.sent_messages) == 1
    message = client.sent_messages[0]

    assert message["To"] == "dest@test.com"
    assert message["From"] == "from@test.com"
    assert "reset-password?token=token123" in message.get_content()


@pytest.mark.interoperability
def test_send_credentials_email_uses_starttls_when_no_ssl(monkeypatch):
    created = []

    def _smtp(host, port, timeout=None):
        client = FakeSMTP(host, port, timeout=timeout)
        created.append(client)
        return client

    monkeypatch.setattr("app.utils.email_client.smtplib.SMTP", _smtp)

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USER", "user@test.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "secret")
    monkeypatch.setattr(settings, "SMTP_FROM", "from@test.com")
    monkeypatch.setattr(settings, "SMTP_SSL", False)

    send_credentials_email("dest@test.com", "Test User", "Temp123!")

    assert len(created) == 1
    client = created[0]
    assert client.starttls_called is True
    assert client.logged_in is True
    assert len(client.sent_messages) == 1


@pytest.mark.interoperability
def test_send_reset_email_skips_when_not_configured(monkeypatch):
    created = []

    def _smtp_ssl(host, port, timeout=None):
        client = FakeSMTP(host, port, timeout=timeout)
        created.append(client)
        return client

    monkeypatch.setattr("app.utils.email_client.smtplib.SMTP_SSL", _smtp_ssl)

    monkeypatch.setattr(settings, "SMTP_HOST", None)
    monkeypatch.setattr(settings, "SMTP_PORT", 0)
    monkeypatch.setattr(settings, "SMTP_USER", None)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", None)
    monkeypatch.setattr(settings, "SMTP_FROM", None)
    monkeypatch.setattr(settings, "SMTP_SSL", True)

    send_reset_email("dest@test.com", "Test User", "token123")

    assert created == []
