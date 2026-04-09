from app.models.user import User
from app.models.department import Department
from app.models.role import Role, Permission, Menu
from app.models.student import Student
from app.models.grade_model import Grade
from app.models.class_model import Class
from app.models.course import Course
from app.models.score import Score
from app.models.schedule import Schedule, Classroom

__all__ = [
    "User",
    "Department",
    "Role",
    "Permission",
    "Menu",
    "Student",
    "Grade",
    "Class",
    "Course",
    "Score",
    "Schedule",
    "Classroom",
]
