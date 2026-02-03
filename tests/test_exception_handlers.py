"""Tests para los manejadores de excepciones."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import DatabaseError, InterfaceError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exception_handlers import (
    UNEXPECTED_ERROR_MSG,
    _build_error_map,
    _service_error_response,
    _translate_message,
    app_exception_handler,
    custom_database_exception_handler,
    database_error_handler,
    database_interface_error_handler,
    database_operational_error_handler,
    email_service_exception_handler,
    external_service_exception_handler,
    global_exception_handler,
    http_exception_handler_wrapped,
    validation_exception_handler,
)
from app.schemas.constants import SERVICE_PROBLEMS_MSG
from app.utils.exceptions import (
    AppException,
    DatabaseException,
    EmailServiceException,
    ExternalServiceException,
)


class TestTranslateMessage:
    """Tests para _translate_message."""

    def test_translate_known_message(self):
        """Verifica traducción de mensaje conocido."""
        result = _translate_message("Field required")
        assert result == "Este campo es obligatorio"

    def test_translate_message_with_prefix(self):
        """Verifica remoción de prefijos."""
        result = _translate_message("Value error, Field required")
        assert result == "Este campo es obligatorio"

    def test_translate_partial_match(self):
        """Verifica match parcial de mensajes."""
        result = _translate_message("ensure this value has at least 5 characters")
        assert result == "Este campo debe tener al menos"

    def test_translate_unknown_message(self):
        """Verifica que mensaje desconocido se retorna sin cambios."""
        result = _translate_message("Unknown error message")
        assert result == "Unknown error message"

    def test_translate_integer_message(self):
        """Verifica traducción de mensaje de entero."""
        result = _translate_message("Input should be a valid integer")
        assert result == "El valor debe ser un número entero"


class TestBuildErrorMap:
    """Tests para _build_error_map."""

    def test_build_error_map_single_field(self):
        """Verifica construcción con un campo."""
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [{"loc": ("body", "email"), "msg": "Field required"}]

        error_map, first_msg = _build_error_map(exc)

        assert "email" in error_map
        assert error_map["email"] == ["Este campo es obligatorio"]
        assert first_msg is None

    def test_build_error_map_multiple_fields(self):
        """Verifica construcción con múltiples campos."""
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "email"), "msg": "Field required"},
            {"loc": ("body", "name"), "msg": "Field required"},
        ]

        error_map, _ = _build_error_map(exc)

        assert "email" in error_map
        assert "name" in error_map

    def test_build_error_map_root_error(self):
        """Verifica construcción con error en raíz."""
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [{"loc": ("body",), "msg": "Invalid data"}]

        error_map, first_msg = _build_error_map(exc)

        assert "__root__" in error_map
        assert first_msg == "Invalid data"

    def test_build_error_map_empty_location(self):
        """Verifica construcción con ubicación vacía."""
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [{"loc": (), "msg": "Error message"}]

        error_map, first_msg = _build_error_map(exc)

        assert "__root__" in error_map
        assert first_msg == "Error message"

    def test_build_error_map_nested_location(self):
        """Verifica construcción con ubicación anidada."""
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "user", "email"), "msg": "Field required"}
        ]

        error_map, _ = _build_error_map(exc)

        assert "user.email" in error_map


class TestServiceErrorResponse:
    """Tests para _service_error_response."""

    def test_default_message(self):
        """Verifica respuesta con mensaje por defecto."""
        response = _service_error_response()

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        content = response.body.decode()
        assert SERVICE_PROBLEMS_MSG in content

    def test_custom_message(self):
        """Verifica respuesta con mensaje personalizado."""
        custom_msg = "Servicio no disponible"
        response = _service_error_response(message=custom_msg)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        content = response.body.decode()
        assert custom_msg in content


class TestValidationExceptionHandler:
    """Tests para validation_exception_handler."""

    @pytest.fixture
    def mock_request(self):
        """Request mock."""
        return MagicMock(spec=Request)

    def test_handler_with_field_error(self, mock_request):
        """Verifica manejo de error de campo."""
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [{"loc": ("body", "email"), "msg": "Field required"}]

        response = validation_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_handler_with_root_error(self, mock_request):
        """Verifica manejo de error raíz."""
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [{"loc": ("body",), "msg": "Custom validation error"}]

        response = validation_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAppExceptionHandler:
    """Tests para app_exception_handler."""

    @pytest.fixture
    def mock_request(self):
        """Request mock."""
        return MagicMock(spec=Request)

    def test_handler_with_422_status(self, mock_request):
        """Verifica manejo con status 422."""
        exc = AppException(status_code=422, message="Validation error")

        response = app_exception_handler(mock_request, exc)

        assert response.status_code == 422
        content = response.body.decode()
        assert "Validation error" in content
        assert "__root__" in content  # errors debe tener __root__

    def test_handler_with_other_status(self, mock_request):
        """Verifica manejo con otro status."""
        exc = AppException(status_code=400, message="Bad request")

        response = app_exception_handler(mock_request, exc)

        assert response.status_code == 400
        content = response.body.decode()
        assert "Bad request" in content


class TestHttpExceptionHandlerWrapped:
    """Tests para http_exception_handler_wrapped."""

    @pytest.fixture
    def mock_request(self):
        """Request mock."""
        request = MagicMock(spec=Request)
        request.app = MagicMock()
        request.state = MagicMock()
        return request

    @pytest.mark.asyncio
    async def test_handler_with_string_detail(self, mock_request):
        """Verifica manejo con detalle string."""
        exc = StarletteHTTPException(status_code=404, detail="Not found")

        response = await http_exception_handler_wrapped(mock_request, exc)

        assert response.status_code == 404
        content = response.body.decode()
        assert "Not found" in content

    @pytest.mark.asyncio
    async def test_handler_with_empty_detail(self, mock_request):
        """Verifica manejo con detalle vacío."""
        exc = StarletteHTTPException(status_code=404, detail=None)

        response = await http_exception_handler_wrapped(mock_request, exc)

        assert response.status_code == 404
        content = response.body.decode()
        # El mensaje por defecto es "Not Found" cuando detail es None
        assert "error" in content

    @pytest.mark.asyncio
    async def test_handler_with_dict_detail(self, mock_request):
        """Verifica manejo con detalle diccionario."""
        exc = StarletteHTTPException(
            status_code=400, detail={"message": "Error details"}
        )

        with patch(
            "app.core.exception_handlers.http_exception_handler", new_callable=AsyncMock
        ) as mock_handler:
            mock_handler.return_value = MagicMock(status_code=400)
            await http_exception_handler_wrapped(mock_request, exc)
            mock_handler.assert_called_once()


class TestDatabaseExceptionHandlers:
    """Tests para manejadores de excepciones de base de datos."""

    @pytest.fixture
    def mock_request(self):
        """Request mock."""
        return MagicMock(spec=Request)

    def test_operational_error_handler(self, mock_request):
        """Verifica manejo de OperationalError."""
        exc = OperationalError("statement", {}, Exception("connection error"))

        with patch("app.core.exception_handlers.logger"):
            response = database_operational_error_handler(mock_request, exc)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_interface_error_handler(self, mock_request):
        """Verifica manejo de InterfaceError."""
        exc = InterfaceError("statement", {}, Exception("interface error"))

        with patch("app.core.exception_handlers.logger"):
            response = database_interface_error_handler(mock_request, exc)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_database_error_handler(self, mock_request):
        """Verifica manejo de DatabaseError."""
        exc = DatabaseError("statement", {}, Exception("db error"))

        with patch("app.core.exception_handlers.logger"):
            response = database_error_handler(mock_request, exc)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_custom_database_exception_handler(self, mock_request):
        """Verifica manejo de DatabaseException personalizada."""
        exc = DatabaseException("Custom DB error")

        with patch("app.core.exception_handlers.logger"):
            response = custom_database_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestEmailServiceExceptionHandler:
    """Tests para email_service_exception_handler."""

    @pytest.fixture
    def mock_request(self):
        """Request mock."""
        return MagicMock(spec=Request)

    def test_handler(self, mock_request):
        """Verifica manejo de EmailServiceException."""
        exc = EmailServiceException("Email send failed")

        with patch("app.core.exception_handlers.logger"):
            response = email_service_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        content = response.body.decode()
        assert "Email send failed" in content


class TestExternalServiceExceptionHandler:
    """Tests para external_service_exception_handler."""

    @pytest.fixture
    def mock_request(self):
        """Request mock."""
        return MagicMock(spec=Request)

    def test_handler(self, mock_request):
        """Verifica manejo de ExternalServiceException."""
        exc = ExternalServiceException("External API failed")

        with patch("app.core.exception_handlers.logger"):
            response = external_service_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        content = response.body.decode()
        assert "External API failed" in content


class TestGlobalExceptionHandler:
    """Tests para global_exception_handler."""

    @pytest.fixture
    def mock_request(self):
        """Request mock."""
        return MagicMock(spec=Request)

    def test_handler(self, mock_request):
        """Verifica manejo de excepción global."""
        exc = Exception("Unexpected error")

        with patch("app.core.exception_handlers.logger"):
            response = global_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        content = response.body.decode()
        assert UNEXPECTED_ERROR_MSG in content

    def test_handler_with_different_exception_types(self, mock_request):
        """Verifica manejo de diferentes tipos de excepción."""
        exceptions = [
            ValueError("value error"),
            TypeError("type error"),
            RuntimeError("runtime error"),
        ]

        for exc in exceptions:
            with patch("app.core.exception_handlers.logger"):
                response = global_exception_handler(mock_request, exc)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
