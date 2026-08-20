"""
Role-specific profile tables — 1:1 extensions of `users`.

Each of these has a `user_id` FK that is both UNIQUE (enforcing 1:1) and
the primary join key. `university_id` is duplicated here (denormalized)
rather than always joining through `users` — this is a deliberate
tradeoff: it lets us index and filter (e.g. "all students in university X")
without a join, at the cost of one extra column kept in sync at creation
time (it never changes after, so there's no update-anomaly risk).
"""
from datetime import date

from sqlalchemy import String, Integer, ForeignKey, Date, UniqueConstraint, Index, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UniversityScopedMixin
from app.models.enums import ParentRelationship


class Student(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("university_id", "roll_number", name="uq_student_university_roll"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    roll_number: Mapped[str] = mapped_column(String(30), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(500))
    profile_photo_url: Mapped[str | None] = mapped_column(String(500))

    enrollment_year: Mapped[int] = mapped_column(Integer, nullable=False)
    current_semester: Mapped[str | None] = mapped_column(String(20))

    user: Mapped["User"] = relationship(back_populates="student_profile")
    department: Mapped["Department"] = relationship()
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")
    parent_links: Mapped[list["ParentStudentLink"]] = relationship(back_populates="student")


class Teacher(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint("university_id", "employee_id", name="uq_teacher_university_employee"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    employee_id: Mapped[str] = mapped_column(String(30), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[str | None] = mapped_column(String(100))  # "Lecturer", "Professor"
    phone: Mapped[str | None] = mapped_column(String(30))
    profile_photo_url: Mapped[str | None] = mapped_column(String(500))
    joined_at: Mapped[date | None] = mapped_column(Date)

    user: Mapped["User"] = relationship(back_populates="teacher_profile")
    department: Mapped["Department"] = relationship()
    sections_taught: Mapped[list["CourseSection"]] = relationship(back_populates="teacher")


class Admin(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))

    user: Mapped["User"] = relationship(back_populates="admin_profile")


class Parent(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "parents"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))

    user: Mapped["User"] = relationship(back_populates="parent_profile")
    child_links: Mapped[list["ParentStudentLink"]] = relationship(back_populates="parent")


class ParentStudentLink(TimestampMixin, Base):
    """
    Many-to-many-capable join table: one parent can have multiple children
    (e.g. two kids at the same university), and — less common but modeled
    for correctness — a student could have more than one guardian
    registered (mother + father each with their own login).
    """
    __tablename__ = "parent_student_links"
    __table_args__ = (
        UniqueConstraint("parent_id", "student_id", name="uq_parent_student"),
        Index("ix_parent_student_student", "student_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("parents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[ParentRelationship] = mapped_column(
        SAEnum(ParentRelationship, name="parent_relationship"), nullable=False
    )

    parent: Mapped["Parent"] = relationship(back_populates="child_links")
    student: Mapped["Student"] = relationship(back_populates="parent_links")
