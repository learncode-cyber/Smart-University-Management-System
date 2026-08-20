"""
User — the single authentication identity table shared by all four roles.

Design decision: single `users` table + role-specific profile tables
----------------------------------------------------------------------
We use "table-per-role-profile", not "table-per-subtype inheritance" or
one giant flat table. Concretely:
    users            <- email, password_hash, role, is_active (auth concerns only)
    students          <- 1:1 with users, student-only fields
    teachers          <- 1:1 with users, teacher-only fields
    admins            <- 1:1 with users, admin-only fields
    parents           <- 1:1 with users, parent-only fields

Why not just one "students" table with login fields inline, etc.?
- Auth logic (login, refresh, password change, RBAC) becomes ONE code path
  that works identically for every role, instead of four near-duplicate
  auth systems.
- Adding a 5th role later (e.g. "Registrar") means adding one new profile
  table + one enum value — the auth/JWT/session code doesn't change at all.
- `role` lives on `users` (not derived from "which profile table has a
  row") so a single indexed column drives every RBAC check — no need to
  join out to 4 different tables just to find out who someone is.

Why NOT single-table inheritance (all fields on one wide `users` table)?
- Role-specific fields (student roll number, teacher designation, parent's
  linked children) are genuinely different data with different constraints.
  Cramming them into one table means dozens of nullable columns that only
  apply to 1-of-4 rows, and no way to enforce "students must have a
  department_id" at the DB level.
"""
from datetime import datetime

from sqlalchemy import String, Boolean, Enum as SAEnum, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UniversityScopedMixin
from app.models.enums import UserRole


class User(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        # Email must be unique WITHIN a university, not globally — two
        # different tenants may both have "admin@university.edu" registered
        # by different real institutions. This is the composite key that
        # makes multi-tenancy safe later.
        UniqueConstraint("university_id", "email", name="uq_users_university_email"),
        Index("ix_users_university_role", "university_id", "role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"), nullable=False, index=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column()

    university: Mapped["University"] = relationship(back_populates="users")

    # one of these four will be populated depending on `role`; the service
    # layer is responsible for creating the matching profile row at signup
    student_profile: Mapped["Student"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    teacher_profile: Mapped["Teacher"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    admin_profile: Mapped["Admin"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    parent_profile: Mapped["Parent"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
