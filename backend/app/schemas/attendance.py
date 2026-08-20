from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import AttendanceStatus


class BulkAttendanceEntry(BaseModel):
    student_id: int
    status: AttendanceStatus


class BulkAttendanceMarkRequest(BaseModel):
    course_section_id: int
    date: date
    entries: list[BulkAttendanceEntry] = Field(min_length=1)


class AttendanceRecordResponse(BaseModel):
    id: int
    course_section_id: int
    student_id: int
    date: date
    status: AttendanceStatus
    marked_by_teacher_id: int
    corrected_by_teacher_id: int | None
    corrected_at: datetime | None
    correction_reason: str | None

    model_config = {"from_attributes": True}


class AttendanceCorrectionRequest(BaseModel):
    status: AttendanceStatus
    correction_reason: str = Field(min_length=1, max_length=500)


class CourseSectionAttendanceSummary(BaseModel):
    course_section_id: int
    total_classes: int
    present_count: int
    percentage: float
    is_below_threshold: bool


class StudentAttendanceStatus(BaseModel):
    student_id: int
    student_name: str
    summaries: list[CourseSectionAttendanceSummary]
    records: list[AttendanceRecordResponse] = []


class MyAttendanceResponse(BaseModel):
    """
    Unified shape for both Student and Parent callers — a Student always
    gets exactly one entry in `students` (themselves); a Parent gets one
    entry per linked child. This mirrors the /fees/me response shape
    (Part 7) for consistency across "my ..." endpoints that Parent can
    also call.
    """
    students: list[StudentAttendanceStatus]


class AttendanceReportRow(BaseModel):
    student_id: int
    student_name: str
    course_section_id: int
    total_classes: int
    present_count: int
    percentage: float
    is_below_threshold: bool
