from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

# ================= DATABASE ENGINE =================
# Configuración optimizada para ALTA CONCURRENCIA
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=QueuePool,
    pool_size=50,
    max_overflow=100,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=60,
    connect_args={
        "client_encoding": "utf8",
        "connect_timeout": 10,
    },
)


# Optimización: configurar conexiones al crearlas
@event.listens_for(engine, "connect")
def set_connection_params(dbapi_conn, connection_record):
    """Configurar parámetros de conexión para mejor rendimiento."""
    cursor = dbapi_conn.cursor()
    cursor.execute("SET statement_timeout = '30s'")
    cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
