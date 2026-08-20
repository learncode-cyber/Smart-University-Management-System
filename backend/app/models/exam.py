"""
Exams & grading.

Table breakdown:
    exams              <- one exam instance for one course_section
    exam_questions      <- ordered questions within an exam (mixed types)
    exam_options         <- answer choices for MCQ questions only
    exam_submissions      <- one row per (student, exam) attempt
    exam_answers           <- one row per (submission, question) — this is
                            where per-question score + feedback lives

Design decision: no separate "exam_grades" table
--------------------------------------------------
The original outline in Part 1's prompt lists `exam_grades` as a separate
table. We fold grading data (score, feedback, graded_by, graded_at)
directly into `exam_answers` instead, because a grade is always 1:1 with
one answer to one question — a separate table would just be a shadow of
`exam_answers` joined 1:1, adding a join for no benefit. The aggregate
`exam_submissions.total_score` (a denormalized, recomputed-on-grade field)
serves the "exam grade" concept at the whole-exam level.

Design decision: JSONB for MCQ metadata vs a fully relational exam_options table
-----------------------------------------------------------------------------
We use a real `exam_options` table (not JSONB) for MCQ choices, because
options need their own primary key so a student's answer can reference
`selected_option_id` with a real FK — this makes "did the student pick
the correct option" a simple join+boolean check rather than string
matching inside JSON.
"""
from datetime import datetime

from sqlalchemy import (
    String, Text, Integer, Boolean, ForeignKey, Index,
    Enum as SAEnum, UniqueConstraint, Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UniversityScopedMixin
from app.models.enums import ExamStatus, QuestionType, SubmissionStatus


class Exam(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "exams"
    __table_args__ = (
        Index("ix_exams_section_status", "course_section_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_section_id: Mapped[int] = mapped_column(
        ForeignKey("course_sections.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_by_teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    status: Mapped[ExamStatus] = mapped_column(
        SAEnum(ExamStatus, name="exam_status"), nullable=False, default=ExamStatus.DRAFT, index=True
    )

    start_time: Mapped[datetime] = mapped_column(nullable=False)
    end_time: Mapped[datetime] = mapped_column(nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    # denormalized sum of exam_questions.marks — recomputed whenever
    # questions change, avoids a SUM() join on every read of exam metadata
    total_marks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    course_section: Mapped["CourseSection"] = relationship()
    questions: Mapped[list["ExamQuestion"]] = relationship(
        back_populates="exam", order_by="ExamQuestion.order_index", cascade="all, delete-orphan"
    )
    submissions: Mapped[list["ExamSubmission"]] = relationship(back_populates="exam")


class ExamQuestion(TimestampMixin, Base):
    __tablename__ = "exam_questions"
    __table_args__ = (
        Index("ix_exam_questions_exam", "exam_id", "order_index"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )

    question_type: Mapped[QuestionType] = mapped_column(
        SAEnum(QuestionType, name="question_type"), nullable=False
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    marks: Mapped[int] = mapped_column(Integer, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # only meaningful for CODING questions; nullable for the other 3 types
    starter_code: Mapped[str | None] = mapped_column(Text)
    expected_output: Mapped[str | None] = mapped_column(Text)

    exam: Mapped["Exam"] = relationship(back_populates="questions")
    options: Mapped[list["ExamOption"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    answers: Mapped[list["ExamAnswer"]] = relationship(back_populates="question")


class ExamOption(Base):
    """Answer choices for MCQ questions. Rows here are ignored for any
    other question_type."""
    __tablename__ = "exam_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("exam_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    question: Mapped["ExamQuestion"] = relationship(back_populates="options")


class ExamSubmission(UniversityScopedMixin, TimestampMixin, Base):
    """One attempt by one student at one exam."""
    __tablename__ = "exam_submissions"
    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_submission_exam_student"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    status: Mapped[SubmissionStatus] = mapped_column(
        SAEnum(SubmissionStatus, name="submission_status"),
        nullable=False, default=SubmissionStatus.IN_PROGRESS,
    )

    started_at: Mapped[datetime] = mapped_column(nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column()

    # denormalized aggregate, recomputed by the marks-aggregation function
    # every time a question is graded (see services/grading.py in Part 4)
    total_score: Mapped[float | None] = mapped_column(Numeric(6, 2))

    exam: Mapped["Exam"] = relationship(back_populates="submissions")
    student: Mapped["Student"] = relationship()
    answers: Mapped[list["ExamAnswer"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )

    @property
    def student_name(self) -> str:
        """Lets ExamSubmissionResponse (Pydantic, from_attributes=True)
        pick up the student's name via plain attribute access, without
        every route that returns a submission needing to build an
        enriched dict by hand."""
        return self.student.full_name


class ExamAnswer(TimestampMixin, Base):
    """
    One student's answer to one question, plus its grade. This row is
    where the "manual grading workflow" writes score + feedback.
    """
    __tablename__ = "exam_answers"
    __table_args__ = (
        UniqueConstraint("submission_id", "question_id", name="uq_answer_submission_question"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("exam_submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("exam_questions.id", ondelete="RESTRICT"), nullable=False
    )

    # for MCQ: selected_option_id is set, answer_text is null
    selected_option_id: Mapped[int | None] = mapped_column(
        ForeignKey("exam_options.id", ondelete="SET NULL")
    )
    # for short_answer / descriptive / coding: free text (or submitted code)
    answer_text: Mapped[str | None] = mapped_column(Text)

    score: Mapped[float | None] = mapped_column(Numeric(6, 2))  # null until graded
    feedback: Mapped[str | None] = mapped_column(Text)
    graded_by_teacher_id: Mapped[int | None] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL")
    )
    graded_at: Mapped[datetime | None] = mapped_column()

    submission: Mapped["ExamSubmission"] = relationship(back_populates="answers")
    question: Mapped["ExamQuestion"] = relationship(back_populates="answers")
