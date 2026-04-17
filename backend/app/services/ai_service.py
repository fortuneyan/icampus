"""
AI 服务
"""

from typing import Optional, List, AsyncGenerator
from uuid import UUID, uuid4
from datetime import datetime
import json
import httpx
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_model import AISession, AIMessage, AIConfig
from app.schemas.ai import (
    AbilityProfile,
    AbilityDimension,
    KnowledgeGraph,
    KnowledgeNode,
    KnowledgeEdge,
    AbilityRadarData,
    RadarIndicator,
    DiagnosisReport,
    QuestionOutput,
    QuestionOption,
    QuestionSetOutput,
    QuestionGenerateRequest,
)
from app.core.exceptions import NotFoundException
from app.services.base_service import BaseService


class AIService:
    """AI服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self, user_id: UUID, title: Optional[str] = None, model_type: str = "deepseek"
    ) -> AISession:
        session = AISession(
            user_id=user_id, title=title or "新对话", model_type=model_type
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_user_sessions(self, user_id: UUID) -> List[AISession]:
        result = await self.db.execute(
            select(AISession)
            .where(AISession.user_id == user_id)
            .order_by(AISession.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_session_messages(self, session_id: UUID) -> List[AIMessage]:
        result = await self.db.execute(
            select(AIMessage)
            .where(AIMessage.session_id == session_id)
            .order_by(AIMessage.created_at)
        )
        return list(result.scalars().all())

    async def add_message(self, session_id: UUID, role: str, content: str) -> AIMessage:
        message = AIMessage(session_id=session_id, role=role, content=content)
        self.db.add(message)

        session = await self.db.get(AISession, session_id)
        if session:
            session.updated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def delete_session(self, session_id: UUID) -> bool:
        session = await self.db.get(AISession, session_id)
        if session:
            await self.db.delete(session)
            await self.db.commit()
            return True
        return False

    async def get_config(self, model_type: str = "deepseek") -> Optional[AIConfig]:
        result = await self.db.execute(
            select(AIConfig).where(
                AIConfig.model_type == model_type, AIConfig.status == "active"
            )
        )
        return result.scalar_one_or_none()

    async def update_config(self, model_type: str, data: dict) -> AIConfig:
        config = await self.get_config(model_type)
        if config:
            for key, value in data.items():
                setattr(config, key, value)
        else:
            config = AIConfig(model_type=model_type, **data)
            self.db.add(config)

        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def chat(
        self,
        user_id: UUID,
        message: str,
        session_id: Optional[UUID] = None,
        model_type: str = "deepseek",
    ) -> dict:
        if not session_id:
            session = await self.create_session(user_id, model_type=model_type)
            session_id = session.id

        await self.add_message(session_id, "user", message)

        config = await self.get_config(model_type)
        if not config or not config.api_key:
            response_content = "[未配置] 请在设置中配置 AI API Key"
        else:
            response_content = await self._call_llm(config, message, model_type)

        await self.add_message(session_id, "assistant", response_content)

        return {
            "session_id": str(session_id),
            "message": response_content,
            "created_at": datetime.now().isoformat(),
        }

    async def _call_llm(
        self, config: AIConfig, message: str, model_type: str = "deepseek"
    ) -> str:
        """调用 LLM API（非流式）"""
        if not config or not config.api_key:
            return "[未配置] 请在设置中配置 AI API Key"

        try:
            # 根据 model_type 构建请求
            api_url = config.api_url or self._get_api_url(model_type)
            model_name = self._get_model_name(model_type)

            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": message}],
                "temperature": (config.temperature or 80) / 100,
                "max_tokens": config.max_tokens or 2000,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{api_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            choices = data.get("choices", [])
            if choices:
                return choices[0]["message"]["content"]
            return "[错误] 未收到有效响应"

        except httpx.TimeoutException:
            return "[错误] 请求超时，请稍后重试"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return "[错误] API Key 无效"
            return f"[错误] API 请求失败: {e.response.status_code}"
        except Exception as e:
            return f"[错误] {str(e)}"

    def _get_api_url(self, model_type: str) -> str:
        """根据模型类型返回 API URL"""
        urls = {
            "deepseek": "https://api.deepseek.com/v1",
            "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "openai": "https://api.openai.com/v1",
        }
        return urls.get(model_type, "https://api.deepseek.com/v1")

    def _get_model_name(self, model_type: str) -> str:
        """根据模型类型返回实际模型名"""
        models = {
            "deepseek": "deepseek-chat",
            "qwen": "qwen-plus",
            "openai": "gpt-4o-mini",
        }
        return models.get(model_type, "deepseek-chat")

    async def chat_stream(
        self,
        user_id: UUID,
        message: str,
        session_id: Optional[UUID] = None,
        model_type: str = "deepseek",
    ) -> AsyncGenerator[str, None]:
        """
        流式对话：返回 SSE 格式的数据块

        Yields:
            str: SSE 格式数据块，如 "data: {\"content\": \"你好\"}\n\n"
        """
        # 创建或复用会话
        if not session_id:
            session = await self.create_session(user_id, model_type=model_type)
            session_id = session.id

        # 保存用户消息
        await self.add_message(session_id, "user", message)

        # 发送 session_id
        yield f"data: {json.dumps({'type': 'session_id', 'value': str(session_id)}, ensure_ascii=False)}\n\n"

        # 获取配置
        config = await self.get_config(model_type)
        if not config or not config.api_key:
            unconfig_msg = "[未配置] 请在设置中配置 AI API Key"
            yield f"data: {json.dumps({'type': 'content', 'value': unconfig_msg}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'session_id': str(session_id)}, ensure_ascii=False)}\n\n"
            return

        # 流式调用 LLM
        try:
            full_response = ""
            api_url = self._get_api_url(model_type)
            model_name = self._get_model_name(model_type)

            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": message}],
                "temperature": (config.temperature or 80) / 100,
                "max_tokens": config.max_tokens or 2000,
                "stream": True,
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{api_url}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code == 401:
                        yield f"data: {json.dumps({'type': 'content', 'value': '[错误] API Key 无效'}, ensure_ascii=False)}\n\n"
                        yield f"data: {json.dumps({'type': 'done', 'session_id': str(session_id)}, ensure_ascii=False)}\n\n"
                        return

                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip() or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = (
                                data.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            if delta:
                                full_response += delta
                                yield f"data: {json.dumps({'type': 'content', 'value': delta}, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            continue

        except httpx.TimeoutException:
            yield f"data: {json.dumps({'type': 'content', 'value': '[错误] 请求超时，请稍后重试'}, ensure_ascii=False)}\n\n"
        except httpx.HTTPStatusError as e:
            yield f"data: {json.dumps({'type': 'content', 'value': f'[错误] API 请求失败: {e.response.status_code}'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'content', 'value': f'[错误] {str(e)}'}, ensure_ascii=False)}\n\n"
        finally:
            # 保存完整回复到数据库
            if full_response:
                await self.add_message(session_id, "assistant", full_response)
            yield f"data: {json.dumps({'type': 'done', 'session_id': str(session_id)}, ensure_ascii=False)}\n\n"

    # ==================== 能力画像分析 ====================

    async def get_ability_profile(
        self,
        student_id: str,
        course_id: Optional[str] = None,
        score_history: Optional[List[dict]] = None,
    ) -> AbilityProfile:
        """
        分析学生能力画像。

        从成绩历史和学习记录中提取多维能力指标，
        使用 AI 辅助分析并给出薄弱点建议。
        """
        from app.models.score import Score
        from app.models.learning_record import LearningRecord
        from app.models.student import Student
        from sqlalchemy import select, desc, func
        from uuid import UUID

        # 解析学生ID
        try:
            student_uuid = UUID(student_id)
        except ValueError:
            query = select(Student).where(Student.student_no == student_id)
            result = await self.db.execute(query)
            student = result.scalar_one_or_none()
            if not student:
                return AbilityProfile(
                    student_id=student_id,
                    overall_score=0,
                    dimensions=[],
                    strengths=[],
                    weaknesses=[],
                    improvement_suggestions=[],
                    generated_at="",
                )
            student_uuid = student.id

        # 获取成绩历史（最近 20 条）
        query = (
            select(Score)
            .where(Score.student_id == student_uuid)
            .order_by(desc(Score.recorded_at))
            .limit(20)
        )
        result = await self.db.execute(query)
        scores = list(result.scalars().all())

        score_data = [
            {
                "course_id": str(s.course_id) if s.course_id else None,
                "score": float(s.score) if s.score else 0,
                "score_type": s.score_type,
                "exam_date": s.recorded_at.isoformat() if s.recorded_at else None,
            }
            for s in scores
        ]

        # 获取学习记录
        rec_query = (
            select(LearningRecord)
            .where(LearningRecord.user_id == student_id)
            .order_by(desc(LearningRecord.created_at))
            .limit(30)
        )
        rec_result = await self.db.execute(rec_query)
        records = list(rec_result.scalars().all())

        record_data = [
            {
                "resource_type": r.resource_type,
                "action_type": r.action_type,
                "duration": r.duration or 0,
                "progress": r.progress or 0,
            }
            for r in records
        ]

        # 计算基础统计
        if score_data:
            avg_score = sum(s["score"] for s in score_data) / len(score_data)
            max_score = max(s["score"] for s in score_data)
            min_score = min(s["score"] for s in score_data)
        else:
            avg_score = max_score = min_score = 0

        total_study_time = sum(r["duration"] for r in record_data)
        total_records = len(record_data)

        # 定义能力维度及规则（基于题目类型）
        # 从 score_type 推断能力维度
        dimension_rules = {
            "选择题": ("选择题能力", 0.4),
            "填空题": ("基础知识掌握", 0.3),
            "解答题": ("综合应用能力", 0.3),
            "计算题": ("计算能力", 0.4),
            "证明题": ("逻辑推理能力", 0.4),
            "应用题": ("问题解决能力", 0.3),
            "实验题": ("实践探究能力", 0.3),
        }

        # 按题型聚合得分
        type_scores: dict = {}
        for s in score_data:
            st = s.get("score_type") or "其他"
            if st not in type_scores:
                type_scores[st] = []
            type_scores[st].append(s["score"])

        # 构建能力维度
        dimensions: List[AbilityDimension] = []
        strengths: List[str] = []
        weaknesses: List[str] = []

        for score_type, (dim_name, weight) in dimension_rules.items():
            scores_for_type = type_scores.get(score_type, [])
            if not scores_for_type:
                continue
            dim_avg = sum(scores_for_type) / len(scores_for_type)

            if dim_avg >= 80:
                level, trend = "优秀", "up"
                strengths.append(dim_name)
            elif dim_avg >= 70:
                level, trend = "良好", "stable"
            elif dim_avg >= 60:
                level, trend = "一般", "stable"
                weaknesses.append(dim_name)
            else:
                level, trend = "薄弱", "down"
                weaknesses.append(dim_name)

            dimensions.append(
                AbilityDimension(
                    name=dim_name,
                    score=round(dim_avg, 1),
                    level=level,
                    trend=trend,
                    evidence=[f"基于{len(scores_for_type)}次{score_type}的平均得分"],
                )
            )

        # 确保至少有基础维度
        if not dimensions:
            dimensions = [
                AbilityDimension(
                    name="综合能力",
                    score=round(avg_score, 1),
                    level="一般" if avg_score >= 60 else "薄弱",
                    trend="stable",
                    evidence=[f"基于{len(score_data)}次考试平均分"],
                )
            ]

        # 生成建议
        suggestions = []
        if weaknesses:
            suggestions.append(f"建议加强练习：{', '.join(weaknesses[:3])}")
        if avg_score < 70:
            suggestions.append("建议夯实基础，增加练习量")
        if total_study_time < 600:
            suggestions.append("建议增加学习时长，保持规律学习习惯")
        if total_records > 0 and total_study_time / total_records < 5:
            suggestions.append("单次学习专注度有待提高，建议使用番茄工作法")
        if not suggestions:
            suggestions.append("继续保持良好的学习状态")

        return AbilityProfile(
            student_id=str(student_id),
            overall_score=round(avg_score, 1),
            dimensions=dimensions,
            strengths=strengths[:3],
            weaknesses=weaknesses[:3],
            improvement_suggestions=suggestions,
            generated_at=datetime.now().isoformat(),
        )

    async def get_ability_radar(
        self,
        student_id: str,
        course_id: Optional[str] = None,
    ) -> AbilityRadarData:
        """获取能力雷达图数据（简化版供前端渲染）"""
        from app.models.score import Score
        from app.models.student import Student
        from sqlalchemy import select, desc
        from uuid import UUID

        try:
            student_uuid = UUID(student_id)
        except ValueError:
            query = select(Student).where(Student.student_no == student_id)
            result = await self.db.execute(query)
            student = result.scalar_one_or_none()
            if not student:
                """错误数据处理"""
                return AbilityRadarData(
                    student_id=student_id,
                    avg_score=0,
                    indicators=[],
                    highest_dimension="",
                    lowest_dimension="",
                )
            student_uuid = student.id

        # 获取最近成绩
        query = (
            select(Score)
            .where(Score.student_id == student_uuid)
            .order_by(desc(Score.recorded_at))
            .limit(20)
        )
        result = await self.db.execute(query)
        scores = list(result.scalars().all())

        score_data = {s.score_type: float(s.score) if s.score else 0 for s in scores}

        # 雷达图指标映射
        radar_map = {
            "选择题": "选择题能力",
            "填空题": "基础知识",
            "解答题": "综合应用",
            "计算题": "计算能力",
            "证明题": "逻辑推理",
            "应用题": "问题解决",
            "实验题": "实践探究",
        }

        indicators = []
        for score_type, indicator_name in radar_map.items():
            if score_type in score_data:
                indicators.append(
                    RadarIndicator(
                        name=indicator_name,
                        value=score_data[score_type],
                    )
                )

        # 若无数据，提供默认指标
        if not indicators:
            indicators = [
                RadarIndicator(name="综合能力", value=60.0),
            ]

        scores_list = [ind.value for ind in indicators]
        avg = sum(scores_list) / len(scores_list) if scores_list else 0
        highest = max(scores_list) if scores_list else 0
        lowest = min(scores_list) if scores_list else 0

        highest_name = next(
            (ind.name for ind in indicators if ind.value == highest), "未知"
        )
        lowest_name = next(
            (ind.name for ind in indicators if ind.value == lowest), "未知"
        )

        return AbilityRadarData(
            student_id=str(student_id),
            indicators=indicators,
            avg_score=round(avg, 1),
            highest_dimension=highest_name,
            lowest_dimension=lowest_name,
            comparison_with_class=None,
        )

    # ==================== 知识图谱构建 ====================

    async def get_knowledge_graph(
        self,
        student_id: UUID,
        course_id: Optional[UUID] = None,
        course_name: Optional[str] = None,
    ) -> KnowledgeGraph:
        """
        构建学生学习知识图谱。

        基于课程/知识点层次 + 成绩历史，
        标注每个节点的掌握度、前置依赖和学习路径。
        """
        from app.models.score import Score
        from app.models.learning_record import LearningRecord
        from sqlalchemy import select, desc

        # 获取成绩历史
        query = (
            select(Score)
            .where(Score.student_id == student_id)
            .order_by(desc(Score.recorded_at))
            .limit(20)
        )
        result = await self.db.execute(query)
        scores = list(result.scalars().all())

        score_data = {
            str(s.course_id): float(s.score) if s.score else 0 for s in scores
        }

        # 获取学习记录
        rec_query = (
            select(LearningRecord)
            .where(LearningRecord.user_id == student_id)
            .order_by(desc(LearningRecord.created_at))
            .limit(30)
        )
        rec_result = await self.db.execute(rec_query)
        records = list(rec_result.scalars().all())

        # 构建知识图谱节点（以数学为例的层次结构）
        # 实际项目中这些节点应从题库/教材结构化数据中读取
        course_label = (
            course_name or f"课程{str(course_id)[:8] if course_id else '未知'}"
        )

        # MOCK DATA
        # 知识节点定义（示例层次结构，可扩展）
        node_definitions = [
            # (node_id, name, parent_id, difficulty, importance, prerequisites, tags)
            ("K001", "基础运算", None, 1.0, 90, [], ["代数"]),
            ("K002", "整式运算", "K001", 1.5, 85, ["K001"], ["代数"]),
            ("K003", "因式分解", "K002", 2.0, 80, ["K002"], ["代数"]),
            ("K004", "一次方程", "K002", 2.0, 85, ["K002"], ["方程"]),
            ("K005", "二次方程", "K004", 3.0, 80, ["K004", "K003"], ["方程"]),
            ("K006", "函数基础", "K001", 2.5, 85, ["K001"], ["函数"]),
            ("K007", "一次函数", "K006", 3.0, 80, ["K006", "K004"], ["函数"]),
            ("K008", "二次函数", "K007", 4.0, 90, ["K007", "K005"], ["函数"]),
            ("K009", "几何基础", None, 2.0, 85, [], ["几何"]),
            ("K010", "三角形", "K009", 3.0, 90, ["K009"], ["几何"]),
            ("K011", "全等三角形", "K010", 3.5, 85, ["K010"], ["几何"]),
            ("K012", "相似三角形", "K010", 4.0, 80, ["K011"], ["几何"]),
            ("K013", "四边形", "K009", 3.0, 85, ["K009"], ["几何"]),
            ("K014", "圆", "K009", 4.0, 80, ["K009"], ["几何"]),
        ]

        nodes: List[KnowledgeNode] = []
        for (
            node_id,
            name,
            parent_id,
            difficulty,
            importance,
            prerequisites,
            tags,
        ) in node_definitions:
            # 查找该知识点在成绩中的得分（简化：用课程得分模拟）
            course_key = str(course_id) if course_id else None
            base_score = score_data.get(course_key, 60.0) if course_key else 60.0

            # 根据节点ID和历史记录计算掌握度
            # 基础运算最简单 → 高分，复杂推导 → 低分
            mastery = min(
                100,
                max(
                    20,
                    base_score
                    - (difficulty - 1) * 8
                    + sum(
                        r.progress
                        for r in records
                        if r.resource_name and name in r.resource_name
                    )
                    / max(1, len(records))
                    * 5,
                ),
            )
            mastery = round(
                mastery + (hash(node_id) % 20 - 10), 1
            )  # 模拟不同知识点的差异
            mastery = max(10, min(99, mastery))

            nodes.append(
                KnowledgeNode(
                    node_id=node_id,
                    name=name,
                    parent_id=parent_id,
                    mastery=mastery,
                    difficulty=difficulty,
                    importance=importance,
                    prerequisites=prerequisites,
                    tags=tags,
                    exam_frequency=round(
                        importance / 100 * (hash(node_id) % 10 + 1), 1
                    ),
                )
            )

        # 构建边
        edges: List[KnowledgeEdge] = []
        for node in nodes:
            for prereq in node.prerequisites:
                edges.append(
                    KnowledgeEdge(
                        source=prereq,
                        target=node.node_id,
                        relation="prerequisite",
                    )
                )

        # 找最薄弱节点（掌握度 < 50）
        weakest = [n.node_id for n in nodes if n.mastery < 50]

        # 找学习前沿：前置已掌握（>= 60）但自身未掌握（< 70）的节点
        mastered_ids = {n.node_id for n in nodes if n.mastery >= 60}
        learning_frontier = [
            n.node_id
            for n in nodes
            if all(p in mastered_ids for p in n.prerequisites) and n.mastery < 70
        ]

        return KnowledgeGraph(
            student_id=str(student_id),
            course_id=str(course_id) if course_id else None,
            course_name=course_label,
            nodes=nodes,
            edges=edges,
            weakest_nodes=weakest[:5],
            learning_frontier=learning_frontier[:5],
            generated_at=datetime.now().isoformat(),
        )

    # ==================== 综合诊断报告 ====================

    async def generate_diagnosis_report(
        self,
        student_id: UUID,
        course_id: Optional[UUID] = None,
        course_name: Optional[str] = None,
        include_ability: bool = True,
        include_knowledge_graph: bool = True,
    ) -> DiagnosisReport:
        """生成综合学习诊断报告"""
        report_id = str(uuid4())

        ability_profile = None
        if include_ability:
            ability_profile = await self.get_ability_profile(student_id, course_id)

        knowledge_graph = None
        if include_knowledge_graph:
            knowledge_graph = await self.get_knowledge_graph(
                student_id, course_id, course_name
            )

        radar_data = await self.get_ability_radar(student_id, course_id)

        # 收集综合建议
        recommendations = []
        if ability_profile:
            for sug in ability_profile.improvement_suggestions:
                recommendations.append(
                    {"type": "ability", "text": sug, "priority": "high"}
                )
        if knowledge_graph and knowledge_graph.weakest_nodes:
            recommendations.append(
                {
                    "type": "knowledge",
                    "text": f"建议优先攻克{len(knowledge_graph.weakest_nodes)}个薄弱知识点",
                    "priority": "medium",
                }
            )
        if not recommendations:
            recommendations.append(
                {
                    "type": "general",
                    "text": "学习状态良好，请继续保持",
                    "priority": "low",
                }
            )

        return DiagnosisReport(
            student_id=str(student_id),
            report_id=report_id,
            ability_profile=ability_profile,
            knowledge_graph=knowledge_graph,
            radar_data=radar_data,
            exam_analysis=None,
            recommendations=recommendations,
            report_date=datetime.now().isoformat(),
        )

    # ==================== AI 出题系统 ====================

    async def generate_questions(
        self,
        request: QuestionGenerateRequest,
    ) -> QuestionSetOutput:
        """
        AI 生成题目。

        Args:
            request: 出题请求参数

        Returns:
            QuestionSetOutput: 生成的题目集
        """
        from uuid import uuid4
        from app.models.exam import Question

        # 题型中文映射
        type_map = {
            "single": "单选题",
            "multiple": "多选题",
            "fill": "填空题",
            "essay": "解答题",
            "calculation": "计算题",
        }

        # 难度中文映射
        difficulty_map = {
            1: "简单",
            2: "中等",
            3: "较难",
            4: "困难",
            5: "极难",
        }

        # 构建 AI prompt
        question_types_str = "、".join(
            [type_map.get(t, t) for t in request.question_types]
        )
        difficulty_text = difficulty_map.get(request.difficulty, "中等")

        knowledge_section = ""
        if request.knowledge_points:
            knowledge_section = f"- 重点知识点：{', '.join(request.knowledge_points)}"

        prompt = f"""请为以下要求生成 {request.count} 道题目：

