from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
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


@router.post(
    "/login",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description="Valida credenciales y devuelve un token JWT.",
)
def login(
    payload: LoginRequest, db: Annotated[Session, Depends(get_db)]
) -> ResponseSchema:
    """Endpoint para iniciar sesión y obtener un token JWT."""
    try:
        result = account_controller.login(db, payload)
        return ResponseSchema(
            status="success",
            message="Inicio de sesión exitoso",
            data=result.model_dump(),
        )
    except AppException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=ResponseSchema(
                status="error",
                message=exc.message,
                data=None,
                errors=None,
            ).model_dump(),
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ResponseSchema(
                status="error",
                message=f"Error inesperado: {str(e)}",
                data=None,
                errors=None,
            ).model_dump(),
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
    db: Annotated[Session, Depends(get_db)],
) -> ResponseSchema:
    """Genera un token de restablecimiento de contraseña y lo envía por correo."""
    try:
        account_controller.request_password_reset(db, payload)
        return ResponseSchema(
            status="success",
            message="Si el correo existe, se ha enviado un enlace de restablecimiento",
            data=None,
        )
    except AppException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=ResponseSchema(
                status="error",
                message=exc.message,
                data=None,
                errors=None,
            ).model_dump(),
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ResponseSchema(
                status="error",
                message=f"Error inesperado: {str(e)}",
                data=None,
                errors=None,
            ).model_dump(),
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
    db: Annotated[Session, Depends(get_db)],
) -> ResponseSchema:
    """Confirma el restablecimiento de contraseña usando el token proporcionado."""
    try:
        account_controller.confirm_password_reset(db, payload)
        return ResponseSchema(
            status="success",
            message="Contraseña actualizada",
            data=None,
        )
    except AppException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content=ResponseSchema(
                status="error",
                message=exc.message,
                data=None,
                errors=None,
            ).model_dump(),
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ResponseSchema(
                status="error",
                message=f"Error inesperado: {str(e)}",
                data=None,
                errors=None,
            ).model_dump(),
        )
