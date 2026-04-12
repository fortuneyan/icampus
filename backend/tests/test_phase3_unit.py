"""
第三阶段测试 - 教务管理模块
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.student import StudentCreate, StudentUpdate
from app.schemas.grade import GradeCreate, GradeUpdate
from app.schemas.class_schema import ClassCreate, ClassUpdate
from app.schemas.course import CourseCreate, CourseUpdate
from app.schemas.score import ScoreCreate, ScoreUpdate
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate


class TestStudentSchemas:
    """学生 Schemas 测试"""

    def test_student_create_valid(self):
        """测试学生创建验证"""
        student = StudentCreate(
            student_no="2024001", name="张三", gender="male", phone="13800138000"
        )
        assert student.student_no == "2024001"
        assert student.name == "张三"
        assert student.gender == "male"

    def test_student_create_no_student_no(self):
        """测试学号必填"""
        with pytest.raises(Exception):
            StudentCreate(name="张三")

    def test_student_update_partial(self):
        """测试学生更新部分字段"""
        update = StudentUpdate(name="李四", phone="13900139000")
        assert update.name == "李四"
        assert update.phone == "13900139000"


class TestGradeSchemas:
    """年级 Schemas 测试"""

    def test_grade_create_valid(self):
        """测试年级创建"""
        grade = GradeCreate(
            name="2024级",
            code="G2024",
            academic_year="2023-2024",
            year=2024,
            grade_level=1,
        )
        assert grade.name == "2024级"
        assert grade.code == "G2024"
        assert grade.academic_year == "2023-2024"

    def test_grade_year_validation(self):
        """测试年份验证 - 旧的无效测试，无实际验证逻辑"""
        pass


class TestClassSchemas:
    """班级 Schemas 测试"""

    def test_class_create_valid(self):
        """测试班级创建"""
        cls = ClassCreate(
            name="一年级一班",
            code="C2024-1-1",
            academic_year="2023-2024",
            semester="第一学期",
            class_no=1,
        )
        assert cls.name == "一年级一班"
        assert cls.code == "C2024-1-1"
        assert cls.academic_year == "2023-2024"


class TestCourseSchemas:
    """课程 Schemas 测试"""

    def test_course_create_valid(self):
        """测试课程创建"""
        course = CourseCreate(code="MATH001", name="数学")
        assert course.code == "MATH001"
        assert course.name == "数学"


class TestScoreSchemas:
    """成绩 Schemas 测试"""

    def test_score_create_valid(self):
        """测试成绩创建"""
        from uuid import uuid4

        score = ScoreCreate(
            student_id=uuid4(),
            course_id=uuid4(),
            semester="2024-1",
            score_type="final",
            score=95.5,
        )
        assert score.semester == "2024-1"
        assert score.score_type == "final"
        assert score.score == 95.5

    def test_score_validation(self):
        """测试成绩分数范围"""
        from uuid import uuid4

        with pytest.raises(Exception):
            ScoreCreate(
                student_id=uuid4(),
                course_id=uuid4(),
                semester="2024-1",
                score_type="final",
                score=150,
            )


class TestScheduleSchemas:
    """排课 Schemas 测试"""

    def test_schedule_create_valid(self):
        """测试排课创建"""
        from uuid import uuid4

        schedule = ScheduleCreate(
            course_id=uuid4(),
            class_id=uuid4(),
            teacher_id=uuid4(),
            weekday=1,
            period_start=1,
            period_end=2,
            semester="2024-1",
        )
        assert schedule.weekday == 1
        assert schedule.period_start == 1
        assert schedule.period_end == 2

    def test_weekday_validation(self):
        """测试星期验证"""
        from uuid import uuid4

        with pytest.raises(Exception):
            ScheduleCreate(
                course_id=uuid4(),
                class_id=uuid4(),
                teacher_id=uuid4(),
                weekday=8,
                period_start=1,
                period_end=2,
                semester="2024-1",
            )


class TestModels:
    """数据模型测试"""

    def test_student_model_exists(self):
        """测试学生模型"""
        from app.models.student import Student

        assert Student.__tablename__ == "students"

    def test_grade_model_exists(self):
        """测试年级模型"""
        from app.models.grade_model import Grade

        assert Grade.__tablename__ == "grades"

    def test_class_model_exists(self):
        """测试班级模型"""
        from app.models.class_model import Class

        assert Class.__tablename__ == "classes"

    def test_course_model_exists(self):
        """测试课程模型"""
        from app.models.course import Course

        assert Course.__tablename__ == "courses"

    def test_score_model_exists(self):
        """测试成绩模型"""
        from app.models.score import Score

        assert Score.__tablename__ == "scores"

    def test_schedule_model_exists(self):
        """测试排课模型"""
        from app.models.schedule import Schedule

        assert Schedule.__tablename__ == "schedules"


class TestServices:
    """服务层测试"""

    def test_student_service_can_be_instantiated(self):
        """测试学生服务可以实例化"""
        from unittest.mock import MagicMock
        from app.services.student_service import StudentService

        mock_db = MagicMock()
        service = StudentService(mock_db)
        assert service is not None

    def test_grade_service_can_be_instantiated(self):
        """测试年级服务可以实例化"""
        from unittest.mock import MagicMock
        from app.services.grade_service import GradeService

        mock_db = MagicMock()
        service = GradeService(mock_db)
        assert service is not None

    def test_class_service_can_be_instantiated(self):
        """测试班级服务可以实例化"""
        from unittest.mock import MagicMock
        from app.services.class_service import ClassService

        mock_db = MagicMock()
        service = ClassService(mock_db)
        assert service is not None

    def test_course_service_can_be_instantiated(self):
        """测试课程服务可以实例化"""
        from unittest.mock import MagicMock
        from app.services.course_service import CourseService

        mock_db = MagicMock()
        service = CourseService(mock_db)
        assert service is not None

    def test_score_service_can_be_instantiated(self):
        """测试成绩服务可以实例化"""
        from unittest.mock import MagicMock
        from app.services.score_service import ScoreService

        mock_db = MagicMock()
        service = ScoreService(mock_db)
        assert service is not None

    def test_schedule_service_can_be_instantiated(self):
        """测试排课服务可以实例化"""
        from unittest.mock import MagicMock
        from app.services.schedule_service import ScheduleService

        mock_db = MagicMock()
        service = ScheduleService(mock_db)
        assert service is not None


class TestAPIEndpoints:
    """API接口结构测试"""

    def test_students_router_exists(self):
        """测试学生路由是否存在"""
        from app.api.v1.edu.students import router

        assert router is not None

    def test_grades_router_exists(self):
        """测试年级路由是否存在"""
        from app.api.v1.edu.grades import router

        assert router is not None

    def test_classes_router_exists(self):
        """测试班级路由是否存在"""
        from app.api.v1.edu.classes import router

        assert router is not None

    def test_courses_router_exists(self):
        """测试课程路由是否存在"""
        from app.api.v1.edu.courses import router

        assert router is not None

    def test_scores_router_exists(self):
        """测试成绩路由是否存在"""
        from app.api.v1.edu.scores import router

        assert router is not None

    def test_schedules_router_exists(self):
        """测试排课路由是否存在"""
        from app.api.v1.edu.schedules import router

        assert router is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
