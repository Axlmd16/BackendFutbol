from datetime import datetime, timedelta
import secrets
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.controllers.account_controller import AccountController
from app.core.config import settings
from app.core.database import get_db
from app.schemas.account_schema import (
	AccountCreate,
	AccountResponse,
	AccountUpdate,
	ForgotPasswordRequest,
	LoginRequest,
	LoginResponse,
	ResetPasswordRequest,
)
from app.schemas.response import ResponseSchema
from app.utils.exceptions import AppException


#Definición del router y controlador de cuentas
router = APIRouter(prefix="/accounts", tags=["Accounts"])
account_controller = AccountController()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
reset_tokens_store: Dict[str, Dict[str, str | datetime]] = {}

#Permite hashear una contraseña
def _hash_password(password: str) -> str:
	return pwd_context.hash(password)


#Permite verificar una contraseña contra su hash
def _verify_password(password: str, hashed: str) -> bool:
	return pwd_context.verify(password, hashed)

#Permite crear un token de acceso JWT
def _create_access_token(subject: str, *, role: str) -> str:
	expire = datetime.utcnow() + timedelta(seconds=settings.TOKEN_EXPIRES)
	payload = {
		"sub": subject,
		"role": role,
		"exp": expire,
		"iat": datetime.utcnow(),
	}
	return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

#Permite purgar tokens de restablecimiento expirados
def _purge_reset_tokens() -> None:
	now = datetime.utcnow()
	expired = [token for token, data in reset_tokens_store.items() if data["expires_at"] < now]
	for token in expired:
		reset_tokens_store.pop(token, None)

#Permite obtener el valor de rol como cadena
def _role_value(role_obj) -> str:
	return role_obj.value if hasattr(role_obj, "value") else str(role_obj)

#Manejo de excepciones personalizadas
def _handle_app_exception(exc: AppException) -> None:
	raise HTTPException(status_code=exc.status_code, detail=exc.message)

# Endpoint para listar cuentas de usuario
@router.get("/", response_model=ResponseSchema)
def list_accounts(
	skip: int = Query(0, ge=0),
	limit: int = Query(100, ge=1, le=500),
	only_active: bool = Query(True),
	db: Session = Depends(get_db),
):
	try:
		accounts = account_controller.list_accounts(
			db, skip=skip, limit=limit, only_active=only_active
		)
	except AppException as exc:
		_handle_app_exception(exc)

	items = [AccountResponse.model_validate(acc) for acc in accounts]
	return ResponseSchema(
		status="success",
		message="Cuentas listadas correctamente",
		data={
			"items": items,
			"count": len(items),
			"skip": skip,
			"limit": limit,
		},
	)

# Endpoint para obtener una cuenta por ID
@router.get("/{account_id}", response_model=ResponseSchema)
def get_account(account_id: int, db: Session = Depends(get_db)):
	try:
		account = account_controller.get_account(db, account_id)
	except AppException as exc:
		_handle_app_exception(exc)

	if not account:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

	return ResponseSchema(
		status="success",
		message="Cuenta obtenida correctamente",
		data=AccountResponse.model_validate(account),
	)

# Endpoint para crear una nueva cuenta de usuario
@router.post("/", response_model=ResponseSchema, status_code=status.HTTP_201_CREATED)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
	hashed_password = _hash_password(payload.password)
	dto = payload.model_copy(update={"password": hashed_password})
	try:
		account = account_controller.create_account(db, dto)
	except AppException as exc:
		_handle_app_exception(exc)

	return ResponseSchema(
		status="success",
		message="Cuenta creada correctamente",
		data=AccountResponse.model_validate(account),
	)

# Endpoint para actualizar una cuenta existente
@router.put("/{account_id}", response_model=ResponseSchema)
def update_account(
	account_id: int,
	payload: AccountUpdate,
	db: Session = Depends(get_db),
):
	update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
	if "password" in update_data and update_data["password"]:
		update_data["password"] = _hash_password(update_data["password"])
	if not update_data:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="No se proporcionaron campos para actualizar",
		)
	update_payload = AccountUpdate(**update_data)
	try:
		account = account_controller.update_account(
			db,
			account_id,
			update_payload,
		)
	except AppException as exc:
		_handle_app_exception(exc)

	if not account:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

	return ResponseSchema(
		status="success",
		message="Cuenta actualizada correctamente",
		data=AccountResponse.model_validate(account),
	)

# Endpoint para eliminar una cuenta de usuario
@router.delete("/{account_id}", response_model=ResponseSchema)
def delete_account(
	account_id: int,
	soft_delete: bool = Query(True),
	db: Session = Depends(get_db),
):
	try:
		deleted = account_controller.delete_account(
			db,
			account_id,
			soft_delete=soft_delete,
		)
	except AppException as exc:
		_handle_app_exception(exc)

	if not deleted:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

	action = "desactivada" if soft_delete else "eliminada"
	return ResponseSchema(
		status="success",
		message=f"Cuenta {action} correctamente",
		data={"id": account_id},
	)

# Endpoint para login de usuario
@router.post("/login", response_model=ResponseSchema)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
	account = account_controller.get_by_email(db, payload.email)
	if not account or not _verify_password(
		payload.password.get_secret_value(), account.password
	):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

	role = _role_value(account.role)
	access_token = _create_access_token(subject=str(account.id), role=role)
	login_response = LoginResponse(access_token=access_token, refresh_token=None, role=role)
	return ResponseSchema(
		status="success",
		message="Login exitoso",
		data=login_response.model_dump(),
	)

# Endpoint para iniciar proceso de recuperación de contraseña
@router.post("/forgot-password", response_model=ResponseSchema)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
	account = account_controller.get_by_email(db, payload.email)
	if not account:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

	_purge_reset_tokens()
	token = secrets.token_urlsafe(32)
	reset_tokens_store[token] = {
		"account_id": account.id,
		"expires_at": datetime.utcnow() + timedelta(hours=1),
	}
	return ResponseSchema(
		status="success",
		message="Token de recuperación generado",
		data={"reset_token": token},
	)

# Endpoint para restablecer la contraseña
@router.post("/reset-password", response_model=ResponseSchema)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
	try:
		payload.validate_passwords()
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

	_purge_reset_tokens()
	token_data = reset_tokens_store.get(payload.token)
	if not token_data:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido o expirado")

	if token_data["expires_at"] < datetime.utcnow():
		reset_tokens_store.pop(payload.token, None)
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expirado")

	hashed_password = _hash_password(payload.new_password.get_secret_value())
	account = account_controller.update_password(db, token_data["account_id"], hashed_password)
	if not account:
		reset_tokens_store.pop(payload.token, None)
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

	reset_tokens_store.pop(payload.token, None)
	return ResponseSchema(
		status="success",
		message="Contraseña restablecida correctamente",
		data={"id": account.id},
	)


