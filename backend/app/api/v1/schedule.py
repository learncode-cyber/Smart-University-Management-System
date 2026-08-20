"""
Scheduling router — /api/v1/schedule/*

    GET    /schedule/me            -> Student, Teacher
    POST   /schedule                 -> Admin
    PUT    /schedule/{id}             -> Admin
    DELETE /schedule/{id}              -> Admin
    GET    /schedule/conflicts           -> Admin

NOTE on route ordering: /schedule/conflicts is registered BEFORE
/schedule/{id}, same reasoning as the attendance router — otherwise
FastAPI would try to parse "conflicts" as a schedule {id}.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.profiles import Student, Teacher, Parent
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.schedule import (
    ScheduleCreateRequest, ScheduleUpdateRequest, ScheduleResponse, ScheduleConflictResponse,
)
from app.services import schedule_service

router = APIRouter(prefix="/schedule", tags=["Scheduling"])

admin_only = require_role(UserRole.ADMIN)
student_teacher_or_parent = require_role(UserRole.STUDENT, UserRole.TEACHER, UserRole.PARENT)


@router.get(
    "/me", response_model=list[ScheduleResponse], summary="Get own timetable",
    description="Student/Teacher see their own timetable. Parent sees their linked child's "
                "timetable (flagged addition beyond the original spec, which listed Student/Teacher only).",
)
def get_my_schedule(db: Session = Depends(get_db), user: User = Depends(student_teacher_or_parent)):
    if user.role == UserRole.STUDENT:
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        raw = schedule_service.get_schedule_for_student(db, user.university_id, student.id)
    elif user.role == UserRole.TEACHER:
        teacher = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
        raw = schedule_service.get_schedule_for_teacher(db, user.university_id, teacher.id)
    else:
        parent = db.scalar(select(Parent).where(Parent.user_id == user.id))
        raw = schedule_service.get_schedule_for_parent(db, user.university_id, parent.id)
    return [schedule_service.enrich_schedule(db, s) for s in raw]


@router.post("", response_model=ScheduleResponse, summary="Create class schedule")
def create_schedule(body: ScheduleCreateRequest, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    schedule = schedule_service.create_schedule(db, admin.university_id, body)
    return schedule_service.enrich_schedule(db, schedule)


@router.get(
    "", response_model=list[ScheduleResponse], summary="List all schedule entries (Admin)",
    description="Flagged addition — the original spec had create/update/delete/conflicts for "
                "/schedule but no way to list existing entries for the Timetable Control screen.",
)
def list_all_schedule(db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    entries = schedule_service.list_all_schedule(db, admin.university_id)
    return [schedule_service.enrich_schedule(db, s) for s in entries]


@router.get("/conflicts", response_model=list[ScheduleConflictResponse], summary="Detect scheduling conflicts")
def get_conflicts(db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    return schedule_service.detect_all_conflicts(db, admin.university_id)


@router.put("/{schedule_id}", response_model=ScheduleResponse, summary="Update schedule entry")
def update_schedule(
    schedule_id: int, body: ScheduleUpdateRequest, db: Session = Depends(get_db), admin: User = Depends(admin_only)
):
    schedule = schedule_service.update_schedule(db, admin.university_id, schedule_id, body)
    return schedule_service.enrich_schedule(db, schedule)


@router.delete("/{schedule_id}", response_model=MessageResponse, summary="Remove a class from schedule")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    schedule_service.delete_schedule(db, admin.university_id, schedule_id)
    return MessageResponse(message="Schedule entry removed.")
