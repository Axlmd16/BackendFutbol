import asyncio
from datetime import datetime, timedelta
import secrets
from typing import Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from jose import jwt
from sqlalchemy.orm import Session

from app.client.person_auth import PersonAuthService
from app.controllers.account_controller import AccountController
from app.core.config import settings
from app.core.database import get_db
from app.schemas.account_schema import (
	AccountResponse,
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
reset_tokens_store: Dict[str, Dict[str, str | datetime]] = {}
person_auth_service = PersonAuthService()


def _create_access_token(subject: str, *, role: str) -> str:
	"""Crea un token de acceso JWT."""
	expire = datetime.utcnow() + timedelta(seconds=settings.TOKEN_EXPIRES)
	payload = {
		"sub": subject,
		"role": role,
		"exp": expire,
		"iat": datetime.utcnow(),
	}
	return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _purge_reset_tokens() -> None:
	"""Purgar tokens de restablecimiento expirados."""
	now = datetime.utcnow()
	expired = [token for token, data in reset_tokens_store.items() if data["expires_at"] < now]
	for token in expired:
		reset_tokens_store.pop(token, None)


def _role_value(role_obj) -> str:
	"""Obtiene el valor de rol como cadena."""
	return role_obj.value if hasattr(role_obj, "value") else str(role_obj)


def _handle_app_exception(exc: AppException) -> None:
	"""Maneja excepciones de la aplicación."""
	raise HTTPException(status_code=exc.status_code, detail=exc.message)



@router.post("/login", response_model=ResponseSchema)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
	"""Endpoint para login de usuario."""
	print("Login endpoint called with:", payload.email)
	try:
		resp = httpx.post(
			f"{settings.PERSON_MS_BASE_URL}/api/person/login",
			json={
				"email": payload.email,
				"password": payload.password.get_secret_value(),
			},
			timeout=10.0,
		)
		resp.raise_for_status()
		body = resp.json()
		external = body["data"]["external"]
		ms_token = body["data"]["token"]
	except httpx.HTTPStatusError:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
	except Exception:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al comunicarse con el servicio de personas")

	account = account_controller.get_by_external(db, external)
	if not account:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no enlazada")

	role = _role_value(account.role)
	access_token = _create_access_token(subject=str(account.id), role=role)
	login_response = LoginResponse(
		access_token=access_token,
		refresh_token=None,
		role=role,
	)
	return ResponseSchema(
		status="success",
		message="Login exitoso",
		data={
			**login_response.model_dump(),
			"external_account_id": external,
			"person_ms_token": ms_token,
		},
	)


@router.post("/forgot-password", response_model=ResponseSchema)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
	"""Solicitud para iniciar proceso de recuperación de contraseña"""
	account = account_controller.get_account(db, payload.account_id)
	if not account:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

	_purge_reset_tokens()
	token = secrets.token_urlsafe(32)
	reset_tokens_store[token] = {
		"external": account.external_account_id,
		"expires_at": datetime.utcnow() + timedelta(hours=1),
	}
	return ResponseSchema(
		status="success",
		message="Token de recuperación generado",
		data={"reset_token": token},
	)




