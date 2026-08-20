"""
Fees service layer.

Design decision: creating a FeeStructure auto-generates one Invoice per
eligible student immediately (not lazily on first view). This means
"define a fee structure" and "every student now has a bill" happen in
the same admin action — matching the proposal's "Define fee structure"
feature description, and making GET /fees/overdue a simple query instead
of needing to know which students *should* have been billed.
"""
from datetime import date, datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.fee import FeeStructure, Invoice, FeePayment
from app.models.academic import Department
from app.models.profiles import Admin, Parent, ParentStudentLink, Student
from app.services.fee_calc import InvoiceState, calculate_invoice_status, outstanding_balance
from app.services.invoice_pdf import InvoiceData, generate_invoice_pdf


def _not_found(entity: str) -> AppError:
    return AppError(404, "NOT_FOUND", f"{entity} not found.")


def _forbidden(message: str) -> AppError:
    return AppError(403, "FORBIDDEN", message)


def _paid_amount(db: Session, invoice_id: int) -> float:
    total = db.scalar(select(func.coalesce(func.sum(FeePayment.amount), 0)).where(FeePayment.invoice_id == invoice_id))
    return float(total or 0)


def _refresh_invoice_status(db: Session, invoice: Invoice, today: date | None = None) -> None:
    """Recomputes and persists invoice.status. Called on every read/write
    path that touches an invoice, since there's no background job in this
    build phase to do it on a schedule (flagged in the design discussion)."""
    paid = _paid_amount(db, invoice.id)
    state = InvoiceState(
        amount_due=float(invoice.amount_due), amount_paid=paid, due_date=invoice.due_date,
        is_waived=(invoice.status.value == "waived"),
    )
    invoice.status = calculate_invoice_status(state, today or date.today())


def _to_invoice_response_dict(db: Session, invoice: Invoice) -> dict:
    paid = _paid_amount(db, invoice.id)
    state = InvoiceState(amount_due=float(invoice.amount_due), amount_paid=paid, due_date=invoice.due_date,
                          is_waived=(invoice.status.value == "waived"))
    student = db.get(Student, invoice.student_id)
    return {
        "id": invoice.id, "student_id": invoice.student_id, "student_name": student.full_name,
        "fee_structure_id": invoice.fee_structure_id,
        "amount_due": float(invoice.amount_due), "amount_paid": paid,
        "outstanding": outstanding_balance(state), "status": invoice.status,
        "due_date": invoice.due_date, "issued_at": invoice.issued_at,
    }


# ---- Fee structures + auto-invoicing ----

def create_fee_structure(db: Session, university_id: int, data) -> tuple[FeeStructure, int]:
    if data.department_id is not None:
        dept = db.get(Department, data.department_id)
        if dept is None or dept.university_id != university_id:
            raise _not_found("Department")

    structure = FeeStructure(
        university_id=university_id, department_id=data.department_id, fee_type=data.fee_type,
        semester=data.semester, academic_year=data.academic_year, amount=data.amount, due_date=data.due_date,
    )
    db.add(structure)
    db.flush()

    stmt = select(Student).where(Student.university_id == university_id)
    if data.department_id is not None:
        stmt = stmt.where(Student.department_id == data.department_id)
    students = list(db.scalars(stmt))

    now = datetime.now(timezone.utc)
    for student in students:
        db.add(Invoice(
            university_id=university_id, student_id=student.id, fee_structure_id=structure.id,
            amount_due=data.amount, due_date=data.due_date, issued_at=now,
        ))

    db.commit()
    db.refresh(structure)
    return structure, len(students)


# ---- Payments ----

def record_payment(db: Session, university_id: int, admin: Admin, data) -> FeePayment:
    invoice = db.get(Invoice, data.invoice_id)
    if invoice is None or invoice.university_id != university_id:
        raise _not_found("Invoice")

    payment = FeePayment(
        invoice_id=invoice.id, amount=data.amount, method=data.method,
        transaction_ref=data.transaction_ref, paid_at=datetime.now(timezone.utc),
        recorded_by_admin_id=admin.id,
    )
    db.add(payment)
    db.flush()

    _refresh_invoice_status(db, invoice)

    db.commit()
    db.refresh(payment)
    return payment


def get_payment_history(db: Session, university_id: int, student_id: int) -> list[FeePayment]:
    student = db.get(Student, student_id)
    if student is None or student.university_id != university_id:
        raise _not_found("Student")

    stmt = (
        select(FeePayment)
        .join(Invoice, FeePayment.invoice_id == Invoice.id)
        .where(Invoice.student_id == student_id)
    )
    return list(db.scalars(stmt))


# ---- Invoice / status views ----

