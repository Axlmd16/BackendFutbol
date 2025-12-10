from fastapi import APIRouter, Depends, Header, HTTPException, status
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
	summary="Crear usuario (admin root)",
	description="Crea un usuario administrador o entrenador."
)
def admin_create_user(
	payload: AdminCreateUserRequest,
	db: Session = Depends(get_db),
	requester_account_id: int = Header(..., alias="X-Admin-Account-Id"),
):
	"""Solo el administrador raíz puede crear nuevos usuarios administradores o entrenadores."""
	try:
		result = user_controller.admin_create_user(
			db=db,
			requester_account_id=requester_account_id,
			payload=payload,
		)
		return ResponseSchema(
			status="success",
			message="Usuario creado correctamente",
			data=result.model_dump(),
		)
	except AppException as exc:
		raise HTTPException(status_code=exc.status_code, detail=exc.message)
