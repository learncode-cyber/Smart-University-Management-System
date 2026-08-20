"""
Results & Transcripts service layer — approval workflow:
    teacher submits -> admin approves (-> published) OR admin rejects
See Part 6 design note in the chat for the {examId} -> course_section
mapping simplification used in this build phase.
"""
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.academic import Course, CourseSection
from app.models.enums import ResultStatus, SubmissionStatus
from app.models.exam import Exam, ExamSubmission
from app.models.profiles import Admin, Parent, Student, Teacher
from app.models.result import Result
from app.models.university import University
from app.services.gpa import CourseResult, calculate_gpa, percentage_to_grade
from app.services.transcript_pdf import TranscriptCourseRow, TranscriptData, generate_transcript_pdf


def _not_found(entity: str) -> AppError:
    return AppError(404, "NOT_FOUND", f"{entity} not found.")


def _forbidden(message: str) -> AppError:
    return AppError(403, "FORBIDDEN", message)


def submit_result(db: Session, university_id: int, teacher: Teacher, exam_id: int, student_id: int) -> Result:
    exam = db.get(Exam, exam_id)
    if exam is None or exam.university_id != university_id:
        raise _not_found("Exam")
    if exam.created_by_teacher_id != teacher.id:
        raise _forbidden("You can only submit results for exams you created.")

    submission = db.scalar(
        select(ExamSubmission).where(ExamSubmission.exam_id == exam_id, ExamSubmission.student_id == student_id)
    )
    if submission is None or submission.status != SubmissionStatus.GRADED:
        raise AppError(400, "SUBMISSION_NOT_GRADED", "This student's exam submission has not been fully graded yet.")

    percentage = (float(submission.total_score) / exam.total_marks) * 100 if exam.total_marks else 0.0
    grade_letter, grade_point = percentage_to_grade(percentage)

    result = db.scalar(
        select(Result).where(Result.student_id == student_id, Result.course_section_id == exam.course_section_id)
    )
    now = datetime.now(timezone.utc)
    if result is None:
        result = Result(
            university_id=university_id,
            student_id=student_id,
            course_section_id=exam.course_section_id,
        )
        db.add(result)

    result.total_marks_obtained = float(submission.total_score)
    result.total_marks_possible = exam.total_marks
    result.grade_letter = grade_letter
    result.grade_point = grade_point
    result.status = ResultStatus.SUBMITTED
    result.submitted_by_teacher_id = teacher.id
    result.submitted_at = now
    # clear any stale approval/rejection state from a previous cycle (e.g. resubmission after rejection)
    result.approved_by_admin_id = None
    result.approved_at = None
    result.rejection_reason = None
    result.published_at = None

    db.commit()
    db.refresh(result)
    return result


def list_pending_results(db: Session, university_id: int) -> list[dict]:
    """Admin-facing queue of SUBMITTED (not yet approved/rejected) results.
    Flagged addition — see PendingResultResponse docstring."""
    stmt = select(Result).where(Result.university_id == university_id, Result.status == ResultStatus.SUBMITTED)
    results = list(db.scalars(stmt))
    rows = []
    for r in results:
        enriched = _enrich_result(db, r)
        student = db.get(Student, r.student_id)
        enriched["student_name"] = student.full_name
        rows.append(enriched)
    return rows


def approve_or_reject_result(db: Session, university_id: int, admin: Admin, result_id: int, approved: bool, rejection_reason: str | None) -> Result:
    result = db.get(Result, result_id)
    if result is None or result.university_id != university_id:
        raise _not_found("Result")
    if result.status != ResultStatus.SUBMITTED:
        raise AppError(400, "NOT_SUBMITTED", "Only results with status SUBMITTED can be approved or rejected.")

    now = datetime.now(timezone.utc)
    if approved:
        result.status = ResultStatus.PUBLISHED
        result.approved_by_admin_id = admin.id
        result.approved_at = now
        result.published_at = now
    else:
        result.status = ResultStatus.REJECTED
        result.rejection_reason = rejection_reason or "No reason provided."

    db.commit()
    db.refresh(result)
    return result


def _published_results_for_student(db: Session, student_id: int) -> list[Result]:
    stmt = select(Result).where(Result.student_id == student_id, Result.status == ResultStatus.PUBLISHED)
    return list(db.scalars(stmt))


def _enrich_result(db: Session, r: Result) -> dict:
    section = db.get(CourseSection, r.course_section_id)
    course = db.get(Course, section.course_id)
    return {
        "id": r.id, "student_id": r.student_id, "course_section_id": r.course_section_id,
        "course_code": course.code, "course_title": course.title,
        "semester": section.semester, "academic_year": section.academic_year,
        "total_marks_obtained": float(r.total_marks_obtained), "total_marks_possible": float(r.total_marks_possible),
        "grade_letter": r.grade_letter, "grade_point": float(r.grade_point) if r.grade_point is not None else None,
        "status": r.status, "submitted_at": r.submitted_at, "approved_at": r.approved_at,
        "published_at": r.published_at, "rejection_reason": r.rejection_reason,
    }


def get_my_results(db: Session, student: Student) -> tuple[list[Result], float | None]:
    results = _published_results_for_student(db, student.id)
    course_results = []
    for r in results:
        section = db.get(CourseSection, r.course_section_id)
        course = db.get(Course, section.course_id)
        course_results.append(CourseResult(grade_point=float(r.grade_point), credit_hours=course.credit_hours))
    gpa = calculate_gpa(course_results)
    return results, gpa


def get_results_status_for_student(db: Session, student: Student) -> dict:
    """Unified per-student shape used by both the Student and Parent
    paths of GET /results/me — mirrors the attendance module's pattern."""
    results, gpa = get_my_results(db, student)
    return {
        "student_id": student.id,
        "student_name": student.full_name,
        "results": [_enrich_result(db, r) for r in results],
        "cumulative_gpa": gpa,
    }


def get_results_status_for_parent(db: Session, parent: Parent) -> list[dict]:
    """One entry per linked child, reusing the same per-student logic as
    the Student path — mirrors the attendance module's parent function."""
    from app.models.profiles import ParentStudentLink
    links = db.scalars(select(ParentStudentLink).where(ParentStudentLink.parent_id == parent.id)).all()
    return [get_results_status_for_student(db, link.student) for link in links]


def generate_transcript(db: Session, university_id: int, student_id: int) -> bytes:
    student = db.get(Student, student_id)
    if student is None or student.university_id != university_id:
        raise _not_found("Student")

    results = _published_results_for_student(db, student_id)
    if not results:
        raise AppError(404, "NO_PUBLISHED_RESULTS", "This student has no published results yet.")

    rows: list[TranscriptCourseRow] = []
    course_results: list[CourseResult] = []
    department_name = student.department.name

    for r in results:
        section = db.get(CourseSection, r.course_section_id)
        course = db.get(Course, section.course_id)
        rows.append(TranscriptCourseRow(
            course_code=course.code, course_title=course.title, credit_hours=course.credit_hours,
            grade_letter=r.grade_letter, grade_point=float(r.grade_point),
            semester=section.semester, academic_year=section.academic_year,
        ))
        course_results.append(CourseResult(grade_point=float(r.grade_point), credit_hours=course.credit_hours))

    gpa = calculate_gpa(course_results) or 0.0
    university = db.get(University, university_id)

    data = TranscriptData(
        university_name=university.name,
        student_name=student.full_name,
        roll_number=student.roll_number,
        department_name=department_name,
        courses=rows,
        cumulative_gpa=gpa,
        generated_on=date.today(),
    )
    return generate_transcript_pdf(data)
