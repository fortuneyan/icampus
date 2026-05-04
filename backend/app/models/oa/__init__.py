"""
OA模块模型

已创建:
- Workflow: OaWorkflowDefinition, OaWorkflowNode, OaWorkflowInstance,
            OaWorkflowTask, OaWorkflowVariable, OaWorkflowCC
- AnnouncementCategory: AnnouncementCategory
- Announcement: OaAnnouncement, OaAnnouncementRead, OaAnnouncementComment
- Room: OaRoom, OaRoomBooking
待创建:
- Asset: OaAssetCategory, OaAsset, OaBorrowRecord
- WorkLog: OaWorkLog
- Task: OaTaskProject, OaTask, OaTaskComment, OaTaskAttachment
"""

from app.models.oa.workflow import (
    OaWorkflowDefinition,
    OaWorkflowNode,
    OaWorkflowInstance,
    OaWorkflowTask,
    OaWorkflowVariable,
    OaWorkflowCC,
)
from app.models.oa.announcement_category import AnnouncementCategory
from app.models.oa.announcement import (
    OaAnnouncement,
    OaAnnouncementRead,
    OaAnnouncementComment,
)
from app.models.oa.room import (
    OaRoom,
    OaRoomBooking,
)
from app.models.oa.asset import (
    OaAssetCategory,
    OaAsset,
    OaBorrowRecord,
)
from app.models.oa.worklog import OaWorkLog
from app.models.oa.task import (
    OaTaskProject,
    OaTask,
    OaTaskComment,
    OaTaskAttachment,
)

__all__ = [
    # Workflow - 已创建
    "OaWorkflowDefinition",
    "OaWorkflowNode",
    "OaWorkflowInstance",
    "OaWorkflowTask",
    "OaWorkflowVariable",
    "OaWorkflowCC",
    # AnnouncementCategory - 已创建
    "AnnouncementCategory",
    # Announcement - 已创建
    "OaAnnouncement",
    "OaAnnouncementRead",
    "OaAnnouncementComment",
    # Room - 已创建
    "OaRoom",
    "OaRoomBooking",
    # Asset - 已创建
    "OaAssetCategory",
    "OaAsset",
    "OaBorrowRecord",
    # WorkLog - 已创建
    "OaWorkLog",
    # Task - 已创建
    "OaTaskProject",
    "OaTask",
    "OaTaskComment",
    "OaTaskAttachment",
]
