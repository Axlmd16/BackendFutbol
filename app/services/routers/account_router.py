from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.account_controller import AccountController
from app.core.database import get_db
from app.schemas.account_schema import LoginRequest, LoginResponse
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