import logging

from sqlalchemy.orm import Session

from app.client.person_ms_service import PersonMSService
from app.dao.athlete_dao import AthleteDAO
from app.dao.statistic_dao import StatisticDAO
from app.models.enums.sex import Sex
from app.schemas.athlete_schema import (
    AthleteCreateDB,
    AthleteInscriptionDTO,
    AthleteInscriptionResponseDTO,
    SexInput,
    StatisticCreateDB,
)
from app.schemas.user_schema import CreatePersonInMSRequest
from app.utils.exceptions import AlreadyExistsException

logger = logging.getLogger(__name__)


class AthleteController:
    """Controlador de atletas del club."""

    def __init__(self) -> None:
        self.athlete_dao = AthleteDAO()
        self.statistic_dao = StatisticDAO()
        self.person_ms_service = PersonMSService()

    async def register_athlete_unl(
        self, db: Session, data: AthleteInscriptionDTO
    ) -> AthleteInscriptionResponseDTO:
        """
        Registra un atleta de la UNL.

        Flujo:
        1. Validar datos y unicidad local
        2. Crear persona en MS de usuarios (o recuperar si ya existe)
        3. Guardar atleta localmente (sin cuenta)
        4. Crear estadísticas iniciales
        """
        # Normalizar datos
        first_name = data.first_name.strip()
        last_name = data.last_name.strip()
        dni = data.dni

        # Validar unicidad en el club
        if self.athlete_dao.exists(db, "dni", dni):
            raise AlreadyExistsException("El DNI ya existe en el club.")

        # Crear o recuperar persona en MS de usuarios
        external_person_id = await self.person_ms_service.create_or_get_person(
            CreatePersonInMSRequest(
                first_name=first_name,
                last_name=last_name,
                dni=dni,
                direction=(data.direction or "").strip(),
                phone=(data.phone or "").strip(),
                type_identification=data.type_identification,
                type_stament=data.type_stament,
            )
        )

        # Crear atleta localmente (sin cuenta, no ingresa al sistema)
        full_name = f"{first_name} {last_name}"

        # Convertir SexInput -> Sex (enum del modelo)
        if data.sex == SexInput.MALE:
            sex = Sex.MALE
        elif data.sex == SexInput.FEMALE:
            sex = Sex.FEMALE
        else:
            sex = Sex.OTHER

        athlete_payload = AthleteCreateDB(
            external_person_id=external_person_id,
            full_name=full_name,
            dni=dni,
            type_athlete=data.type_stament.value,
            date_of_birth=data.birth_date,
            height=data.height,
            weight=data.weight,
            sex=sex,
        )

        athlete = self.athlete_dao.create(db, athlete_payload.model_dump())

        # Crear estadísticas iniciales
        statistic_payload = StatisticCreateDB(athlete_id=athlete.id)
        statistic = self.statistic_dao.create(db, statistic_payload.model_dump())

        return AthleteInscriptionResponseDTO(
            athlete_id=athlete.id,
            statistic_id=statistic.id,
            full_name=athlete.full_name,
            dni=athlete.dni,
        )

    def get_all_athletes(self, db: Session, filters):
        """
        Obtiene atletas aplicando los filtros recibidos.
        """
        return self.athlete_dao.get_all_with_filters(db, filters=filters)

    def get_athlete_by_id(self, db: Session, athlete_id: int):
        """
        Obtiene un atleta por su ID.
        """
        return self.athlete_dao.get_by_id(db=db, id=athlete_id)

    def update_athlete(self, db: Session, athlete_id: int, update_data: dict):
        """
        Actualiza los datos básicos de un atleta.
        """
        athlete = self.athlete_dao.get_by_id(db=db, id=athlete_id)
        if not athlete:
            return None

        return self.athlete_dao.update(db, athlete_id, update_data)

    def desactivate_athlete(self, db: Session, athlete_id: int) -> None:
        """
        Desactiva un atleta (soft delete).
        """
        athlete = self.athlete_dao.get_by_id(db=db, id=athlete_id)
        if not athlete:
            return None

        self.athlete_dao.update(db, athlete_id, {"is_active": False})

    def activate_athlete(self, db: Session, athlete_id: int) -> None:
        """
        Activa un atleta (revierte soft delete).
        """
        athlete = self.athlete_dao.get_by_id(db=db, id=athlete_id)
        if not athlete:
            return None

        self.athlete_dao.update(db, athlete_id, {"is_active": True})
