"""
Fees router — /api/v1/fees/* (optional module per proposal)

    GET  /fees/me                      -> Student, Parent
    POST /fees                          -> Admin
    POST /fees/payments                  -> Admin
    GET  /fees/payments/{studentId}       -> Admin, Parent
    GET  /fees/invoices/{id}               -> Student, Admin
    GET  /fees/overdue                       -> Admin
"""
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.errors import insufficient_permissions
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.profiles import Admin, Parent, ParentStudentLink, Student
from app.models.user import User
from app.schemas.fee import (
    FeeStructureCreateRequest, FeeStructureResponse,
    PaymentRecordRequest, PaymentResponse,
    InvoiceResponse, StudentFeeStatus, MyFeeStatusResponse, FeeDashboardSummary,
)
from app.schemas.auth import MessageResponse
from app.services import fee_service

router = APIRouter(prefix="/fees", tags=["Fees (Optional)"])

admin_only = require_role(UserRole.ADMIN)
student_or_parent = require_role(UserRole.STUDENT, UserRole.PARENT)


@router.get("/me", response_model=MyFeeStatusResponse, summary="Get own fee status and history")
def get_my_fee_status(db: Session = Depends(get_db), user: User = Depends(student_or_parent)):
    if user.role == UserRole.STUDENT:
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        statuses = fee_service.get_my_fee_status_as_student(db, student)
    else:
        parent = db.scalar(select(Parent).where(Parent.user_id == user.id))
        statuses = fee_service.get_my_fee_status_as_parent(db, parent)
    return MyFeeStatusResponse(students=[StudentFeeStatus(**s) for s in statuses])


@router.post("", response_model=FeeStructureResponse, summary="Define fee structure")
def create_fee_structure(
    body: FeeStructureCreateRequest, db: Session = Depends(get_db), admin: User = Depends(admin_only)
):
    structure, invoice_count = fee_service.create_fee_structure(db, admin.university_id, body)
    return FeeStructureResponse(
        id=structure.id, department_id=structure.department_id, fee_type=structure.fee_type,
        semester=structure.semester, academic_year=structure.academic_year, amount=float(structure.amount),
        due_date=structure.due_date, invoices_generated=invoice_count,
    )


@router.post("/payments", response_model=PaymentResponse, summary="Record a payment")
def record_payment(
    body: PaymentRecordRequest, db: Session = Depends(get_db), user: User = Depends(admin_only)
):
    admin = db.scalar(select(Admin).where(Admin.user_id == user.id))
    return fee_service.record_payment(db, user.university_id, admin, body)


@router.get(
    "/payments/{student_id}", response_model=list[PaymentResponse], summary="Get payment history",
    description="Admin: any student. Parent: only their own linked children. Student: only themselves "
                "(flagged addition — the original spec listed Admin/Parent only, but the Student "
                "feature description explicitly promises 'view full payment history').",
)
def get_payment_history(student_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == UserRole.PARENT:
        parent = db.scalar(select(Parent).where(Parent.user_id == user.id))
        link = db.scalar(
            select(ParentStudentLink).where(
                ParentStudentLink.parent_id == parent.id, ParentStudentLink.student_id == student_id
            )
        )
        if link is None:
            raise insufficient_permissions()
    elif user.role == UserRole.STUDENT:
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        if student is None or student.id != student_id:
            raise insufficient_permissions()
    elif user.role != UserRole.ADMIN:
        raise insufficient_permissions()

    return fee_service.get_payment_history(db, user.university_id, student_id)


@router.get(
    "/dashboard-summary", response_model=FeeDashboardSummary, summary="Real-time revenue dashboard",
    description="Flagged addition — the proposal describes this screen but never defined a backing endpoint.",
)
def get_dashboard_summary(db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    return fee_service.get_dashboard_summary(db, admin.university_id)


@router.post(
    "/overdue/send-notices", response_model=MessageResponse, summary="Send overdue notices to all affected students",
    description="Flagged addition — 'bulk notice sender' is described in the proposal's Admin Fee "
                "Dashboard screen but has no endpoint of its own in Section 6.",
)
def send_overdue_notices(db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    count = fee_service.send_overdue_notices(db, admin.university_id)
    return MessageResponse(message=f"Sent {count} overdue notice(s).")


@router.get("/overdue", response_model=list[InvoiceResponse], summary="List all overdue accounts")
def list_overdue(db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    return [InvoiceResponse(**row) for row in fee_service.list_overdue(db, admin.university_id)]


@router.get("/invoices/{invoice_id}", summary="Download invoice PDF")
def download_invoice(invoice_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == UserRole.STUDENT:
        student = db.scalar(select(Student).where(Student.user_id == user.id))
        owner_id = fee_service.get_invoice_owner_student_id(db, user.university_id, invoice_id)
        if student is None or student.id != owner_id:
            raise insufficient_permissions()
    elif user.role != UserRole.ADMIN:
        raise insufficient_permissions()

    pdf_bytes = fee_service.get_invoice_for_download(db, user.university_id, invoice_id)
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="invoice_{invoice_id}.pdf"'},
    )
