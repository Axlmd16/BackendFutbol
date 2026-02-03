"""Script para inicializar la base de datos de testing en CI."""

import logging
import sys
from pathlib import Path

# Agregar la raíz del proyecto al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.core.database import Base, engine  # noqa: E402
from app.models import *  # noqa: F401, F403, E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_test_database():
    """Crea todas las tablas en la base de datos."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info(" Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f" Error creating tables: {e}")
        return False


if __name__ == "__main__":
    success = init_test_database()
    exit(0 if success else 1)
