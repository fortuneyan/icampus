"""
考勤规则数据模型
"""
from datetime import datetime, time
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Text, DateTime, Time
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class AttendanceRule(Base):
    """
    考勤规则模型
    
    用于管理系统中的考勤规则，包括学生和教师的考勤时间设置。
    """
    __tablename__ = "attendance_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="规则名称")
    rule_type = Column(String(20), nullable=False, comment="规则类型: student/teacher")
    description = Column(Text, nullable=True, comment="规则描述")
    
    # 签到时间
    check_in_start = Column(Time, nullable=False, comment="签到开始时间")
    check_in_end = Column(Time, nullable=False, comment="签到结束时间")
    
    # 签退时间
    check_out_start = Column(Time, nullable=False, comment="签退开始时间")
    check_out_end = Column(Time, nullable=False, comment="签退结束时间")
    
    # 阈值设置
    late_threshold = Column(Integer, default=0, comment="迟到阈值(分钟)")
    early_leave_threshold = Column(Integer, default=0, comment="早退阈值(分钟)")
    absent_threshold = Column(Integer, default=0, comment="旷课阈值(分钟)")
    grace_period = Column(Integer, default=5, comment="宽限期(分钟)")
    
    # 状态
    status = Column(String(20), default="active", comment="状态: active/inactive")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<AttendanceRule(id={self.id}, name={self.name}, type={self.rule_type})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": str(self.id),
            "name": self.name,
            "rule_type": self.rule_type,
            "description": self.description,
            "check_in_start": self.check_in_start.strftime("%H:%M:%S") if self.check_in_start else None,
            "check_in_end": self.check_in_end.strftime("%H:%M:%S") if self.check_in_end else None,
            "check_out_start": self.check_out_start.strftime("%H:%M:%S") if self.check_out_start else None,
            "check_out_end": self.check_out_end.strftime("%H:%M:%S") if self.check_out_end else None,
            "late_threshold": self.late_threshold,
            "early_leave_threshold": self.early_leave_threshold,
            "absent_threshold": self.absent_threshold,
            "grace_period": self.grace_period,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
