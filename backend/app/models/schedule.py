"""
Class scheduling.

NOTE — deviation flag: no `schedule_conflicts` table.
`GET /schedule/conflicts` (Section 6) is served by a pure detection
function that scans `class_schedules` for overlapping (room, day,
time-range) or (teacher, day, time-range) pairs at request time — it is
NOT a persisted table. Storing "conflicts" as rows would mean keeping
them in sync every time a schedule changes (delete stale conflicts,
insert new ones) for zero real benefit, since conflict-free scheduling
is the goal, not conflict history. We'll build `detect_conflicts()` as
the testable pure function in Part 8.
"""
from datetime import time

from sqlalchemy import String, Time, ForeignKey, Index, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UniversityScopedMixin
from app.models.enums import DayOfWeek


class ClassSchedule(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "class_schedules"
    __table_args__ = (
        # these two indexes are exactly what the conflict-detection query
        # needs: "any other row with the same room/teacher on this day
        # whose time range overlaps mine?"
        Index("ix_schedule_room_day", "room", "day_of_week"),
        Index("ix_schedule_teacher_day", "teacher_id", "day_of_week"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_section_id: Mapped[int] = mapped_column(
        ForeignKey("course_sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False
    )

    day_of_week: Mapped[DayOfWeek] = mapped_column(
        SAEnum(DayOfWeek, name="day_of_week"), nullable=False
    )
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room: Mapped[str] = mapped_column(String(50), nullable=False)

    course_section: Mapped["CourseSection"] = relationship()
    teacher: Mapped["Teacher"] = relationship()
