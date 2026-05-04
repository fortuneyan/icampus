"""
OA模块Schema

已创建:
- Workflow Schemas
- Announcement Schemas
- Room Schemas
- Asset Schemas
- WorkLog Schemas
- Task Schemas
"""

from app.schemas.oa.workflow import (
    # WorkflowDefinition
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate,
    WorkflowDefinitionOut,
    WorkflowDefinitionListOut,
    # WorkflowNode
    WorkflowNodeCreate,
    WorkflowNodeUpdate,
    WorkflowNodeOut,
    # WorkflowInstance
    WorkflowInstanceCreate,
    WorkflowInstanceOut,
    WorkflowInstanceListOut,
    WorkflowInstanceCancel,
    WorkflowInstanceQuery,
    # WorkflowTask
    WorkflowTaskOut,
    WorkflowTaskListOut,
    TaskAction,
    TaskTransfer,
    TaskDelegate,
    WorkflowTaskQuery,
    # WorkflowCC
    WorkflowCCOut,
    WorkflowCCMarkRead,
    WorkflowCCQuery,
    # WorkflowVariable
    WorkflowVariableSchema,
    WorkflowVariableCreate,
    WorkflowVariableOut,
)

from app.schemas.oa.announcement import (
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementRead,
    AnnouncementListItem,
    AnnouncementCommentCreate,
    AnnouncementCommentRead,
    AnnouncementStats,
    AnnouncementReadRecord,
)

from app.schemas.oa.room import (
    MeetingRoomCreate,
    MeetingRoomUpdate,
    MeetingRoomRead,
    RoomBookingCreate,
    RoomBookingUpdate,
    RoomBookingRead,
    RoomBookingListItem,
    AvailableSlot,
    BookingConflict,
)

from app.schemas.oa.asset import (
    AssetCategoryCreate,
    AssetCategoryUpdate,
    AssetCategoryRead,
    AssetCreate,
    AssetUpdate,
    AssetRead,
    AssetListItem,
    AssetOperationCreate,
    AssetOperationRead,
    AssetImportItem,
    AssetImportResult,
)

from app.schemas.oa.worklog import (
    WorklogCategoryCreate,
    WorklogCategoryUpdate,
    WorklogCategoryRead,
    WorklogCreate,
    WorklogUpdate,
    WorklogRead,
    WorklogListItem,
    WorklogCommentCreate,
    WorklogCommentRead,
    WorklogStats,
    WorklogWeeklyReport,
)

from app.schemas.oa.task import (
    TaskBoardCreate,
    TaskBoardUpdate,
    TaskBoardRead,
    TaskColumnCreate,
    TaskColumnUpdate,
    TaskColumnRead,
    TaskCardCreate,
    TaskCardUpdate,
    TaskCardRead,
    TaskCardListItem,
    TaskSubtaskCreate,
    TaskSubtaskRead,
    TaskCommentCreate,
    TaskCommentRead,
    TaskMoveRequest,
    TaskBoardMemberBase,
    TaskBoardMemberRead,
)

__all__ = [
    # Workflow
    "WorkflowDefinitionCreate",
    "WorkflowDefinitionUpdate",
    "WorkflowDefinitionOut",
    "WorkflowDefinitionListOut",
    "WorkflowNodeCreate",
    "WorkflowNodeUpdate",
    "WorkflowNodeOut",
    "WorkflowInstanceCreate",
    "WorkflowInstanceOut",
    "WorkflowInstanceListOut",
    "WorkflowInstanceCancel",
    "WorkflowInstanceQuery",
    "WorkflowTaskOut",
    "WorkflowTaskListOut",
    "TaskAction",
    "TaskTransfer",
    "TaskDelegate",
    "WorkflowTaskQuery",
    "WorkflowCCOut",
    "WorkflowCCMarkRead",
    "WorkflowCCQuery",
    "WorkflowVariableSchema",
    "WorkflowVariableCreate",
    "WorkflowVariableOut",
    # Announcement
    "AnnouncementCreate",
    "AnnouncementUpdate",
    "AnnouncementRead",
    "AnnouncementListItem",
    "AnnouncementCommentCreate",
    "AnnouncementCommentRead",
    "AnnouncementStats",
    "AnnouncementReadRecord",
    # Room
    "MeetingRoomCreate",
    "MeetingRoomUpdate",
    "MeetingRoomRead",
    "RoomBookingCreate",
    "RoomBookingUpdate",
    "RoomBookingRead",
    "RoomBookingListItem",
    "AvailableSlot",
    "BookingConflict",
    # Asset
    "AssetCategoryCreate",
    "AssetCategoryUpdate",
    "AssetCategoryRead",
    "AssetCreate",
    "AssetUpdate",
    "AssetRead",
    "AssetListItem",
    "AssetOperationCreate",
    "AssetOperationRead",
    "AssetImportItem",
    "AssetImportResult",
    # Worklog
    "WorklogCategoryCreate",
    "WorklogCategoryUpdate",
    "WorklogCategoryRead",
    "WorklogCreate",
    "WorklogUpdate",
    "WorklogRead",
    "WorklogListItem",
    "WorklogCommentCreate",
    "WorklogCommentRead",
    "WorklogStats",
    "WorklogWeeklyReport",
    # Task
    "TaskBoardCreate",
    "TaskBoardUpdate",
    "TaskBoardRead",
    "TaskColumnCreate",
    "TaskColumnUpdate",
    "TaskColumnRead",
    "TaskCardCreate",
    "TaskCardUpdate",
    "TaskCardRead",
    "TaskCardListItem",
    "TaskSubtaskCreate",
    "TaskSubtaskRead",
    "TaskCommentCreate",
    "TaskCommentRead",
    "TaskMoveRequest",
    "TaskBoardMemberBase",
    "TaskBoardMemberRead",
]
