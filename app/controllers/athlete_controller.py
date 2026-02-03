import logging

from sqlalchemy.orm import Session

from app.client.person_ms_service import PersonMSService
from app.dao.athlete_dao import AthleteDAO
from app.dao.representative_dao import RepresentativeDAO
from app.dao.statistic_dao import StatisticDAO
from app.dao.user_dao import UserDAO
from app.models.enums.relationship import Relationship
from app.models.enums.sex import Sex
from app.schemas.athlete_schema import (
    AthleteCreateDB,
    AthleteDetailResponse,
    AthleteFilter,
    AthleteInscriptionDTO,
    AthleteInscriptionResponseDTO,
    AthleteResponse,
    AthleteUpdateResponse,
    MinorAthleteInscriptionDTO,
    MinorAthleteInscriptionResponseDTO,
    SexInput,
    StatisticCreateDB,
)
from app.schemas.representative_schema import RepresentativeCreateDB
from app.schemas.response import PaginatedResponse
from app.schemas.user_schema import CreatePersonInMSRequest, TypeStament
from app.utils.exceptions import AlreadyExistsException, ValidationException

logger = logging.getLogger(__name__)


class AthleteController:
    """Controlador de atletas del club."""

    def __init__(self) -> None:
        self.athlete_dao = AthleteDAO()
        self.statistic_dao = StatisticDAO()
        self.representative_dao = RepresentativeDAO()
        self.user_dao = UserDAO()
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
        self, db: Session, data: MinorAthleteInscriptionDTO
    ) -> MinorAthleteInscriptionResponseDTO:
        """
        Registra un deportista menor de edad junto con su representante.

        Flujo:
        1. Verificar si representante existe por DNI
        2. Si no existe, crear en MS + local
        3. Crear atleta menor en MS + local con representative_id
        4. Crear estadísticas iniciales
        5. Retornar respuesta combinada

        Este endpoint es público (sin autenticación) para auto-registro.
        """
        rep_data = data.representative
        athlete_data = data.athlete

        # Validar que el DNI del atleta no exista
        if self.athlete_dao.exists(db, "dni", athlete_data.dni):
            raise AlreadyExistsException(
                "Ya existe un deportista con ese DNI en el club."
            )

        # 1. Buscar representante existente por DNI
        existing_rep = self.representative_dao.get_by_field(
            db, "dni", rep_data.dni, only_active=True
        )

        representative_is_new = False
        representative_id: int

        if existing_rep:
            # Usar representante existente
            representative_id = existing_rep.id
            representative_full_name = existing_rep.full_name
            representative_dni = existing_rep.dni
            logger.info(
                f"Representante existente encontrado: {existing_rep.full_name} "
                f"(ID: {existing_rep.id})"
            )
        else:
            # 2. Crear representante nuevo
            representative_is_new = True

            # Crear persona del representante en MS de usuarios
            try:
                rep_external_person_id = (
                    await self.person_ms_service.create_or_get_person(
                        CreatePersonInMSRequest(
                            first_name=rep_data.first_name.strip(),
                            last_name=rep_data.last_name.strip(),
                            dni=rep_data.dni,
                            direction=(rep_data.direction or "S/N").strip(),
                            phone=(rep_data.phone or "S/N").strip(),
                            type_identification=rep_data.type_identification,
                            type_stament=TypeStament.EXTERNOS,
                        )
                    )
                )
            except ValidationException as e:
                # Agregar contexto: el error es del REPRESENTANTE
                error_msg = getattr(e, "message", str(e))
                raise ValidationException(f"[REPRESENTANTE] {error_msg}") from e

            # Mapear relationship_type string -> Relationship enum
            relationship_mapping = {
                "FATHER": Relationship.FATHER,
                "MADRE": Relationship.MOTHER,
                "MOTHER": Relationship.MOTHER,
                "PADRE": Relationship.FATHER,
                "LEGAL_GUARDIAN": Relationship.LEGAL_GUARDIAN,
                "TUTOR": Relationship.LEGAL_GUARDIAN,
            }
            relationship = relationship_mapping.get(
                rep_data.relationship_type.upper(), Relationship.LEGAL_GUARDIAN
            )

            # Crear representante localmente
            rep_full_name = (
                f"{rep_data.first_name.strip()} {rep_data.last_name.strip()}"
            )
            rep_payload = RepresentativeCreateDB(
                external_person_id=rep_external_person_id,
                full_name=rep_full_name,
                dni=rep_data.dni,
                phone=(rep_data.phone or "S/N").strip(),
                email=rep_data.email,
                relationship_type=relationship,  # Pasar enum, no el value
            )

            new_representative = self.representative_dao.create(
                db, rep_payload.model_dump(mode="python")
            )
            representative_id = new_representative.id
            representative_full_name = new_representative.full_name
            representative_dni = new_representative.dni

            logger.info(
                f"Nuevo representante creado: {rep_full_name} (ID: {representative_id})"
            )

        # 3. Crear atleta menor en MS de usuarios
        try:
            athlete_external_person_id = (
                await self.person_ms_service.create_or_get_person(
                    CreatePersonInMSRequest(
                        first_name=athlete_data.first_name.strip(),
                        last_name=athlete_data.last_name.strip(),
                        dni=athlete_data.dni,
                        direction=(athlete_data.direction or "S/N").strip(),
                        phone=(athlete_data.phone or "S/N").strip(),
                        type_identification=athlete_data.type_identification,
                        type_stament=TypeStament.EXTERNOS,
                    )
                )
            )
        except ValidationException as e:
            # Agregar contexto: el error es del DEPORTISTA MENOR
            error_msg = getattr(e, "message", str(e))
            raise ValidationException(f"[DEPORTISTA] {error_msg}") from e

        # Convertir SexInput -> Sex del modelo
        sex_mapping = {
            SexInput.MALE: Sex.MALE,
            SexInput.FEMALE: Sex.FEMALE,
            SexInput.OTHER: Sex.OTHER,
        }
        sex = sex_mapping.get(athlete_data.sex, Sex.MALE)

        # Crear atleta localmente con representative_id
        athlete_full_name = (
            f"{athlete_data.first_name.strip()} {athlete_data.last_name.strip()}"
        )
        athlete_payload = AthleteCreateDB(
            external_person_id=athlete_external_person_id,
            full_name=athlete_full_name,
            dni=athlete_data.dni,
            type_athlete=TypeStament.EXTERNOS.value,  # Siempre EXTERNOS para menores
            date_of_birth=athlete_data.birth_date,
            height=athlete_data.height,
            weight=athlete_data.weight,
            sex=sex,
        )

        # Incluir representative_id en el payload
        athlete_dict = athlete_payload.model_dump()
        athlete_dict["representative_id"] = representative_id

        athlete = self.athlete_dao.create(db, athlete_dict)

        # 4. Crear estadísticas iniciales
        statistic_payload = StatisticCreateDB(athlete_id=athlete.id)
        statistic = self.statistic_dao.create(db, statistic_payload.model_dump())

        logger.info(
            f"Atleta menor registrado: {athlete_full_name} "
            f"(ID: {athlete.id}) con representante ID: {representative_id}"
        )

        return MinorAthleteInscriptionResponseDTO(
            representative_id=representative_id,
            representative_full_name=representative_full_name,
            representative_dni=representative_dni,
            representative_is_new=representative_is_new,
            athlete_id=athlete.id,
            athlete_full_name=athlete.full_name,
            athlete_dni=athlete.dni,
            statistic_id=statistic.id,
        )

    def get_all_athletes(
        self, db: Session, filters: AthleteFilter
    ) -> PaginatedResponse:
        """
        Obtiene atletas aplicando los filtros recibidos.
        Retorna un PaginatedResponse con lista de AthleteResponse.
        """
        items, total = self.athlete_dao.get_all_with_filters(db, filters=filters)

        # Obtener DNIs de todos los atletas para verificar cuentas
        athlete_dnis = [athlete.dni for athlete in items]

        # Verificar cuáles tienen cuenta en el sistema
        existing_users = {}
        for dni in athlete_dnis:
            user = self.user_dao.get_by_field(db, "dni", dni, only_active=False)
            existing_users[dni] = user is not None

        athlete_responses = [
            AthleteResponse(
                id=athlete.id,
                full_name=athlete.full_name,
                dni=athlete.dni,
                type_athlete=athlete.type_athlete,
                sex=getattr(athlete.sex, "value", str(athlete.sex)),
                is_active=athlete.is_active,
                has_account=existing_users.get(athlete.dni, False),
                height=athlete.height,
                weight=athlete.weight,
                created_at=(
                    athlete.created_at.isoformat() if athlete.created_at else None
                ),
                updated_at=(
                    athlete.updated_at.isoformat() if athlete.updated_at else None
                ),
            )
            for athlete in items
        ]

        return PaginatedResponse(
            items=[r.model_dump() for r in athlete_responses],
            total=total,
            page=filters.page,
            limit=filters.limit,
        )

    def get_athlete_by_id(self, db: Session, athlete_id: int):
        """
        Obtiene un atleta por su ID.
        """
        athlete = self.athlete_dao.get_by_id(db=db, id=athlete_id)
        if not athlete:
            raise ValidationException("Atleta no encontrado")
        return athlete

    async def update_athlete(
        self, db: Session, athlete_id: int, update_data: dict
    ) -> AthleteUpdateResponse:
        """
        Actualiza los datos básicos de un atleta y sincroniza con MS de personas.
        Similar a admin_update_user: simple y directo.
        """
        athlete = self.athlete_dao.get_by_id(db=db, id=athlete_id, only_active=False)
        if not athlete:
            raise ValidationException("Atleta no encontrado")

        # Extraer campos del payload
        direction = update_data.pop("direction", None)
        phone = update_data.pop("phone", None)
        _type_identification = update_data.pop("type_identification", None)
        _type_stament = update_data.pop("type_stament", None)
        _dni = update_data.pop("dni", None)  # No permitimos cambiar DNI

        # Extraer nombres
        first_name = update_data.pop("first_name", None)
        last_name = update_data.pop("last_name", None)

        # Para el MS, usar nombres del payload o el full_name actual
        ms_first = first_name.strip() if first_name else athlete.full_name
        ms_last = last_name.strip() if last_name else ""

        # Siempre actualizar en MS de usuarios (mantiene sync)
        new_external = await self.person_ms_service.update_person(
            external=athlete.external_person_id,
            first_name=ms_first,
            last_name=ms_last,
            dni=athlete.dni,
            direction=direction,
            phone=phone,
        )

        # Actualizar external_person_id
        update_data["external_person_id"] = new_external

        # Actualizar full_name si se enviaron nombres
        if first_name and last_name:
            update_data["full_name"] = f"{first_name.strip()} {last_name.strip()}"
        elif first_name:
            update_data["full_name"] = first_name.strip()
        elif last_name:
            update_data["full_name"] = last_name.strip()

        # Convertir birth_date a date_of_birth para el modelo
        birth_date = update_data.pop("birth_date", None)
        if birth_date:
            update_data["date_of_birth"] = birth_date

        # Convertir sex enum si está presente
        sex = update_data.pop("sex", None)
        if sex:
            from app.models.enums.sex import Sex as SexEnum

            sex_mapping = {
                "MALE": SexEnum.MALE,
                "FEMALE": SexEnum.FEMALE,
                "OTHER": SexEnum.OTHER,
            }
            sex_value = getattr(sex, "value", str(sex)).upper()
            if sex_value in sex_mapping:
                update_data["sex"] = sex_mapping[sex_value]

        # Actualizar datos locales del atleta
        updated_athlete = self.athlete_dao.update(db, athlete_id, update_data)
        if not updated_athlete:
            raise ValidationException("Error al actualizar el atleta")

        return AthleteUpdateResponse(
            id=updated_athlete.id,
            full_name=updated_athlete.full_name,
            height=updated_athlete.height,
            weight=updated_athlete.weight,
            updated_at=(
                updated_athlete.updated_at.isoformat()
                if updated_athlete.updated_at
                else None
            ),
        )

    def desactivate_athlete(self, db: Session, athlete_id: int) -> None:
        """
        Desactiva un atleta (soft delete).
        """
        athlete = self.athlete_dao.get_by_id(db=db, id=athlete_id)
        if not athlete:
            raise ValidationException("Atleta no encontrado")

        self.athlete_dao.update(db, athlete_id, {"is_active": False})

    def activate_athlete(self, db: Session, athlete_id: int) -> None:
        """
        Activa un atleta (revierte soft delete).
        """
        # Buscar incluyendo inactivos para poder reactivarlos
        athlete = self.athlete_dao.get_by_id(db=db, id=athlete_id, only_active=False)
        if not athlete:
            raise ValidationException("Atleta no encontrado")

        self.athlete_dao.update(db, athlete_id, {"is_active": True})

    async def get_athlete_with_ms_info(
        self, db: Session, athlete_id: int
    ) -> AthleteDetailResponse:
        """
        Obtiene un atleta con toda la información local y del MS de usuarios.
        Retorna AthleteDetailResponse con datos unificados (sin duplicados).
        """
        athlete = self.get_athlete_by_id(db=db, athlete_id=athlete_id)

        # Datos base del atleta local
        first_name: str | None = None
        last_name: str | None = None
        direction: str | None = None
        phone: str | None = None
        type_identification: str | None = None
        type_stament: str | None = None
        photo: str | None = None

        # Intentar obtener información del MS de usuarios
        try:
            person_data = await self.person_ms_service.get_user_by_identification(
                athlete.dni
            )
            if person_data and person_data.get("data"):
                ms_data = person_data["data"]
                first_name = ms_data.get("firts_name")
                last_name = ms_data.get("last_name")
                direction = ms_data.get("direction")
                phone = ms_data.get("phono")
                type_identification = ms_data.get("type_identification")
                type_stament = ms_data.get("type_stament")
                photo = ms_data.get("photo")
        except Exception as ms_error:
            # Si el MS no está disponible, continuar sin esa información
            logger.warning(
                "No se pudo obtener información del MS para atleta %s: %s",
                athlete_id,
                ms_error,
            )

        return AthleteDetailResponse(
            id=athlete.id,
            external_person_id=athlete.external_person_id,
            full_name=athlete.full_name,
            dni=athlete.dni,
            type_athlete=athlete.type_athlete,
            date_of_birth=athlete.date_of_birth,
            height=athlete.height,
            weight=athlete.weight,
            sex=getattr(athlete.sex, "value", str(athlete.sex)),
            is_active=athlete.is_active,
            created_at=athlete.created_at.isoformat(),
            updated_at=(athlete.updated_at.isoformat() if athlete.updated_at else None),
            # Campos del MS de personas
            first_name=first_name,
            last_name=last_name,
            direction=direction,
            phone=phone,
            type_identification=type_identification,
            type_stament=type_stament,
            photo=photo,
        )
