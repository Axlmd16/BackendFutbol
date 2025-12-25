from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.account_controller import AccountController
from app.core.database import get_db
from app.schemas.account_schema import (
    LoginRequest,
    LoginResponse,
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
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> ResponseSchema:  # noqa: B008 (FastAPI dependency injection)
    """Endpoint para iniciar sesión y obtener un token JWT."""
    try:
        token_data: LoginResponse = account_controller.login(db, payload)
        return ResponseSchema(
            status="success",
            message="Inicio de sesión exitoso",
            data=token_data.model_dump(),
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:  # pragma: no cover - catch-all defensivo
        raise HTTPException(status_code=500, detail="Error inesperado") from exc


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
    """Genera un token de restablecimiento de contraseña."""
    try:
        reset_token = account_controller.request_password_reset(db, payload)
        # En desarrollo devolvemos el token para que puedas usarlo sin SMTP
        return ResponseSchema(
            status="success",
            message="Si el correo existe, se generó un token de reset",
            data={"reset_token": reset_token},
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:  # pragma: no cover - catch-all defensivo
        raise HTTPException(status_code=500, detail="Error inesperado") from exc


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
    try:
        account_controller.confirm_password_reset(db, payload)
        return ResponseSchema(
            status="success",
            message="Contraseña actualizada",
            data=None,
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:  # pragma: no cover - catch-all defensivo
        raise HTTPException(status_code=500, detail="Error inesperado") from exc