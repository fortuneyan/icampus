from fastapi import APIRouter
from app.api.v1.resource import resources, favorites, recommend

router = APIRouter()
router.include_router(resources.router, prefix="", tags=["资源管理"])
router.include_router(favorites.router, prefix="/favorites", tags=["资源收藏"])
router.include_router(recommend.router, prefix="/recommendations", tags=["个性化推荐"])
