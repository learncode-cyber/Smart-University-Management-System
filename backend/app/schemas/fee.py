from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import InvoiceStatus, PaymentMethod


class FeeStructureCreateRequest(BaseModel):
    department_id: int | None = None  # None = applies to the whole university
    fee_type: str = Field(max_length=100)
    semester: str = Field(max_length=20)
    academic_year: str = Field(max_length=9)
    amount: float = Field(gt=0)
    due_date: date


class FeeStructureResponse(BaseModel):
    id: int
    department_id: int | None
    fee_type: str
    semester: str
    academic_year: str
    amount: float
    due_date: date
    invoices_generated: int  # how many student invoices were created for this structure

    model_config = {"from_attributes": True}


class PaymentRecordRequest(BaseModel):
    invoice_id: int
    amount: float = Field(gt=0)
    method: PaymentMethod
    transaction_ref: str | None = Field(default=None, max_length=100)


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    amount: float
    method: PaymentMethod
    transaction_ref: str | None
    paid_at: datetime

    model_config = {"from_attributes": True}


class InvoiceResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    fee_structure_id: int
    amount_due: float
    amount_paid: float
    outstanding: float
    status: InvoiceStatus
    due_date: date
    issued_at: datetime


class StudentFeeStatus(BaseModel):
    student_id: int
    student_name: str
    invoices: list[InvoiceResponse]
    total_due: float
    total_paid: float
    total_outstanding: float


class FeeDashboardSummary(BaseModel):
    total_invoiced: float
    total_collected: float
    total_outstanding: float
    invoice_count: int
    overdue_count: int


class MyFeeStatusResponse(BaseModel):
    students: list[StudentFeeStatus]
