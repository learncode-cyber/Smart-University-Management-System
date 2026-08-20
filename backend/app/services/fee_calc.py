"""
Pure fee due-date / invoice-status logic — no DB, no FastAPI.
"""
from dataclasses import dataclass
from datetime import date

from app.models.enums import InvoiceStatus


@dataclass
class InvoiceState:
    amount_due: float
    amount_paid: float
    due_date: date
    is_waived: bool = False


def calculate_invoice_status(state: InvoiceState, today: date) -> InvoiceStatus:
    """
    Precedence: WAIVED > PAID > OVERDUE > PARTIAL > PENDING.
    - WAIVED is a manual admin override, always wins.
    - Fully paid (amount_paid >= amount_due) is PAID even if the due date
      has passed — the debt is settled, it isn't "overdue" anymore.
    - Otherwise, if today is past due_date -> OVERDUE (whether or not a
      partial payment was made).
    - Some payment but not enough, and not yet overdue -> PARTIAL.
    - No payment, not yet overdue -> PENDING.
    """
    if state.is_waived:
        return InvoiceStatus.WAIVED
    if state.amount_paid >= state.amount_due:
        return InvoiceStatus.PAID
    if today > state.due_date:
        return InvoiceStatus.OVERDUE
    if state.amount_paid > 0:
        return InvoiceStatus.PARTIAL
    return InvoiceStatus.PENDING


def outstanding_balance(state: InvoiceState) -> float:
    return round(max(state.amount_due - state.amount_paid, 0.0), 2)
