"""
Exam service layer. Business rules enforced here (not in the router):

- A teacher can only create/edit/delete exams for course_sections THEY
  teach (ownership check), even though they're already role-gated to
  "Teacher" — role alone doesn't stop Teacher A from touching Teacher B's
  exam.
- A student can only see/submit exams for course_sections they're
  enrolled in.
- Editing questions is only allowed while status == DRAFT — once an exam
  is scheduled/open, changing questions under students' feet would be
  unfair and could invalidate already-started attempts.
- Submitting is only allowed within [start_time, end_time], enforced
  server-side regardless of what the frontend timer shows.
- MCQ answers are auto-graded the instant they're submitted; other types
  are graded later by the teacher via /exams/{id}/grade.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.models.academic import CourseSection, Enrollment
from app.models.enums import ExamStatus, QuestionType, SubmissionStatus
from app.models.exam import Exam, ExamQuestion, ExamOption, ExamSubmission, ExamAnswer
from app.models.profiles import Student, Teacher
from app.services.grading import GradableAnswer, calculate_total_score, grade_mcq_answer, is_fully_graded


def _not_found(entity: str) -> AppError:
    return AppError(404, "NOT_FOUND", f"{entity} not found.")


def _forbidden(message: str) -> AppError:
    return AppError(403, "FORBIDDEN", message)


def _get_owned_section(db: Session, university_id: int, course_section_id: int, teacher_id: int) -> CourseSection:
    section = db.get(CourseSection, course_section_id)
    if section is None or section.university_id != university_id:
        raise _not_found("Course section")
    if section.teacher_id != teacher_id:
        raise _forbidden("You can only manage exams for course sections you teach.")
    return section


def _load_exam(db: Session, university_id: int, exam_id: int) -> Exam:
    stmt = (
        select(Exam)
        .where(Exam.id == exam_id, Exam.university_id == university_id)
        .options(selectinload(Exam.questions).selectinload(ExamQuestion.options))
    )
    exam = db.scalar(stmt)
    if exam is None:
        raise _not_found("Exam")
    return exam


# ---- create / update / delete ----

def create_exam(db: Session, university_id: int, teacher: Teacher, data) -> Exam:
    _get_owned_section(db, university_id, data.course_section_id, teacher.id)

    total_marks = sum(q.marks for q in data.questions)
    exam = Exam(
        university_id=university_id,
        course_section_id=data.course_section_id,
        created_by_teacher_id=teacher.id,
        title=data.title,
        description=data.description,
        status=ExamStatus.DRAFT,
        start_time=data.start_time,
        end_time=data.end_time,
        duration_minutes=data.duration_minutes,
        total_marks=total_marks,
    )
    db.add(exam)
    db.flush()

    _replace_questions(db, exam, data.questions)

    db.commit()
    db.refresh(exam)
    return exam


def _replace_questions(db: Session, exam: Exam, questions_data) -> None:
    for q in questions_data:
        if q.question_type == QuestionType.MCQ:
            if len(q.options) < 2 or sum(1 for o in q.options if o.is_correct) != 1:
                raise AppError(
                    400, "INVALID_MCQ_OPTIONS",
                    f"MCQ question '{q.question_text[:40]}...' needs at least 2 options with exactly one marked correct.",
                )

        question = ExamQuestion(
            exam_id=exam.id,
            question_type=q.question_type,
            question_text=q.question_text,
            marks=q.marks,
            order_index=q.order_index,
            starter_code=q.starter_code,
            expected_output=q.expected_output,
        )
        db.add(question)
        db.flush()

        for opt in q.options:
            db.add(ExamOption(question_id=question.id, option_text=opt.option_text, is_correct=opt.is_correct))


def update_exam(db: Session, university_id: int, teacher: Teacher, exam_id: int, data) -> Exam:
    exam = _load_exam(db, university_id, exam_id)
    if exam.created_by_teacher_id != teacher.id:
        raise _forbidden("You can only edit exams you created.")
    if exam.status != ExamStatus.DRAFT:
        raise AppError(400, "EXAM_NOT_EDITABLE", "Only draft exams can be edited. This exam has already been scheduled/opened.")

    if data.title is not None:
        exam.title = data.title
    if data.description is not None:
        exam.description = data.description
    if data.start_time is not None:
        exam.start_time = data.start_time
    if data.end_time is not None:
        exam.end_time = data.end_time
    if data.duration_minutes is not None:
        exam.duration_minutes = data.duration_minutes

    if data.questions is not None:
        # full replace — simplest correct behavior for a draft exam
        for q in list(exam.questions):
            db.delete(q)
        db.flush()
        _replace_questions(db, exam, data.questions)
        exam.total_marks = sum(q.marks for q in data.questions)

    db.commit()
    db.refresh(exam)
    return exam


def delete_exam(db: Session, university_id: int, requester_teacher_id: int | None, exam_id: int, is_admin: bool) -> None:
    exam = _load_exam(db, university_id, exam_id)
    if not is_admin and exam.created_by_teacher_id != requester_teacher_id:
        raise _forbidden("You can only delete exams you created.")
    if exam.status not in (ExamStatus.DRAFT, ExamStatus.SCHEDULED):
        raise AppError(400, "EXAM_NOT_DELETABLE", "Only unpublished (draft/scheduled) exams can be deleted.")
    db.delete(exam)
    db.commit()


# ---- listing / viewing (role-scoped) ----

def list_exams_for_student(db: Session, university_id: int, student: Student) -> list[Exam]:
    section_ids = db.scalars(
        select(Enrollment.course_section_id).where(Enrollment.student_id == student.id)
    ).all()
    if not section_ids:
        return []
    stmt = select(Exam).where(Exam.university_id == university_id, Exam.course_section_id.in_(section_ids))
    return list(db.scalars(stmt))


def list_exams_for_teacher(db: Session, university_id: int, teacher: Teacher) -> list[Exam]:
    stmt = select(Exam).where(Exam.university_id == university_id, Exam.created_by_teacher_id == teacher.id)
    return list(db.scalars(stmt))


def list_exams_for_admin(db: Session, university_id: int) -> list[Exam]:
    stmt = select(Exam).where(Exam.university_id == university_id)
    return list(db.scalars(stmt))


def get_exam_for_viewing(db: Session, university_id: int, exam_id: int) -> Exam:
    """Access-control on WHO can view a specific exam happens in the
    router (it knows the caller's role/profile); this just loads it."""
    return _load_exam(db, university_id, exam_id)


def assert_student_enrolled(db: Session, student: Student, course_section_id: int) -> None:
    exists = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student.id, Enrollment.course_section_id == course_section_id
        )
    )
    if exists is None:
        raise _forbidden("You are not enrolled in this course section.")


