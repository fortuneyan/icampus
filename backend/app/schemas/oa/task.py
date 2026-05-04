"""
任务看板Schema
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class TaskBoardBase(BaseModel):
    """看板基础Schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    color: Optional[str] = Field(default=None, max_length=7)


class TaskBoardCreate(TaskBoardBase):
    """创建看板Schema"""
    pass


class TaskBoardUpdate(BaseModel):
    """更新看板Schema"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    color: Optional[str] = Field(default=None, max_length=7)
    is_archived: Optional[bool] = None


class TaskBoardRead(TaskBoardBase):
    """看板读取Schema"""
    id: UUID
    owner_id: UUID
    owner_name: Optional[str] = None
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskColumnBase(BaseModel):
    """列基础Schema"""
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(default=None, max_length=7)
    sort_order: int = Field(default=0)
    wip_limit: Optional[int] = Field(default=None, ge=1, le=100)


class TaskColumnCreate(TaskColumnBase):
    """创建列Schema"""
    pass


class TaskColumnUpdate(BaseModel):
    """更新列Schema"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    color: Optional[str] = Field(default=None, max_length=7)
    sort_order: Optional[int] = None
    wip_limit: Optional[int] = None


class TaskColumnRead(TaskColumnBase):
    """列读取Schema"""
    id: UUID
    board_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class TaskCardBase(BaseModel):
    """任务卡片基础Schema"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None)
    priority: str = Field(default="medium", description="优先级: low/medium/high/urgent")
    due_date: Optional[datetime] = None
    labels: Optional[List[str]] = Field(default=None)
    estimated_hours: Optional[float] = Field(default=None, ge=0)


class TaskCardCreate(TaskCardBase):
    """创建任务Schema"""
    column_id: UUID
    assignee_ids: Optional[List[UUID]] = Field(default=None)


class TaskCardUpdate(BaseModel):
    """更新任务Schema"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    labels: Optional[List[str]] = None
    estimated_hours: Optional[float] = None
    column_id: Optional[UUID] = None


class TaskCardRead(TaskCardBase):
    """任务读取Schema"""
    id: UUID
    board_id: UUID
    column_id: UUID
    column_name: Optional[str] = None
    creator_id: UUID
    creator_name: Optional[str] = None
    assignees: Optional[List[dict]] = None
    subtask_count: int = 0
    completed_subtask_count: int = 0
    comment_count: int = 0
    attachment_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskCardListItem(BaseModel):
    """任务列表项Schema"""
    id: UUID
    title: str
    priority: str
    due_date: Optional[datetime] = None
    assignee_names: Optional[List[str]] = None
    subtask_count: int
    comment_count: int

    class Config:
        from_attributes = True


class TaskSubtaskBase(BaseModel):
    """子任务基础Schema"""
    title: str = Field(..., min_length=1, max_length=200)


class TaskSubtaskCreate(TaskSubtaskBase):
    """创建子任务Schema"""
    pass


class TaskSubtaskRead(TaskSubtaskBase):
    """子任务读取Schema"""
    id: UUID
    card_id: UUID
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskCommentCreate(BaseModel):
    """评论Schema"""
    content: str = Field(..., min_length=1, max_length=2000)


class TaskCommentRead(BaseModel):
    """评论读取Schema"""
    id: UUID
    card_id: UUID
    content: str
    user_id: UUID
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskMoveRequest(BaseModel):
    """移动任务请求Schema"""
    column_id: UUID
    sort_order: Optional[int] = None


class TaskBoardMemberBase(BaseModel):
    """看板成员基础Schema"""
    user_id: UUID
    role: str = Field(default="member", description="角色: owner/admin/member")


class TaskBoardMemberRead(BaseModel):
    """成员读取Schema"""
    id: UUID
    board_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True
