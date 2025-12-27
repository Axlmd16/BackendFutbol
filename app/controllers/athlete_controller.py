import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.client.person_ms_service import PersonMSService
from app.dao.athlete_dao import AthleteDAO
from app.dao.statistic_dao import StatisticDAO
from app.models.enums.sex import Sex
from app.schemas.athlete_schema import (
    AthleteInscriptionDTO,
    AthleteInscriptionResponseDTO,
)
from app.schemas.user_schema import CreatePersonInMSRequest
from app.utils.exceptions import AlreadyExistsException, ValidationException
from app.utils.security import validate_ec_dni

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
        dni = validate_ec_dni(data.dni)

        # Validar unicidad en el club
        if self.athlete_dao.exists(db, "dni", dni):
            raise AlreadyExistsException("El DNI ya existe en el club.")

        # Normalizar type_identification y type_stament
        type_identification = (data.type_identification or "CEDULA").upper()
        if type_identification == "DNI":
            type_identification = "CEDULA"
        
        type_stament = (data.type_stament or "ESTUDIANTES").upper()

        # Crear o recuperar persona en MS de usuarios
        external_person_id = await self.person_ms_service.create_or_get_person(
            CreatePersonInMSRequest(
                first_name=first_name,
                last_name=last_name,
                dni=dni,
                direction=(data.direction or "").strip(),
                phone=(data.phone or "").strip(),
                type_identification=type_identification,
                type_stament=type_stament,
            )
        )

        # Crear atleta localmente (sin cuenta, no ingresa al sistema)
        full_name = f"{first_name} {last_name}"

        # Convertir birth_date si existe
        date_of_birth = None
        if data.birth_date:
            try:
                date_of_birth = datetime.strptime(data.birth_date, "%Y-%m-%d").date()
            except ValueError as e:
                raise ValidationException(
                    "Formato de fecha inválido. Use YYYY-MM-DD"
                ) from e

        # Convertir sex
        sex = Sex.MALE  # Valor por defecto
        if data.sex:
            sex_value = data.sex.upper()
            if sex_value not in ["MALE", "FEMALE"]:
                raise ValidationException("El sexo debe ser MALE o FEMALE")
            sex = Sex.MALE if sex_value == "MALE" else Sex.FEMALE

        # Normalizar type_athlete
        type_athlete = (data.type_athlete or "UNL").upper()

        athlete = self.athlete_dao.create(
            db,
            {
                "external_person_id": external_person_id,
                "full_name": full_name,
                "dni": dni,
                "type_athlete": type_athlete,
                "date_of_birth": date_of_birth,
                "height": float(data.height) if data.height else None,
                "weight": float(data.weight) if data.weight else None,
                "sex": sex,
            },
        )

        # Crear estadísticas iniciales
        statistic = self.statistic_dao.create(
            db,
            {
                "athlete_id": athlete.id,
                "matches_played": 0,
                "goals": 0,
                "assists": 0,
                "yellow_cards": 0,
                "red_cards": 0,
            },
        )

        return AthleteInscriptionResponseDTO(
            athlete_id=athlete.id,
            statistic_id=statistic.id,
            full_name=athlete.full_name,
            dni=athlete.dni,
        )
