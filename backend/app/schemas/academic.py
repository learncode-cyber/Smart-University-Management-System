"""
Schemas for the lightweight Academic Structure module — added beyond the
proposal's explicit endpoint list because Users/Exams/Attendance/Schedule
all need a department_id / course_section_id to attach to. Admin-only.
"""
from pydantic import BaseModel, Field


class DepartmentCreateRequest(BaseModel):
    name: str = Field(max_length=255)
    code: str = Field(max_length=20)


class DepartmentResponse(BaseModel):
    id: int
    name: str
    code: str

    model_config = {"from_attributes": True}


class CourseCreateRequest(BaseModel):
    department_id: int
    code: str = Field(max_length=20)
    title: str = Field(max_length=255)
    credit_hours: int = Field(default=3, ge=1, le=6)


class CourseResponse(BaseModel):
    id: int
    department_id: int
    code: str
    title: str
    credit_hours: int

    model_config = {"from_attributes": True}


class CourseSectionCreateRequest(BaseModel):
    course_id: int
    teacher_id: int
    section_name: str = Field(default="A", max_length=20)
    semester: str = Field(max_length=20)       # e.g. "Spring", "Fall"
    academic_year: str = Field(max_length=9)   # e.g. "2026-2027"


class CourseSectionResponse(BaseModel):
    id: int
    course_id: int
    course_code: str
    course_title: str
    teacher_id: int
    section_name: str
    semester: str
    academic_year: str


class EnrollmentCreateRequest(BaseModel):
    student_id: int
    course_section_id: int


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_section_id: int

    model_config = {"from_attributes": True}


class EnrolledStudentResponse(BaseModel):
    student_id: int
    full_name: str
    roll_number: str
