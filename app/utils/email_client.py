"""Cliente simple de correo para notificar credenciales temporales."""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_credentials_email(to_email: str, full_name: str, temp_password: str) -> None:
    """Envía un correo con la contraseña temporal.

    Si la configuración SMTP no está presente, solo se registra el evento.
    """
    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD
    smtp_from = settings.SMTP_FROM or smtp_user
    use_tls = settings.SMTP_TLS

    if not smtp_host or not smtp_port or not smtp_from:
        logger.warning("SMTP no configurado; se omite envío de correo a %s", to_email)
        return

    message = EmailMessage()
    message["Subject"] = "Credenciales temporales"
    message["From"] = smtp_from
    message["To"] = to_email
    message.set_content(
        f"Hola {full_name},\n\n"
        "Se creó una cuenta para ti en la plataforma de Backend Fútbol.\n"
        "Estas son tus credenciales temporales:\n"
        f"Usuario: {to_email}\n"
        f"Contraseña temporal: {temp_password}\n\n"
        "Por seguridad, cámbiala al iniciar sesión.\n"
        "Si no solicitaste esta cuenta, contacta al administrador.\n"
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            if use_tls:
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(message)
        logger.info("Correo de credenciales enviado a %s", to_email)
    except Exception as exc:  # pragma: no cover - entorno sin SMTP
        logger.error("No se pudo enviar correo a %s: %s", to_email, str(exc))
