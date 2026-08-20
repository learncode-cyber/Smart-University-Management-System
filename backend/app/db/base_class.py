"""
Declarative base + reusable mixins.

Design decision: mixins over repetition
----------------------------------------
Almost every table needs (a) created_at/updated_at timestamps and
(b) a university_id FK for multi-tenancy. Rather than retype these on
every model (and risk one table quietly missing the university_id FK —
which is exactly the kind of thing that costs a full migration later),
we define them once as mixins and every tenant-scoped model inherits
`UniversityScopedMixin`. If a future model forgets to inherit it, that's
an obvious, greppable review flag instead of a silent gap.
"""
from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


class TimestampMixin:
    """Adds created_at / updated_at columns, managed by the database itself."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )


class UniversityScopedMixin:
    """
    Adds university_id to any table that holds tenant-owned data.

    Every query in the service layer MUST filter by university_id once
    we have more than one tenant. For now (single university) this column
    is always the same seeded value, but it is indexed and enforced as
    NOT NULL from day one — so turning on multi-tenancy later is a
    WHERE-clause change in the repository layer, not a schema migration.
    """

    @classmethod
    def __declare_last__(cls):
        # placeholder hook kept intentionally simple; index is declared
        # per-model via __table_args__ so each model controls composite
        # index column order (see individual model files).
        pass

    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