# ---- submission ----

def submit_exam(db: Session, university_id: int, student: Student, exam_id: int, data) -> ExamSubmission:
    exam = _load_exam(db, university_id, exam_id)
    assert_student_enrolled(db, student, exam.course_section_id)

    now = datetime.now(timezone.utc)
    if now < exam.start_time:
        raise AppError(400, "EXAM_NOT_OPEN", "This exam has not started yet.")
    if now > exam.end_time:
        raise AppError(400, "EXAM_CLOSED", "The submission deadline for this exam has passed.")

    existing = db.scalar(
        select(ExamSubmission).where(ExamSubmission.exam_id == exam_id, ExamSubmission.student_id == student.id)
    )
    if existing is not None:
        raise AppError(409, "ALREADY_SUBMITTED", "You have already submitted this exam. Resubmission is not allowed.")

    submission = ExamSubmission(
        university_id=university_id,
        exam_id=exam_id,
        student_id=student.id,
        status=SubmissionStatus.SUBMITTED,
        started_at=now,  # simplification: we don't track a separate "exam room opened" event in this build phase
        submitted_at=now,
    )
    db.add(submission)
    db.flush()

    questions_by_id = {q.id: q for q in exam.questions}
    options_by_id = {opt.id: opt for q in exam.questions for opt in q.options}

    graded_so_far: list[GradableAnswer] = []

    for ans in data.answers:
        question = questions_by_id.get(ans.question_id)
        if question is None:
            raise AppError(400, "INVALID_QUESTION", f"Question {ans.question_id} does not belong to this exam.")

        score = None
        if question.question_type == QuestionType.MCQ:
            selected = options_by_id.get(ans.selected_option_id) if ans.selected_option_id else None
            is_correct = selected.is_correct if selected else False
            score = grade_mcq_answer(is_correct, question.marks)

        db.add(ExamAnswer(
            submission_id=submission.id,
            question_id=question.id,
            selected_option_id=ans.selected_option_id,
            answer_text=ans.answer_text,
            score=score,
        ))
        graded_so_far.append(GradableAnswer(marks_possible=question.marks, score=score))

    # if every question was MCQ, the whole exam is already fully graded
    if is_fully_graded(graded_so_far):
        submission.status = SubmissionStatus.GRADED
        submission.total_score = calculate_total_score(graded_so_far)

    db.commit()
    db.refresh(submission)
    return submission


# ---- grading (manual, for non-MCQ questions) ----

def grade_submission(db: Session, university_id: int, teacher: Teacher, exam_id: int, data) -> ExamSubmission:
    exam = _load_exam(db, university_id, exam_id)
    if exam.created_by_teacher_id != teacher.id:
        raise _forbidden("You can only grade exams you created.")

    submission = db.scalar(
        select(ExamSubmission)
        .where(ExamSubmission.exam_id == exam_id, ExamSubmission.student_id == data.student_id)
        .options(selectinload(ExamSubmission.answers))
    )
    if submission is None:
        raise _not_found("Submission")

    answers_by_question_id = {a.question_id: a for a in submission.answers}
    now = datetime.now(timezone.utc)

    for grade in data.grades:
        answer = answers_by_question_id.get(grade.question_id)
        if answer is None:
            raise AppError(400, "INVALID_QUESTION", f"No answer found for question {grade.question_id}.")
        answer.score = grade.score
        answer.feedback = grade.feedback
        answer.graded_by_teacher_id = teacher.id
        answer.graded_at = now

    gradable = [GradableAnswer(marks_possible=0, score=a.score) for a in submission.answers]
    if is_fully_graded(gradable):
        submission.status = SubmissionStatus.GRADED
        submission.total_score = calculate_total_score(gradable)

    db.commit()
    db.refresh(submission)
    return submission


def get_exam_results(db: Session, university_id: int, requester_teacher_id: int | None, exam_id: int, is_admin: bool) -> list[ExamSubmission]:
    exam = _load_exam(db, university_id, exam_id)
    if not is_admin and exam.created_by_teacher_id != requester_teacher_id:
        raise _forbidden("You can only view results for exams you created.")

    stmt = (
        select(ExamSubmission)
        .where(ExamSubmission.exam_id == exam_id)
        .options(selectinload(ExamSubmission.answers))
    )
    return list(db.scalars(stmt))
