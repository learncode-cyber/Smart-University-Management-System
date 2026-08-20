"""
Schemas for /api/v1/exams/*.

Security-relevant detail: two different "question" response shapes.
`ExamQuestionTeacherView` includes `is_correct` on each MCQ option;
`ExamQuestionStudentView` strips it out entirely. The router decides
which one to return based on the caller's role — a student must never
be able to see the correct answer by reading the exam detail response,
even before they've submitted.
"""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ExamStatus, QuestionType, SubmissionStatus


# ---- Question / Option (input) ----

class ExamOptionCreate(BaseModel):
    option_text: str
    is_correct: bool = False


class ExamQuestionCreate(BaseModel):
    question_type: QuestionType
    question_text: str
    marks: int = Field(gt=0)
    order_index: int = 0
    starter_code: str | None = None       # coding questions only
    expected_output: str | None = None    # coding questions only
    options: list[ExamOptionCreate] = []  # required (>=2, exactly one is_correct) for MCQ, ignored otherwise


class ExamCreateRequest(BaseModel):
    course_section_id: int
    title: str = Field(max_length=255)
    description: str | None = None
    start_time: datetime
    end_time: datetime
    duration_minutes: int = Field(gt=0)
    questions: list[ExamQuestionCreate] = Field(min_length=1)


class ExamUpdateRequest(BaseModel):
    """Only allowed while exam.status == DRAFT — see service layer."""
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    questions: list[ExamQuestionCreate] | None = None  # if provided, REPLACES all questions


# ---- Question / Option (output) ----

class ExamOptionStudentView(BaseModel):
    id: int
    option_text: str
    # NOTE: is_correct deliberately omitted

    model_config = {"from_attributes": True}


class ExamOptionTeacherView(BaseModel):
    id: int
    option_text: str
    is_correct: bool

    model_config = {"from_attributes": True}


class ExamQuestionStudentView(BaseModel):
    id: int
    question_type: QuestionType
    question_text: str
    marks: int
    order_index: int
    starter_code: str | None
    options: list[ExamOptionStudentView]

    model_config = {"from_attributes": True}


class ExamQuestionTeacherView(BaseModel):
    id: int
    question_type: QuestionType
    question_text: str
    marks: int
    order_index: int
    starter_code: str | None
    expected_output: str | None
    options: list[ExamOptionTeacherView]

    model_config = {"from_attributes": True}


class ExamListItemResponse(BaseModel):
    id: int
    course_section_id: int
    title: str
    status: ExamStatus
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    total_marks: int

    model_config = {"from_attributes": True}


class ExamDetailStudentResponse(ExamListItemResponse):
    description: str | None
    questions: list[ExamQuestionStudentView]


class ExamDetailTeacherResponse(ExamListItemResponse):
    description: str | None
    questions: list[ExamQuestionTeacherView]


# ---- Submission ----

class ExamAnswerSubmit(BaseModel):
    question_id: int
    selected_option_id: int | None = None  # for MCQ
    answer_text: str | None = None          # for short_answer / descriptive / coding


class ExamSubmitRequest(BaseModel):
    answers: list[ExamAnswerSubmit]


class ExamAnswerResponse(BaseModel):
    question_id: int
    selected_option_id: int | None
    answer_text: str | None
    score: float | None
    feedback: str | None

    model_config = {"from_attributes": True}


class ExamSubmissionResponse(BaseModel):
    id: int
    exam_id: int
    student_id: int
    student_name: str
    status: SubmissionStatus
    started_at: datetime
    submitted_at: datetime | None
    total_score: float | None
    answers: list[ExamAnswerResponse]

    model_config = {"from_attributes": True}


# ---- Grading ----

class AnswerGradeInput(BaseModel):
    question_id: int
    score: float = Field(ge=0)
    feedback: str | None = None


class ExamGradeRequest(BaseModel):
    student_id: int
    grades: list[AnswerGradeInput]


class ExamResultsResponse(BaseModel):
    exam_id: int
    submissions: list[ExamSubmissionResponse]
