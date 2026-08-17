from app.routers.auth import router as auth_router
from app.routers.items import router as items_router
from app.routers.matching import router as matching_router
from app.routers.verification import router as verification_router
from app.routers.workflow import router as workflow_router
from app.routers.admin import router as admin_router
from app.routers.notifications import router as notifications_router

__all__ = [
    "auth_router",
    "items_router",
    "matching_router",
    "verification_router",
    "workflow_router",
    "admin_router",
    "notifications_router"
]
