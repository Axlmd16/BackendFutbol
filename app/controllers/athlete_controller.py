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

    async def register_minor_athlete(
        self, db: Session, data
    ):
        """
        Registra un deportista menor de edad con su representante legal.

        Flujo de negocio:
        1. Validar edad < 18 años (ya validado en schema)
        2. Validar autorización parental explícita (ya validado en schema)
        3. Verificar unicidad de DNI del menor en el club
        4. Crear o vincular al representante legal:
           a. Si el representante ya existe en el MS (mismo DNI),
              se vincula al menor
           b. Si no existe, se crea en el MS con email real y se vincula
        5. Crear al menor en el MS de usuarios (con email dummy autogenerado)
        6. Guardar localmente al menor con type_athlete='MINOR'
        7. Retornar datos del menor y representante

        Args:
            db: Sesión de base de datos
            data: MinorAthleteCreateSchema validado

        Returns:
            MinorAthleteRegistrationResponse con datos del menor y representante

        Raises:
            AlreadyExistsException: Si el DNI del menor ya existe en el club
            ValidationException: Si hay errores en la comunicación con el MS
        """
        from app.dao.representative_dao import RepresentativeDAO
        from app.schemas.athlete_schema import (
            MinorAthleteRegistrationResponse,
            MinorAthleteResponseSchema,
            RepresentativeResponseSchema,
        )

        representative_dao = RepresentativeDAO()

        # 1. Validar unicidad del DNI del menor
        if self.athlete_dao.exists(db, "dni", data.dni):
            raise AlreadyExistsException(
                f"Ya existe un deportista registrado con el DNI: {data.dni}"
            )

        # 2. Procesar representante (crear en MS con email real)
        guardian_external_id = await self.person_ms_service.create_or_get_person(
            CreatePersonInMSRequest(
                first_name=data.representative.first_name.strip(),
                last_name=data.representative.last_name.strip(),
                dni=data.representative.dni,
                email=data.representative.email,
                direction=data.representative.address.strip(),
                phone=data.representative.phone.strip(),
                type_identification="CEDULA",
                type_stament="EXTERNOS",
            )
        )

        # Verificar si el representante ya existe localmente
        existing_representative = representative_dao.get_by_external_person_id(
            db, guardian_external_id
        )

        if existing_representative:
            logger.info(
                f"Representante con DNI {data.representative.dni} ya existe "
                f"localmente (ID: {existing_representative.id}). Reutilizando."
            )
            representative = existing_representative
        else:
            # Crear representante localmente
            representative_payload = {
                "external_person_id": guardian_external_id,
                "full_name": (
                    f"{data.representative.first_name} "
                    f"{data.representative.last_name}"
                ),
                "first_name": data.representative.first_name,
                "last_name": data.representative.last_name,
                "dni": data.representative.dni,
                "email": data.representative.email,
                "phone": data.representative.phone,
                "address": data.representative.address,
                "relationship_type": data.representative.relationship_type,
            }
            representative = representative_dao.create(db, representative_payload)
            logger.info(
                f"Representante creado localmente con ID: {representative.id}"
            )

        # 3. Crear menor en MS (sin email, se genera dummy automáticamente)
        minor_external_id = await self.person_ms_service.create_or_get_person(
            CreatePersonInMSRequest(
                first_name=data.first_name.strip(),
                last_name=data.last_name.strip(),
                dni=data.dni,
                email=None,
                direction="S/N",
                phone="S/N",
                type_identification="CEDULA",
                type_stament="EXTERNOS",
            )
        )

        # 4. Guardar menor localmente
        if data.sex == SexInput.MALE:
            sex = Sex.MALE
        elif data.sex == SexInput.FEMALE:
            sex = Sex.FEMALE
        else:
            sex = Sex.OTHER

        athlete_payload = {
            "external_person_id": minor_external_id,
            "full_name": f"{data.first_name} {data.last_name}",
            "first_name": data.first_name,
            "last_name": data.last_name,
            "dni": data.dni,
            "type_athlete": "MINOR",
            "date_of_birth": data.birth_date,
            "birth_date": data.birth_date,
            "sex": sex,
            "representative_id": representative.id,
            "parental_authorization": (
                "SI" if data.parental_authorization else "NO"
            ),
        }

        athlete = self.athlete_dao.create(db, athlete_payload)

        logger.info(
            f"Menor registrado exitosamente. "
            f"Atleta ID: {athlete.id}, Representante ID: {representative.id}"
        )

        # 5. Construir respuesta
        return MinorAthleteRegistrationResponse(
            athlete=MinorAthleteResponseSchema(
                id=athlete.id,
                first_name=athlete.first_name,
                last_name=athlete.last_name,
                dni=athlete.dni,
                birth_date=athlete.birth_date,
                sex=athlete.sex.value,
                type_athlete=athlete.type_athlete,
                representative_id=athlete.representative_id,
                external_person_id=athlete.external_person_id,
                created_at=athlete.created_at,
                is_active=athlete.is_active,
            ),
            representative=RepresentativeResponseSchema(
                id=representative.id,
                first_name=representative.first_name,
                last_name=representative.last_name,
                dni=representative.dni,
                email=representative.email,
                phone=representative.phone,
                address=representative.address,
                relationship_type=representative.relationship_type,
                external_person_id=representative.external_person_id,
                created_at=representative.created_at,
                is_active=representative.is_active,
            ),
        )
