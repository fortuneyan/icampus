from fastapi import APIRouter
from app.api.v1.system import users, departments, roles

router = APIRouter()

router.include_router(users.router, prefix="/users", tags=["用户管理"])
router.include_router(departments.router, prefix="/departments", tags=["部门管理"])
router.include_router(roles.router, prefix="", tags=["角色权限管理"], dependencies=[])
