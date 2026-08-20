"""
Attendance.

Design decision: correction as an audit trail, not an update-in-place
------------------------------------------------------------------------
`PUT /attendance/{id}` ("correct an attendance record") overwrites the
`status` field but we keep `corrected_by_id` / `corrected_at` /
`correction_reason` columns on the SAME row rather than a separate
attendance_audit_log table. This is a deliberate simpler-first choice:
- Attendance corrections are rare and single-step (one correction per
  record is the realistic case for a university).
- The columns directly answer "who changed this and why" without a join.
If multi-step correction history ever becomes a real requirement, this
can be split into an `attendance_audit_log` table later without touching
any other part of the schema — flagging this as a conscious scope
tradeoff, not an oversight.
"""
from datetime import date, datetime

from sqlalchemy import ForeignKey, Date, Text, Index, UniqueConstraint, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UniversityScopedMixin
from app.models.enums import AttendanceStatus


class AttendanceRecord(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        # a student can only have ONE attendance status per class per day
        UniqueConstraint(
            "course_section_id", "student_id", "date",
            name="uq_attendance_section_student_date",
        ),
        # this composite index is what powers both "attendance/me" (filter
        # by student_id, order by date) and "attendance reports" (filter by
        # course_section_id + date range)
        Index("ix_attendance_student_date", "student_id", "date"),
        Index("ix_attendance_section_date", "course_section_id", "date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_section_id: Mapped[int] = mapped_column(
        ForeignKey("course_sections.id", ondelete="RESTRICT"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )

    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(
        SAEnum(AttendanceStatus, name="attendance_status"), nullable=False
    )

    marked_by_teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False
    )

    # populated only if this record has been corrected after initial marking
    corrected_by_teacher_id: Mapped[int | None] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL")
    )
    corrected_at: Mapped[datetime | None] = mapped_column()
    correction_reason: Mapped[str | None] = mapped_column(Text)

    course_section: Mapped["CourseSection"] = relationship()
    student: Mapped["Student"] = relationship()
