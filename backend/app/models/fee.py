"""
Fees (optional module per proposal, but scaffolded now since it's cheap
to add to the schema and the proposal marks it "Optional" not "excluded").

Table breakdown:
    fee_structures     <- a fee definition: e.g. "Fall 2026 Tuition, CSE
                         dept, 50000 BDT, due Sep 1" — department-nullable
                         so a fee can apply university-wide or per-dept
    invoices             <- one row per (student, fee_structure): what THIS
                           student owes for THIS fee, and current status
    fee_payments          <- individual payments applied against an invoice
                            (supports partial payment over time)

Design decision: invoices as the per-student join, not a raw balance field
--------------------------------------------------------------------------
We don't store "amount_due" directly on the student. Instead, fee_structures
(the definition) x students = invoices (the per-student obligation), and
fee_payments accumulate against an invoice. This means:
- Overdue detection is a pure query (invoice.due_date < today AND
  amount_paid < amount_due), not a scheduled job mutating balances.
- Partial payments are naturally supported (sum of fee_payments vs
  invoice.amount_due).
"""
from datetime import date, datetime

from sqlalchemy import (
    String, Numeric, Date, ForeignKey, Index, Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UniversityScopedMixin
from app.models.enums import InvoiceStatus, PaymentMethod


class FeeStructure(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "fee_structures"

    id: Mapped[int] = mapped_column(primary_key=True)
    # nullable: a fee structure can be university-wide (null) or scoped to
    # one department (e.g. lab fee only for Engineering)
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT")
    )

    fee_type: Mapped[str] = mapped_column(String(100), nullable=False)  # "Tuition", "Lab Fee"
    semester: Mapped[str] = mapped_column(String(20), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(9), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    department: Mapped["Department | None"] = relationship()
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="fee_structure")


class Invoice(UniversityScopedMixin, TimestampMixin, Base):
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_student_status", "student_id", "status"),
        Index("ix_invoices_due_date_status", "due_date", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )
    fee_structure_id: Mapped[int] = mapped_column(
        ForeignKey("fee_structures.id", ondelete="RESTRICT"), nullable=False
    )

    amount_due: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        SAEnum(InvoiceStatus, name="invoice_status"), nullable=False, default=InvoiceStatus.PENDING
    )
    issued_at: Mapped[datetime] = mapped_column(nullable=False)

    student: Mapped["Student"] = relationship()
    fee_structure: Mapped["FeeStructure"] = relationship(back_populates="invoices")
    payments: Mapped[list["FeePayment"]] = relationship(back_populates="invoice")


class FeePayment(TimestampMixin, Base):
    __tablename__ = "fee_payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(
        SAEnum(PaymentMethod, name="payment_method"), nullable=False
    )
    transaction_ref: Mapped[str | None] = mapped_column(String(100))
    paid_at: Mapped[datetime] = mapped_column(nullable=False)
    recorded_by_admin_id: Mapped[int] = mapped_column(
        ForeignKey("admins.id", ondelete="RESTRICT"), nullable=False
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")
