from app.dao.athlete_dao import AthleteDAO
from app.dao.representative_dao import RepresentativeDAO
from app.schemas.athlete_schema import MinorAthleteCreateSchema, MinorAthleteResponseSchema
from app.utils.exceptions import AlreadyExistsException, ValidationException, DatabaseException
from app.utils.person_creator import create_person_only_in_ms
from sqlalchemy.orm import Session
from datetime import date
import logging

logger = logging.getLogger(__name__)


class AthleteController:
    """Controlador de deportistas."""

    def __init__(self):
        self.athlete_dao = AthleteDAO()
