"""Controlador de representantes - maneja la lógica de negocio."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.client.person_ms_service import PersonMSService
from app.dao.representative_dao import RepresentativeDAO
from app.models.enums.relationship import Relationship
from app.schemas.representative_schema import (
    RelationshipType,
    RepresentativeCreateDB,
    RepresentativeDetailResponse,
    RepresentativeFilter,
    RepresentativeInscriptionDTO,
    RepresentativeInscriptionResponseDTO,
    RepresentativeResponse,
    RepresentativeUpdateDTO,
)
from app.schemas.response import PaginatedResponse
from app.schemas.user_schema import CreatePersonInMSRequest
from app.utils.exceptions import AlreadyExistsException, ValidationException

logger = logging.getLogger(__name__)


class RepresentativeController:
    """Controlador de representantes."""

    def __init__(self):
        self.representative_dao = RepresentativeDAO()
        self.person_ms_service = PersonMSService()

    async def create_representative(
        self, db: Session, data: RepresentativeInscriptionDTO
    ) -> RepresentativeInscriptionResponseDTO:
        """
        Registra un representante.

        Flujo:
        1. Validar unicidad local (DNI)
        2. Crear persona en MS de usuarios (o recuperar si ya existe)
        3. Guardar representante localmente
        """
        first_name = data.first_name.strip()
        last_name = data.last_name.strip()
        dni = data.dni

        # Validar unicidad en representantes
        if self.representative_dao.exists(db, "dni", dni):
            raise AlreadyExistsException(
                "Ya existe un representante con ese DNI en el club."
            )

        # Crear o recuperar persona en MS de usuarios
        external_person_id = await self.person_ms_service.create_or_get_person(
            CreatePersonInMSRequest(
                first_name=first_name,
                last_name=last_name,
                dni=dni,
                direction=(data.direction or "S/N").strip(),
                phone=(data.phone or "S/N").strip(),
                type_identification=data.type_identification,
                type_stament=data.type_stament,
            )
        )

        # Mapear RelationshipType -> Relationship enum del modelo
        relationship_mapping = {
            RelationshipType.FATHER: Relationship.FATHER,
            RelationshipType.MOTHER: Relationship.MOTHER,
            RelationshipType.LEGAL_GUARDIAN: Relationship.LEGAL_GUARDIAN,
        }
        relationship = relationship_mapping.get(
            data.relationship_type, Relationship.LEGAL_GUARDIAN
        )

        # Crear representante localmente
        full_name = f"{first_name} {last_name}"
        representative_payload = RepresentativeCreateDB(
            external_person_id=external_person_id,
            full_name=full_name,
            dni=dni,
            phone=(data.phone or "S/N").strip(),
            email=data.email,
            relationship_type=relationship.value,
        )

        representative = self.representative_dao.create(
            db, representative_payload.model_dump()
        )

        return RepresentativeInscriptionResponseDTO(
            representative_id=representative.id,
            full_name=representative.full_name,
            dni=representative.dni,
            relationship_type=representative.relationship_type.value,
        )

    def get_or_create_representative_sync(
        self, db: Session, dni: str
    ) -> Optional[object]:
        """
        Obtiene un representante por DNI (versión síncrona).
        Retorna None si no existe.
        """
        return self.representative_dao.get_by_field(db, "dni", dni, only_active=True)

    def get_all_representatives(
        self, db: Session, filters: RepresentativeFilter
    ) -> PaginatedResponse:
        """
        Obtiene representantes aplicando los filtros recibidos.
        """
        items, total = self.representative_dao.get_all_with_filters(db, filters=filters)

        representative_responses = [
            RepresentativeResponse(
                id=rep.id,
                full_name=rep.full_name,
                dni=rep.dni,
                phone=rep.phone,
                relationship_type=getattr(
                    rep.relationship_type, "value", str(rep.relationship_type)
                ),
                is_active=rep.is_active,
                created_at=(rep.created_at.isoformat() if rep.created_at else None),
            )
            for rep in items
        ]

        return PaginatedResponse(
            items=[r.model_dump() for r in representative_responses],
            total=total,
            page=filters.page,
            limit=filters.limit,
        )

    async def get_representative_by_id(
        self, db: Session, representative_id: int
    ) -> RepresentativeDetailResponse:
        """
        Obtiene un representante con toda la información local y del MS.
        """
        representative = self.representative_dao.get_by_id(
            db=db, id=representative_id, only_active=True
        )
        if not representative:
            raise ValidationException("Representante no encontrado")

        # Datos base
        first_name: Optional[str] = None
        last_name: Optional[str] = None
        direction: Optional[str] = None
        type_identification: Optional[str] = None
        type_stament: Optional[str] = None

        # Intentar obtener información del MS
        try:
            person_data = await self.person_ms_service.get_user_by_identification(
                representative.dni
            )
            if person_data and person_data.get("data"):
                ms_data = person_data["data"]
                first_name = ms_data.get("firts_name")
                last_name = ms_data.get("last_name")
                direction = ms_data.get("direction")
                type_identification = ms_data.get("type_identification")
                type_stament = ms_data.get("type_stament")
        except Exception as ms_error:
            logger.warning(
                "No se pudo obtener información del MS para representante %s: %s",
                representative_id,
                ms_error,
            )

        return RepresentativeDetailResponse(
            id=representative.id,
            external_person_id=representative.external_person_id,
            full_name=representative.full_name,
            dni=representative.dni,
            phone=representative.phone,
            email=representative.email,
            relationship_type=getattr(
                representative.relationship_type,
                "value",
                str(representative.relationship_type),
            ),
            is_active=representative.is_active,
            created_at=representative.created_at.isoformat(),
            updated_at=(
                representative.updated_at.isoformat()
                if representative.updated_at
                else None
            ),
            first_name=first_name,
            last_name=last_name,
            direction=direction,
            type_identification=type_identification,
            type_stament=type_stament,
        )

    def get_representative_by_dni(
        self, db: Session, dni: str
    ) -> Optional[RepresentativeResponse]:
        """
        Busca un representante por DNI.
        Retorna None si no existe (útil para verificar existencia desde frontend).
        """
        representative = self.representative_dao.get_by_field(
            db, "dni", dni, only_active=True
        )
        if not representative:
            return None

        return RepresentativeResponse(
            id=representative.id,
            full_name=representative.full_name,
            dni=representative.dni,
            phone=representative.phone,
            relationship_type=getattr(
                representative.relationship_type,
                "value",
                str(representative.relationship_type),
            ),
            is_active=representative.is_active,
            created_at=(
                representative.created_at.isoformat()
                if representative.created_at
                else None
            ),
        )

    async def update_representative(
        self, db: Session, representative_id: int, data: RepresentativeUpdateDTO
    ) -> RepresentativeDetailResponse:
        """
        Actualiza los datos de un representante.
        """
        representative = self.representative_dao.get_by_id(
            db=db, id=representative_id, only_active=False
        )
        if not representative:
            raise ValidationException("Representante no encontrado")

        update_data = data.model_dump(exclude_unset=True)

        # Actualizar full_name si se enviaron nombres
        first_name = update_data.pop("first_name", None)
        last_name = update_data.pop("last_name", None)
        if first_name or last_name:
            current_names = representative.full_name.split(" ", 1)
            new_first = first_name if first_name else current_names[0]
            new_last = (
                last_name
                if last_name
                else (current_names[1] if len(current_names) > 1 else "")
            )
            update_data["full_name"] = f"{new_first} {new_last}".strip()

        # Convertir relationship_type si está presente
        relationship_type = update_data.pop("relationship_type", None)
        if relationship_type:
            relationship_mapping = {
                RelationshipType.FATHER: Relationship.FATHER,
                RelationshipType.MOTHER: Relationship.MOTHER,
                RelationshipType.LEGAL_GUARDIAN: Relationship.LEGAL_GUARDIAN,
            }
            update_data["relationship_type"] = relationship_mapping.get(
                relationship_type, Relationship.LEGAL_GUARDIAN
            )

        # Actualizar en MS si hay datos de contacto
        direction = update_data.get("direction")
        phone = update_data.get("phone")
        if direction is not None or phone is not None:
            names = update_data.get("full_name", representative.full_name).split(" ", 1)
            ms_first_name = names[0] if names else representative.full_name
            ms_last_name = names[1] if len(names) > 1 else ""

            await self.person_ms_service.update_person(
                external=representative.external_person_id,
                first_name=ms_first_name,
                last_name=ms_last_name,
                dni=representative.dni,
                direction=direction,
                phone=phone,
            )

        # Actualizar localmente
        updated_rep = self.representative_dao.update(db, representative_id, update_data)
        if not updated_rep:
            raise ValidationException("Error al actualizar el representante")

        return await self.get_representative_by_id(db, representative_id)

    def deactivate_representative(self, db: Session, representative_id: int) -> None:
        """
        Desactiva un representante (soft delete).
        """
        representative = self.representative_dao.get_by_id(
            db=db, id=representative_id, only_active=True
        )
        if not representative:
            raise ValidationException("Representante no encontrado")

        self.representative_dao.update(db, representative_id, {"is_active": False})

    def activate_representative(self, db: Session, representative_id: int) -> None:
        """
        Activa un representante (revierte soft delete).
        """
        representative = self.representative_dao.get_by_id(
            db=db, id=representative_id, only_active=False
        )
        if not representative:
            raise ValidationException("Representante no encontrado")

        self.representative_dao.update(db, representative_id, {"is_active": True})