- 课程名称：{request.course_name}
- 年级：{request.grade_level}
- 课题：{request.topic}
- 题型：{question_types_str}
- 难度：{difficulty_text}
{knowledge_section}
{f"- 特殊要求：{request.requirements}" if request.requirements else ""}

请按以下 JSON 格式返回 {request.count} 道题目：
[
    {{
        "content": "题目内容",
        "question_type": "题型标识(single/multiple/fill/essay/calculation)",
        "options": [{{"label": "A", "content": "选项A内容", "is_correct": true/false}}],  // 选择题需要，其他题型为null
        "answer": "答案内容",  // 填空题和解答题填答案
        "analysis": "题目解析",
        "difficulty": {request.difficulty},
        "score": 5,
        "knowledge_points": ["知识点1", "知识点2"]
    }}
]

要求：
1. 题目内容科学准确，无歧义
2. 选择题的选项要有区分度，干扰项合理
3. 填空题的答案唯一或给出得分标准
4. 解答题要有明确的解题步骤和得分点
5. 答案和解析要准确详细"""

        # 调用 LLM
        config = await self.get_config("deepseek")
        if not config or not config.api_key:
            # 返回示例题目
            return self._generate_sample_questions(request, uuid4().hex)

        try:
            response = await self._call_llm(config, prompt, "deepseek")
            questions = self._parse_questions_from_response(
                response, request.question_types
            )

            if not questions:
                return self._generate_sample_questions(request, uuid4().hex)

            # 构建题目集
            set_id = uuid4().hex
            return QuestionSetOutput(
                set_id=set_id,
                title=f"{request.course_name} - {request.topic} 练习题",
                course_name=request.course_name,
                grade_level=request.grade_level,
                topic=request.topic,
                total_count=len(questions),
                questions=questions,
                generated_at=datetime.now().isoformat(),
                saved_count=0,
            )

        except Exception:
            return self._generate_sample_questions(request, uuid4().hex)

    def _parse_questions_from_response(
        self, response: str, expected_types: List[str]
    ) -> List[QuestionOutput]:
        """从 LLM 响应中解析题目"""
        import re

        # 尝试提取 JSON
        json_match = re.search(r"\[.*\]", response, re.DOTALL)
        if not json_match:
            return []

        try:
            import json

            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            return []

        if not isinstance(data, list):
            return []

        questions = []
        for item in data:
            if not isinstance(item, dict):
                continue

            question_type = item.get("question_type", "single")
            if question_type not in [
                "single",
                "multiple",
                "fill",
                "essay",
                "calculation",
            ]:
                question_type = expected_types[0] if expected_types else "single"

            # 处理选项
            options = None
            if question_type in ["single", "multiple"] and item.get("options"):
                options = [
                    QuestionOption(
                        label=opt.get("label", chr(65 + i)),
                        content=opt.get("content", ""),
                        is_correct=opt.get("is_correct", False),
                    )
                    for i, opt in enumerate(item.get("options", []))
                ]

            questions.append(
                QuestionOutput(
                    content=item.get("content", ""),
                    question_type=question_type,
                    options=options,
                    answer=item.get("answer"),
                    analysis=item.get("analysis"),
                    difficulty=item.get("difficulty", 2),
                    score=float(item.get("score", 5)),
                    knowledge_points=item.get("knowledge_points", []),
                    source="ai",
                    saved=False,
                )
            )

        return questions

    def _generate_sample_questions(
        self, request: QuestionGenerateRequest, set_id: str
    ) -> QuestionSetOutput:
        """生成示例题目（当 AI 服务不可用时）"""
        from app.schemas.ai import QuestionOption

        # 根据题型生成示例
        sample_questions: List[QuestionOutput] = []
        type_cycle = request.question_types * (
            request.count // len(request.question_types) + 1
        )

        for i in range(min(request.count, len(type_cycle))):
            q_type = type_cycle[i]

            if q_type == "single":
                q = QuestionOutput(
                    content=f"【单选题】关于{request.topic}的说法，以下哪一项是正确的？",
                    question_type="single",
                    options=[
                        QuestionOption(label="A", content="选项A内容", is_correct=True),
                        QuestionOption(
                            label="B", content="选项B内容", is_correct=False
                        ),
                        QuestionOption(
                            label="C", content="选项C内容", is_correct=False
                        ),
                        QuestionOption(
                            label="D", content="选项D内容", is_correct=False
                        ),
                    ],
                    answer="A",
                    analysis=f"本题考察{request.topic}的基本概念，选项A正确描述了这一知识点。",
                    difficulty=request.difficulty,
                    score=5.0,
                    knowledge_points=[request.topic],
                    source="ai",
                    saved=False,
                )
            elif q_type == "multiple":
                q = QuestionOutput(
                    content=f"【多选题】下列关于{request.topic}的说法，正确的有（ ）？",
                    question_type="multiple",
                    options=[
                        QuestionOption(label="A", content="选项A内容", is_correct=True),
                        QuestionOption(
                            label="B", content="选项B内容", is_correct=False
                        ),
                        QuestionOption(label="C", content="选项C内容", is_correct=True),
                        QuestionOption(
                            label="D", content="选项D内容", is_correct=False
                        ),
                    ],
                    answer="AC",
                    analysis=f"本题考察{request.topic}的多个方面，选项A和C正确。",
                    difficulty=request.difficulty,
                    score=5.0,
                    knowledge_points=[request.topic],
                    source="ai",
                    saved=False,
                )
            elif q_type == "fill":
                q = QuestionOutput(
                    content=f"【填空题】{request.topic}的定义是______。",
                    question_type="fill",
                    answer="[根据实际情况填空]",
                    analysis=f"本题考察{request.topic}的定义和基本概念。",
                    difficulty=request.difficulty,
                    score=5.0,
                    knowledge_points=[request.topic],
                    source="ai",
                    saved=False,
                )
            elif q_type == "essay":
                q = QuestionOutput(
                    content=f"【解答题】请详细说明{request.topic}的原理和应用场景，并举例说明。",
                    question_type="essay",
                    answer="[参考要点：1. 原理说明 2. 应用场景 3. 具体实例]",
                    analysis=f"本题考察{request.topic}的理解和应用能力，评分标准：原理准确(4分)、应用恰当(3分)、举例合适(3分)。",
                    difficulty=request.difficulty,
                    score=10.0,
                    knowledge_points=[request.topic],
                    source="ai",
                    saved=False,
                )
            else:  # calculation
                q = QuestionOutput(
                    content=f"【计算题】已知条件A和B，请计算{request.topic}的结果，并写出计算过程。",
                    question_type="calculation",
                    answer="[计算过程和答案根据具体数值]",
                    analysis=f"本题考察{request.topic}的计算能力和逻辑推理能力。",
                    difficulty=request.difficulty,
                    score=10.0,
                    knowledge_points=[request.topic],
                    source="ai",
                    saved=False,
                )

            sample_questions.append(q)

        return QuestionSetOutput(
            set_id=set_id,
            title=f"{request.course_name} - {request.topic} 练习题",
            course_name=request.course_name,
            grade_level=request.grade_level,
            topic=request.topic,
            total_count=len(sample_questions),
            questions=sample_questions,
            generated_at=datetime.now().isoformat(),
            saved_count=0,
        )

    async def save_generated_question(
        self,
        question_data: QuestionOutput,
        creator_id: UUID,
    ) -> str:
        """保存生成的题目到数据库"""
        from app.models.exam import Question

        # 构建 options JSON
        options_json = None
        if question_data.options:
            options_json = [
                {
                    "label": opt.label,
                    "content": opt.content,
                    "is_correct": opt.is_correct,
                }
                for opt in question_data.options
            ]

        question = Question(
            content=question_data.content,
            question_type=question_data.question_type,
            options=options_json,
            answer=question_data.answer,
            analysis=question_data.analysis,
            difficulty=question_data.difficulty,
            score=question_data.score,
            creator_id=creator_id,
        )

        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)

        return str(question.id)
