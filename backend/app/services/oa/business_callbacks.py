"""
OA工作流业务回调处理器

使用策略模式（Strategy Pattern）实现：
- 每种 business_type 对应一个回调处理器（Handler）
- 引擎通过注册表查找并调用对应处理器
- 处理器之间完全解耦，新增业务类型只需添加新 Handler 类并注册

使用方式：
    # 1. 在应用启动时（main.py 或各模块的 __init__.py 中）注册回调
    from app.services.oa.business_callbacks import BusinessCallbackRegistry
    registry = BusinessCallbackRegistry.instance()
    registry.register("room_booking", RoomBookingCallbackHandler)
    registry.register("asset_borrow", AssetBorrowCallbackHandler)

    # 2. 引擎自动调用（在 _on_instance_completed 中）
    handler = registry.get_handler("room_booking", db)
    await handler.on_approved(instance)
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.oa.workflow import OaWorkflowInstance

logger = logging.getLogger(__name__)


class BusinessCallbackHandler(ABC):
    """
    业务回调处理器抽象基类

    每种 business_type 继承此类并实现 on_approved / on_rejected。
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    @abstractmethod
    async def on_approved(self, instance: OaWorkflowInstance) -> None:
        """
        审批通过时回调

        Args:
            instance: 已完成的审批实例（status="APPROVED"）
                - instance.business_type: str  业务类型标识（如 "leave", "asset_borrow"）
                - instance.business_id: UUID   业务数据主键
                - instance.form_data: dict     审批时提交的表单数据
                - instance.initiator_id: UUID  发起人ID
        """
        ...

    @abstractmethod
    async def on_rejected(self, instance: OaWorkflowInstance) -> None:
        """
        审批拒绝时回调

        Args:
            instance: 已拒绝的审批实例（status="REJECTED"）
        """
        ...


class DefaultCallbackHandler(BusinessCallbackHandler):
    """
    默认回调处理器（无业务逻辑，仅记录日志）

    当 business_type 未注册对应处理器时使用。
    """

    async def on_approved(self, instance: OaWorkflowInstance) -> None:
        logger.info(
            "[WorkflowCallback] APPROVED: business_type=%s, business_id=%s",
            instance.business_type,
            instance.business_id,
        )

    async def on_rejected(self, instance: OaWorkflowInstance) -> None:
        logger.info(
            "[WorkflowCallback] REJECTED: business_type=%s, business_id=%s",
            instance.business_type,
            instance.business_id,
        )


class BusinessCallbackRegistry:
    """
    业务回调注册表（全局单例）

    线程安全（Python GIL 保证同一进程内）。
    多进程场景下每个进程维护自己的注册表，启动时各自注册。
    """

    _instance: Optional["BusinessCallbackRegistry"] = None
    _registry: Dict[str, Type[BusinessCallbackHandler]] = {}

    @classmethod
    def instance(cls) -> "BusinessCallbackRegistry":
        """获取全局单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(
        self,
        business_type: str,
        handler_class: Type[BusinessCallbackHandler],
    ) -> None:
        """
        注册业务回调处理器

        Args:
            business_type: 业务类型标识（如 "leave", "asset_borrow", "room_booking"）
            handler_class: 处理器类（必须是 BusinessCallbackHandler 的子类）
        """
        self._registry[business_type] = handler_class
        logger.debug("[WorkflowCallback] Registered handler for business_type=%s", business_type)

    def get_handler(
        self,
        business_type: str,
        db: AsyncSession,
    ) -> BusinessCallbackHandler:
        """
        获取业务回调处理器实例

        Args:
            business_type: 业务类型标识
            db: 数据库会话（传给处理器构造函数）

        Returns:
            处理器实例。若 business_type 未注册，返回 DefaultCallbackHandler。
        """
        handler_class = self._registry.get(business_type, DefaultCallbackHandler)
        return handler_class(db)

    def unregister(self, business_type: str) -> None:
        """注销指定业务类型的处理器（主要用于测试）"""
        self._registry.pop(business_type, None)

    @classmethod
    def reset(cls) -> None:
        """重置单例（主要用于测试隔离）"""
        cls._instance = None
        cls._registry = {}
