"""
扩展业务模块API
宿舍管理、图书管理、一卡通、奖助学金
"""
from fastapi import APIRouter
from app.api.v1.extended import dormitory, library, card, scholarship

router = APIRouter()

router.include_router(dormitory.router, prefix="/dormitory", tags=["宿舍管理"])
router.include_router(library.router, prefix="/library", tags=["图书管理"])
router.include_router(card.router, prefix="/card", tags=["一卡通管理"])
router.include_router(scholarship.router, prefix="/scholarship", tags=["奖助学金管理"])
