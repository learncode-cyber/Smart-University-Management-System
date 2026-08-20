"""
Academic Structure router — /api/v1/academic/*

Admin-only. Not part of the original proposal spec (Section 6 has no
endpoints for this) — added because exams/attendance/results/schedule all
reference course_section_id, and course_sections need departments/courses/
teachers to exist first. Flagged to the client in Part 1 & 3 discussion.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.errors import insufficient_permissions
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.academic import (
    DepartmentCreateRequest, DepartmentResponse,
    CourseCreateRequest, CourseResponse,
    CourseSectionCreateRequest, CourseSectionResponse,
    EnrollmentCreateRequest, EnrollmentResponse, EnrolledStudentResponse,
)
from app.services import academic_service

router = APIRouter(prefix="/academic", tags=["Academic Structure (Admin)"])

admin_only = require_role(UserRole.ADMIN)


@router.post("/departments", response_model=DepartmentResponse, summary="Create a department")
def create_department(
    body: DepartmentCreateRequest, db: Session = Depends(get_db), admin: User = Depends(admin_only)
):
    return academic_service.create_department(db, admin.university_id, body.name, body.code)


@router.get("/departments", response_model=list[DepartmentResponse], summary="List departments")
def list_departments(db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    return academic_service.list_departments(db, admin.university_id)


@router.post("/courses", response_model=CourseResponse, summary="Create a course")
def create_course(
    body: CourseCreateRequest, db: Session = Depends(get_db), admin: User = Depends(admin_only)
):
    return academic_service.create_course(
        db, admin.university_id, body.department_id, body.code, body.title, body.credit_hours
    )


@router.get("/courses", response_model=list[CourseResponse], summary="List courses")
def list_courses(
    department_id: int | None = None, db: Session = Depends(get_db), admin: User = Depends(admin_only)
):
    return academic_service.list_courses(db, admin.university_id, department_id)


@router.post(
    "/course-sections", response_model=CourseSectionResponse,
    summary="Create a course section (a specific class taught by a teacher this semester)",
)
def create_course_section(
    body: CourseSectionCreateRequest, db: Session = Depends(get_db), admin: User = Depends(admin_only)
):
    return academic_service.create_course_section(
        db, admin.university_id, body.course_id, body.teacher_id,
        body.section_name, body.semester, body.academic_year,
    )


@router.get(
    "/course-sections", response_model=list[CourseSectionResponse], summary="List course sections",
    description="Admin: all sections (optionally filtered by teacher_id). Teacher: only their own "
                "sections — flagged addition, needed so a teacher can discover their own "
                "course_section_id when building an exam or marking attendance.",
)
def list_course_sections(
    teacher_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    if user.role == UserRole.TEACHER:
        from sqlalchemy import select
        from app.models.profiles import Teacher
        teacher = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
        return academic_service.list_course_sections(db, user.university_id, teacher.id)
    return academic_service.list_course_sections(db, user.university_id, teacher_id)


@router.post(
    "/enrollments", response_model=EnrollmentResponse,
    summary="Enroll a student into a course section",
)
def create_enrollment(
    body: EnrollmentCreateRequest, db: Session = Depends(get_db), admin: User = Depends(admin_only)
):
    return academic_service.create_enrollment(db, admin.university_id, body.student_id, body.course_section_id)


@router.get(
    "/course-sections/{course_section_id}/students", response_model=list[EnrolledStudentResponse],
    summary="List students enrolled in a course section (class roster)",
    description="Flagged addition — needed for the Teacher Attendance Marker screen. "
                "Admin: any section. Teacher: only sections they teach.",
)
def list_enrolled_students(
    course_section_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    if user.role == UserRole.TEACHER:
        from sqlalchemy import select
        from app.models.profiles import Teacher
        from app.models.academic import CourseSection
        teacher = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
        section = db.get(CourseSection, course_section_id)
        if section is None or section.teacher_id != teacher.id:
            raise insufficient_permissions()
    return academic_service.list_enrolled_students(db, user.university_id, course_section_id)
