"""
学习助手 Agent API
提供学习会话、计划、路径、目标等完整功能

数据存储策略：
- 临时数据（学习会话）→ Redis（TTL自动过期）
- 计划/目标/路径 → 内存（T6迁移到Redis）
- Redis不可用时 → 内存降级
"""

import json
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.exceptions import NotFoundException
from app.core.redis_client import get_redis_client
from app.core.logger import logger
from app.models.user import User
from app.models.score import Score
from app.models.learning_record import LearningRecord
from app.schemas.response import success, page_response
from app.services.ai_service import AIService

router = APIRouter()


# ==================== 内存降级存储 ====================
sessions_store = {}
plans_store = {}
goals_store = {}
paths_store = {}


# ==================== Redis 存储层（会话） ====================

# Redis 键前缀和 TTL
SESSION_PREFIX = "learning:session:"
USER_SESSIONS_PREFIX = "learning:user_sessions:"
SESSION_TTL = 2 * 60 * 60  # 2小时


async def _get_redis():
    """获取 Redis 客户端，不可用返回 None"""
    try:
        client = await get_redis_client()
        if client._redis is not None:
            return client
    except Exception:
        pass
    return None


async def _save_session(session: dict) -> None:
    """保存学习会话到 Redis（降级到内存）"""
    session_id = session["id"]
    student_id = session["student_id"]

    # 始终写入内存（降级保障）
    sessions_store[session_id] = session

    redis = await _get_redis()
    if redis is None:
        return

    try:
        r = await redis.connect()
        session_key = f"{SESSION_PREFIX}{session_id}"
        user_key = f"{USER_SESSIONS_PREFIX}{student_id}"

        pipe = r.pipeline(transaction=False)
        pipe.setex(session_key, SESSION_TTL, json.dumps(session, ensure_ascii=False))
        pipe.sadd(user_key, session_id)
        pipe.expire(user_key, SESSION_TTL)
        await pipe.execute()
    except Exception as e:
        logger.warning(f"Redis 保存会话失败（降级到内存）: {e}")


async def _get_session(session_id: str) -> Optional[dict]:
    """从 Redis 获取学习会话（降级到内存）"""
    redis = await _get_redis()
    if redis is not None:
        try:
            r = await redis.connect()
            session_key = f"{SESSION_PREFIX}{session_id}"
            data = await r.get(session_key)
            if data:
                return json.loads(data)
        except Exception:
            pass

    # 降级到内存
    return sessions_store.get(session_id)


async def _get_sessions_by_student(
    student_id: str, subject_id: Optional[int] = None
) -> List[dict]:
    """获取学生的所有会话（降级到内存）"""
    redis = await _get_redis()
    if redis is not None:
        try:
            r = await redis.connect()
            user_key = f"{USER_SESSIONS_PREFIX}{student_id}"
            session_ids = await r.smembers(user_key)

            sessions = []
            for sid in session_ids:
                sid_str = sid.decode() if isinstance(sid, bytes) else sid
                session = await _get_session(sid_str)
                if session:
                    if subject_id is None or session.get("subject_id") == subject_id:
                        sessions.append(session)
            return sessions
        except Exception:
            pass

    # 降级到内存
    sessions = [
        s
        for s in sessions_store.values()
        if s["student_id"] == student_id
        and (subject_id is None or s.get("subject_id") == subject_id)
    ]
    return sessions


async def _get_active_sessions_by_student(student_id: str) -> List[dict]:
    """获取学生的活跃会话（降级到内存）"""
    all_sessions = await _get_sessions_by_student(student_id)
    return [s for s in all_sessions if s.get("status") == "active"]


# ==================== 学习会话管理 ====================


class SessionCreate(BaseModel):
    studentId: str = Field(..., alias="student_id")
    subjectId: Optional[int] = Field(None, alias="subject_id")
    topic: Optional[str] = None
    difficulty: Optional[str] = "medium"

    model_config = {"populate_by_name": True}


class MessageCreate(BaseModel):
    message: str
    attachments: Optional[List[dict]] = None


class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


