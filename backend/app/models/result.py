"""
Results & transcripts — approval workflow: teacher submits -> admin
approves -> published -> visible to student/parent.

Table breakdown:
    results            <- one row per (student, course_section): the final
                         grade for that course in that semester, carrying
                         the approval-workflow state
    semester_gpas        <- cached per-semester GPA + CGPA snapshot, used to
                           render transcripts quickly and consistently

Design decision: why cache semester_gpas instead of computing on every request?
-----------------------------------------------------------------------------
GPA/CGPA calculation aggregates across potentially many `results` rows.
Recomputing on every "view transcript" request is fine at small scale,
but transcripts are also legal-ish documents (official PDF with university
seal) — once published, the GPA on a transcript for a past semester should
NEVER silently change if, say, a grading bug is fixed later and someone
recalculates. So we snapshot it at publish time. The pure `calculate_gpa()`
function (Part 6) is still what computes the number; this table just
freezes the result once it's official.
"""
from datetime import datetime

from sqlalchemy import String, Numeric, ForeignKey, UniqueConstraint, Index, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UniversityScopedMixin
from app.models.enums import ResultStatus


class Result(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "results"
    __table_args__ = (
        UniqueConstraint("student_id", "course_section_id", name="uq_result_student_section"),
        Index("ix_results_student_status", "student_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )
    course_section_id: Mapped[int] = mapped_column(
        ForeignKey("course_sections.id", ondelete="RESTRICT"), nullable=False
    )

    total_marks_obtained: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    total_marks_possible: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    grade_letter: Mapped[str | None] = mapped_column(String(2))   # "A+", "B", ...
    grade_point: Mapped[float | None] = mapped_column(Numeric(3, 2))  # 0.00 - 4.00

    status: Mapped[ResultStatus] = mapped_column(
        SAEnum(ResultStatus, name="result_status"), nullable=False, default=ResultStatus.DRAFT
    )

    submitted_by_teacher_id: Mapped[int | None] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL")
    )
    submitted_at: Mapped[datetime | None] = mapped_column()

    approved_by_admin_id: Mapped[int | None] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column()
    rejection_reason: Mapped[str | None] = mapped_column(String(1000))

    published_at: Mapped[datetime | None] = mapped_column()

    student: Mapped["Student"] = relationship()
    course_section: Mapped["CourseSection"] = relationship()


class SemesterGPA(UniversityScopedMixin, TimestampMixin, Base):
    """Frozen snapshot, written once all of a semester's results are
    published. Powers fast transcript rendering."""
    __tablename__ = "semester_gpas"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "semester", "academic_year",
            name="uq_semester_gpa_student_period",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    semester: Mapped[str] = mapped_column(String(20), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)

    semester_gpa: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    cumulative_gpa: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)

    student: Mapped["Student"] = relationship()
