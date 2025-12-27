from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.controllers.athlete_controller import AthleteController
from app.core.database import get_db
from app.schemas.athlete_schema import (
    AthleteInscriptionDTO,
    AthleteInscriptionResponseDTO,
)
from app.schemas.response import ResponseSchema
from app.utils.exceptions import AppException

router = APIRouter(prefix="/athletes", tags=["Athletes"])
athlete_controller = AthleteController()


@router.post(
    "/register-unl",
    response_model=ResponseSchema[AthleteInscriptionResponseDTO],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar deportista UNL",
    description="Inscribe un nuevo deportista de la Universidad Nacional de Loja",
)
async def register_athlete_unl(
    payload: AthleteInscriptionDTO,
    db: Annotated[Session, Depends(get_db)],
) -> ResponseSchema[AthleteInscriptionResponseDTO]:
    """Registra un deportista de la UNL en el sistema."""
    try:
        result = await athlete_controller.register_athlete_unl(db=db, data=payload)
        return ResponseSchema(
            status="success",
            message="Deportista registrado exitosamente",
            data=result,
        )
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500, detail=f"Error inesperado: {str(exc)}"
        ) from exc
