"""
Suite de pruebas unitarias e integración para HS-004: Registro de Deportista Menor.

Este módulo contiene pruebas exhaustivas para validar:
- Happy path (registro exitoso)
- Validaciones de seguridad (autenticación)
- Reglas de negocio (edad, autorización, duplicados)
- Sanitización OWASP (prevención de inyección)
- Manejo de errores y edge cases

Tecnologías: pytest, FastAPI TestClient, unittest.mock
Arquitectura: Limpia/Sensible con inyección de dependencias
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi import status
from httpx import AsyncClient

from app.schemas.athlete_schema import MinorAthleteCreateSchema
from app.utils.exceptions import AlreadyExistsException, ValidationException, DatabaseException
from app.utils.security import CurrentUser
from app.models.athlete import Athlete
from app.models.representative import Representative


# ============================================================================
# FIXTURES - Datos de Prueba
# ============================================================================

@pytest.fixture
def valid_minor_data():
    """
    Datos válidos de un deportista menor de edad.
    
    Cumple con todas las validaciones:
    - Menor de 18 años
    - Autorización parental
    - DNI único
    - Formato de datos correcto
    """
    return {
        "first_name": "Juan Carlos",
        "last_name": "Pérez López",
        "dni": "12345678",
        "birth_date": "2010-05-15",  # ~15 años
        "sex": "M",
        "parental_authorization": True,
        "representative": {
            "first_name": "María Elena",
            "last_name": "López García",
            "dni": "87654321",
            "address": "Av. Principal 123, Ciudad",
            "phone": "+593991234567",
            "email": "maria.lopez@email.com"
        }
    }


@pytest.fixture
def mock_authenticated_user():
    """
    Usuario autenticado simulado para inyectar en dependencias.
    
    Simula un usuario con rol ADMIN que ha pasado la autenticación JWT.
    """
    return CurrentUser(
        id=1,
        email="admin@test.com",
        role="ADMIN",
        external_id="ext-123",
        is_active=True
    )


@pytest.fixture
def mock_athlete_model():
    """Mock del modelo Athlete para respuestas de DAO."""
    athlete = Mock(spec=Athlete)
    athlete.id = 1
    athlete.first_name = "Juan Carlos"
    athlete.last_name = "Pérez López"
    athlete.dni = "12345678"
    athlete.birth_date = date(2010, 5, 15)
    athlete.sex = "M"
    athlete.type_athlete = "MINOR"
    athlete.representative_id = 1
    athlete.parental_authorization = "SI"
    athlete.created_at = date.today()
    athlete.updated_at = None
    athlete.is_active = True
    return athlete


@pytest.fixture
def mock_representative_model():
    """Mock del modelo Representative para respuestas de DAO."""
    rep = Mock(spec=Representative)
    rep.id = 1
    rep.first_name = "María Elena"
    rep.last_name = "López García"
    rep.dni = "87654321"
    rep.address = "Av. Principal 123, Ciudad"
    rep.phone = "+593991234567"
    rep.email = "maria.lopez@email.com"
    rep.created_at = date.today()
    rep.updated_at = None
    rep.is_active = True
    return rep


# ============================================================================
# GRUPO 1: HAPPY PATH - Registro Exitoso
# ============================================================================

class TestHappyPath:
    """Pruebas de casos exitosos de registro de deportista menor."""
    
    @pytest.mark.asyncio
    async def test_should_register_minor_athlete_successfully(
        self,
        client: AsyncClient,
        mock_db_session,
        valid_minor_data,
        mock_authenticated_user,
        mock_athlete_model,
        mock_representative_model
    ):
        """
        GIVEN: Usuario autenticado con datos válidos de menor
        WHEN: Se envía POST a /inscription/escuela-futbol/deportista-menor
        THEN: Retorna 201 Created con datos del atleta y representante
        """
        # Arrange - Configurar mocks
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        # Override de autenticación
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        # Mock de DAOs
        with patch('app.controllers.athlete_controller.AthleteDAO') as MockAthleteDAO, \
             patch('app.controllers.athlete_controller.RepresentativeDAO') as MockRepDAO:
            
            # Configurar comportamiento de mocks
            mock_athlete_dao = MockAthleteDAO.return_value
            mock_rep_dao = MockRepDAO.return_value
            
            # No existe deportista previo (DNI único)
            mock_athlete_dao.get_by_dni.return_value = None
            
            # No existe representante previo (crear nuevo)
            mock_rep_dao.get_by_dni.return_value = None
            mock_rep_dao.create.return_value = mock_representative_model
            
            # Crear deportista exitosamente
            mock_athlete_dao.create.return_value = mock_athlete_model
            
            # Act - Ejecutar request
            response = await client.post(
                "/api/v1/inscription/escuela-futbol/deportista-menor",
                json=valid_minor_data
            )
            
            # Assert - Verificar respuesta
            assert response.status_code == status.HTTP_201_CREATED
            
            data = response.json()
            assert data["status"] == "success"
            assert "deportista menor de edad registrado exitosamente" in data["message"].lower()
            
            # Verificar estructura de datos
            assert "athlete" in data["data"]
            assert "representative" in data["data"]
            
            athlete_data = data["data"]["athlete"]
            assert athlete_data["dni"] == "12345678"
            assert athlete_data["first_name"] == "Juan Carlos"
            assert athlete_data["type_athlete"] == "MINOR"
            assert athlete_data["parental_authorization"] == "SI"
            
            rep_data = data["data"]["representative"]
            assert rep_data["dni"] == "87654321"
            assert rep_data["email"] == "maria.lopez@email.com"
            
            # Verificar que se llamaron los métodos del DAO
            mock_athlete_dao.get_by_dni.assert_called_once_with(mock_db_session, "12345678")
            mock_rep_dao.get_by_dni.assert_called_once()
            mock_rep_dao.create.assert_called_once()
            mock_athlete_dao.create.assert_called_once()
        
        # Cleanup
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_should_reuse_existing_representative(
        self,
        client: AsyncClient,
        mock_db_session,
        valid_minor_data,
        mock_authenticated_user,
        mock_athlete_model,
        mock_representative_model
    ):
        """
        GIVEN: Usuario autenticado y representante ya existe en BD
        WHEN: Se registra un nuevo menor con ese representante
        THEN: Reutiliza el representante existente sin crear duplicado
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        with patch('app.controllers.athlete_controller.AthleteDAO') as MockAthleteDAO, \
             patch('app.controllers.athlete_controller.RepresentativeDAO') as MockRepDAO:
            
            mock_athlete_dao = MockAthleteDAO.return_value
            mock_rep_dao = MockRepDAO.return_value
            
            # Deportista nuevo
            mock_athlete_dao.get_by_dni.return_value = None
            
            # Representante YA EXISTE (reutilizar)
            mock_rep_dao.get_by_dni.return_value = mock_representative_model
            
            mock_athlete_dao.create.return_value = mock_athlete_model
            
            response = await client.post(
                "/api/v1/inscription/escuela-futbol/deportista-menor",
                json=valid_minor_data
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            
            # Verificar que NO se creó nuevo representante
            mock_rep_dao.create.assert_not_called()
            
            # Verificar que sí se usó el existente
            mock_rep_dao.get_by_dni.assert_called_once()
        
        app.dependency_overrides.clear()


# ============================================================================
# GRUPO 2: VALIDACIÓN DE SEGURIDAD - Autenticación
# ============================================================================

class TestSecurityValidation:
    """Pruebas de validación de autenticación y autorización."""
    
    @pytest.mark.asyncio
    async def test_should_reject_request_without_token(
        self,
        client: AsyncClient,
        valid_minor_data
    ):
        """
        GIVEN: Request sin token de autenticación
        WHEN: Se intenta registrar un menor
        THEN: Retorna 401 Unauthorized antes de ejecutar lógica de negocio
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        # NO configurar override de autenticación (simula sin token)
        
        response = await client.post(
            "/api/v1/inscription/escuela-futbol/deportista-menor",
            json=valid_minor_data
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Verificar que incluye header WWW-Authenticate
        # (puede variar según implementación exacta de HTTPBearer)
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_should_reject_request_with_invalid_token(
        self,
        client: AsyncClient,
        valid_minor_data
    ):
        """
        GIVEN: Token JWT inválido o corrupto
        WHEN: Se intenta registrar un menor
        THEN: Retorna 401 Unauthorized con mensaje descriptivo
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        from fastapi import HTTPException
        
        # Simular que get_current_user lanza excepción por token inválido
        async def override_auth_invalid():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o corrupto"
            )
        
        app.dependency_overrides[get_current_user] = override_auth_invalid
        
        response = await client.post(
            "/api/v1/inscription/escuela-futbol/deportista-menor",
            json=valid_minor_data
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_should_reject_inactive_user(
        self,
        client: AsyncClient,
        valid_minor_data
    ):
        """
        GIVEN: Usuario autenticado pero inactivo
        WHEN: Se intenta registrar un menor
        THEN: Retorna 403 Forbidden
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        # Usuario inactivo
        inactive_user = CurrentUser(
            id=1,
            email="inactive@test.com",
            role="USER",
            is_active=False
        )
        
        async def override_auth():
            return inactive_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        with patch('app.controllers.athlete_controller.AthleteDAO'), \
             patch('app.controllers.athlete_controller.RepresentativeDAO'):
            
            response = await client.post(
                "/api/v1/inscription/escuela-futbol/deportista-menor",
                json=valid_minor_data
            )
            
            # Según implementación, podría ser 403 si se usa get_current_active_user
            assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        
        app.dependency_overrides.clear()


# ============================================================================
# GRUPO 3: REGLAS DE NEGOCIO - Validaciones de Datos
# ============================================================================

class TestBusinessRules:
    """Pruebas de reglas de negocio y validaciones."""
    
    @pytest.mark.asyncio
    async def test_should_reject_athlete_over_18_years_old(
        self,
        client: AsyncClient,
        mock_db_session,
        mock_authenticated_user
    ):
        """
        GIVEN: Datos de persona mayor de 18 años
        WHEN: Se intenta registrar como menor
        THEN: Retorna 422 con mensaje de validación de edad
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        # Persona de 19 años (mayor de edad)
        adult_birth_date = (date.today() - timedelta(days=19*365)).isoformat()
        
        adult_data = {
            "first_name": "Adulto",
            "last_name": "Test",
            "dni": "99999999",
            "birth_date": adult_birth_date,
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "88888888",
                "address": "Calle 123",
                "phone": "+593991234567",
                "email": "rep@test.com"
            }
        }
        
        response = await client.post(
            "/api/v1/inscription/escuela-futbol/deportista-menor",
            json=adult_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        data = response.json()
        # Validación puede venir de Pydantic o del controlador
        assert "18 años" in str(data).lower() or "edad" in str(data).lower()
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_should_reject_without_parental_authorization(
        self,
        client: AsyncClient,
        valid_minor_data,
        mock_authenticated_user
    ):
        """
        GIVEN: Datos de menor SIN autorización parental
        WHEN: Se intenta registrar
        THEN: Retorna 422 con mensaje de autorización requerida
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        # Modificar datos para quitar autorización
        invalid_data = valid_minor_data.copy()
        invalid_data["parental_authorization"] = False
        
        response = await client.post(
            "/api/v1/inscription/escuela-futbol/deportista-menor",
            json=invalid_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        data = response.json()
        assert "autorización" in str(data).lower() or "authorization" in str(data).lower()
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_should_reject_duplicate_dni_athlete(
        self,
        client: AsyncClient,
        mock_db_session,
        valid_minor_data,
        mock_authenticated_user,
        mock_athlete_model
    ):
        """
        GIVEN: DNI de menor ya existe en base de datos
        WHEN: Se intenta registrar nuevamente
        THEN: Retorna 409 Conflict con mensaje de duplicado
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        with patch('app.controllers.athlete_controller.AthleteDAO') as MockAthleteDAO, \
             patch('app.controllers.athlete_controller.RepresentativeDAO'):
            
            mock_athlete_dao = MockAthleteDAO.return_value
            
            # Simular que YA EXISTE deportista con ese DNI
            mock_athlete_dao.get_by_dni.return_value = mock_athlete_model
            
            response = await client.post(
                "/api/v1/inscription/escuela-futbol/deportista-menor",
                json=valid_minor_data
            )
            
            assert response.status_code == status.HTTP_409_CONFLICT
            
            data = response.json()
            assert data["status"] == "error"
            assert "ya existe" in data["message"].lower() or "duplicado" in data["message"].lower()
            assert "12345678" in data["message"]  # DNI en el mensaje
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_should_reject_minor_under_5_years(
        self,
        client: AsyncClient,
        mock_authenticated_user
    ):
        """
        GIVEN: Datos de menor con menos de 5 años
        WHEN: Se intenta registrar
        THEN: Retorna 422 con mensaje de edad mínima
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        # Niño de 3 años (muy joven)
        very_young_birth_date = (date.today() - timedelta(days=3*365)).isoformat()
        
        young_data = {
            "first_name": "Muy",
            "last_name": "Joven",
            "dni": "11111111",
            "birth_date": very_young_birth_date,
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "22222222",
                "address": "Calle 123",
                "phone": "+593991234567",
                "email": "rep2@test.com"
            }
        }
        
        response = await client.post(
            "/api/v1/inscription/escuela-futbol/deportista-menor",
            json=young_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        data = response.json()
        assert "5 años" in str(data).lower() or "edad" in str(data).lower()
        
        app.dependency_overrides.clear()


# ============================================================================
# GRUPO 4: SANITIZACIÓN OWASP - Prevención de Inyección
# ============================================================================

class TestOWASPSanitization:
    """Pruebas de sanitización y prevención de inyección."""
    
    @pytest.mark.asyncio
    async def test_should_sanitize_or_reject_xss_in_names(
        self,
        client: AsyncClient,
        mock_authenticated_user
    ):
        """
        GIVEN: Nombre con script XSS malicioso
        WHEN: Se intenta registrar
        THEN: Rechaza por validación de formato o sanitiza el input
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        xss_data = {
            "first_name": "<script>alert('XSS')</script>",
            "last_name": "Normal",
            "dni": "33333333",
            "birth_date": "2010-05-15",
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "44444444",
                "address": "Calle 123",
                "phone": "+593991234567",
                "email": "rep3@test.com"
            }
        }
        
        response = await client.post(
            "/api/v1/inscription/escuela-futbol/deportista-menor",
            json=xss_data
        )
        
        # Debe rechazar por validación de Pydantic (solo letras permitidas)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        data = response.json()
        # Verificar que menciona problema con el nombre
        assert "first_name" in str(data).lower() or "nombre" in str(data).lower()
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_should_sanitize_or_reject_sql_injection_in_dni(
        self,
        client: AsyncClient,
        mock_authenticated_user
    ):
        """
        GIVEN: DNI con intento de inyección SQL
        WHEN: Se intenta registrar
        THEN: Rechaza por validación de formato (solo alfanuméricos)
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        sql_injection_data = {
            "first_name": "Test",
            "last_name": "User",
            "dni": "12345'; DROP TABLE athletes; --",
            "birth_date": "2010-05-15",
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "55555555",
                "address": "Calle 123",
                "phone": "+593991234567",
                "email": "rep4@test.com"
            }
        }
        
        response = await client.post(
            "/api/v1/inscription/escuela-futbol/deportista-menor",
            json=sql_injection_data
        )
        
        # Debe rechazar por validación regex de DNI
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        data = response.json()
        assert "dni" in str(data).lower()
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_should_sanitize_phone_with_special_chars(
        self,
        client: AsyncClient,
        mock_db_session,
        mock_authenticated_user,
        mock_athlete_model,
        mock_representative_model
    ):
        """
        GIVEN: Teléfono con caracteres especiales peligrosos
        WHEN: Se intenta registrar
        THEN: Rechaza o sanitiza manteniendo solo caracteres válidos
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        dangerous_phone_data = {
            "first_name": "Test",
            "last_name": "User",
            "dni": "66666666",
            "birth_date": "2010-05-15",
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "77777777",
                "address": "Calle 123",
                "phone": "+593<script>alert('xss')</script>",  # Inyección en teléfono
                "email": "rep5@test.com"
            }
        }
        
        response = await client.post(
            "/api/v1/inscription/escuela-futbol/deportista-menor",
            json=dangerous_phone_data
        )
        
        # Debe rechazar por validación de teléfono
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        data = response.json()
        assert "phone" in str(data).lower() or "teléfono" in str(data).lower()
        
        app.dependency_overrides.clear()


