from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["All Version 1 Endpoints"])

router.include_router(auth_router)
router.include_router(user_router)
router.include_router(admin_router)
