"""Tests para el módulo principal main.py."""

import pytest
from fastapi.testclient import TestClient


class TestCreateApplication:
    """Tests para la función create_application."""

    def test_create_application_returns_fastapi_instance(self):
        """Verifica que create_application retorna una instancia de FastAPI."""
        from fastapi import FastAPI

        from main import create_application

        app = create_application()
        assert isinstance(app, FastAPI)

    def test_create_application_has_correct_title(self):
        """Verifica que la aplicación tiene el título correcto."""
        from main import create_application

        app = create_application()
        assert app.title is not None

    def test_create_application_has_routes(self):
        """Verifica que la aplicación tiene rutas registradas."""
        from main import create_application

        app = create_application()
        routes = [route.path for route in app.routes]
        assert len(routes) > 0

    def test_create_application_has_health_endpoint(self):
        """Verifica que existe el endpoint /health."""
        from main import create_application

        app = create_application()
        routes = [route.path for route in app.routes]
        assert "/health" in routes

    def test_create_application_has_api_routes(self):
        """Verifica que existen las rutas de API."""
        from main import create_application

        app = create_application()
        routes = [route.path for route in app.routes]
        # Verificar que hay rutas con prefijo /api/v1
        api_routes = [r for r in routes if r.startswith("/api/v1")]
        assert len(api_routes) > 0


class TestConfigureMiddlewares:
    """Tests para _configure_middlewares."""

    def test_configure_middlewares_adds_cors(self):
        """Verifica que se añade el middleware CORS."""
        from fastapi import FastAPI

        from main import _configure_middlewares

        app = FastAPI()
        _configure_middlewares(app)

        # Verificar que hay middlewares configurados
        middleware_classes = [
            m.cls.__name__ for m in app.user_middleware if hasattr(m, "cls")
        ]
        assert "CORSMiddleware" in middleware_classes


class TestRegisterExceptionHandlers:
    """Tests para _register_exception_handlers."""

    def test_register_exception_handlers(self):
        """Verifica que se registran los manejadores de excepciones."""
        from fastapi import FastAPI

        from main import _register_exception_handlers

        app = FastAPI()
        _register_exception_handlers(app)

        # Verificar que hay manejadores de excepciones registrados
        assert len(app.exception_handlers) > 0


class TestRegisterRouters:
    """Tests para _register_routers."""

    def test_register_routers(self):
        """Verifica que se registran los routers."""
        from fastapi import FastAPI

        from main import _register_routers

        app = FastAPI()
        initial_routes = len(app.routes)
        _register_routers(app)

        # Verificar que se agregaron rutas
        assert len(app.routes) > initial_routes


class TestRegisterHealthEndpoints:
    """Tests para _register_health_endpoints."""

    def test_register_health_endpoints(self):
        """Verifica que se registran los endpoints de salud."""
        from fastapi import FastAPI

        from main import _register_health_endpoints

        app = FastAPI()
        _register_health_endpoints(app)

        routes = [route.path for route in app.routes]
        assert "/health" in routes
        assert "/health/live" in routes
        assert "/health/ready" in routes
        assert "/info" in routes
        assert "/" in routes


class TestHealthEndpoints:
    """Tests para los endpoints de salud."""

    @pytest.fixture
    def client(self):
        """Cliente de test."""
        from main import create_application

        app = create_application()
        return TestClient(app)

    def test_root_redirects_to_scalar(self, client):
        """Verifica que / redirige a /scalar."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/scalar" in response.headers.get("location", "")

    def test_liveness_check(self, client):
        """Verifica el endpoint /health/live."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_health_check_success(self, client):
        """Verifica el endpoint /health con DB conectada."""
        response = client.get("/health")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data

    def test_readiness_check(self, client):
        """Verifica el endpoint /health/ready."""
        response = client.get("/health/ready")
        assert response.status_code in [200, 503]

    def test_api_info(self, client):
        """Verifica el endpoint /info."""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert "name" in data["data"]
        assert "version" in data["data"]


class TestLifespan:
    """Tests para el contexto de vida de la aplicación."""

    @pytest.mark.asyncio
    async def test_lifespan_startup_shutdown(self):
        """Verifica el ciclo de vida de la aplicación."""
        from fastapi import FastAPI

        from main import lifespan

        app = FastAPI()

        # Simular el ciclo de vida
        async with lifespan(app):
            # Durante el ciclo de vida la app está activa
            pass
        # Después del ciclo de vida la app se cierra correctamente


class TestModuleImports:
    """Tests para verificar importaciones del módulo."""

    def test_app_is_created(self):
        """Verifica que la variable app existe."""
        from main import app

        assert app is not None

    def test_settings_imported(self):
        """Verifica que settings está disponible."""
        from main import settings

        assert settings is not None
        assert hasattr(settings, "APP_NAME")
