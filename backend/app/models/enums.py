"""
Centralized enum definitions for the University Management System.

Why one file for all enums?
- Every enum here maps 1:1 to a PostgreSQL native ENUM type (via SQLAlchemy's
  `Enum` construct). Keeping them together makes it trivial to see every
  fixed-vocabulary field in the system at a glance, and avoids circular
  imports between model files that would otherwise need to import enums
  from each other.
- Using native Postgres enums (instead of plain strings / CHECK constraints)
  means invalid values are rejected at the database layer too, not just by
  Pydantic — defense in depth.
"""
import enum


class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    PARENT = "parent"


class ParentRelationship(str, enum.Enum):
    FATHER = "father"
    MOTHER = "mother"
    GUARDIAN = "guardian"
    OTHER = "other"


class QuestionType(str, enum.Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    DESCRIPTIVE = "descriptive"
    CODING = "coding"


class ExamStatus(str, enum.Enum):
    DRAFT = "draft"          # being built by teacher, not visible to students
    SCHEDULED = "scheduled"  # published with a future start_time
    OPEN = "open"            # currently within [start_time, end_time], students can submit
    CLOSED = "closed"        # end_time has passed, awaiting grading
    GRADED = "grading_done"  # all submissions graded, not yet visible as "results"
    PUBLISHED = "published"  # results released to students/parents


class SubmissionStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"  # student has started but not submitted
    SUBMITTED = "submitted"      # submitted, awaiting/undergoing grading
    GRADED = "graded"            # fully graded


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class ResultStatus(str, enum.Enum):
    DRAFT = "draft"          # teacher still working on it
    SUBMITTED = "submitted"  # teacher submitted, awaiting admin approval
    APPROVED = "approved"    # admin approved, not yet published
    PUBLISHED = "published"  # visible to student/parent
    REJECTED = "rejected"    # admin sent back to teacher with changes requested


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    WAIVED = "waived"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_BANKING = "mobile_banking"
    CARD = "card"
    OTHER = "other"


class DayOfWeek(str, enum.Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class NotificationType(str, enum.Enum):
    EXAM_PUBLISHED = "exam_published"
    RESULT_PUBLISHED = "result_published"
    ATTENDANCE_WARNING = "attendance_warning"
    FEE_DUE = "fee_due"
    FEE_OVERDUE = "fee_overdue"
    SCHEDULE_CHANGE = "schedule_change"
    GENERAL = "general"
