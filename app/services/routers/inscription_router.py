"""Router para inscripción de deportistas UNL."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.controllers.athlete_controller import AthleteController
from app.core.database import get_db
from app.schemas.athlete_schema import AthleteInscriptionDTO
from app.schemas.response import ResponseSchema
from app.utils.exceptions import (
    AlreadyExistsException,
    AppException,
    DatabaseException,
    ValidationException,
)

router = APIRouter(prefix="/inscription", tags=["Inscription"])
athlete_controller = AthleteController()


@router.post(
    "/deportista",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar deportista UNL",
)
def register_athlete(
    inscription_data: AthleteInscriptionDTO,
    db: Session = Depends(get_db),  # noqa: B008 (FastAPI dependency pattern)
):
    try:
        result = athlete_controller.register_athlete_unl(db, inscription_data)
        return ResponseSchema(
            status="success",
            message="Deportista registrado exitosamente",
            data={
                "athlete_id": result.athlete_id,
                "statistic_id": result.statistic_id,
                "first_name": result.first_name,
                "last_name": result.last_name,
                "institutional_email": result.institutional_email,
            },
        )
    except ValidationException as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": exc.message, "data": None},
        )
    except AlreadyExistsException as exc:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"status": "error", "message": exc.message, "data": None},
        )
    except DatabaseException as exc:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": exc.message, "data": None},
        )
    except AppException as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": exc.message, "data": None},
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Error al procesar la inscripción. Intente más tarde.",
                "data": None,
            },
        )
