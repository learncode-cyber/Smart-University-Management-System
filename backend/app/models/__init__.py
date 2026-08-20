"""
Import every model module here so that `Base.metadata` is fully populated
before Alembic's `--autogenerate` (or `Base.metadata.create_all`) runs.
SQLAlchemy only registers a table when its module has been imported at
least once — forgetting an import here is the #1 cause of "why didn't my
migration pick up this new table" bugs.
"""
from app.db.base_class import Base  # noqa: F401

from app.models.university import University  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.auth import RefreshToken  # noqa: F401
from app.models.profiles import Student, Teacher, Admin, Parent, ParentStudentLink  # noqa: F401
from app.models.academic import Department, Course, CourseSection, Enrollment  # noqa: F401
from app.models.exam import (  # noqa: F401
    Exam, ExamQuestion, ExamOption, ExamSubmission, ExamAnswer,
)
from app.models.attendance import AttendanceRecord  # noqa: F401
from app.models.result import Result, SemesterGPA  # noqa: F401
from app.models.fee import FeeStructure, Invoice, FeePayment  # noqa: F401
from app.models.schedule import ClassSchedule  # noqa: F401
from app.models.notification import Notification  # noqa: F401

__all__ = [
    "Base",
    "University",
    "User",
    "RefreshToken",
    "Student", "Teacher", "Admin", "Parent", "ParentStudentLink",
    "Department", "Course", "CourseSection", "Enrollment",
    "Exam", "ExamQuestion", "ExamOption", "ExamSubmission", "ExamAnswer",
    "AttendanceRecord",
    "Result", "SemesterGPA",
    "FeeStructure", "Invoice", "FeePayment",
    "ClassSchedule",
    "Notification",
]
