"""
Invoice PDF generation — same reportlab approach as transcript_pdf.py,
kept as its own module since invoice layout will evolve independently.
"""
from dataclasses import dataclass
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


@dataclass
class InvoiceData:
    university_name: str
    student_name: str
    roll_number: str
    fee_type: str
    semester: str
    academic_year: str
    amount_due: float
    amount_paid: float
    outstanding: float
    due_date: date
    status: str
    invoice_id: int
    issued_at: date


def generate_invoice_pdf(data: InvoiceData) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("InvoiceTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=16)

    elements = [
        Paragraph(data.university_name, title_style),
        Paragraph(f"Invoice #{data.invoice_id}", ParagraphStyle("sub", parent=styles["Normal"], alignment=TA_CENTER)),
        Spacer(1, 0.6 * cm),
        Paragraph(f"<b>Student:</b> {data.student_name} ({data.roll_number})", styles["Normal"]),
        Paragraph(f"<b>Fee Type:</b> {data.fee_type}", styles["Normal"]),
        Paragraph(f"<b>Period:</b> {data.semester} {data.academic_year}", styles["Normal"]),
        Paragraph(f"<b>Issued:</b> {data.issued_at.isoformat()}", styles["Normal"]),
        Paragraph(f"<b>Due Date:</b> {data.due_date.isoformat()}", styles["Normal"]),
        Spacer(1, 0.6 * cm),
    ]

    table_data = [
        ["Amount Due", "Amount Paid", "Outstanding", "Status"],
        [f"{data.amount_due:.2f}", f"{data.amount_paid:.2f}", f"{data.outstanding:.2f}", data.status.upper()],
    ]
    table = Table(table_data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()
