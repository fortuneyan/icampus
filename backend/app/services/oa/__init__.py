"""
OA模块服务

已创建:
- ApproverResolver: 审批人解析器
- WorkflowEngine: 工作流引擎核心

待创建:
- AnnouncementService: 公告服务
- RoomBookingService: 教室预约服务
- AssetService: 资产管理服务
- WorkLogService: 工作日志服务
- TaskService: 任务看板服务
"""

from app.services.oa.approver_resolver import ApproverResolver
from app.services.oa.workflow_engine import WorkflowEngine

# 注释掉未创建的服务导入，待后续实现时取消注释
# from app.services.oa.announcement_svc import AnnouncementService
# from app.services.oa.room_booking_svc import RoomBookingService
# from app.services.oa.asset_svc import AssetService
# from app.services.oa.worklog_svc import WorkLogService
# from app.services.oa.task_svc import TaskService

__all__ = [
    # Workflow - 已创建
    "ApproverResolver",
    "WorkflowEngine",
]
