"""Tests para PersonMSService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.client.person_ms_service import SERVICE_UNAVAILABLE_MSG, PersonMSService
from app.schemas.user_schema import CreatePersonInMSRequest
from app.utils.exceptions import ExternalServiceException, ValidationException


class TestPersonMSServiceInit:
    """Tests para la inicialización de PersonMSService."""

    def test_init_with_default_client(self):
        """Verifica inicialización con cliente por defecto."""
        service = PersonMSService()
        assert service.person_client is not None

    def test_init_with_custom_client(self):
        """Verifica inicialización con cliente personalizado."""
        mock_client = MagicMock()
        service = PersonMSService(person_client=mock_client)
        assert service.person_client == mock_client


class TestCreateOrGetPerson:
    """Tests para create_or_get_person."""

    @pytest.fixture
    def service(self):
        """Servicio con cliente mock."""
        mock_client = MagicMock()
        return PersonMSService(person_client=mock_client)

    @pytest.fixture
    def sample_data(self):
        """Datos de ejemplo para crear persona."""
        return CreatePersonInMSRequest(
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
            type_identification="CEDULA",
            type_stament="EXTERNOS",
            direction="Calle 123",
            phone="0991234567",
        )

    @pytest.mark.asyncio
    async def test_create_person_success(self, service, sample_data):
        """Verifica creación exitosa de persona."""
        service.person_client.create_person_with_account = AsyncMock(
            return_value={
                "status": "success",
                "data": {"external": "ext-12345"},
            }
        )

        result = await service.create_or_get_person(sample_data)
        assert result == "ext-12345"

    @pytest.mark.asyncio
    async def test_create_person_duplicate_gets_existing(self, service, sample_data):
        """Verifica que busca persona existente si hay duplicado."""
        service.person_client.create_person_with_account = AsyncMock(
            side_effect=ValidationException(
                "La persona ya esta registrada con esa identificacion"
            )
        )
        service.person_client.get_by_identification = AsyncMock(
            return_value={
                "data": {
                    "external": "existing-ext",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                }
            }
        )

        result = await service.create_or_get_person(sample_data)
        assert result == "existing-ext"

    @pytest.mark.asyncio
    async def test_create_person_external_service_error(self, service, sample_data):
        """Verifica manejo de error de servicio externo."""
        service.person_client.create_person_with_account = AsyncMock(
            side_effect=ExternalServiceException("Servicio no disponible")
        )

        with pytest.raises(ExternalServiceException):
            await service.create_or_get_person(sample_data)

    @pytest.mark.asyncio
    async def test_create_person_unexpected_error(self, service, sample_data):
        """Verifica manejo de error inesperado."""
        service.person_client.create_person_with_account = AsyncMock(
            side_effect=Exception("Error inesperado")
        )

        with pytest.raises(ExternalServiceException) as exc_info:
            await service.create_or_get_person(sample_data)
        assert SERVICE_UNAVAILABLE_MSG in str(exc_info.value.message)


class TestUpdatePerson:
    """Tests para update_person."""

    @pytest.fixture
    def service(self):
        """Servicio con cliente mock."""
        mock_client = MagicMock()
        return PersonMSService(person_client=mock_client)

    @pytest.mark.asyncio
    async def test_update_person_success(self, service):
        """Verifica actualización exitosa."""
        service.person_client.update_person = AsyncMock(
            return_value={"data": {"external": "ext-updated"}}
        )

        result = await service.update_person(
            external="ext-123",
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
        )
        assert result == "ext-updated"

    @pytest.mark.asyncio
    async def test_update_person_fallback_to_dni(self, service):
        """Verifica que busca por DNI si no hay external en respuesta."""
        service.person_client.update_person = AsyncMock(
            return_value={"status": "success"}  # Sin external
        )
        service.person_client.get_by_identification = AsyncMock(
            return_value={"data": {"external": "ext-from-dni"}}
        )

        result = await service.update_person(
            external="ext-123",
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
        )
        assert result == "ext-from-dni"

    @pytest.mark.asyncio
    async def test_update_person_external_service_error(self, service):
        """Verifica manejo de error de servicio externo."""
        service.person_client.update_person = AsyncMock(
            side_effect=ExternalServiceException("Error")
        )

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
        """Servicio con cliente mock."""
        mock_client = MagicMock()
        return PersonMSService(person_client=mock_client)

    @pytest.mark.asyncio
    async def test_get_all_users_success(self, service):
        """Verifica obtención de usuarios."""
        service.person_client.get_all_filter = AsyncMock(
            return_value={"data": [{"id": 1}, {"id": 2}]}
        )

        result = await service.get_all_users()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_all_users_external_error(self, service):
        """Verifica manejo de error externo."""
        service.person_client.get_all_filter = AsyncMock(
            side_effect=ExternalServiceException("Error")
        )

        with pytest.raises(ExternalServiceException):
            await service.get_all_users()


class TestGetUserByIdentification:
    """Tests para get_user_by_identification."""

    @pytest.fixture
    def service(self):
        """Servicio con cliente mock."""
        mock_client = MagicMock()
        return PersonMSService(person_client=mock_client)

    @pytest.mark.asyncio
    async def test_get_user_by_identification_success(self, service):
        """Verifica obtención de usuario por identificación."""
        service.person_client.get_by_identification = AsyncMock(
            return_value={"data": {"dni": "1234567890"}}
        )

        result = await service.get_user_by_identification("1234567890")
        assert result["data"]["dni"] == "1234567890"


class TestHelperMethods:
    """Tests para métodos auxiliares."""

    def test_build_person_payload(self):
        """Verifica construcción del payload."""
        service = PersonMSService()
        data = CreatePersonInMSRequest(
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
            type_identification="CEDULA",
            type_stament="EXTERNOS",
            direction="Calle 123",
            phone="0991234567",
        )

        payload = service._build_person_payload(data)

        assert payload["first_name"] == "Juan"
        assert payload["last_name"] == "Pérez"
        assert payload["identification"] == "1234567890"
        assert payload["direction"] == "Calle 123"
        assert payload["phono"] == "0991234567"
        assert "email" in payload
        assert "password" in payload

    def test_build_person_payload_with_none_values(self):
        """Verifica payload con valores None."""
        service = PersonMSService()
        data = CreatePersonInMSRequest(
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
            type_identification="CEDULA",
            type_stament="EXTERNOS",
            direction=None,
            phone=None,
        )

        payload = service._build_person_payload(data)

        assert payload["direction"] == "S/N"
        assert payload["phono"] == "S/N"

    def test_extract_external_from_data_dict(self):
        """Verifica extracción de external desde dict."""
        result = PersonMSService._extract_external({"data": {"external": "ext-123"}})
        assert result == "ext-123"

    def test_extract_external_from_data_list(self):
        """Verifica extracción de external desde lista."""
        result = PersonMSService._extract_external({"data": [{"external": "ext-123"}]})
        assert result == "ext-123"

    def test_extract_external_from_root(self):
        """Verifica extracción de external desde raíz."""
        result = PersonMSService._extract_external({"external": "ext-123"})
        assert result == "ext-123"

    def test_extract_external_none(self):
        """Verifica que retorna None si no hay external."""
        result = PersonMSService._extract_external({"data": {}})
        assert result is None

    def test_extract_external_invalid_type(self):
        """Verifica manejo de tipo inválido."""
        result = PersonMSService._extract_external("not a dict")
        assert result is None

    def test_extract_name_fields_from_dict(self):
        """Verifica extracción de nombres desde dict."""
        first, last, full = PersonMSService._extract_name_fields(
            {"data": {"first_name": "Juan", "last_name": "Pérez"}}
        )
        assert first == "Juan"
        assert last == "Pérez"

    def test_extract_name_fields_from_list(self):
        """Verifica extracción de nombres desde lista."""
        first, last, full = PersonMSService._extract_name_fields(
            {"data": [{"first_name": "Juan", "last_name": "Pérez"}]}
        )
        assert first == "Juan"
        assert last == "Pérez"

    def test_extract_name_fields_alternative_keys(self):
        """Verifica extracción con keys alternativas."""
        first, last, full = PersonMSService._extract_name_fields(
            {
                "data": {
                    "firts_name": "Juan",
                    "lastName": "Pérez",
                    "fullName": "Juan Pérez",
                }
            }
        )
        assert first == "Juan"
        assert last == "Pérez"
        assert full == "Juan Pérez"

    def test_normalize_name(self):
        """Verifica normalización de nombres."""
        assert PersonMSService._normalize_name("  Juan  ") == "juan"
        assert PersonMSService._normalize_name("José") == "jose"
        assert PersonMSService._normalize_name("María") == "maria"
        assert PersonMSService._normalize_name(None) == ""
        assert PersonMSService._normalize_name("") == ""

    def test_is_duplicate_message(self):
        """Verifica detección de mensaje de duplicado."""
        assert PersonMSService._is_duplicate_message(
            "La persona ya esta registrada con esa identificacion"
        )
        assert PersonMSService._is_duplicate_message("already exists")
        assert PersonMSService._is_duplicate_message("duplicado")
        assert not PersonMSService._is_duplicate_message("otro error")

    def test_is_duplicate_error(self):
        """Verifica detección de error de duplicado."""
        exc = ValidationException(
            "La persona ya esta registrada con esa identificacion"
        )
        assert PersonMSService._is_duplicate_error(exc)

        exc2 = ValidationException("Otro error")
        assert not PersonMSService._is_duplicate_error(exc2)


class TestValidateSameIdentity:
    """Tests para _validate_same_identity."""

    @pytest.fixture
    def service(self):
        """Servicio de test."""
        return PersonMSService()

    @pytest.fixture
    def sample_data(self):
        """Datos de ejemplo."""
        return CreatePersonInMSRequest(
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
            type_identification="CEDULA",
            type_stament="EXTERNOS",
        )

    def test_validate_same_identity_match(self, service, sample_data):
        """Verifica validación exitosa con misma identidad."""
        existing = {"data": {"first_name": "Juan", "last_name": "Pérez"}}
        # No debe lanzar excepción
        service._validate_same_identity(existing, sample_data)

    def test_validate_same_identity_no_match(self, service, sample_data):
        """Verifica fallo con identidad diferente."""
        existing = {"data": {"first_name": "Pedro", "last_name": "García"}}

        with pytest.raises(ValidationException) as exc_info:
            service._validate_same_identity(existing, sample_data)

        assert "no coinciden" in str(exc_info.value.message)

    def test_validate_same_identity_no_names(self, service, sample_data):
        """Verifica fallo cuando no hay nombres en respuesta."""
        existing = {"data": {}}

        with pytest.raises(ValidationException) as exc_info:
            service._validate_same_identity(existing, sample_data)

        assert "no se pudieron obtener los nombres" in str(exc_info.value.message)

    def test_validate_same_identity_with_full_name(self, service, sample_data):
        """Verifica validación con full_name."""
        existing = {"data": {"full_name": "Juan Pérez"}}
        # No debe lanzar excepción
        service._validate_same_identity(existing, sample_data)


class TestHandleCreateResponse:
    """Tests para _handle_create_response."""

    @pytest.fixture
    def service(self):
        """Servicio con cliente mock."""
        mock_client = MagicMock()
        return PersonMSService(person_client=mock_client)

    @pytest.fixture
    def sample_data(self):
        """Datos de ejemplo."""
        return CreatePersonInMSRequest(
            first_name="Juan",
            last_name="Pérez",
            dni="1234567890",
            type_identification="CEDULA",
            type_stament="EXTERNOS",
        )

    @pytest.mark.asyncio
    async def test_handle_create_response_success_with_external(
        self, service, sample_data
    ):
        """Verifica respuesta exitosa con external."""
        response = {"status": "success", "data": {"external": "ext-123"}}

        result = await service._handle_create_response(response, sample_data)
        assert result == "ext-123"

    @pytest.mark.asyncio
    async def test_handle_create_response_success_no_external(
        self, service, sample_data
    ):
        """Verifica respuesta exitosa sin external (busca por DNI)."""
        response = {"status": "success", "data": {}}
        service.person_client.get_by_identification = AsyncMock(
            return_value={"data": {"external": "ext-from-dni"}}
        )

        result = await service._handle_create_response(response, sample_data)
        assert result == "ext-from-dni"

    @pytest.mark.asyncio
    async def test_handle_create_response_duplicate(self, service, sample_data):
        """Verifica respuesta de duplicado."""
        response = {
            "status": "error",
            "message": "La persona ya esta registrada con esa identificacion",
        }
        service.person_client.get_by_identification = AsyncMock(
            return_value={
                "data": {
                    "external": "existing-ext",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                }
            }
        )

        result = await service._handle_create_response(response, sample_data)
        assert result == "existing-ext"

    @pytest.mark.asyncio
    async def test_handle_create_response_error(self, service, sample_data):
        """Verifica respuesta de error."""
        response = {"status": "error", "message": "Error específico"}

        with pytest.raises(ValidationException) as exc_info:
            await service._handle_create_response(response, sample_data)

        assert "Error específico" in str(exc_info.value.message)
