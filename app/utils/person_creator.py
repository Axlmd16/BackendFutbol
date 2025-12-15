# app/utils/person_creator.py
import logging
from typing import Dict, Any

from app.client.person_client import PersonClient
from app.utils.exceptions import ValidationException
from app.utils.security import validate_ec_dni

logger = logging.getLogger(__name__)


async def create_person_with_account_in_ms(
    first_name: str,
    last_name: str,
    dni: str,
    email: str,
    password: str,
    type_identification: str = "CEDULA",
    type_stament: str = "GENERAL",
    direction: str | None = None,
    phone: str | None = None,
) -> Dict[str, Any]:
    """
    Crea una persona con cuenta en el MS institucional de usuarios.
    """
    # Validar y limpiar datos
    first_name = first_name.strip()
    last_name = last_name.strip()
    email = email.strip().lower()
    dni = validate_ec_dni(dni)
    
    if not first_name or not last_name:
        raise ValidationException("Nombre y apellidos son requeridos")
    
    # Preparar payload para el MS
    person_payload = {
        "first_name": first_name,
        "last_name": last_name,
        "identification": dni,
        "type_identification": type_identification,
        "type_stament": type_stament,
        "direction": direction or "S/N",
        "phono": phone or "S/N",
        "email": email,
        "password": password,
    }
    
    person_client = PersonClient()
    
    # 1) Crear persona + cuenta en el MS
    try:
        save_resp = await person_client.create_person_with_account(person_payload)
    except Exception as e:
        logger.error(f"Error al llamar a save-account en MS usuarios: {e}")
        raise ValidationException("No se pudo registrar la persona en el sistema institucional")
    
    if save_resp.get("status") != "success":
        raise ValidationException(f"Error desde MS de usuarios: {save_resp.get('message')}")
    
    # 2) Obtener external_id consultando por DNI
    try:
        person_data = await person_client.get_by_identification(dni)
    except Exception as e:
        logger.error(f"Error al obtener persona por DNI en MS usuarios: {e}")
        raise ValidationException("La persona se creó pero no se pudo recuperar del sistema institucional")
    
    person = person_data.get("data") or {}
    external_person_id = person.get("external")
    external_account_id = person.get("external")
    
    if not external_person_id:
        raise ValidationException("El MS de usuarios no devolvió external_id de la persona")
    
    full_name = f"{first_name} {last_name}"
    
    return {
        "external_person_id": external_person_id,
        "external_account_id": external_account_id,
        "full_name": full_name,
        "dni": dni,
        "email": email,
    }


async def create_person_only_in_ms(
    first_name: str,
    last_name: str,
    dni: str,
    type_identification: str = "CEDULA",
    type_stament: str = "GENERAL",
    direction: str | None = None,
    phone: str | None = None,
) -> Dict[str, Any]:
    """
    Crea solo una persona (sin cuenta) en el MS institucional de usuarios.
    Útil para registrar atletas, familiares, etc. que no necesitan login.
    """
    # Validar y limpiar datos
    first_name = first_name.strip()
    last_name = last_name.strip()
    dni = validate_ec_dni(dni)
    
    if not first_name or not last_name:
        raise ValidationException("Nombre y apellidos son requeridos")
    
    # Preparar payload para el MS (sin email ni password)
    person_payload = {
        "first_name": first_name,
        "last_name": last_name,
        "identification": dni,
        "type_identification": type_identification,
        "type_stament": type_stament,
        "direction": direction or "S/N",
        "phono": phone or "S/N",
    }
    
    person_client = PersonClient()
    
    # 1) Crear solo persona en el MS
    try:
        save_resp = await person_client.create_person(person_payload)
    except Exception as e:
        logger.error(f"Error al llamar a crear persona en MS usuarios: {e}")
        raise ValidationException("No se pudo registrar la persona en el sistema institucional")
    
    if save_resp.get("status") != "success":
        raise ValidationException(f"Error desde MS de usuarios: {save_resp.get('message')}")
    
    # 2) Obtener external_id consultando por DNI
    try:
        person_data = await person_client.get_by_identification(dni)
    except Exception as e:
        logger.error(f"Error al obtener persona por DNI en MS usuarios: {e}")
        raise ValidationException("La persona se creó pero no se pudo recuperar del sistema institucional")
    
    person = person_data.get("data") or {}
    external_person_id = person.get("external")
    
    if not external_person_id:
        raise ValidationException("El MS de usuarios no devolvió external_id de la persona")
    
    full_name = f"{first_name} {last_name}"
    
    return {
        "external_person_id": external_person_id,
        "full_name": full_name,
        "dni": dni,
    }
