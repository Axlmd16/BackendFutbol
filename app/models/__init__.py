# Importar Base primero
from app.models.account import Account
from app.models.athlete import Athlete
from app.models.attendance import Attendance
from app.models.base import BaseModel
from app.models.endurance_test import EnduranceTest
from app.models.evaluation import Evaluation
from app.models.representative import Representative
from app.models.sprint_test import SprintTest
from app.models.statistic import Statistic
from app.models.technical_assessment import TechnicalAssessment
from app.models.test import Test
from app.models.user import User
from app.models.yoyo_test import YoyoTest

# Exportar todos los modelos
__all__ = [
    "BaseModel",
    "Athlete",
    "Evaluation",
    "Test",
    "Attendance",
    "Statistic",
    "SprintTest",
    "EnduranceTest",
    "YoyoTest",
    "TechnicalAssessment",
    "User",
    "Account",
    "Representative",
]
