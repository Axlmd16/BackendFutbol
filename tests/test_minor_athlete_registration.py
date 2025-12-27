"""
Tests unitarios para el registro de deportistas menores de edad.

Valida la integración con el MS de Usuarios y la persistencia local.
Adaptado para usar PersonMSService con generación automática de credenciales dummy.
"""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.controllers.athlete_controller import AthleteController
from app.models.athlete import Athlete
from app.models.representative import Representative
from app.schemas.athlete_schema import (
    MinorAthleteCreateSchema,
    RepresentativeCreateSchema,
)
from app.utils.exceptions import AlreadyExistsException, ValidationException


@pytest.fixture
def mock_db_session():
    """
    Mock de la sesión de base de datos.
    """
    session = MagicMock(spec=Session)
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.add = MagicMock()
    session.refresh = MagicMock()
    return session


@pytest.fixture
def athlete_controller():
    """
    Fixture del controlador de atletas.
    """
    return AthleteController()


@pytest.fixture
def valid_minor_data():
    """
    Fixture con datos válidos para un menor de edad.
    Usa DNIs ecuatorianos válidos con dígito verificador correcto.
    """
    birth_date = date.today() - timedelta(days=365 * 12)  # 12 años
    
    return MinorAthleteCreateSchema(
        first_name="Juan Carlos",
        last_name="Pérez López",
        dni="1722345673",  # DNI válido ecuatoriano (verificador correcto)
        birth_date=birth_date,
        sex="M",
        representative=RepresentativeCreateSchema(
            first_name="María Elena",
            last_name="López García",
            dni="1721234563",  # DNI válido ecuatoriano (verificador correcto)
            address="Av. Principal 123, Ciudad",
            phone="+593991234567",
            email="maria.lopez@email.com",
            relationship_type="PADRE/MADRE"
        ),
        parental_authorization=True
    )


@pytest.fixture
def mock_ms_external_id_minor():
    """
    Mock del external_id devuelto por PersonMSService para el menor.
    El servicio ahora retorna solo el string del external_id.
    """
    return "ext-minor-uuid-12345"


@pytest.fixture
def mock_ms_external_id_guardian():
    """
    Mock del external_id devuelto por PersonMSService para el representante.
    El servicio ahora retorna solo el string del external_id.
    """
    return "ext-guardian-uuid-67890"


