"""
University — the root tenant entity.

Every other tenant-owned table has a university_id FK pointing here.
For this build phase we seed exactly one row, but nothing in the schema
assumes that: adding a second university is just INSERT-ing a second row
and creating users/data against its id.
"""
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class University(TimestampMixin, Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # short unique code used in subdomains / API keys later e.g. "nsu", "buet"
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    contact_email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(500))

    # --- white-label / branding config (used by future commercial version) ---
    logo_url: Mapped[str | None] = mapped_column(String(500))
    primary_color: Mapped[str | None] = mapped_column(String(20))   # e.g. "#0F172A"
    secondary_color: Mapped[str | None] = mapped_column(String(20))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # relationships (back_populates set on the child side)
    users: Mapped[list["User"]] = relationship(back_populates="university")
    departments: Mapped[list["Department"]] = relationship(back_populates="university")
