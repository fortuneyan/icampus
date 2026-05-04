"""
学生管理模块API
"""
from fastapi import APIRouter

from app.api.v1.student import growth_records

router = APIRouter()

# 注册子路由
router.include_router(growth_records.router, tags=["学生成长档案"])
