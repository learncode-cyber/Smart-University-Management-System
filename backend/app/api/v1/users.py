"""
Users & Profiles router — /api/v1/users/*

Access matrix (exact match to proposal Section 6, NOT the simplified
description in the master build prompt — see the flagged discrepancy):
    GET/PUT /users/me                  -> any authenticated role
    GET     /users/students            -> Admin, Teacher
    POST    /users/students            -> Admin
    GET     /users/students/{id}       -> Admin, Teacher
    PUT     /users/students/{id}       -> Admin
    DELETE  /users/students/{id}       -> Admin (soft-delete/deactivate)
    GET     /users/teachers            -> Admin
    POST    /users/teachers            -> Admin
    PUT     /users/teachers/{id}       -> Admin
    (no GET /users/teachers/{id}, no DELETE /users/teachers/{id} — proposal
     genuinely doesn't define these; flagged in Part 3 design discussion)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.profiles import Student, Teacher
from app.models.user import User
from app.schemas.user import (
    UserMeResponse, UserMeUpdateRequest,
    StudentCreateRequest, StudentUpdateRequest, StudentResponse,
    TeacherCreateRequest, TeacherUpdateRequest, TeacherResponse,
)
from app.schemas.auth import MessageResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users & Profiles"])

admin_only = require_role(UserRole.ADMIN)
admin_or_teacher = require_role(UserRole.ADMIN, UserRole.TEACHER)


def _student_response(student: Student) -> StudentResponse:
    return StudentResponse(
        id=student.id, user_id=student.user_id, email=student.user.email,
        is_active=student.user.is_active, department_id=student.department_id,
        roll_number=student.roll_number, full_name=student.full_name,
        date_of_birth=student.date_of_birth, phone=student.phone, address=student.address,
        enrollment_year=student.enrollment_year, current_semester=student.current_semester,
    )


def _teacher_response(teacher: Teacher) -> TeacherResponse:
    return TeacherResponse(
        id=teacher.id, user_id=teacher.user_id, email=teacher.user.email,
        is_active=teacher.user.is_active, department_id=teacher.department_id,
        employee_id=teacher.employee_id, full_name=teacher.full_name,
        designation=teacher.designation, phone=teacher.phone, joined_at=teacher.joined_at,
    )


# ---- own profile (any role) ----

@router.get("/me", response_model=UserMeResponse, summary="Get own profile")
def get_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return user_service.get_own_profile_merged(db, current_user)


@router.put(
    "/me", response_model=UserMeResponse, summary="Update own profile",
    description="Editable here: email, full name, phone, address, profile photo. "
                "NOT editable here: roll number, department, employee ID — those remain "
                "Admin-only via /users/students/{id} or /users/teachers/{id}.",
)
def update_me(
    body: UserMeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.update_own_profile(db, current_user, body)


# ---- students ----

@router.get("/students", response_model=list[StudentResponse], summary="List all students")
def list_students(
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db), user: User = Depends(admin_or_teacher),
):
    students = user_service.list_students(db, user.university_id, skip, limit)
    return [_student_response(s) for s in students]


@router.post("/students", response_model=StudentResponse, summary="Create student account")
def create_student(
    body: StudentCreateRequest, db: Session = Depends(get_db), admin: User = Depends(admin_only)
):
    student = user_service.create_student(db, admin.university_id, body)
    return _student_response(student)


@router.get("/students/{student_id}", response_model=StudentResponse, summary="Get single student")
def get_student(
    student_id: int, db: Session = Depends(get_db), user: User = Depends(admin_or_teacher)
):
    student = user_service.get_student(db, user.university_id, student_id)
    return _student_response(student)


@router.put("/students/{student_id}", response_model=StudentResponse, summary="Update student")
def update_student(
    student_id: int, body: StudentUpdateRequest,
    db: Session = Depends(get_db), admin: User = Depends(admin_only),
):
    student = user_service.update_student(db, admin.university_id, student_id, body)
    return _student_response(student)


@router.delete("/students/{student_id}", response_model=MessageResponse, summary="Deactivate student account")
def deactivate_student(
    student_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_only)
):
    user_service.deactivate_student(db, admin.university_id, student_id)
    return MessageResponse(message="Student account deactivated.")


# ---- teachers ----

@router.get("/teachers", response_model=list[TeacherResponse], summary="List all teachers")
def list_teachers(
    skip: int = 0, limit: int = 50, db: Session = Depends(get_db), admin: User = Depends(admin_only)
):
    teachers = user_service.list_teachers(db, admin.university_id, skip, limit)
    return [_teacher_response(t) for t in teachers]


@router.post("/teachers", response_model=TeacherResponse, summary="Create teacher account")
def create_teacher(
    body: TeacherCreateRequest, db: Session = Depends(get_db), admin: User = Depends(admin_only)
):
    teacher = user_service.create_teacher(db, admin.university_id, body)
    return _teacher_response(teacher)


@router.put("/teachers/{teacher_id}", response_model=TeacherResponse, summary="Update teacher")
def update_teacher(
    teacher_id: int, body: TeacherUpdateRequest,
    db: Session = Depends(get_db), admin: User = Depends(admin_only),
):
    teacher = user_service.update_teacher(db, admin.university_id, teacher_id, body)
    return _teacher_response(teacher)
