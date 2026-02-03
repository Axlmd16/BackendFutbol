"""
Pruebas de integración para la conexión a la base de datos PostgreSQL.

Verifica:
- Conexión exitosa a la base de datos
- Ciclo de vida de sesiones
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.database import SessionLocal, engine, get_db


class TestDatabaseConnection:
    """Pruebas esenciales de conexión a PostgreSQL."""

    def test_database_connection_success(self):
        """Verifica que se puede establecer conexión con PostgreSQL."""
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1 AS test_value"))
                row = result.fetchone()

                assert row is not None, "La consulta no retornó resultados"
                assert row[0] == 1

        except OperationalError as e:
            pytest.fail(f"No se pudo conectar a PostgreSQL: {e}")

    def test_database_version_is_postgresql(self):
        """Verifica que estamos conectados a PostgreSQL."""
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            assert "PostgreSQL" in version

    def test_session_lifecycle(self):
        """Verifica que las sesiones se crean y cierran correctamente."""
        session = SessionLocal()
        try:
            result = session.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        finally:
            session.close()

    def test_get_db_dependency(self):
        """Verifica que get_db() devuelve una sesión válida."""
        db_generator = get_db()
        db = next(db_generator)

        try:
            result = db.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        finally:
            try:
                next(db_generator)
            except StopIteration:
                pass

    def test_database_url_configuration(self):
        """Verifica que la URL de la base de datos está configurada."""
        db_url = settings.DATABASE_URL
        assert db_url.startswith("postgresql://")
        assert settings.DB_HOST in db_url
        assert settings.DB_NAME in db_url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
