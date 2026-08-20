from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ResultStatus


class ResultSubmitRequest(BaseModel):
    """Submitted by the teacher for one student, based on a graded exam.
    See the Part 6 design note: in this build phase, one exam == one
    course_section's final assessment (no multi-exam aggregation yet)."""
    student_id: int


class ResultApproveRequest(BaseModel):
    approved: bool
    rejection_reason: str | None = Field(default=None, max_length=1000)


class ResultResponse(BaseModel):
    id: int
    student_id: int
    course_section_id: int
    course_code: str
    course_title: str
    semester: str
    academic_year: str
    total_marks_obtained: float
    total_marks_possible: float
    grade_letter: str | None
    grade_point: float | None
    status: ResultStatus
    submitted_at: datetime | None
    approved_at: datetime | None
    published_at: datetime | None
    rejection_reason: str | None

    model_config = {"from_attributes": True}


class StudentResultsStatus(BaseModel):
    student_id: int
    student_name: str
    results: list[ResultResponse]
    cumulative_gpa: float | None


class PendingResultResponse(ResultResponse):
    """ResultResponse + the student's name, so the admin approval queue
    doesn't need a second lookup per row. Added because the proposal's
    Admin 'Result approval' feature needs a queue to review, but Section
    6 never defined a listing endpoint for it — flagged addition."""
    student_name: str


class MyResultsResponse(BaseModel):
    """Unified shape: Student gets one entry (themselves); Parent gets
    one entry per linked child — same pattern as attendance/fees."""
    students: list[StudentResultsStatus]
