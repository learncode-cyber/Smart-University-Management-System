"""
Academic structure: departments, courses, and course_sections.

NOTE — deviation flag:
The proposal's feature list mentions "departments", "assigned courses",
and "class" repeatedly (teacher's "assigned courses", exam "assigned to a
class", attendance "by class", schedule by room/teacher) but Section 6
(REST API spec) never explicitly lists endpoints for departments/courses.
These tables are added because exams, attendance, and schedules all need
*something* to group students + a teacher + a time period — without it,
"mark attendance for a class" has no definition of what "a class" is.

We model this as:
    departments        <- e.g. "Computer Science"
    courses             <- catalog entry, e.g. "CSE301 - Database Systems"
    course_sections      <- one actual offering of a course in a given
                           semester/year, taught by one teacher (this is
                           "the class" referred to throughout the proposal)
    enrollments          <- which students belong to which course_section

This will need small dedicated CRUD endpoints (not in the original spec)
which we'll add as a lightweight "Academic Structure" module before Part 4
(Exams), since exams/attendance/schedule all depend on course_section_id
existing. Flagging this now so you can confirm before we build it.
"""
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UniversityScopedMixin


class Department(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("university_id", "code", name="uq_department_university_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "CSE"

    university: Mapped["University"] = relationship(back_populates="departments")
    courses: Mapped[list["Course"]] = relationship(back_populates="department")


class Course(UniversityScopedMixin, TimestampMixin, Base):
    """Catalog entry — e.g. 'CSE301: Database Systems, 3 credits'. Not tied
    to a specific semester; course_sections are the semester-specific
    instances of a course."""
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("university_id", "code", name="uq_course_university_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    code: Mapped[str] = mapped_column(String(20), nullable=False)   # e.g. "CSE301"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    credit_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    department: Mapped["Department"] = relationship(back_populates="courses")
    sections: Mapped[list["CourseSection"]] = relationship(back_populates="course")


class CourseSection(UniversityScopedMixin, TimestampMixin, Base):
    """
    A specific offering of a course: 'CSE301, Section A, Fall 2026, taught
    by Teacher X'. This is "the class" that exams, attendance records, and
    schedules all reference.
    """
    __tablename__ = "course_sections"
    __table_args__ = (
        Index("ix_course_sections_teacher_semester", "teacher_id", "semester", "academic_year"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    section_name: Mapped[str] = mapped_column(String(20), nullable=False, default="A")
    semester: Mapped[str] = mapped_column(String(20), nullable=False)   # "Spring" / "Fall"
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)  # "2026-2027"

    course: Mapped["Course"] = relationship(back_populates="sections")
    teacher: Mapped["Teacher"] = relationship(back_populates="sections_taught")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course_section")


class Enrollment(UniversityScopedMixin, TimestampMixin, Base):
    """Which students belong to which course_section. This is the roster
    used by attendance marking, exam assignment, and result submission."""
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_section_id", name="uq_enrollment_student_section"),
        Index("ix_enrollment_section", "course_section_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    course_section_id: Mapped[int] = mapped_column(
        ForeignKey("course_sections.id", ondelete="RESTRICT"), nullable=False
    )

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course_section: Mapped["CourseSection"] = relationship(back_populates="enrollments")
