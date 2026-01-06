"""Servicio para gestionar operaciones con el MS de personas/usuarios."""

import logging
import secrets
import unicodedata
from typing import Optional

from app.client.person_client import PersonClient
from app.schemas.user_schema import CreatePersonInMSRequest
from app.utils.exceptions import ValidationException

logger = logging.getLogger(__name__)


class PersonMSService:
    """Servicio que encapsula toda la lógica de interacción con el MS de usuarios."""

    def __init__(self, person_client: Optional[PersonClient] = None):
        self.person_client = person_client or PersonClient()

    async def create_or_get_person(self, data: CreatePersonInMSRequest) -> str:
        """
        Crea una persona en el MS de usuarios o retorna su external si ya existe.
        Es idempotente: si la persona ya existe con ese DNI, valida identidad y
        retorna external.
        """
        person_payload = self._build_person_payload(data)

        try:
            save_resp = await self.person_client.create_person_with_account(
                person_payload
            )
            return await self._handle_create_response(save_resp, data)
        except ValidationException as e:
            if self._is_duplicate_error(e):
                logger.info(
                    f"Persona con DNI {data.dni} ya existe, validando identidad..."
                )
                return await self._get_and_validate_existing_person(data)
            raise
        except Exception as e:
            logger.error(f"Error inesperado al comunicarse con MS de usuarios: {e}")
            raise ValidationException(
                "Error de comunicación con el módulo de usuarios"
            ) from e

    async def update_person(
        self,
        *,
        external: str,
        first_name: str,
        last_name: str,
        dni: str,
        direction: Optional[str] = None,
        phone: Optional[str] = None,
        type_identification: str = "CEDULA",
        type_stament: str = "EXTERNOS",
    ) -> str:
        """
        Actualiza una persona en el MS de usuarios.

        Args:
            external: Identificador externo actual de la persona
            first_name: Nombre
            last_name: Apellido
            dni: Documento de identidad
            direction: Dirección (opcional)
            phone: Teléfono (opcional)
            type_identification: Tipo de identificación
            type_stament: Tipo de declaración
        """
        person_payload = {
            "first_name": first_name,
            "last_name": last_name,
            "external": external,
            "type_identification": type_identification,
            "type_stament": type_stament,
            "direction": direction or "S/N",
            "phono": phone or "S/N",
        }

        try:
            update_resp = await self.person_client.update_person(person_payload)
            external = self._extract_external(update_resp)

            if external:
                return external

            return await self._get_external_by_dni(dni)

        except Exception as e:
            logger.error(f"Error al actualizar persona en MS de usuarios: {e}")
            raise ValidationException(
                "Error de comunicación con el módulo de usuarios"
            ) from e

    async def get_all_users(self):
        """
        Obtiene todos los usuarios del club desde el MS de usuarios.
        """
        try:
            users_resp = await self.person_client.get_all_filter()
            return users_resp.get("data", [])
        except Exception as e:
            logger.error(f"Error al obtener usuarios del MS de usuarios: {e}")
            raise ValidationException(
                "Error de comunicación con el módulo de usuarios"
            ) from e

    async def get_user_by_identification(self, identification: str) -> dict:
        """
        Obtiene un usuario por su identificación desde el MS de usuarios.
        """
        try:
            user_resp = await self.person_client.get_by_identification(identification)
            return user_resp
        except Exception as e:
            logger.error(
                f"Error al obtener usuario por identificación del MS de usuarios: {e}"
            )
            raise ValidationException(
                "Error de comunicación con el módulo de usuarios"
            ) from e

    # Metodos privados

    def _build_person_payload(self, data: CreatePersonInMSRequest) -> dict:
        """Construye el payload para crear persona en el MS."""
        return {
            "first_name": data.first_name,
            "last_name": data.last_name,
            "identification": data.dni,
            "type_identification": data.type_identification,
            "type_stament": data.type_stament,
            "direction": data.direction or "S/N",
            "email": f"user{secrets.randbelow(89999) + 10000}@example.com",
            "password": f"Pass{secrets.randbelow(89999) + 10000}!",
        }

    async def _handle_create_response(
        self, save_resp: dict, data: CreatePersonInMSRequest
    ) -> str:
        """Procesa la respuesta del MS al crear persona."""
        status = save_resp.get("status")
        raw_message = save_resp.get("message") or save_resp.get("detail") or ""

        if status == "success":
            external = self._extract_external(save_resp)
            if external:
                return external

            logger.warning(
                f"MS respondió 'success' sin external para DNI {data.dni}. "
                "Intentando recuperar external por DNI..."
            )
            return await self._get_and_validate_existing_person(data)

        if self._is_duplicate_message(raw_message):
            logger.info(f"Persona con DNI {data.dni} ya existe en MS usuarios")
            return await self._get_and_validate_existing_person(data)

        raise ValidationException(
            save_resp.get("message")
            or save_resp.get("detail")
            or "Error desconocido al crear persona"
        )

    async def _get_and_validate_existing_person(
        self, data: CreatePersonInMSRequest
    ) -> str:
        """Obtiene persona existente por DNI y valida que sea la misma identidad."""
        try:
            existing = await self.person_client.get_by_identification(data.dni)
        except Exception as e:
            logger.error(
                f"No se pudo consultar persona existente por DNI {data.dni}: {e}"
            )
            raise ValidationException(
                "La persona ya existe en el módulo de usuarios, "
                "pero no se pudo recuperar su identificador externo"
            ) from e

        self._validate_same_identity(existing, data)

        external = self._extract_external(existing)
        if not external:
            raise ValidationException(
                "La persona existe en el módulo de usuarios, "
                "pero la respuesta no contiene el identificador externo"
            )

        return external

    async def _get_external_by_dni(self, dni: str) -> str:
        """Recupera el external de una persona por su DNI."""
        try:
            existing = await self.person_client.get_by_identification(dni)
            external = self._extract_external(existing)

            if not external:
                raise ValidationException(
                    "No se pudo obtener el identificador externo de la persona"
                )

            return external
        except Exception as e:
            logger.error(f"Error al consultar persona por DNI {dni}: {e}")
            raise ValidationException(
                "No se pudo recuperar el identificador externo"
            ) from e

    def _validate_same_identity(
        self, existing_resp: dict, expected_data: CreatePersonInMSRequest
    ) -> None:
        """
        Valida que la persona existente en el MS sea la misma que se intenta registrar.

        Raises:
            ValidationException: Si los nombres no coinciden
        """
        ms_first, ms_last, ms_full = self._extract_name_fields(existing_resp)

        expected_first = self._normalize_name(expected_data.first_name)
        expected_last = self._normalize_name(expected_data.last_name)
        expected_full = self._normalize_name(
            f"{expected_data.first_name} {expected_data.last_name}"
        )

        ms_first_n = self._normalize_name(ms_first)
        ms_last_n = self._normalize_name(ms_last)
        ms_full_n = self._normalize_name(ms_full)
        ms_joined_n = self._normalize_name(
            " ".join([p for p in [ms_first or "", ms_last or ""] if p.strip()])
        )

        if not (ms_first_n or ms_last_n or ms_full_n or ms_joined_n):
            raise ValidationException(
                "El DNI ya existe en el módulo de usuarios, pero no se pudieron "
                "obtener los nombres para validar identidad."
            )

        # Verificar coincidencia
        matches = False
        if ms_first_n and ms_last_n:
            matches = ms_first_n == expected_first and ms_last_n == expected_last
        if not matches and ms_full_n:
            matches = ms_full_n == expected_full
        if not matches and ms_joined_n:
            matches = ms_joined_n == expected_full

        if not matches:
            raise ValidationException(
                "Los datos personales no coinciden con el DNI registrado"
                " en el módulo de usuarios. "
            )

    @staticmethod
    def _extract_external(resp: object) -> Optional[str]:
        """Extrae el external de diferentes estructuras de respuesta del MS."""
        if not isinstance(resp, dict):
            return None

        data_block = resp.get("data")

        if isinstance(data_block, dict):
            external = data_block.get("external")
            return str(external) if external else None

        if isinstance(data_block, list) and data_block:
            first = data_block[0]
            if isinstance(first, dict):
                external = first.get("external")
                return str(external) if external else None

        external = resp.get("external")
        return str(external) if external else None

    @staticmethod
    def _extract_name_fields(
        resp: object,
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extrae nombres desde la respuesta del MS.

        Returns:
            tuple: (first_name, last_name, full_name)
        """
        if not isinstance(resp, dict):
            return None, None, None

        data_block = resp.get("data")
        if isinstance(data_block, list) and data_block:
            data_block = data_block[0]

        if not isinstance(data_block, dict):
            return None, None, None

        first_name = data_block.get("first_name") or data_block.get("firts_name")

        last_name = data_block.get("last_name") or data_block.get("lastName")

        full_name = data_block.get("full_name") or data_block.get("fullName")

        return (
            str(first_name) if first_name else None,
            str(last_name) if last_name else None,
            str(full_name) if full_name else None,
        )

    @staticmethod
    def _normalize_name(value: Optional[str]) -> str:
        """
        Normaliza un nombre para comparación (lowercase, sin acentos, sin espacios).
        """
        if not value:
            return ""

        raw = value.strip().lower()
        raw = " ".join(raw.split())
        raw = unicodedata.normalize("NFKD", raw)
        return "".join(ch for ch in raw if not unicodedata.combining(ch))

    @staticmethod
    def _is_duplicate_message(raw_message: str) -> bool:
        """Detecta si el mensaje indica que la persona ya existe."""
        msg = (raw_message or "").strip().lower()
        return (
            "la persona ya esta registrada con esa identificacion" in msg
            or "la persona ya está registrada con esa identificacion" in msg
            or ("ya existe una persona" in msg and "identific" in msg)
            or "already exists" in msg
            or "duplicad" in msg
        )

    @staticmethod
    def _is_duplicate_error(exc: ValidationException) -> bool:
        """Detecta si una excepción indica duplicación."""
        message = getattr(exc, "message", "") or str(exc)
        return PersonMSService._is_duplicate_message(message)
