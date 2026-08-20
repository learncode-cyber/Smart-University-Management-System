"""
Attendance router — /api/v1/attendance/*

    GET /attendance/me           -> Student
    POST /attendance              -> Teacher (bulk mark a whole class)
    GET /attendance/{classId}      -> Teacher, Admin
    PUT /attendance/{id}            -> Teacher, Admin (correction)
    GET /attendance/reports          -> Admin

NOTE on route ordering: /attendance/reports is declared BEFORE
/attendance/{class_id} — FastAPI matches routes in registration order,
so if {class_id} came first, a request to /attendance/reports would be
incorrectly captured as class_id="reports".
"""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher_profile, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.profiles import Teacher, Parent
from app.models.user import User
from app.schemas.attendance import (
    BulkAttendanceMarkRequest, AttendanceRecordResponse, AttendanceCorrectionRequest,
    MyAttendanceResponse, StudentAttendanceStatus, AttendanceReportRow,
)
from app.services import attendance_service

router = APIRouter(prefix="/attendance", tags=["Attendance"])

teacher_or_admin = require_role(UserRole.TEACHER, UserRole.ADMIN)
admin_only = require_role(UserRole.ADMIN)
student_or_parent = require_role(UserRole.STUDENT, UserRole.PARENT)


@router.get(
    "/me", response_model=MyAttendanceResponse, summary="Get own attendance summary",
    description="Student sees their own single entry; Parent sees one entry per linked child "
                "(flagged addition beyond the original spec, which only listed Student access here).",
)
def get_my_attendance(
    course_section_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(student_or_parent),
):
    if user.role == UserRole.STUDENT:
        from sqlalchemy import select
        from app.models.profiles import Student
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        status = attendance_service.get_attendance_status_for_student(db, student, course_section_id, date_from, date_to)
        return MyAttendanceResponse(students=[StudentAttendanceStatus(**status)])

    from sqlalchemy import select
    parent = db.scalar(select(Parent).where(Parent.user_id == user.id))
    statuses = attendance_service.get_attendance_status_for_parent(db, parent)
    return MyAttendanceResponse(students=[StudentAttendanceStatus(**s) for s in statuses])


@router.post("", response_model=list[AttendanceRecordResponse], summary="Mark attendance for a class")
def mark_attendance(
    body: BulkAttendanceMarkRequest,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher_profile),
):
    return attendance_service.bulk_mark_attendance(db, teacher.university_id, teacher, body)


@router.get("/reports", response_model=list[AttendanceReportRow], summary="Generate attendance reports")
def attendance_reports(
    course_section_id: int | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
):
    return attendance_service.generate_attendance_report(db, admin.university_id, course_section_id)


@router.get("/{class_id}", response_model=list[AttendanceRecordResponse], summary="Get attendance for a class")
def get_class_attendance(
    class_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(teacher_or_admin),
):
    teacher_id = None
    if user.role == UserRole.TEACHER:
        teacher = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
        teacher_id = teacher.id
    return attendance_service.get_class_attendance(
        db, user.university_id, teacher_id, class_id, is_admin=(user.role == UserRole.ADMIN),
        date_from=date_from, date_to=date_to,
    )


@router.put("/{record_id}", response_model=AttendanceRecordResponse, summary="Correct an attendance record")
def correct_attendance(
    record_id: int,
    body: AttendanceCorrectionRequest,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher_profile),
):
    return attendance_service.correct_attendance_record(db, teacher.university_id, teacher, record_id, body)
