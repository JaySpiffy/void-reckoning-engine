from .status import router as status_router
from .metrics import router as metrics_router
from .economic import router as economic_router
from .military import router as military_router
from .industrial import router as industrial_router
from .galaxy import router as galaxy_router
from .alerts import router as alerts_router
from .export import router as export_router
from .performance import router as performance_router
from .diagnostics import router as diagnostics_router
from .analytics import router as analytics_router
from .research import router as research_router
from .control import router as control_router
from .runs import router as runs_router

__all__ = [
    "status_router",
    "metrics_router",
    "economic_router",
    "military_router",
    "industrial_router",
    "galaxy_router",
    "alerts_router",
    "export_router",
    "performance_router",
    "diagnostics_router",
    "analytics_router",
    "research_router",
    "control_router",
    "runs_router"
]
