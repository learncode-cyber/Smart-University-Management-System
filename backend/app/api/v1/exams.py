"""
Exams & Grading router — /api/v1/exams/*

    GET    /exams                -> all roles, filtered by role
    POST   /exams                -> Teacher
    GET    /exams/{id}           -> all roles (question view differs: student
                                     never sees is_correct on MCQ options)
    PUT    /exams/{id}           -> Teacher (own exam, DRAFT only)
    DELETE /exams/{id}           -> Teacher, Admin (unpublished only)
    POST   /exams/{id}/submit    -> Student
    POST   /exams/{id}/grade     -> Teacher
    GET    /exams/{id}/results   -> Teacher, Admin
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_student_profile, get_current_teacher_profile, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.profiles import Student, Teacher
from app.models.user import User
from app.schemas.exam import (
    ExamCreateRequest, ExamUpdateRequest, ExamListItemResponse,
    ExamDetailStudentResponse, ExamDetailTeacherResponse,
    ExamSubmitRequest, ExamSubmissionResponse, ExamGradeRequest, ExamResultsResponse,
)
from app.schemas.auth import MessageResponse
from app.services import exam_service

router = APIRouter(prefix="/exams", tags=["Exams & Grading"])

teacher_only = require_role(UserRole.TEACHER)
teacher_or_admin = require_role(UserRole.TEACHER, UserRole.ADMIN)


def _teacher_profile_for(db: Session, user: User) -> Teacher | None:
    if user.role != UserRole.TEACHER:
        return None
    return db.scalar(select(Teacher).where(Teacher.user_id == user.id))


@router.get("", response_model=list[ExamListItemResponse], summary="List exams (filtered by role)")
def list_exams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == UserRole.STUDENT:
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        return exam_service.list_exams_for_student(db, user.university_id, student)
    if user.role == UserRole.TEACHER:
        teacher = _teacher_profile_for(db, user)
        return exam_service.list_exams_for_teacher(db, user.university_id, teacher)
    if user.role == UserRole.ADMIN:
        return exam_service.list_exams_for_admin(db, user.university_id)
    # UserRole.PARENT: the proposal says "GET /exams -> All roles" but doesn't
    # define what a parent should see. Falling through to the admin branch
    # here would be a real data-scope bug (a parent seeing every exam
    # university-wide, not just their child's) — flagged rather than
    # silently allowed. Returning an empty list until a "child's exams"
    # scoping rule is confirmed.
    return []


@router.post("", response_model=ExamDetailTeacherResponse, summary="Create new exam")
def create_exam(
    body: ExamCreateRequest, db: Session = Depends(get_db), teacher: Teacher = Depends(get_current_teacher_profile)
):
    return exam_service.create_exam(db, teacher.university_id, teacher, body)


@router.get(
    "/{exam_id}",
    summary="Get exam details and questions",
    description="Students never see `is_correct` on MCQ options in this response, "
                "even before submitting — that field is stripped entirely, not just hidden by the frontend.",
)
def get_exam(exam_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    exam = exam_service.get_exam_for_viewing(db, user.university_id, exam_id)

    if user.role == UserRole.STUDENT:
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        exam_service.assert_student_enrolled(db, student, exam.course_section_id)
        return ExamDetailStudentResponse.model_validate(exam)

    if user.role == UserRole.TEACHER:
        teacher = _teacher_profile_for(db, user)
        if exam.created_by_teacher_id != teacher.id:
            # a teacher who does NOT own this exam still shouldn't see the
            # answer key — fall back to the student-safe view for them
            return ExamDetailStudentResponse.model_validate(exam)
        return ExamDetailTeacherResponse.model_validate(exam)

    # admin sees everything, including the answer key
    return ExamDetailTeacherResponse.model_validate(exam)


@router.put("/{exam_id}", response_model=ExamDetailTeacherResponse, summary="Update exam")
def update_exam(
    exam_id: int, body: ExamUpdateRequest,
    db: Session = Depends(get_db), teacher: Teacher = Depends(get_current_teacher_profile),
):
    return exam_service.update_exam(db, teacher.university_id, teacher, exam_id, body)


@router.delete("/{exam_id}", response_model=MessageResponse, summary="Delete unpublished exam")
def delete_exam(exam_id: int, db: Session = Depends(get_db), user: User = Depends(teacher_or_admin)):
    teacher = _teacher_profile_for(db, user)
    exam_service.delete_exam(
        db, user.university_id, teacher.id if teacher else None, exam_id, is_admin=(user.role == UserRole.ADMIN)
    )
    return MessageResponse(message="Exam deleted.")


@router.post("/{exam_id}/submit", response_model=ExamSubmissionResponse, summary="Student submits answers")
def submit_exam(
    exam_id: int, body: ExamSubmitRequest,
    db: Session = Depends(get_db), student: Student = Depends(get_current_student_profile),
):
    return exam_service.submit_exam(db, student.university_id, student, exam_id, body)


@router.post("/{exam_id}/grade", response_model=ExamSubmissionResponse, summary="Teacher grades submission")
def grade_exam(
    exam_id: int, body: ExamGradeRequest,
    db: Session = Depends(get_db), teacher: Teacher = Depends(get_current_teacher_profile),
):
    return exam_service.grade_submission(db, teacher.university_id, teacher, exam_id, body)


@router.get("/{exam_id}/results", response_model=ExamResultsResponse, summary="Get results for an exam")
def get_exam_results(exam_id: int, db: Session = Depends(get_db), user: User = Depends(teacher_or_admin)):
    teacher = _teacher_profile_for(db, user)
    submissions = exam_service.get_exam_results(
        db, user.university_id, teacher.id if teacher else None, exam_id, is_admin=(user.role == UserRole.ADMIN)
    )
    return ExamResultsResponse(exam_id=exam_id, submissions=submissions)