def _fee_status_for_student(db: Session, student: Student) -> dict:
    stmt = select(Invoice).where(Invoice.student_id == student.id)
    invoices = list(db.scalars(stmt))
    for inv in invoices:
        _refresh_invoice_status(db, inv)
    db.commit()

    invoice_dicts = [_to_invoice_response_dict(db, inv) for inv in invoices]
    total_due = sum(i["amount_due"] for i in invoice_dicts)
    total_paid = sum(i["amount_paid"] for i in invoice_dicts)
    return {
        "student_id": student.id, "student_name": student.full_name, "invoices": invoice_dicts,
        "total_due": round(total_due, 2), "total_paid": round(total_paid, 2),
        "total_outstanding": round(total_due - total_paid, 2),
    }


def get_my_fee_status_as_student(db: Session, student: Student) -> list[dict]:
    return [_fee_status_for_student(db, student)]


def get_my_fee_status_as_parent(db: Session, parent: Parent) -> list[dict]:
    links = db.scalars(select(ParentStudentLink).where(ParentStudentLink.parent_id == parent.id)).all()
    return [_fee_status_for_student(db, link.student) for link in links]


def get_invoice_for_download(db: Session, university_id: int, invoice_id: int) -> bytes:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None or invoice.university_id != university_id:
        raise _not_found("Invoice")
    _refresh_invoice_status(db, invoice)
    db.commit()

    student = db.get(Student, invoice.student_id)
    structure = db.get(FeeStructure, invoice.fee_structure_id)
    paid = _paid_amount(db, invoice.id)
    state = InvoiceState(amount_due=float(invoice.amount_due), amount_paid=paid, due_date=invoice.due_date)

    from app.models.university import University
    university = db.get(University, university_id)

    data = InvoiceData(
        university_name=university.name, student_name=student.full_name, roll_number=student.roll_number,
        fee_type=structure.fee_type, semester=structure.semester, academic_year=structure.academic_year,
        amount_due=float(invoice.amount_due), amount_paid=paid, outstanding=outstanding_balance(state),
        due_date=invoice.due_date, status=invoice.status.value, invoice_id=invoice.id,
        issued_at=invoice.issued_at.date(),
    )
    return generate_invoice_pdf(data)


def get_invoice_owner_student_id(db: Session, university_id: int, invoice_id: int) -> int:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None or invoice.university_id != university_id:
        raise _not_found("Invoice")
    return invoice.student_id


def list_overdue(db: Session, university_id: int) -> list[dict]:
    stmt = select(Invoice).where(Invoice.university_id == university_id)
    invoices = list(db.scalars(stmt))
    overdue = []
    for inv in invoices:
        _refresh_invoice_status(db, inv)
        if inv.status.value == "overdue":
            overdue.append(inv)
    db.commit()
    return [_to_invoice_response_dict(db, inv) for inv in overdue]


def get_dashboard_summary(db: Session, university_id: int) -> dict:
    """Real-time revenue view for the Admin Fee Dashboard — flagged
    addition, the original spec described this screen but never defined
    a backing endpoint for the aggregate numbers it needs."""
    stmt = select(Invoice).where(Invoice.university_id == university_id)
    invoices = list(db.scalars(stmt))

    total_invoiced = 0.0
    total_collected = 0.0
    overdue_count = 0
    for inv in invoices:
        _refresh_invoice_status(db, inv)
        paid = _paid_amount(db, inv.id)
        total_invoiced += float(inv.amount_due)
        total_collected += paid
        if inv.status.value == "overdue":
            overdue_count += 1
    db.commit()

    return {
        "total_invoiced": round(total_invoiced, 2),
        "total_collected": round(total_collected, 2),
        "total_outstanding": round(total_invoiced - total_collected, 2),
        "invoice_count": len(invoices),
        "overdue_count": overdue_count,
    }


def send_overdue_notices(db: Session, university_id: int) -> int:
    """Creates a FEE_OVERDUE notification for every student currently in
    OVERDUE status — the 'bulk notice sender' the Admin Fee Dashboard
    screen needs (flagged addition, same reasoning as get_dashboard_summary)."""
    from app.models.enums import NotificationType
    from app.models.notification import Notification

    overdue_invoices = list_overdue(db, university_id)
    sent = 0
    for inv in overdue_invoices:
        student = db.get(Student, inv["student_id"])
        db.add(Notification(
            university_id=university_id,
            user_id=student.user_id,
            type=NotificationType.FEE_OVERDUE,
            title="Overdue fee reminder",
            message=f"You have an overdue invoice (#{inv['id']}) with an outstanding balance of {inv['outstanding']}.",
            related_entity_type="invoice",
            related_entity_id=inv["id"],
        ))
        sent += 1
    db.commit()
    return sent
