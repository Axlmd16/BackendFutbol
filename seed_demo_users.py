"""Seed de usuarios demo (roles) para BackendFutbol.

Crea 3 usuarios locales con diferentes roles:
- Administrator
- Coach
- Intern

Uso:
  - Desde la raíz de BackendFutbol (donde está este archivo):
    python seed_demo_users.py

Requisitos:
  - Tener configurado el archivo .env (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, JWT_SECRET, etc.)
  - Tener la base de datos y tablas creadas/migradas.

Nota:
  - Es idempotente: si el email o DNI ya existen, no crea duplicados.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.controllers.user_controller import UserController
from app.core.database import SessionLocal
from app.models.enums.rol import Role
from app.schemas.user_schema import CreateLocalUserAccountRequest
from app.utils.exceptions import (
    AlreadyExistsException,
    DatabaseException,
    ValidationException,
)


@dataclass(frozen=True)
class DemoUser:
    full_name: str
    email: str
    password: str
    role: Role
    dni_seed: int


def _compute_check_digit(first9: str) -> int:
    coef = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0
    for i in range(9):
        prod = int(first9[i]) * coef[i]
        total += prod if prod < 10 else prod - 9
    return (10 - (total % 10)) % 10


def generate_valid_ec_dni(*, province: int, third_digit: int, serial: int) -> str:
    """Genera un DNI ecuatoriano válido (10 dígitos) compatible con validate_ec_dni."""

    if not (1 <= province <= 24 or province == 30):
        raise ValueError("Provincia inválida")
    if not (0 <= third_digit <= 5):
        raise ValueError("Tercer dígito inválido")

    province_str = f"{province:02d}"
    serial_str = f"{serial:06d}"[-6:]
    first9 = f"{province_str}{third_digit}{serial_str}"  # 2 + 1 + 6 = 9
    check = _compute_check_digit(first9)
    return f"{first9}{check}"


def seed_users(db: Session, users: Iterable[DemoUser]) -> None:
    controller = UserController()

    for u in users:
        # DNI válido y determinístico por seed
        dni = generate_valid_ec_dni(province=1, third_digit=1, serial=u.dni_seed)

        try:
            controller.create_local_user_account(
                db,
                CreateLocalUserAccountRequest(
                    full_name=u.full_name,
                    dni=dni,
                    email=u.email,
                    password=u.password,
                    role=u.role,
                ),
            )
            db.commit()
            print(
                f"[OK] Creado: {u.email} | pass={u.password} | role={u.role.value} | dni={dni}"
            )
        except AlreadyExistsException as e:
            db.rollback()
            print(f"[SKIP] {u.email} ({u.role.value}) ya existe: {e}")
        except (ValidationException, DatabaseException) as e:
            db.rollback()
            print(f"[ERROR] No se pudo crear {u.email}: {e}")
            raise
        except SQLAlchemyError as e:
            db.rollback()
            print(f"[ERROR] Error de base de datos al crear {u.email}: {e}")
            raise
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Error inesperado al crear {u.email}: {e}")
            raise


def main() -> int:
    demo_password = "Pass12345!"

    demo_users = [
        DemoUser(
            full_name="Admin Demo",
            email="admin.kallpa@example.com",
            password=demo_password,
            role=Role.ADMINISTRATOR,
            dni_seed=12345,
        ),
        DemoUser(
            full_name="Entrenador Demo",
            email="coach.kallpa@example.com",
            password=demo_password,
            role=Role.COACH,
            dni_seed=23456,
        ),
        DemoUser(
            full_name="Pasante Demo",
            email="pasante.kallpa@example.com",
            password=demo_password,
            role=Role.INTERN,
            dni_seed=34567,
        ),
    ]

    try:
        db = SessionLocal()
    except Exception as e:
        print(
            "[ERROR] No se pudo abrir conexión a DB. Verifica tu .env y Postgres.\n"
            f"Detalle: {e}"
        )
        return 1

    try:
        seed_users(db, demo_users)
    except Exception as e:
        print(
            "[ERROR] El seed falló. Verifica que: \n"
            "- La DB esté levantada y accesible\n"
            "- Las tablas users/accounts existan (migraciones)\n"
            f"Detalle: {e}"
        )
        return 1
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
