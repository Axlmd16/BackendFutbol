"""
Tests unitarios para el registro de deportistas menores de edad.

Valida la integración con el MS de Usuarios y la persistencia local.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.controllers.athlete_controller import AthleteController
from app.schemas.athlete_schema import MinorAthleteCreateSchema, RepresentativeCreateSchema
from app.utils.exceptions import ValidationException, AlreadyExistsException
from app.models.athlete import Athlete
from app.models.representative import Representative


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
    """
    birth_date = date.today() - timedelta(days=365 * 12)  # 12 años
    
    return MinorAthleteCreateSchema(
        first_name="Juan Carlos",
        last_name="Pérez López",
        dni="1234567890",
        birth_date=birth_date,
        sex="M",
        representative=RepresentativeCreateSchema(
            first_name="María Elena",
            last_name="López García",
            dni="0987654321",
            address="Av. Principal 123, Ciudad",
            phone="+593991234567",
            email="maria.lopez@email.com",
            relationship_type="PADRE/MADRE"
        ),
        parental_authorization=True
    )


@pytest.fixture
def mock_ms_response_minor():
    """
    Mock de la respuesta del MS de Usuarios para el menor.
    """
    return {
        "external_person_id": "ext-minor-uuid-12345",
        "full_name": "Juan Carlos Pérez López",
        "dni": "1234567890"
    }


@pytest.fixture
def mock_ms_response_guardian():
    """
    Mock de la respuesta del MS de Usuarios para el representante.
    """
    return {
        "external_person_id": "ext-guardian-uuid-67890",
        "full_name": "María Elena López García",
        "dni": "0987654321"
    }


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
        mock_ms_response_minor,
        mock_ms_response_guardian
    ):
        """
        Test: Registro exitoso de menor con integración MS de Usuarios.
        
        Verifica que:
        1. Se invoca el MS de Usuarios para crear al menor
        2. Se invoca el MS de Usuarios para crear al representante
        3. Se persiste localmente con external_person_id
        4. Se retorna la respuesta correcta
        """
        # ARRANGE: Mockear las llamadas al MS de Usuarios
        with patch('app.controllers.athlete_controller.create_person_only_in_ms') as mock_create_person:
            # Configurar respuestas del mock
            mock_create_person.side_effect = [
                mock_ms_response_minor,     # Primera llamada: menor
                mock_ms_response_guardian   # Segunda llamada: representante
            ]
            
            # Mockear DAOs para simular que no existen registros previos
            athlete_controller.athlete_dao.get_by_dni = MagicMock(return_value=None)
            athlete_controller.representative_dao.get_by_dni = MagicMock(return_value=None)
            
            # Mockear creación de representante
            from datetime import datetime
            mock_representative = MagicMock(spec=Representative)
            mock_representative.id = 1
            mock_representative.external_person_id = "ext-guardian-uuid-67890"
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
            athlete_controller.representative_dao.create = MagicMock(return_value=mock_representative)
            
            # Mockear creación de atleta
            mock_athlete = MagicMock(spec=Athlete)
            mock_athlete.id = 1
            mock_athlete.external_person_id = "ext-minor-uuid-12345"
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
                mock_db_session,
                valid_minor_data
            )
            
            # ASSERT: Verificar llamadas al MS
            assert mock_create_person.call_count == 2, "Debe llamar 2 veces al MS (menor y representante)"
            
            # Verificar primera llamada (menor)
            first_call_kwargs = mock_create_person.call_args_list[0][1]
            assert first_call_kwargs['first_name'] == "Juan Carlos"
            assert first_call_kwargs['last_name'] == "Pérez López"
            assert first_call_kwargs['dni'] == "1234567890"
            
            # Verificar segunda llamada (representante)
            second_call_kwargs = mock_create_person.call_args_list[1][1]
            assert second_call_kwargs['first_name'] == "María Elena"
            assert second_call_kwargs['last_name'] == "López García"
            assert second_call_kwargs['dni'] == "0987654321"
            
            # Verificar persistencia local del representante
            athlete_controller.representative_dao.create.assert_called_once()
            rep_data = athlete_controller.representative_dao.create.call_args[0][1]
            assert rep_data['external_person_id'] == "ext-guardian-uuid-67890"
            assert rep_data['dni'] == "0987654321"
            
            # Verificar persistencia local del atleta
            athlete_controller.athlete_dao.create.assert_called_once()
            athlete_data = athlete_controller.athlete_dao.create.call_args[0][1]
            assert athlete_data['external_person_id'] == "ext-minor-uuid-12345"
            assert athlete_data['dni'] == "1234567890"
            assert athlete_data['type_athlete'] == "MINOR"
            assert athlete_data['representative_id'] == 1
            
            # Verificar respuesta
            assert result.athlete.dni == "1234567890"
            assert result.representative.dni == "0987654321"
    
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
            sex="M"
        )
        athlete_controller.athlete_dao.get_by_dni = MagicMock(return_value=existing_athlete)
        
        # ACT & ASSERT: Verificar que se lance la excepción
        with pytest.raises(AlreadyExistsException) as exc_info:
            await athlete_controller.register_minor_athlete(
                mock_db_session,
                valid_minor_data
            )
        
        assert "Ya existe un deportista registrado con el DNI" in str(exc_info.value.message)
    
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
        mock_ms_response_minor
    ):
        """
        Test: Reutilizar representante existente en lugar de crear uno nuevo.
        
        Verifica que si el representante ya existe, no se crea uno nuevo.
        """
        # ARRANGE: Mockear que existe un representante con ese DNI
        from datetime import datetime
        existing_representative = MagicMock(spec=Representative)
        existing_representative.id = 5
        existing_representative.external_person_id = "existing-guardian-ext-id"
        existing_representative.full_name = "María Elena López García"
        existing_representative.first_name = "María Elena"
        existing_representative.last_name = "López García"
        existing_representative.dni = "0987654321"
        existing_representative.phone = "+593991234567"
        existing_representative.email = "maria.lopez@email.com"
        existing_representative.address = "Av. Principal 123, Ciudad"
        existing_representative.relationship_type = "PADRE/MADRE"
        existing_representative.created_at = datetime.now()
        existing_representative.updated_at = None
        existing_representative.is_active = True
        
        with patch('app.controllers.athlete_controller.create_person_only_in_ms') as mock_create_person:
            mock_create_person.return_value = mock_ms_response_minor
            
            athlete_controller.athlete_dao.get_by_dni = MagicMock(return_value=None)
            athlete_controller.representative_dao.get_by_dni = MagicMock(
                return_value=existing_representative
            )
            
            mock_athlete = MagicMock(spec=Athlete)
            mock_athlete.id = 1
            mock_athlete.external_person_id = "ext-minor-uuid-12345"
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
                mock_db_session,
                valid_minor_data
            )
            
            # ASSERT: Verificar que solo se llamó al MS una vez (para el menor)
            assert mock_create_person.call_count == 1, "Solo debe crear persona del menor en MS"
            
            # Verificar que el atleta se vinculó al representante existente
            athlete_data = athlete_controller.athlete_dao.create.call_args[0][1]
            assert athlete_data['representative_id'] == 5
            
            # Verificar respuesta
            assert result.representative.id == 5
            assert result.athlete.representative_id == 5


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
