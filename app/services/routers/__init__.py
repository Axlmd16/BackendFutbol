from app.services.routers.athlete_router import router as athlete_router
from app.services.routers.attendance_router import router as attendance_router
from app.services.routers.evaluator_router import router as evaluator_router
from app.services.routers.evaluation_router import router as evaluation_router
from app.services.routers.test_router import router as test_router
from app.services.routers.statistic_router import router as statistic_router
from app.services.routers.sprint_test_router import router as sprint_test_router
from app.services.routers.endurance_test_router import router as endurance_test_router
from app.services.routers.yoyo_test_router import router as yoyo_test_router
from app.services.routers.technical_assessment_router import router as technical_assessment_router
from app.services.routers.inscription_router import router as inscription_router

__all__ = [
	"athlete_router",
	"attendance_router",
	"evaluator_router",
	"evaluation_router",
	"test_router",
	"statistic_router",
	"sprint_test_router",
	"endurance_test_router",
	"yoyo_test_router",
	"technical_assessment_router",
]