@router.post("/session", response_model=dict)
async def start_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """开始新的学习会话"""
    session_id = str(uuid4())

    subject_map = {1: "数学", 2: "语文", 3: "英语", 4: "物理", 5: "化学"}
    subject_name = subject_map.get(data.subjectId) if data.subjectId else None

    session = {
        "id": session_id,
        "student_id": data.studentId,
        "subject_id": data.subjectId,
        "subject_name": subject_name,
        "status": "active",
        "start_time": datetime.now().isoformat(),
        "messages": [],
        "context": {
            "difficulty": data.difficulty,
            "topic": data.topic,
            "preferred_style": "visual",
        },
    }

    welcome_msg = {
        "id": str(uuid4()),
        "role": "assistant",
        "content": f"你好！我是你的AI学习助手。{f'今天我们来学习{subject_name}。' if subject_name else '有什么我可以帮你的吗？'}",
        "timestamp": datetime.now().isoformat(),
        "suggestions": ["解释这个概念", "出几道练习题", "总结知识点"],
    }
    session["messages"].append(welcome_msg)

    await _save_session(session)

    return success(session)


@router.get("/session/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话详情"""
    session = await _get_session(session_id)
    if not session:
        raise NotFoundException("会话不存在")
    return success(session)


@router.post("/session/{session_id}/message", response_model=dict)
async def send_message(
    session_id: str,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送消息并获取AI回复"""
    session = await _get_session(session_id)
    if not session:
        raise NotFoundException("会话不存在")

    user_msg = {
        "id": str(uuid4()),
        "role": "user",
        "content": data.message,
        "timestamp": datetime.now().isoformat(),
    }
    session["messages"].append(user_msg)

    ai_content = generate_default_response(data.message)

    ai_msg = {
        "id": str(uuid4()),
        "role": "assistant",
        "content": ai_content,
        "timestamp": datetime.now().isoformat(),
        "suggestions": generate_suggestions(data.message),
    }
    session["messages"].append(ai_msg)

    await _save_session(session)

    return success({"message": ai_msg, "suggestions": ai_msg["suggestions"]})


def generate_default_response(message: str) -> str:
    """生成默认回复"""
    if "解释" in message:
        return "好的，让我为你详细解释这个概念。\\n\\n**核心要点：**\\n1. 理解基本定义\\n2. 掌握关键特征\\n3. 学会实际应用"
    elif "练习" in message:
        return "好的，为你准备了几道练习题：\\n\\n**基础题：**\\n1. 计算下列各式...\\n2. 判断下列说法..."
    elif "总结" in message:
        return "学习总结：\\n\\n**已完成：**\\n- 基础概念掌握\\n- 核心定理理解"
    return "好的，我来帮你分析这个问题。请告诉我更多细节..."


def generate_suggestions(message: str) -> List[str]:
    """生成建议快捷回复"""
    if "解释" in message:
        return ["举个例题", "做练习题", "总结要点"]
    elif "练习" in message:
        return ["查看答案", "详细解析", "下一组"]
    return ["继续提问", "换个话题", "查看更多"]


@router.post("/session/{session_id}/end", response_model=dict)
async def end_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """结束会话"""
    session = await _get_session(session_id)
    if not session:
        raise NotFoundException("会话不存在")

    session["status"] = "completed"
    session["end_time"] = datetime.now().isoformat()

    await _save_session(session)

    return success(session)


@router.post("/message/{message_id}/feedback", response_model=dict)
async def rate_message(
    message_id: str,
    data: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """评价消息"""
    return success(
        {"message_id": message_id, "rating": data.rating, "comment": data.comment}
    )


# ==================== 学习计划 ====================


class PlanCreate(BaseModel):
    studentId: str = Field(..., alias="student_id")
    subjectId: int = Field(..., alias="subject_id")
    target_hours: int = 20
    target_date: datetime
    learning_style: Optional[str] = "visual"


@router.get("/plan", response_model=dict)
async def get_learning_plan(
    student_id: str,
    subject_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学习计划"""
    for plan in plans_store.values():
        if plan["student_id"] == student_id and (
            not subject_id or plan["subject_id"] == subject_id
        ):
            return success(plan)

    # 返回默认计划
    subject_map = {1: "数学", 2: "语文", 3: "英语", 4: "物理", 5: "化学"}
    subject_name = subject_map.get(subject_id, "通用")

    default_plan = {
        "id": str(uuid4()),
        "student_id": student_id,
        "subject_id": subject_id,
        "subject_name": subject_name,
        "total_hours": 20,
        "completed_hours": 5,
        "progress": 25.0,
        "milestones": [
            {
                "id": "1",
                "title": f"{subject_name}基础概念",
                "description": "掌握基础概念和定义",
                "target_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "completed": True,
                "tasks": ["阅读教材第一章", "完成基础练习"],
            },
            {
                "id": "2",
                "title": f"{subject_name}核心定理",
                "description": "理解并应用核心定理",
                "target_date": (datetime.now() + timedelta(days=14)).isoformat(),
                "completed": False,
                "tasks": ["学习定理证明", "完成定理应用题"],
            },
        ],
        "start_date": datetime.now().isoformat(),
        "target_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "status": "active",
    }
    return success(default_plan)


@router.post("/plan/generate", response_model=dict)
async def generate_learning_plan(
    data: PlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生成学习计划"""
    plan_id = str(uuid4())
    subject_map = {1: "数学", 2: "语文", 3: "英语", 4: "物理", 5: "化学"}
    subject_name = subject_map.get(data.subjectId, "未知科目")

    plan = {
        "id": plan_id,
        "student_id": data.studentId,
        "subject_id": data.subjectId,
        "subject_name": subject_name,
        "total_hours": data.target_hours,
        "completed_hours": 0,
        "progress": 0.0,
        "milestones": [
            {
                "id": str(uuid4()),
                "title": f"{subject_name}基础阶段",
                "description": "掌握基础知识和概念",
                "target_date": (data.target_date - timedelta(days=20)).isoformat(),
                "completed": False,
                "tasks": ["学习基础概念", "完成基础练习", "阅读教材"],
            },
            {
                "id": str(uuid4()),
                "title": f"{subject_name}进阶阶段",
                "description": "深入理解和应用",
                "target_date": (data.target_date - timedelta(days=10)).isoformat(),
                "completed": False,
                "tasks": ["学习进阶内容", "完成综合练习", "总结知识点"],
            },
            {
                "id": str(uuid4()),
                "title": f"{subject_name}冲刺阶段",
                "description": "巩固提升和查漏补缺",
                "target_date": data.target_date.isoformat(),
                "completed": False,
                "tasks": ["模拟测试", "错题复习", "重点突破"],
            },
        ],
        "start_date": datetime.now().isoformat(),
        "target_date": data.target_date.isoformat(),
        "status": "active",
    }

    plans_store[plan_id] = plan
    return success(plan)


@router.put("/plan/{plan_id}", response_model=dict)
async def update_learning_plan(
    plan_id: str,
    updates: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新学习计划"""
    plan = plans_store.get(plan_id)
    if not plan:
        raise NotFoundException("计划不存在")

    plan.update(updates)
    return success(plan)


# ==================== 学习路径 ====================


class PathCreate(BaseModel):
    studentId: str = Field(..., alias="student_id")
    subjectId: int = Field(..., alias="subject_id")
    current_level: Optional[int] = 1
    target_level: Optional[int] = 5


@router.get("/path/{student_id}/{subject_id}", response_model=dict)
async def get_learning_path(
    student_id: str,
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学习路径"""
    path_key = f"{student_id}_{subject_id}"

    if path_key in paths_store:
        return success(paths_store[path_key])

    # 生成默认路径
    subject_map = {1: "数学", 2: "语文", 3: "英语", 4: "物理", 5: "化学"}
    subject_name = subject_map.get(subject_id, "未知科目")

    path = {
        "id": str(uuid4()),
        "student_id": student_id,
        "subject_id": subject_id,
        "subject_name": subject_name,
        "nodes": [
            {
                "id": "node_1",
                "type": "concept",
                "title": f"{subject_name}基础概念",
                "description": "学习基础概念和定义",
                "prerequisites": [],
                "duration": 30,
                "difficulty": "easy",
                "status": "completed",
                "position": {"x": 100, "y": 100},
            },
            {
                "id": "node_2",
                "type": "lesson",
                "title": f"{subject_name}核心知识",
                "description": "深入理解核心知识点",
                "prerequisites": ["node_1"],
                "duration": 45,
                "difficulty": "medium",
                "status": "in_progress",
                "position": {"x": 300, "y": 100},
            },
            {
                "id": "node_3",
                "type": "exercise",
                "title": "综合练习",
                "description": "通过练习巩固知识",
                "prerequisites": ["node_2"],
                "duration": 60,
                "difficulty": "medium",
                "status": "locked",
                "position": {"x": 500, "y": 100},
            },
        ],
        "edges": [
            {
                "id": "edge_1",
                "source": "node_1",
                "target": "node_2",
                "type": "sequence",
            },
            {
                "id": "edge_2",
                "source": "node_2",
                "target": "node_3",
                "type": "sequence",
            },
        ],
        "current_node_id": "node_2",
        "completed_nodes": ["node_1"],
        "total_nodes": 3,
        "estimated_duration": 135,
    }

    paths_store[path_key] = path
    return success(path)


@router.post("/path/generate", response_model=dict)
async def generate_learning_path(
    data: PathCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生成学习路径"""
    path_key = f"{data.studentId}_{data.subjectId}"

    subject_name = subject_map.get(data.subjectId, "未知科目")

    plan = {
        "id": plan_id,
        "student_id": data.studentId,
        "subject_id": data.subjectId,
        "subject_name": subject_name,
        "nodes": [
            {
                "id": f"node_{i}",
                "type": "concept"
                if i % 3 == 0
                else ("exercise" if i % 3 == 1 else "quiz"),
                "title": f"{subject_name}知识点 {i + 1}",
                "description": f"学习{subject_name}的第{i + 1}个知识点",
                "prerequisites": [f"node_{i - 1}"] if i > 0 else [],
                "duration": 30 + (i * 5),
                "difficulty": ["easy", "medium", "hard"][i % 3],
                "status": "completed"
                if i < data.current_level
                else ("available" if i == data.current_level else "locked"),
                "position": {"x": 100 + (i * 200), "y": 100 + ((i % 2) * 100)},
            }
            for i in range(data.target_level)
        ],
        "edges": [
            {
                "id": f"edge_{i}",
                "source": f"node_{i}",
                "target": f"node_{i + 1}",
                "type": "sequence",
            }
            for i in range(data.target_level - 1)
        ],
        "current_node_id": f"node_{data.current_level}",
        "completed_nodes": [f"node_{i}" for i in range(data.current_level)],
        "total_nodes": data.target_level,
        "estimated_duration": sum(30 + (i * 5) for i in range(data.target_level)),
    }

    paths_store[path_key] = path
    return success(path)


@router.put("/path/{path_id}/node/{node_id}", response_model=dict)
async def update_path_node(
    path_id: str,
    node_id: str,
    status: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新路径节点状态"""
    for path in paths_store.values():
        if path["id"] == path_id:
            for node in path["nodes"]:
                if node["id"] == node_id:
                    node_status = status.get("status", "available")
                    node["status"] = node_status
                    if (
                        node_status == "completed"
                        and node_id not in path["completed_nodes"]
                    ):
                        path["completed_nodes"].append(node_id)
                    return success(node)

    raise NotFoundException("节点不存在")


# ==================== 学习目标 ====================


class GoalCreate(BaseModel):
    studentId: str = Field(..., alias="student_id")
    title: str
    description: Optional[str] = None
    target_date: datetime
    progress: Optional[float] = 0.0
    status: Optional[str] = "active"
    milestones: Optional[List[dict]] = []


@router.get("/goals/{student_id}", response_model=dict)
async def get_learning_goals(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学习目标列表"""
    goals = [g for g in goals_store.values() if g["student_id"] == student_id]

    if not goals:
        # 返回默认目标
        default_goals = [
            {
                "id": str(uuid4()),
                "student_id": student_id,
                "title": "掌握二次函数",
                "description": "能够熟练解决二次函数相关问题",
                "target_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "progress": 65.0,
                "status": "active",
                "milestones": [
                    {"id": "1", "title": "理解基本概念", "completed": True},
                    {"id": "2", "title": "掌握解题方法", "completed": False},
                ],
            }
        ]
        return success(default_goals)

    return success(goals)


@router.post("/goals", response_model=dict)
async def create_learning_goal(
    data: GoalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建学习目标"""
    goal_id = str(uuid4())
    goal = {
        "id": goal_id,
        "student_id": data.studentId,
        "title": data.title,
        "description": data.description or "",
        "target_date": data.target_date.isoformat()
        if isinstance(data.target_date, datetime)
        else data.target_date,
        "progress": data.progress or 0.0,
        "status": data.status or "active",
        "milestones": data.milestones or [],
    }

    goals_store[goal_id] = goal
    return success(goal)


@router.put("/goals/{goal_id}", response_model=dict)
async def update_learning_goal(
    goal_id: str,
    updates: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新学习目标"""
    goal = goals_store.get(goal_id)
    if not goal:
        raise NotFoundException("目标不存在")

    goal.update(updates)
    return success(goal)


@router.delete("/goals/{goal_id}", response_model=dict)
async def delete_learning_goal(
    goal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除学习目标"""
    if goal_id in goals_store:
        del goals_store[goal_id]
    return success(message="删除成功")


# ==================== 知识掌握度 ====================


@router.get("/mastery/{student_id}", response_model=dict)
async def get_knowledge_mastery(
    student_id: str,
    subject_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取知识掌握度"""
    # 模拟数据
    mastery_data = [
        {
            "node_id": "1",
            "node_name": "代数基础",
            "mastery": 85,
            "trend": "up",
            "last_practiced": (datetime.now() - timedelta(days=2)).isoformat(),
            "next_review": (datetime.now() + timedelta(days=5)).isoformat(),
        },
        {
            "node_id": "2",
            "node_name": "函数概念",
            "mastery": 72,
            "trend": "stable",
            "last_practiced": (datetime.now() - timedelta(days=1)).isoformat(),
            "next_review": (datetime.now() + timedelta(days=3)).isoformat(),
        },
        {
            "node_id": "3",
            "node_name": "几何证明",
            "mastery": 58,
            "trend": "down",
            "last_practiced": (datetime.now() - timedelta(days=5)).isoformat(),
            "next_review": datetime.now().isoformat(),
        },
        {
            "node_id": "4",
            "node_name": "应用题",
            "mastery": 45,
            "trend": "down",
            "last_practiced": (datetime.now() - timedelta(days=3)).isoformat(),
            "next_review": (datetime.now() + timedelta(days=1)).isoformat(),
        },
    ]

    if subject_id:
        subject_topics = {
            1: ["代数基础", "函数概念", "几何证明", "应用题"],
            2: ["阅读理解", "写作技巧", "古诗文", "现代文"],
            3: ["词汇语法", "阅读理解", "听力口语", "写作翻译"],
            4: ["力学基础", "电磁学", "热学", "光学"],
            5: ["化学基础", "有机化学", "无机化学", "实验操作"],
        }
        topics = subject_topics.get(subject_id, [])
        mastery_data = [
            m for m in mastery_data if any(t in m["node_name"] for t in topics)
        ]

    return success(mastery_data)


# ==================== AI推荐 ====================


@router.get("/recommendations/{student_id}", response_model=dict)
async def get_recommendations(
    student_id: str,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取AI推荐"""
    recommendations = [
        {
            "id": "1",
            "type": "practice",
            "title": "二次函数专项练习",
            "description": "针对你的薄弱环节进行专项训练",
            "reason": "最近正确率有所下降",
            "priority": 1,
            "estimated_minutes": 20,
            "confidence": 0.85,
        },
        {
            "id": "2",
            "type": "review",
            "title": "复习上周知识点",
            "description": "根据遗忘曲线安排复习",
            "reason": "临近遗忘高峰期",
            "priority": 2,
            "estimated_minutes": 15,
            "confidence": 0.92,
        },
        {
            "id": "3",
            "type": "content",
            "title": "观看教学视频",
            "description": "几何证明技巧讲解",
            "reason": "该知识点掌握度较低",
            "priority": 3,
            "estimated_minutes": 25,
            "confidence": 0.78,
        },
    ]

    return success(recommendations[:limit])


# ==================== 学习统计 ====================


@router.get("/stats/{student_id}", response_model=dict)
async def get_learning_stats(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学习统计"""
    stats = {
        "total_study_time": 45,
        "weekly_study_time": 8,
        "daily_average": 1.2,
        "current_streak": 7,
        "longest_streak": 14,
        "sessions_completed": 28,
        "topics_learned": 15,
        "exercises_completed": 120,
        "accuracy_rate": 82,
        "engagement_score": 88,
    }
    return success(stats)


# ==================== 会话历史 ====================


@router.get("/sessions/{student_id}", response_model=dict)
async def get_session_history(
    student_id: str,
    subject_id: Optional[int] = None,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话历史"""
    sessions = await _get_sessions_by_student(student_id, subject_id)

    # 按时间倒序
    sessions = sorted(sessions, key=lambda x: x["start_time"], reverse=True)

    total = len(sessions)
    sessions = sessions[offset : offset + limit]

    return page_response(sessions, total, offset // limit + 1, limit)


# ==================== 助手状态 ====================


@router.get("/status/{student_id}", response_model=dict)
async def get_assistant_status(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学习助手状态"""
    active_sessions = await _get_active_sessions_by_student(student_id)

    return success(
        {
            "online": True,
            "current_session": active_sessions[0] if active_sessions else None,
            "pending_recommendations": 3,
            "streak_info": {"current": 7, "longest": 14},
        }
    )
