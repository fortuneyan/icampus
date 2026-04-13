from fastapi import APIRouter
from app.api.v1.system import (
    users,
    departments,
    roles,
    teacher_profiles,
    logs,
    regions,
    encryption,
    dictionary,
    monitor,
    online_users,
    scheduler,
    cache,
)

router = APIRouter()

router.include_router(users.router, prefix="/users", tags=["用户管理"])
router.include_router(departments.router, prefix="/departments", tags=["部门管理"])
router.include_router(roles.router, prefix="", tags=["角色权限管理"], dependencies=[])
router.include_router(
    teacher_profiles.router, prefix="/teacher-profiles", tags=["教师扩展信息"]
)
router.include_router(logs.router, prefix="/logs", tags=["日志审计"])
router.include_router(regions.router, prefix="/regions", tags=["地区管理"])
router.include_router(encryption.router, prefix="/encryption-keys", tags=["加密密钥"])
router.include_router(dictionary.router, prefix="", tags=["字典管理"])
router.include_router(monitor.router, prefix="/monitor", tags=["服务监控"])
router.include_router(online_users.router, prefix="", tags=["在线用户监控"])
router.include_router(scheduler.router, prefix="", tags=["定时任务管理"])
router.include_router(cache.router, prefix="", tags=["缓存监控"])