# ============================================================================
# GRUPO 5: MANEJO DE ERRORES - Edge Cases
# ============================================================================

class TestErrorHandling:
    """Pruebas de manejo de errores y casos excepcionales."""
    
    @pytest.mark.asyncio
    async def test_should_handle_database_error_gracefully(
        self,
        client: AsyncClient,
        mock_db_session,
        valid_minor_data,
        mock_authenticated_user
    ):
        """
        GIVEN: Error inesperado de base de datos durante registro
        WHEN: Se intenta registrar un menor
        THEN: Retorna 500 con mensaje genérico (sin exponer detalles internos)
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        with patch('app.controllers.athlete_controller.AthleteDAO') as MockAthleteDAO, \
             patch('app.controllers.athlete_controller.RepresentativeDAO') as MockRepDAO:
            
            mock_athlete_dao = MockAthleteDAO.return_value
            mock_rep_dao = MockRepDAO.return_value
            
            # Simular error de base de datos
            mock_athlete_dao.get_by_dni.return_value = None
            mock_rep_dao.get_by_dni.return_value = None
            mock_rep_dao.create.side_effect = Exception("Database connection lost")
            
            response = await client.post(
                "/api/v1/inscription/escuela-futbol/deportista-menor",
                json=valid_minor_data
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            
            data = response.json()
            assert data["status"] == "error"
            # No debe exponer el error real de base de datos
            assert "Database connection lost" not in data["message"]
            assert "error" in data["message"].lower() or "servidor" in data["message"].lower()
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_should_validate_email_format(
        self,
        client: AsyncClient,
        mock_authenticated_user
    ):
        """
        GIVEN: Email con formato inválido
        WHEN: Se intenta registrar
        THEN: Retorna 422 con error de validación de email
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        invalid_email_data = {
            "first_name": "Test",
            "last_name": "User",
            "dni": "88888888",
            "birth_date": "2010-05-15",
            "sex": "M",
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "99999999",
                "address": "Calle 123",
                "phone": "+593991234567",
                "email": "email_invalido_sin_arroba.com"  # Email inválido
            }
        }
        
        response = await client.post(
            "/api/v1/inscription/escuela-futbol/deportista-menor",
            json=invalid_email_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        data = response.json()
        assert "email" in str(data).lower()
        
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_should_validate_sex_field_values(
        self,
        client: AsyncClient,
        mock_authenticated_user
    ):
        """
        GIVEN: Campo sex con valor inválido (no M ni F)
        WHEN: Se intenta registrar
        THEN: Retorna 422 con error de validación
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        invalid_sex_data = {
            "first_name": "Test",
            "last_name": "User",
            "dni": "00000000",
            "birth_date": "2010-05-15",
            "sex": "X",  # Valor inválido (solo M o F permitidos)
            "parental_authorization": True,
            "representative": {
                "first_name": "Rep",
                "last_name": "Test",
                "dni": "11111111",
                "address": "Calle 123",
                "phone": "+593991234567",
                "email": "rep6@test.com"
            }
        }
        
        response = await client.post(
            "/api/v1/inscription/escuela-futbol/deportista-menor",
            json=invalid_sex_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        data = response.json()
        assert "sex" in str(data).lower() or "sexo" in str(data).lower()
        
        app.dependency_overrides.clear()


# ============================================================================
# GRUPO 6: AUDITORÍA - Logging y Trazabilidad
# ============================================================================

class TestAuditLogging:
    """Pruebas de logging y auditoría de acciones."""
    
    @pytest.mark.asyncio
    async def test_should_log_registration_with_user_info(
        self,
        client: AsyncClient,
        mock_db_session,
        valid_minor_data,
        mock_authenticated_user,
        mock_athlete_model,
        mock_representative_model
    ):
        """
        GIVEN: Usuario autenticado registra un menor
        WHEN: Se completa el registro exitosamente
        THEN: Se registra en logs quién realizó la acción con todos los detalles
        """
        from main import app
        # from app.utils.security import get_current_user  # Comentado: get_current_user no implementado aún
        
        async def override_auth():
            return mock_authenticated_user
        
        app.dependency_overrides[get_current_user] = override_auth
        
        with patch('app.controllers.athlete_controller.AthleteDAO') as MockAthleteDAO, \
             patch('app.controllers.athlete_controller.RepresentativeDAO') as MockRepDAO, \
             patch('app.services.routers.inscription_router.logger') as mock_logger:
            
            mock_athlete_dao = MockAthleteDAO.return_value
            mock_rep_dao = MockRepDAO.return_value
            
            mock_athlete_dao.get_by_dni.return_value = None
            mock_rep_dao.get_by_dni.return_value = None
            mock_rep_dao.create.return_value = mock_representative_model
            mock_athlete_dao.create.return_value = mock_athlete_model
            
            response = await client.post(
                "/api/v1/inscription/escuela-futbol/deportista-menor",
                json=valid_minor_data
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            
            # Verificar que se logueó la acción con información del usuario
            assert mock_logger.info.called
            
            # Buscar el log que contiene información del usuario
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            user_log_found = any("admin@test.com" in call for call in log_calls)
            
            assert user_log_found, "Debe registrar quién realizó el registro"
        
        app.dependency_overrides.clear()
