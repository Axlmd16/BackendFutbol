# Importar Base primero
from app.models.base import BaseModel
from app.models.athlete import Athlete
from app.models.evaluator import Evaluator
from app.models.evaluation import Evaluation
from app.models.test import Test
from app.models.attendance import Attendance
from app.models.statistic import Statistic
from app.models.sprint_test import SprintTest
from app.models.endurance_test import EnduranceTest
from app.models.yoyo_test import YoyoTest
from app.models.technical_assessment import TechnicalAssessment

# Exportar todos los modelos
__all__ = [
    "BaseModel",
    "Athlete",
    "Evaluator",
    "Evaluation",
    "Test",
    "Attendance",
    "Statistic",
    "SprintTest",
    "EnduranceTest",
    "YoyoTest",
    "TechnicalAssessment",
]
