from datetime import date

from app.models.enums import InvoiceStatus
from app.services.fee_calc import InvoiceState, calculate_invoice_status, outstanding_balance

TODAY = date(2026, 7, 22)


def test_pending_no_payment_not_due_yet():
    state = InvoiceState(amount_due=1000, amount_paid=0, due_date=date(2026, 8, 1))
    assert calculate_invoice_status(state, TODAY) == InvoiceStatus.PENDING


def test_partial_payment_not_due_yet():
    state = InvoiceState(amount_due=1000, amount_paid=400, due_date=date(2026, 8, 1))
    assert calculate_invoice_status(state, TODAY) == InvoiceStatus.PARTIAL


def test_overdue_no_payment():
    state = InvoiceState(amount_due=1000, amount_paid=0, due_date=date(2026, 7, 1))
    assert calculate_invoice_status(state, TODAY) == InvoiceStatus.OVERDUE


def test_overdue_with_partial_payment():
    state = InvoiceState(amount_due=1000, amount_paid=400, due_date=date(2026, 7, 1))
    assert calculate_invoice_status(state, TODAY) == InvoiceStatus.OVERDUE


def test_paid_in_full_even_if_due_date_passed():
    state = InvoiceState(amount_due=1000, amount_paid=1000, due_date=date(2026, 7, 1))
    assert calculate_invoice_status(state, TODAY) == InvoiceStatus.PAID


def test_paid_overpayment_still_paid():
    state = InvoiceState(amount_due=1000, amount_paid=1200, due_date=date(2026, 8, 1))
    assert calculate_invoice_status(state, TODAY) == InvoiceStatus.PAID


def test_waived_overrides_everything():
    state = InvoiceState(amount_due=1000, amount_paid=0, due_date=date(2026, 1, 1), is_waived=True)
    assert calculate_invoice_status(state, TODAY) == InvoiceStatus.WAIVED


def test_outstanding_balance():
    state = InvoiceState(amount_due=1000, amount_paid=400, due_date=date(2026, 8, 1))
    assert outstanding_balance(state) == 600.0


def test_outstanding_balance_never_negative():
    state = InvoiceState(amount_due=1000, amount_paid=1200, due_date=date(2026, 8, 1))
    assert outstanding_balance(state) == 0.0
