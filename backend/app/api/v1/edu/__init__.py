from fastapi import APIRouter
from app.api.v1.edu import students, grades, classes, courses, scores, schedules

router = APIRouter()

router.include_router(students.router, prefix="/students", tags=["学生管理"])
router.include_router(grades.router, prefix="/grades", tags=["年级管理"])
router.include_router(classes.router, prefix="/classes", tags=["班级管理"])
router.include_router(courses.router, prefix="/courses", tags=["课程管理"])
router.include_router(scores.router, prefix="/scores", tags=["成绩管理"])
router.include_router(schedules.router, prefix="/schedules", tags=["排课管理"])
