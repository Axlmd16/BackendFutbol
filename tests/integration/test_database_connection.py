"""
Pruebas de integración para la conexión a la base de datos PostgreSQL.

Estas pruebas verifican la conexión exitosa a la base de datos.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.database import engine


class TestDatabaseConnection:
    """Pruebas para verificar la conexión a PostgreSQL."""

    def test_database_url_format(self):
        """Verifica que la URL de la base de datos tenga el formato correcto."""
        db_url = settings.DATABASE_URL

        # Verificar que sea una URL de PostgreSQL
        assert db_url.startswith("postgresql://"), (
            f"La URL debe empezar con 'postgresql://'. URL: {db_url[:30]}..."
        )

        # Verificar componentes de la URL
        assert settings.DB_HOST in db_url
        assert str(settings.DB_PORT) in db_url
        assert settings.DB_NAME in db_url

    def test_database_connection_success(self):
        """Verifica que se puede establecer conexión con PostgreSQL."""
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1 AS test_value"))
                row = result.fetchone()

                assert row is not None, "La consulta no retornó resultados"
                assert row[0] == 1, f"El valor esperado es 1, obtenido: {row[0]}"

        except OperationalError as e:
            pytest.fail(
                f"No se pudo conectar a PostgreSQL. "
                f"Verifica que el servidor esté corriendo. Error: {e}"
            )

    def test_database_version(self):
        """Verifica la versión de PostgreSQL."""
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]

            assert "PostgreSQL" in version, (
                f"Se esperaba PostgreSQL, pero se conectó a: {version}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
