"""Tests para PersonMSService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.client.person_ms_service import PersonMSService
from app.schemas.user_schema import CreatePersonInMSRequest
from app.utils.exceptions import ExternalServiceException, ValidationException


class TestPersonMSServiceInit:
    """Tests para inicialización de PersonMSService."""

    def test_init_default_client(self):
        """Inicializa con PersonClient por defecto."""
        service = PersonMSService()
        assert service.person_client is not None

    def test_init_custom_client(self):
        """Inicializa con cliente personalizado."""
        mock_client = MagicMock()
        service = PersonMSService(person_client=mock_client)
        assert service.person_client == mock_client


class TestCreateOrGetPerson:
    """Tests para create_or_get_person."""

    @pytest.fixture
    def service(self):
        """Service con mock client."""
        mock_client = AsyncMock()
        return PersonMSService(person_client=mock_client)

    @pytest.fixture
    def person_data(self):
        """Datos de persona para crear."""
        return CreatePersonInMSRequest(
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
            phone="0999123456",
            direction="Av. Principal 123",
            type_identification="CEDULA",
            type_stament="ESTUDIANTES",
        )

    @pytest.mark.asyncio
    async def test_create_person_success(self, service, person_data):
        """Crea persona exitosamente."""
        service.person_client.create_person_with_account = AsyncMock(
            return_value={
                "status": "success",
                "data": {"external": "ext-123"},
            }
        )

        result = await service.create_or_get_person(person_data)

        assert result == "ext-123"
        service.person_client.create_person_with_account.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_person_duplicate_gets_existing(self, service, person_data):
        """Si ya existe, obtiene la persona existente."""
        # Simular error de duplicado
        service.person_client.create_person_with_account = AsyncMock(
            side_effect=ValidationException(
                "la persona ya esta registrada con esa identificacion"
            )
        )
        service.person_client.get_by_identification = AsyncMock(
            return_value={
                "data": {
                    "external": "ext-456",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                }
            }
        )

        result = await service.create_or_get_person(person_data)

        assert result == "ext-456"

    @pytest.mark.asyncio
    async def test_create_person_external_service_error(self, service, person_data):
        """Propaga ExternalServiceException."""
        service.person_client.create_person_with_account = AsyncMock(
            side_effect=ExternalServiceException("Servicio no disponible")
        )

        with pytest.raises(ExternalServiceException):
            await service.create_or_get_person(person_data)

    @pytest.mark.asyncio
    async def test_create_person_unexpected_error(self, service, person_data):
        """Envuelve errores inesperados en ExternalServiceException."""
        service.person_client.create_person_with_account = AsyncMock(
            side_effect=Exception("Error inesperado")
        )

        with pytest.raises(ExternalServiceException) as exc_info:
            await service.create_or_get_person(person_data)

        assert "no está disponible" in str(exc_info.value)


class TestUpdatePerson:
    """Tests para update_person."""

    @pytest.fixture
    def service(self):
        """Service con mock client."""
        mock_client = AsyncMock()
        return PersonMSService(person_client=mock_client)

    @pytest.mark.asyncio
    async def test_update_person_success(self, service):
        """Actualiza persona exitosamente."""
        service.person_client.update_person = AsyncMock(
            return_value={"external": "ext-123"}
        )

        result = await service.update_person(
            external="ext-123",
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
        )

        assert result == "ext-123"
        service.person_client.update_person.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_person_no_external_in_response(self, service):
        """Busca external por DNI si no viene en respuesta."""
        service.person_client.update_person = AsyncMock(return_value={})
        service.person_client.get_by_identification = AsyncMock(
            return_value={"external": "ext-456"}
        )

        result = await service.update_person(
            external="ext-123",
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
        )

        assert result == "ext-456"

    @pytest.mark.asyncio
    async def test_update_person_external_service_error(self, service):
        """Propaga ExternalServiceException."""
        service.person_client.update_person = AsyncMock(
            side_effect=ExternalServiceException("Servicio no disponible")
        )

        with pytest.raises(ExternalServiceException):
            await service.update_person(
                external="ext-123",
                first_name="Juan",
                last_name="Pérez",
                dni="1234567890",
            )

    @pytest.mark.asyncio
    async def test_update_person_unexpected_error(self, service):
        """Envuelve errores inesperados."""
        service.person_client.update_person = AsyncMock(side_effect=Exception("Error"))

        with pytest.raises(ExternalServiceException):
            await service.update_person(
                external="ext-123",
                first_name="Juan",
                last_name="Pérez",
                dni="1234567890",
            )


class TestGetAllUsers:
    """Tests para get_all_users."""

    @pytest.fixture
    def service(self):
        """Service con mock client."""
        mock_client = AsyncMock()
        return PersonMSService(person_client=mock_client)

    @pytest.mark.asyncio
    async def test_get_all_users_success(self, service):
        """Obtiene usuarios exitosamente."""
        service.person_client.get_all_filter = AsyncMock(
            return_value={"data": [{"id": 1}, {"id": 2}]}
        )

        result = await service.get_all_users()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_all_users_empty(self, service):
        """Retorna lista vacía si no hay usuarios."""
        service.person_client.get_all_filter = AsyncMock(return_value={})

        result = await service.get_all_users()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_users_external_error(self, service):
        """Propaga ExternalServiceException."""
        service.person_client.get_all_filter = AsyncMock(
            side_effect=ExternalServiceException("Error")
        )

        with pytest.raises(ExternalServiceException):
            await service.get_all_users()

    @pytest.mark.asyncio
    async def test_get_all_users_unexpected_error(self, service):
        """Envuelve errores inesperados."""
        service.person_client.get_all_filter = AsyncMock(side_effect=Exception("Error"))

        with pytest.raises(ExternalServiceException):
            await service.get_all_users()


class TestGetUserByIdentification:
    """Tests para get_user_by_identification."""

    @pytest.fixture
    def service(self):
        """Service con mock client."""
        mock_client = AsyncMock()
        return PersonMSService(person_client=mock_client)

    @pytest.mark.asyncio
    async def test_get_user_by_identification_success(self, service):
        """Obtiene usuario por identificación."""
        service.person_client.get_by_identification = AsyncMock(
            return_value={"dni": "1234567890", "name": "Juan"}
        )

        result = await service.get_user_by_identification("1234567890")

        assert result["dni"] == "1234567890"

    @pytest.mark.asyncio
    async def test_get_user_by_identification_external_error(self, service):
        """Propaga ExternalServiceException."""
        service.person_client.get_by_identification = AsyncMock(
            side_effect=ExternalServiceException("Error")
        )

        with pytest.raises(ExternalServiceException):
            await service.get_user_by_identification("1234567890")

    @pytest.mark.asyncio
    async def test_get_user_by_identification_unexpected_error(self, service):
        """Envuelve errores inesperados."""
        service.person_client.get_by_identification = AsyncMock(
            side_effect=Exception("Error")
        )

        with pytest.raises(ExternalServiceException):
            await service.get_user_by_identification("1234567890")


class TestBuildPersonPayload:
    """Tests para _build_person_payload."""

    def test_build_payload_basic(self):
        """Construye payload básico."""
        service = PersonMSService()
        data = CreatePersonInMSRequest(
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
            type_identification="CEDULA",
            type_stament="ESTUDIANTES",
        )

        payload = service._build_person_payload(data)

        assert payload["first_name"] == "Juan"
        assert payload["last_name"] == "Pérez"
        assert payload["identification"] == "1234567890"
        assert payload["direction"] == "S/N"  # Default
        assert payload["phono"] == "S/N"  # Default

    def test_build_payload_with_phone_and_direction(self):
        """Construye payload con teléfono y dirección."""
        service = PersonMSService()
        data = CreatePersonInMSRequest(
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
            phone="0999123456",
            direction="Av. Principal",
            type_identification="CEDULA",
            type_stament="ESTUDIANTES",
        )

        payload = service._build_person_payload(data)

        assert payload["direction"] == "Av. Principal"
        assert payload["phono"] == "0999123456"


class TestPrivateMethods:
    """Tests para métodos privados de validación."""

    def test_extract_external_from_data(self):
        """Extrae external de data."""
        service = PersonMSService()
        response = {"data": {"external": "ext-123"}}

        result = service._extract_external(response)

        assert result == "ext-123"

    def test_extract_external_from_root(self):
        """Extrae external de raíz."""
        service = PersonMSService()
        response = {"external": "ext-456"}

        result = service._extract_external(response)

        assert result == "ext-456"

    def test_extract_external_not_found(self):
        """Retorna None si no hay external."""
        service = PersonMSService()
        response = {"other": "data"}

        result = service._extract_external(response)

        assert result is None

    def test_is_duplicate_message_true(self):
        """Detecta mensaje de duplicado."""
        service = PersonMSService()

        assert service._is_duplicate_message(
            "la persona ya esta registrada con esa identificacion"
        )
        assert service._is_duplicate_message("already exists")
        assert service._is_duplicate_message("registro duplicado")

    def test_is_duplicate_message_false(self):
        """No detecta mensaje que no es duplicado."""
        service = PersonMSService()

        assert not service._is_duplicate_message("Error de conexión")
        assert not service._is_duplicate_message("Validation failed")

    def test_normalize_name(self):
        """Normaliza nombres."""
        service = PersonMSService()

        assert service._normalize_name("  Juan  Pérez  ") == "juan perez"
        assert service._normalize_name("MARÍA") == "maria"
        assert service._normalize_name("José") == "jose"

    def test_normalize_name_empty(self):
        """Normaliza nombre vacío."""
        service = PersonMSService()

        assert service._normalize_name("") == ""
        assert service._normalize_name(None) == ""


class TestValidateSameIdentity:
    """Tests para _validate_same_identity."""

    @pytest.fixture
    def service(self):
        return PersonMSService()

    @pytest.fixture
    def person_data(self):
        return CreatePersonInMSRequest(
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
            type_identification="CEDULA",
            type_stament="ESTUDIANTES",
        )

    def test_validate_same_identity_success(self, service, person_data):
        """Valida identidad correcta."""
        # La respuesta del MS viene en formato data: {...}
        existing = {
            "data": {
                "first_name": "Juan",
                "last_name": "Pérez",
            }
        }

        # No debe lanzar excepción
        service._validate_same_identity(existing, person_data)

    def test_validate_same_identity_case_insensitive(self, service, person_data):
        """Valida identidad case-insensitive."""
        existing = {
            "data": {
                "first_name": "JUAN",
                "last_name": "PÉREZ",
            }
        }

        # No debe lanzar excepción
        service._validate_same_identity(existing, person_data)

    def test_validate_same_identity_full_name(self, service, person_data):
        """Valida identidad con full_name."""
        existing = {
            "data": {
                "full_name": "Juan Pérez",
            }
        }

        # No debe lanzar excepción
        service._validate_same_identity(existing, person_data)

    def test_validate_same_identity_mismatch(self, service, person_data):
        """Rechaza identidad diferente."""
        existing = {
            "data": {
                "first_name": "Carlos",
                "last_name": "López",
            }
        }

        with pytest.raises(ValidationException):
            service._validate_same_identity(existing, person_data)

    def test_validate_same_identity_no_names(self, service, person_data):
        """Rechaza si no hay nombres."""
        existing = {"data": {}}

        with pytest.raises(ValidationException) as exc_info:
            service._validate_same_identity(existing, person_data)

        assert "no se pudieron obtener los nombres" in str(exc_info.value)


class TestHandleCreateResponse:
    """Tests para _handle_create_response."""

    @pytest.fixture
    def service(self):
        mock_client = AsyncMock()
        return PersonMSService(person_client=mock_client)

    @pytest.fixture
    def person_data(self):
        return CreatePersonInMSRequest(
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
            type_identification="CEDULA",
            type_stament="ESTUDIANTES",
        )

    @pytest.mark.asyncio
    async def test_handle_success_with_external(self, service, person_data):
        """Maneja respuesta exitosa con external."""
        response = {"status": "success", "data": {"external": "ext-123"}}

        result = await service._handle_create_response(response, person_data)

        assert result == "ext-123"

    @pytest.mark.asyncio
    async def test_handle_success_without_external(self, service, person_data):
        """Busca external si no viene en respuesta."""
        response = {"status": "success", "data": {}}
        service.person_client.get_by_identification = AsyncMock(
            return_value={"external": "ext-456"}
        )

        result = await service._handle_create_response(response, person_data)

        assert result == "ext-456"

    @pytest.mark.asyncio
    async def test_handle_duplicate_message(self, service, person_data):
        """Maneja mensaje de duplicado."""
        response = {
            "status": "error",
            "message": "la persona ya esta registrada con esa identificacion",
        }
        service.person_client.get_by_identification = AsyncMock(
            return_value={
                "data": {
                    "external": "ext-789",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                }
            }
        )

        result = await service._handle_create_response(response, person_data)

        assert result == "ext-789"

    @pytest.mark.asyncio
    async def test_handle_unknown_error(self, service, person_data):
        """Lanza ValidationException en error desconocido."""
        response = {"status": "error", "message": "Unknown error"}

        with pytest.raises(ValidationException):
            await service._handle_create_response(response, person_data)
