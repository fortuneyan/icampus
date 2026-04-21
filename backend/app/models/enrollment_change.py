from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class EnrollmentChange(Base):
    """学籍变动记录表"""
    __tablename__ = "enrollment_changes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    change_type = Column(String(20), nullable=False, index=True)

    from_grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=True)
    to_grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=True)

    from_class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)
    to_class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True)

    from_status = Column(String(20), nullable=True)
    to_status = Column(String(20), nullable=True)

    change_date = Column(DateTime, nullable=False)
    effective_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    operator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    student = relationship("Student", back_populates="enrollment_changes")
    to_grade = relationship("Grade", foreign_keys=[to_grade_id])
    to_class = relationship("Class", foreign_keys=[to_class_id])

    __table_args__ = (
        Index("idx_enrollment_changes_student_date", "student_id", "change_date"),
    )

    @property
    def change_type_name(self):
        type_names = {
            "enroll": "入学",
            "re_enroll": "重新入学",
            "promote": "升级",
            "repeat": "留级",
            "retry": "复读",
            "suspend": "休学",
            "resume": "复学",
            "graduate": "毕业",
            "incomplete": "肄业",
            "quit": "退学",
            "transfer": "转学",
            "class_change": "班级调整",
            "entry": "入学分班",
        }
        return type_names.get(self.change_type, self.change_type)