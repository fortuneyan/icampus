from app.models.user import User
from app.models.department import Department
from app.models.role import Role, Permission, Menu
from app.models.student import Student
from app.models.grade_model import Grade
from app.models.class_model import Class
from app.models.course import Course
from app.models.score import Score
from app.models.schedule import Schedule, Classroom
from app.models.student_profile import StudentProfile
from app.models.teacher_profile import TeacherProfile
from app.models.operation_log import OperationLog
from app.models.login_log import LoginLog
from app.models.data_access_log import DataAccessLog
from app.models.quality import QualityRecord
from app.models.teaching_plan import TeachingPlan
from app.models.resource_favorite import ResourceFavorite
from app.models.lesson_plan import LessonPlan
from app.models.research import ResearchProject
from app.models.message_subscription import MessageSubscription
from app.models.notification import Notification
from app.models.notification_read import NotificationRead
from app.models.leave import LeaveRequest, LeaveQuota
from app.models.recruitment import RecruitmentPlan, Applicant, ApplicantFollowUp
from app.models.region import Region
from app.models.encryption_key import EncryptionKey
from app.models.recommendation import Recommendation
from app.models.learning_record import LearningRecord
from app.models.question import Question, QuestionAnnotation, SimilarityCheckRecord
from app.models.quality_score import (
    QuestionQualityScore, 
    QualityReviewRecord, 
    QualityEvaluationPrompt,
    QualityLevel,
    ApprovalSuggestion,
    ReviewPriority,
    EvaluationMode,
)
from app.models.paper import Paper, PaperQuestion, PaperVersion
from app.models.teaching_progress import TeachingProgress, ProgressUpdate, ProgressReport
from app.models.textbook import Textbook, TextbookAdoption
from app.models.attendance_rule import AttendanceRule
from app.models.attendance import AttendanceRecord
from app.models.dashboard import ReportConfig, Message, SystemSetting
from app.models.card import CampusCard, CardTransaction, AccessRecord, Merchant
from app.models.dormitory import Dormitory, DormitoryRoom, DormitoryAssignment, DormitoryAttendance
from app.models.scholarship import Scholarship, ScholarshipApplication, GrantRecord, PoorStudent
from app.models.notice import Notice, NoticeRead
from app.models.homework import Homework, HomeworkSubmission, WrongQuestion, HomeworkFeedback, HomeworkNotification
from app.models.enrollment_change import EnrollmentChange

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
    "StudentProfile",
    "TeacherProfile",
    "OperationLog",
    "LoginLog",
    "DataAccessLog",
    "QualityRecord",
    "TeachingPlan",
    "ResourceFavorite",
    "LessonPlan",
    "ResearchProject",
    "MessageSubscription",
    "Region",
    "EncryptionKey",
    "Recommendation",
    "LearningRecord",
    "Question",
    "QuestionAnnotation",
    "SimilarityCheckRecord",
    "QuestionQualityScore",
    "QualityReviewRecord",
    "QualityEvaluationPrompt",
    "QualityLevel",
    "ApprovalSuggestion",
    "ReviewPriority",
    "EvaluationMode",
    "Paper",
    "PaperQuestion",
    "PaperVersion",
    "TeachingProgress",
    "ProgressUpdate",
    "ProgressReport",
    "Textbook",
    "TextbookAdoption",
    "AttendanceRule",
    "AttendanceRecord",
    "ReportConfig",
    "Message",
    "SystemSetting",
    "CampusCard",
    "CardTransaction",
    "AccessRecord",
    "Merchant",
    "Dormitory",
    "DormitoryRoom",
    "DormitoryAssignment",
    "DormitoryAttendance",
    "Scholarship",
    "ScholarshipApplication",
    "GrantRecord",
    "PoorStudent",
    "Notice",
    "NoticeRead",
    "EnrollmentChange",
]
