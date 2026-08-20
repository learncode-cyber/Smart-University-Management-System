"""
Results & Transcripts router — /api/v1/results/*

    GET  /results/me                          -> Student
    POST /results/{examId}/submit              -> Teacher
    POST /results/{id}/approve                  -> Admin
    GET  /results/{studentId}/transcript          -> Student, Admin
"""
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher_profile, require_role, get_current_user
from app.core.errors import insufficient_permissions
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.profiles import Admin, Parent, Student, Teacher
from app.models.user import User
from app.schemas.result import (
    ResultSubmitRequest, ResultApproveRequest, ResultResponse, MyResultsResponse, StudentResultsStatus,
    PendingResultResponse,
)
from app.services import result_service

router = APIRouter(prefix="/results", tags=["Results & Transcripts"])

admin_only = require_role(UserRole.ADMIN)
student_or_parent = require_role(UserRole.STUDENT, UserRole.PARENT)


@router.get(
    "/pending", response_model=list[PendingResultResponse], summary="List results awaiting admin approval",
    description="Flagged addition beyond the original spec — needed to actually operate the "
                "teacher-submits / admin-approves workflow described in the proposal.",
)
def list_pending_results(db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    return result_service.list_pending_results(db, admin.university_id)


@router.get(
    "/me", response_model=MyResultsResponse, summary="Get own results (all semesters)",
    description="Student sees their own single entry; Parent sees one entry per linked child "
                "(flagged addition beyond the original spec, which only listed Student access here).",
)
def get_my_results(db: Session = Depends(get_db), user: User = Depends(student_or_parent)):
    if user.role == UserRole.STUDENT:
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        status = result_service.get_results_status_for_student(db, student)
        return MyResultsResponse(students=[StudentResultsStatus(**status)])

    parent = db.scalar(select(Parent).where(Parent.user_id == user.id))
    statuses = result_service.get_results_status_for_parent(db, parent)
    return MyResultsResponse(students=[StudentResultsStatus(**s) for s in statuses])


@router.post("/{exam_id}/submit", response_model=ResultResponse, summary="Teacher submits results for approval")
def submit_result(
    exam_id: int, body: ResultSubmitRequest,
    db: Session = Depends(get_db), teacher: Teacher = Depends(get_current_teacher_profile),
):
    return result_service.submit_result(db, teacher.university_id, teacher, exam_id, body.student_id)


@router.post("/{result_id}/approve", response_model=ResultResponse, summary="Admin approves and publishes results")
def approve_result(
    result_id: int, body: ResultApproveRequest,
    db: Session = Depends(get_db), user: User = Depends(admin_only),
):
    admin = db.scalar(select(Admin).where(Admin.user_id == user.id))
    return result_service.approve_or_reject_result(
        db, user.university_id, admin, result_id, body.approved, body.rejection_reason
    )


@router.get("/{student_id}/transcript", summary="Download transcript as PDF")
def download_transcript(
    student_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    # access rule: a student may only download their OWN transcript;
    # admin may download anyone's within their university
    if user.role == UserRole.STUDENT:
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if student is None or student.id != student_id:
            raise insufficient_permissions()
    elif user.role != UserRole.ADMIN:
        raise insufficient_permissions()

    pdf_bytes = result_service.generate_transcript(db, user.university_id, student_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="transcript_{student_id}.pdf"'},
    )
