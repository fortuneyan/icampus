from fastapi import APIRouter
from app.api.v1.edu import (
    students,
    grades,
    classes,
    courses,
    scores,
    schedules,
    classrooms,
    student_profiles,
    quality_records,
    teaching_plans,
    lesson_plans,
    research,
    scheduling,
)

router = APIRouter()

router.include_router(students.router, prefix="/students", tags=["学生管理"])
router.include_router(grades.router, prefix="/grades", tags=["年级管理"])
router.include_router(classes.router, prefix="/classes", tags=["班级管理"])
router.include_router(courses.router, prefix="/courses", tags=["课程管理"])
router.include_router(scores.router, prefix="/scores", tags=["成绩管理"])
router.include_router(schedules.router, prefix="/schedules", tags=["排课管理"])
router.include_router(scheduling.router, prefix="/scheduling", tags=["智能排课"])
router.include_router(classrooms.router, prefix="/classrooms", tags=["教室管理"])
router.include_router(
    student_profiles.router, prefix="/student-profiles", tags=["学生扩展信息"]
)
router.include_router(
    quality_records.router, prefix="/quality-records", tags=["综合素质评价"]
)
router.include_router(
    teaching_plans.router, prefix="/teaching-plans", tags=["教学计划"]
)
router.include_router(lesson_plans.router, prefix="/lesson-plans", tags=["教案管理"])
router.include_router(research.router, prefix="/research-projects", tags=["教研课题"])
