from typing import Callable, TypeVar

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.account_controller import AccountController
from app.core.database import get_db
from app.schemas.account_schema import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
)
from app.schemas.response import ResponseSchema
from app.utils.exceptions import AppException

router = APIRouter(prefix="/accounts", tags=["Accounts"])
account_controller = AccountController()

T = TypeVar("T")


def handle_exceptions(fn: Callable[[], T]) -> T:
    """Aplica manejo consistente de errores en endpoints."""

    try:
        return fn()
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:  # pragma: no cover - catch-all defensivo
        raise HTTPException(status_code=500, detail="Error inesperado") from exc


@router.post(
    "/login",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description="Valida credenciales y devuelve un token JWT.",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> ResponseSchema:  # noqa: B008 (FastAPI dependency injection)
    """Endpoint para iniciar sesión y obtener un token JWT."""
    return handle_exceptions(
        lambda: ResponseSchema(
            status="success",
            message="Inicio de sesión exitoso",
            data=account_controller.login(db, payload).model_dump(),
        )
    )


@router.post(
    "/password-reset/request",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Solicitar restablecimiento de contraseña",
    description="Genera un token de reset.",
)
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> ResponseSchema:
    """Genera un token de restablecimiento de contraseña y lo envía por correo."""
    return handle_exceptions(
        lambda: (
            account_controller.request_password_reset(db, payload),
            ResponseSchema(
                status="success",
                message="Si el correo existe, se ha enviado un enlace de restablecimiento",
                data=None,
            ),
        )[1]
    )


@router.post(
    "/password-reset/confirm",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Confirmar restablecimiento de contraseña",
    description="Valida el token de reset y actualiza la contraseña.",
)
def confirm_password_reset(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db),  # noqa: B008
) -> ResponseSchema:
    """Confirma el restablecimiento de contraseña usando el token proporcionado."""
    return handle_exceptions(
        lambda: (
            account_controller.confirm_password_reset(db, payload),
            ResponseSchema(
                status="success",
                message="Contraseña actualizada",
                data=None,
            ),
        )[1]
    )