from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.user_controller import UserController
from app.core.database import get_db
from app.schemas.response import ResponseSchema
from app.schemas.user_schema import AdminCreateUserRequest
from app.utils.exceptions import AppException

router = APIRouter(prefix="/users", tags=["Users"])
user_controller = UserController()

@router.post(
    "/admin-create",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario administrador/entrenador",
    description="Crea un usuario administrador o entrenador en el club y en el sistema institucional."
)
async def admin_create_user(
    payload: AdminCreateUserRequest,
    db: Session = Depends(get_db),
    # TODO: agregar dependencia de autenticación
    # current_account_id: int = Depends(get_current_admin_account_id),
):
    """Solo el administrador puede crear nuevos usuarios administradores o entrenadores."""
    try:
        result = await user_controller.admin_create_user(
            db=db,
            payload=payload,
            # requester_account_id=current_account_id,  # descomentar cuando tengas auth
        )
        return ResponseSchema(
            status="success",
            message="Usuario creado correctamente en el club y en el sistema institucional",
            data=result.model_dump(),
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