class TestMinorAthleteRegistration:
    """
    Suite de tests para el registro de deportistas menores de edad.
    """
    
    @pytest.mark.asyncio
    async def test_register_minor_athlete_success(
        self,
        athlete_controller,
        mock_db_session,
        valid_minor_data,
        mock_ms_external_id_minor,
        mock_ms_external_id_guardian,
    ):
        """
        Test: Registro exitoso de menor con integración MS de Usuarios.

        Verifica que:
        1. Se invoca PersonMSService.create_or_get_person para crear al menor
        2. Se invoca PersonMSService.create_or_get_person para crear
           al representante
        3. El servicio genera automáticamente credenciales dummy
           (no las pasamos nosotros)
        4. Se persiste localmente con external_person_id
        5. Se retorna la respuesta correcta
        """
        # ARRANGE: Mockear las llamadas al PersonMSService
        with patch.object(
            athlete_controller.person_ms_service,
            "create_or_get_person",
            new_callable=AsyncMock,
        ) as mock_create_person:
            # Configurar respuestas del mock: retorna solo el external_id
            mock_create_person.side_effect = [
                mock_ms_external_id_minor,  # Primera llamada: menor
                mock_ms_external_id_guardian,  # Segunda llamada: representante
            ]

            # Mockear DAOs para simular que no existen registros previos
            athlete_controller.athlete_dao.get_by_dni = MagicMock(return_value=None)
            athlete_controller.representative_dao.get_by_dni = MagicMock(
                return_value=None
            )

            # Mockear creación de representante
            mock_representative = MagicMock(spec=Representative)
            mock_representative.id = 1
            mock_representative.external_person_id = mock_ms_external_id_guardian
            mock_representative.full_name = "María Elena López García"
            mock_representative.first_name = "María Elena"
            mock_representative.last_name = "López García"
            mock_representative.dni = "0987654321"
            mock_representative.phone = "+593991234567"
            mock_representative.email = "maria.lopez@email.com"
            mock_representative.address = "Av. Principal 123, Ciudad"
            mock_representative.relationship_type = "PADRE/MADRE"
            mock_representative.created_at = datetime.now()
            mock_representative.updated_at = None
            mock_representative.is_active = True
            athlete_controller.representative_dao.create = MagicMock(
                return_value=mock_representative
            )

            # Mockear creación de atleta
            mock_athlete = MagicMock(spec=Athlete)
            mock_athlete.id = 1
            mock_athlete.external_person_id = mock_ms_external_id_minor
            mock_athlete.full_name = "Juan Carlos Pérez López"
            mock_athlete.first_name = "Juan Carlos"
            mock_athlete.last_name = "Pérez López"
            mock_athlete.dni = "1234567890"
            mock_athlete.type_athlete = "MINOR"
            mock_athlete.date_of_birth = valid_minor_data.birth_date
            mock_athlete.birth_date = valid_minor_data.birth_date
            mock_athlete.sex = "M"
            mock_athlete.representative_id = 1
            mock_athlete.parental_authorization = None
            mock_athlete.created_at = datetime.now()
            mock_athlete.updated_at = None
            mock_athlete.is_active = True
            athlete_controller.athlete_dao.create = MagicMock(return_value=mock_athlete)

            # ACT: Ejecutar el registro
            result = await athlete_controller.register_minor_athlete(
                mock_db_session, valid_minor_data
            )

            # ASSERT: Verificar llamadas al PersonMSService
            assert (
                mock_create_person.call_count == 2
            ), "Debe llamar 2 veces a create_or_get_person (menor y representante)"

            # Verificar primera llamada (menor) - debe recibir CreatePersonInMSRequest
            first_call_arg = mock_create_person.call_args_list[0][0][0]
            assert first_call_arg.first_name == "Juan Carlos"
            assert first_call_arg.last_name == "Pérez López"
            assert first_call_arg.dni == "1722345673"
            assert first_call_arg.type_stament == "EXTERNOS"
            # El menor NO debe tener email (se genera dummy)
            assert first_call_arg.email is None

            # Verificar segunda llamada (representante)
            second_call_arg = mock_create_person.call_args_list[1][0][0]
            assert second_call_arg.first_name == "María Elena"
            assert second_call_arg.last_name == "López García"
            assert second_call_arg.dni == "1721234563"
            assert second_call_arg.type_stament == "EXTERNOS"
            # CRITICO: El representante DEBE tener el email REAL del formulario
            assert second_call_arg.email == "maria.lopez@email.com"
            assert not second_call_arg.email.startswith("user")  # No dummy

            # Verificar persistencia local del representante
            athlete_controller.representative_dao.create.assert_called_once()
            rep_data = athlete_controller.representative_dao.create.call_args[0][1]
            assert rep_data["external_person_id"] == mock_ms_external_id_guardian
            assert rep_data["dni"] == "1721234563"

            # Verificar persistencia local del atleta
            athlete_controller.athlete_dao.create.assert_called_once()
            athlete_data = athlete_controller.athlete_dao.create.call_args[0][1]
            assert athlete_data["external_person_id"] == mock_ms_external_id_minor
            assert athlete_data["dni"] == "1722345673"
            assert athlete_data["type_athlete"] == "MINOR"
            assert athlete_data["representative_id"] == 1

            # Verificar respuesta
            assert result.athlete.dni == "1722345673"
            assert result.representative.dni == "1721234563"

    
    @pytest.mark.asyncio
    async def test_register_minor_athlete_duplicate_dni(
        self,
        athlete_controller,
        mock_db_session,
        valid_minor_data
    ):
        """
        Test: Error al intentar registrar menor con DNI duplicado.
        
        Verifica que se lance AlreadyExistsException.
        """
        # ARRANGE: Mockear que ya existe un atleta con ese DNI
        existing_athlete = Athlete(
            id=99,
            external_person_id="existing-ext-id",
            full_name="Otro Atleta",
            dni="1234567890",
            type_athlete="MINOR",
            date_of_birth=date.today() - timedelta(days=365 * 10),
            sex="M",
        )
        athlete_controller.athlete_dao.get_by_dni = MagicMock(
            return_value=existing_athlete
        )

        # ACT & ASSERT: Verificar que se lance la excepción
        with pytest.raises(AlreadyExistsException) as exc_info:
            await athlete_controller.register_minor_athlete(
                mock_db_session, valid_minor_data
            )

        assert "Ya existe un deportista registrado con el DNI" in str(
            exc_info.value.message
        )
    
    @pytest.mark.asyncio
    async def test_register_minor_athlete_no_parental_authorization(
        self,
        athlete_controller,
        mock_db_session,
        valid_minor_data
    ):
        """
        Test: Error al intentar registrar sin autorización parental.
        
        Verifica que se lance ValidationException.
        """
        # ARRANGE: Modificar datos para que no haya autorización
        invalid_data = valid_minor_data.model_copy()
        invalid_data.parental_authorization = False
        
        # ACT & ASSERT: Verificar que el schema rechace esto
        # (En realidad, el schema ya valida esto antes de llegar al controller)
        # Pero el controller también debe validarlo
        athlete_controller.athlete_dao.get_by_dni = MagicMock(return_value=None)
        
        with pytest.raises(ValidationException) as exc_info:
            await athlete_controller.register_minor_athlete(
                mock_db_session,
                invalid_data
            )
        
        assert "autorización parental" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_register_minor_athlete_over_18_years(
        self,
        athlete_controller,
        mock_db_session,
        valid_minor_data
    ):
        """
        Test: Error al intentar registrar persona mayor de 18 años.
        
        Verifica que se lance ValidationException.
        """
        # ARRANGE: Modificar fecha de nacimiento para que sea mayor de edad
        invalid_data = valid_minor_data.model_copy()
        invalid_data.birth_date = date.today() - timedelta(days=365 * 20)  # 20 años
        
        athlete_controller.athlete_dao.get_by_dni = MagicMock(return_value=None)
        
        # ACT & ASSERT: Verificar que se lance la excepción
        with pytest.raises(ValidationException) as exc_info:
            await athlete_controller.register_minor_athlete(
                mock_db_session,
                invalid_data
            )
        
        assert "menor de 18 años" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_register_minor_athlete_reuse_existing_representative(
        self,
        athlete_controller,
        mock_db_session,
        valid_minor_data,
        mock_ms_external_id_minor,
    ):
        """
        Test: Reutilizar representante existente en lugar de crear uno nuevo.

        Verifica que si el representante ya existe, no se crea uno nuevo
        ni se invoca al MS para crearlo.
        """
        # ARRANGE: Mockear que existe un representante con ese DNI
        existing_representative = MagicMock(spec=Representative)
        existing_representative.id = 5
        existing_representative.external_person_id = "existing-guardian-ext-id"
        existing_representative.full_name = "María Elena López García"
        existing_representative.first_name = "María Elena"
        existing_representative.last_name = "López García"
        existing_representative.dni = "1721234563"
        existing_representative.phone = "+593991234567"
        existing_representative.email = "maria.lopez@email.com"
        existing_representative.address = "Av. Principal 123, Ciudad"
        existing_representative.relationship_type = "PADRE/MADRE"
        existing_representative.created_at = datetime.now()
        existing_representative.updated_at = None
        existing_representative.is_active = True

        with patch.object(
            athlete_controller.person_ms_service,
            "create_or_get_person",
            new_callable=AsyncMock,
        ) as mock_create_person:
            mock_create_person.return_value = mock_ms_external_id_minor

            athlete_controller.athlete_dao.get_by_dni = MagicMock(return_value=None)
            athlete_controller.representative_dao.get_by_dni = MagicMock(
                return_value=existing_representative
            )

            mock_athlete = MagicMock(spec=Athlete)
            mock_athlete.id = 1
            mock_athlete.external_person_id = mock_ms_external_id_minor
            mock_athlete.full_name = "Juan Carlos Pérez López"
            mock_athlete.first_name = "Juan Carlos"
            mock_athlete.last_name = "Pérez López"
            mock_athlete.dni = "1234567890"
            mock_athlete.type_athlete = "MINOR"
            mock_athlete.date_of_birth = valid_minor_data.birth_date
            mock_athlete.birth_date = valid_minor_data.birth_date
            mock_athlete.sex = "M"
            mock_athlete.representative_id = 5
            mock_athlete.parental_authorization = None
            mock_athlete.created_at = datetime.now()
            mock_athlete.updated_at = None
            mock_athlete.is_active = True
            athlete_controller.athlete_dao.create = MagicMock(return_value=mock_athlete)

            # ACT: Ejecutar el registro
            result = await athlete_controller.register_minor_athlete(
                mock_db_session, valid_minor_data
            )

            # ASSERT: Verificar que solo se llamó al MS una vez (para el menor)
            assert (
                mock_create_person.call_count == 1
            ), "Solo debe crear persona del menor en MS"

            # Verificar que el atleta se vinculó al representante existente
            athlete_data = athlete_controller.athlete_dao.create.call_args[0][1]
            assert athlete_data["representative_id"] == 5

            # Verificar respuesta
            assert result.representative.id == 5
            assert result.athlete.representative_id == 5

    @pytest.mark.asyncio
    async def test_guardian_email_is_real_not_dummy(
        self, athlete_controller, mock_db_session, valid_minor_data
    ):
        """
        Test CRITICO: Verificar que el email del representante sea real.
        
        AUDITORIA DE LOGICA DE NEGOCIO:
        - El menor NO tiene email -> debe generar dummy
        - El representante SI tiene email real -> debe usar ese, NO dummy
        """
        with patch.object(
            athlete_controller.person_ms_service,
            "create_or_get_person",
            new_callable=AsyncMock,
        ) as mock_create_person:
            mock_create_person.side_effect = ["ext-minor-id", "ext-guardian-id"]

            athlete_controller.athlete_dao.get_by_dni = MagicMock(return_value=None)
            athlete_controller.representative_dao.get_by_dni = MagicMock(
                return_value=None
            )

            mock_representative = MagicMock(spec=Representative)
            mock_representative.id = 1
            mock_representative.external_person_id = "ext-guardian-id"
            mock_representative.full_name = "Guardian Name"
            mock_representative.first_name = "Guardian"
            mock_representative.last_name = "Name"
            mock_representative.dni = "0987654321"
            mock_representative.phone = "+593991234567"
            mock_representative.email = "maria.lopez@email.com"
            mock_representative.address = "Address"
            mock_representative.relationship_type = "PADRE/MADRE"
            mock_representative.created_at = datetime.now()
            mock_representative.updated_at = None
            mock_representative.is_active = True
            athlete_controller.representative_dao.create = MagicMock(
                return_value=mock_representative
            )

            mock_athlete = MagicMock(spec=Athlete)
            mock_athlete.id = 1
            mock_athlete.external_person_id = "ext-minor-id"
            mock_athlete.full_name = "Minor Name"
            mock_athlete.first_name = "Minor"
            mock_athlete.last_name = "Name"
            mock_athlete.dni = "1234567890"
            mock_athlete.type_athlete = "MINOR"
            mock_athlete.date_of_birth = valid_minor_data.birth_date
            mock_athlete.birth_date = valid_minor_data.birth_date
            mock_athlete.sex = "M"
            mock_athlete.representative_id = 1
            mock_athlete.parental_authorization = None
            mock_athlete.created_at = datetime.now()
            mock_athlete.updated_at = None
            mock_athlete.is_active = True
            athlete_controller.athlete_dao.create = MagicMock(return_value=mock_athlete)

            # ACT
            await athlete_controller.register_minor_athlete(
                mock_db_session, valid_minor_data
            )

            # ASSERT: Email del representante debe ser REAL
            guardian_req = mock_create_person.call_args_list[1][0][0]
            assert guardian_req.email == "maria.lopez@email.com"
            assert not guardian_req.email.startswith("user")
            assert "@example.com" not in guardian_req.email

            # Email del menor debe ser None (se genera dummy)
            minor_req = mock_create_person.call_args_list[0][0][0]
            assert minor_req.email is None


