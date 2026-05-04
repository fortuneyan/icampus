"""
OA审批人解析器

根据审批规则解析出实际的审批人用户ID列表

支持规则类型:
- user: 指定用户
- role: 按角色
- department_leader: 部门负责人
- direct_manager: 直接上级
- multi_level: 多级审批
- or/and: 条件组合
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, Department, Role
from app.core.exceptions import BusinessException, ErrorCode


class ApproverResolver:
    """审批人解析器"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve(
        self, 
        rule: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> List[UUID]:
        """
        根据审批规则解析审批人

        Args:
            rule: 审批规则配置
                {
                    "type": "user|role|department_leader|direct_manager|multi_level|or|and",
                    "value": ...,  # 规则值，根据type不同而不同
                    "levels": 3   # multi_level专用，审批层级数
                }
            context: 上下文信息
                {
                    "initiator_id": UUID,      # 发起人ID
                    "initiator_dept_id": UUID, # 发起人部门ID
                    "business_data": {},        # 业务数据
                    ...
                }

        Returns:
            审批人用户ID列表
        """
        rule_type = rule.get("type")
        
        if rule_type == "user":
            return await self._resolve_user(rule, context)
        elif rule_type == "role":
            return await self._resolve_role(rule, context)
        elif rule_type == "department_leader":
            return await self._resolve_department_leader(rule, context)
        elif rule_type == "direct_manager":
            return await self._resolve_direct_manager(rule, context)
        elif rule_type == "multi_level":
            return await self._resolve_multi_level(rule, context)
        elif rule_type == "or":
            return await self._resolve_or(rule, context)
        elif rule_type == "and":
            return await self._resolve_and(rule, context)
        elif rule_type == "cc":
            # CC类型不返回审批人
            return []
        else:
            raise BusinessException(
                ErrorCode.VALIDATION_ERROR,
                f"未知的审批规则类型: {rule_type}"
            )

    async def _resolve_user(
        self, 
        rule: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> List[UUID]:
        """解析指定用户"""
        user_ids = rule.get("value", [])
        if isinstance(user_ids, UUID):
            return [user_ids]
        elif isinstance(user_ids, str):
            # 可能是单个用户ID
            return [UUID(user_ids)]
        elif isinstance(user_ids, list):
            return [UUID(uid) if isinstance(uid, str) else uid for uid in user_ids]
        return []

    async def _resolve_role(
        self, 
        rule: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> List[UUID]:
        """按角色解析审批人"""
        role_codes = rule.get("value", [])
        if isinstance(role_codes, str):
            role_codes = [role_codes]

        # 查询拥有指定角色的用户
        stmt = (
            select(User.id)
            .join(User.roles)
            .where(
                Role.code.in_(role_codes),
                User.status == "active"
            )
        )
        result = await self.db.execute(stmt)
        return [row[0] for row in result.fetchall()]

    async def _resolve_department_leader(
        self, 
        rule: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> List[UUID]:
        """解析部门负责人"""
        # 获取部门ID
        dept_id = rule.get("dept_id") or context.get("initiator_dept_id")
        if not dept_id:
            return []

        # 查询部门负责人
        stmt = select(Department.leader_id).where(Department.id == dept_id)
        result = await self.db.execute(stmt)
        row = result.fetchone()
        
        if row and row[0]:
            return [row[0]]
        return []

    async def _resolve_direct_manager(
        self, 
        rule: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> List[UUID]:
        """解析直接上级
        
        直接上级的定义：从用户表中查找manager_id字段或者从department的leader获取
        这里简化处理，优先使用部门的负责人作为直接上级
        """
        initiator_id = context.get("initiator_id")
        if not initiator_id:
            return []

        # 查询发起人的部门负责人
        stmt = (
            select(Department.leader_id)
            .join(User, User.department_id == Department.id)
            .where(User.id == initiator_id)
        )
        result = await self.db.execute(stmt)
        row = result.fetchone()

        if row and row[0]:
            return [row[0]]
        return []

    async def _resolve_multi_level(
        self, 
        rule: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> List[UUID]:
        """解析多级审批
        
        沿部门层级向上查找N级负责人
        """
        levels = rule.get("levels", 1)
        dept_id = context.get("initiator_dept_id")
        if not dept_id:
            return []

        approvers = []
        current_dept_id = dept_id
        visited = set()

        for _ in range(levels):
            if current_dept_id in visited:
                break
            visited.add(current_dept_id)

            # 查询当前部门的负责人
            stmt = select(Department).where(Department.id == current_dept_id)
            result = await self.db.execute(stmt)
            dept = result.scalar_one_or_none()

            if not dept:
                break

            if dept.leader_id and dept.leader_id != context.get("initiator_id"):
                approvers.append(dept.leader_id)

            # 继续向上一级部门查找
            if dept.parent_id:
                current_dept_id = dept.parent_id
            else:
                break

        return approvers

    async def _resolve_or(
        self, 
        rule: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> List[UUID]:
        """或条件解析 - 只要满足任一规则即可"""
        rules = rule.get("rules", [])
        for r in rules:
            approvers = await self.resolve(r, context)
            if approvers:
                return approvers
        return []

    async def _resolve_and(
        self, 
        rule: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> List[UUID]:
        """与条件解析 - 需要满足所有规则"""
        rules = rule.get("rules", [])
        all_approvers = set()
        
        for r in rules:
            approvers = await self.resolve(r, context)
            all_approvers.update(approvers)
        
        return list(all_approvers)

    async def resolve_node_approvers(
        self, 
        node_config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[UUID]:
        """
        解析节点审批人

        Args:
            node_config: 节点配置，包含审批人规则
            context: 上下文信息

        Returns:
            审批人用户ID列表
        """
        # 从节点配置中获取审批人规则
        approver_rule = node_config.get("approver_rule")
        if not approver_rule:
            return []

        return await self.resolve(approver_rule, context)

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """根据ID获取用户"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users_by_ids(self, user_ids: List[UUID]) -> List[User]:
        """根据ID列表获取用户"""
        if not user_ids:
            return []
        
        stmt = select(User).where(User.id.in_(user_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_department_chain(self, dept_id: UUID) -> List[Department]:
        """获取部门层级链（从当前部门到根部门）"""
        chain = []
        current_id = dept_id
        visited = set()

        while current_id and current_id not in visited:
            visited.add(current_id)
            stmt = select(Department).where(Department.id == current_id)
            result = await self.db.execute(stmt)
            dept = result.scalar_one_or_none()
            
            if dept:
                chain.append(dept)
                current_id = dept.parent_id
            else:
                break

        return chain
