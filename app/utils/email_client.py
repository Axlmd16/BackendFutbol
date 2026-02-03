"""Cliente simple de correo para notificar credenciales temporales."""

import logging
import smtplib
import socket
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings
from app.utils.exceptions import EmailServiceException

logger = logging.getLogger(__name__)

# Mensajes de error constantes para evitar duplicación
_ERROR_AUTH = (
    "No se pudo enviar el correo. Error de configuración del servicio de correo."
)
_ERROR_CONNECT = (
    "El servicio de correo no está disponible. Por favor, intente nuevamente más tarde."
)
_ERROR_DISCONNECT = (
    "El servicio de correo se desconectó. Por favor, intente nuevamente más tarde."
)
_ERROR_NETWORK = (
    "No se pudo conectar al servicio de correo. "
    "Por favor, intente nuevamente más tarde."
)
_ERROR_SMTP = (
    "No se pudo enviar el correo electrónico. Por favor, intente nuevamente más tarde."
)
_ERROR_UNEXPECTED = (
    "Ocurrió un error al enviar el correo. Por favor, intente nuevamente más tarde."
)


def _get_smtp_config() -> tuple[
    Optional[str], Optional[int], Optional[str], Optional[str], Optional[str], bool
]:
    """Obtiene la configuración SMTP desde settings.

    Returns:
        Tupla con (host, port, user, password, from_addr, use_ssl)
    """
    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD
    smtp_from = settings.SMTP_FROM or smtp_user
    use_ssl = settings.SMTP_SSL
    return smtp_host, smtp_port, smtp_user, smtp_password, smtp_from, use_ssl


def _send_email(
    message: EmailMessage,
    smtp_host: str,
    smtp_port: int,
    smtp_user: Optional[str],
    smtp_password: Optional[str],
    use_ssl: bool,
    to_email: str,
    log_success_message: str,
) -> None:
    """Envía un email usando la configuración SMTP proporcionada.

    Args:
        message: Mensaje de correo a enviar.
        smtp_host: Host del servidor SMTP.
        smtp_port: Puerto del servidor SMTP.
        smtp_user: Usuario SMTP (opcional).
        smtp_password: Contraseña SMTP (opcional).
        use_ssl: Si usar SSL o STARTTLS.
        to_email: Email del destinatario (para logging).
        log_success_message: Mensaje a loguear en caso de éxito.

    Raises:
        EmailServiceException: Si el envío falla.
    """
    try:
        if use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(message)
        logger.info(log_success_message, to_email)
    except smtplib.SMTPAuthenticationError as exc:
        logger.error("Error de autenticación SMTP para %s: %s", to_email, str(exc))
        raise EmailServiceException(_ERROR_AUTH) from exc
    except smtplib.SMTPConnectError as exc:
        logger.error(
            "No se pudo conectar al servidor SMTP para %s: %s", to_email, str(exc)
        )
        raise EmailServiceException(_ERROR_CONNECT) from exc
    except smtplib.SMTPServerDisconnected as exc:
        logger.error("Servidor SMTP desconectado para %s: %s", to_email, str(exc))
        raise EmailServiceException(_ERROR_DISCONNECT) from exc
    except (socket.timeout, socket.gaierror, socket.error) as exc:
        logger.error("Error de conexión de red SMTP para %s: %s", to_email, str(exc))
        raise EmailServiceException(_ERROR_NETWORK) from exc
    except smtplib.SMTPException as exc:
        logger.error("Error SMTP general para %s: %s", to_email, str(exc))
        raise EmailServiceException(_ERROR_SMTP) from exc
    except Exception as exc:
        logger.error("Error inesperado enviando correo a %s: %s", to_email, str(exc))
        raise EmailServiceException(_ERROR_UNEXPECTED) from exc


def send_credentials_email(to_email: str, full_name: str, temp_password: str) -> None:
    """Envía un correo con la contraseña temporal.

    Args:
        to_email: Destinatario del correo.
        full_name: Nombre del usuario que recibirá las credenciales.
        temp_password: Contraseña temporal generada.

    Raises:
        EmailServiceException: Si el servicio SMTP no está disponible o falla el envío.

    Si la configuración SMTP no está presente, solo se registra el evento.
    """
    smtp_host, smtp_port, smtp_user, smtp_password, smtp_from, use_ssl = (
        _get_smtp_config()
    )

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

    _send_email(
        message=message,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        use_ssl=use_ssl,
        to_email=to_email,
        log_success_message="Correo de credenciales enviado a %s",
    )


def send_reset_email(to_email: str, full_name: str, reset_token: str) -> None:
    """Envía correo con el token de reseteo (o link).

    Args:
        to_email: Destinatario del correo.
        full_name: Nombre del usuario.
        reset_token: Token de restablecimiento que se incluirá en el mensaje.

    Raises:
        EmailServiceException: Si el servicio SMTP no está disponible o falla el envío.

    Si la configuración SMTP no está presente, solo se registra el evento.
    """
    smtp_host, smtp_port, smtp_user, smtp_password, smtp_from, use_ssl = (
        _get_smtp_config()
    )

    if not smtp_host or not smtp_port or not smtp_from:
        logger.warning("SMTP no configurado; se omite envío de reset a %s", to_email)
        logger.info("Token de reset para %s: %s", to_email, reset_token)  # útil en dev
        return

    frontend_base = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_base.rstrip('/')}/reset-password?token={reset_token}"

    message = EmailMessage()
    message["Subject"] = "Restablecer contraseña"
    message["From"] = smtp_from
    message["To"] = to_email
    message.set_content(
        f"Hola {full_name},\n\n"
        "Solicitaste restablecer tu contraseña.\n"
        f"Usa este enlace para continuar: {reset_link}\n\n"
        "Si no fuiste tú, ignora este correo.\n"
    )

    _send_email(
        message=message,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        use_ssl=use_ssl,
        to_email=to_email,
        log_success_message="Correo de reset enviado a %s",
    )