class TestMinorAthleteSchemaValidations:
    """
    Tests para validaciones del schema MinorAthleteCreateSchema.
    """
    
    def test_schema_rejects_invalid_dni_format(self):
        """
        Test: Schema rechaza DNI con caracteres inválidos.
        """
        birth_date = date.today() - timedelta(days=365 * 12)
        
        with pytest.raises(ValueError):
            MinorAthleteCreateSchema(
                first_name="Juan",
                last_name="Pérez",
                dni="ABC@#$%",  # DNI inválido
                birth_date=birth_date,
                sex="M",
                representative=RepresentativeCreateSchema(
                    first_name="María",
                    last_name="López",
                    dni="0987654321",
                    address="Av. Test 123",
                    phone="0991234567",
                    email="test@example.com"
                ),
                parental_authorization=True
            )
    
    def test_schema_rejects_invalid_sex(self):
        """
        Test: Schema rechaza valores de sexo inválidos.
        """
        birth_date = date.today() - timedelta(days=365 * 12)
        
        with pytest.raises(ValueError):
            MinorAthleteCreateSchema(
                first_name="Juan",
                last_name="Pérez",
                dni="1234567890",
                birth_date=birth_date,
                sex="X",  # Sexo inválido
                representative=RepresentativeCreateSchema(
                    first_name="María",
                    last_name="López",
                    dni="0987654321",
                    address="Av. Test 123",
                    phone="0991234567",
                    email="test@example.com"
                ),
                parental_authorization=True
            )
    
    def test_schema_rejects_invalid_email(self):
        """
        Test: Schema rechaza email inválido del representante.
        """
        birth_date = date.today() - timedelta(days=365 * 12)
        
        with pytest.raises(ValueError):
            MinorAthleteCreateSchema(
                first_name="Juan",
                last_name="Pérez",
                dni="1234567890",
                birth_date=birth_date,
                sex="M",
                representative=RepresentativeCreateSchema(
                    first_name="María",
                    last_name="López",
                    dni="0987654321",
                    address="Av. Test 123",
                    phone="0991234567",
                    email="email-invalido"  # Email inválido
                ),
                parental_authorization=True
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
