from fastapi import APIRouter
from app.api.v1.resource import resources

router = APIRouter()
router.include_router(resources.router, prefix="", tags=["资源管理"])
