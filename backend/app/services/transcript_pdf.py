"""
Transcript PDF generation, using reportlab (chosen over WeasyPrint/
wkhtmltopdf-based approaches specifically because it's pure-Python — no
external system binary needs to be installed in the deployment
container, which keeps Part 11's Docker image simple and one less thing
that can break in grading/production).

Kept separate from result_service.py so the PDF *layout* can change
without touching the approval-workflow business logic, and vice versa.
"""
from dataclasses import dataclass
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


@dataclass
class TranscriptCourseRow:
    course_code: str
    course_title: str
    credit_hours: int
    grade_letter: str
    grade_point: float
    semester: str
    academic_year: str


@dataclass
class TranscriptData:
    university_name: str
    student_name: str
    roll_number: str
    department_name: str
    courses: list[TranscriptCourseRow]
    cumulative_gpa: float
    generated_on: date


def generate_transcript_pdf(data: TranscriptData) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TranscriptTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=16)
    subtitle_style = ParagraphStyle("TranscriptSubtitle", parent=styles["Normal"], alignment=TA_CENTER, fontSize=11)

    elements = [
        Paragraph(data.university_name, title_style),
        Paragraph("Official Academic Transcript", subtitle_style),
        Spacer(1, 0.6 * cm),
        Paragraph(f"<b>Student:</b> {data.student_name}", styles["Normal"]),
        Paragraph(f"<b>Roll Number:</b> {data.roll_number}", styles["Normal"]),
        Paragraph(f"<b>Department:</b> {data.department_name}", styles["Normal"]),
        Spacer(1, 0.6 * cm),
    ]

    table_data = [["Semester", "Course Code", "Course Title", "Credits", "Grade", "Grade Point"]]
    for row in data.courses:
        table_data.append([
            f"{row.semester} {row.academic_year}", row.course_code, row.course_title,
            str(row.credit_hours), row.grade_letter, f"{row.grade_point:.2f}",
        ])

    table = Table(table_data, repeatRows=1, colWidths=[3 * cm, 2.5 * cm, 6 * cm, 2 * cm, 2 * cm, 2.5 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)

    elements.append(Spacer(1, 0.8 * cm))
    elements.append(Paragraph(f"<b>Cumulative GPA:</b> {data.cumulative_gpa:.2f} / 4.00", styles["Heading3"]))
    elements.append(Spacer(1, 1.5 * cm))
    elements.append(Paragraph(
        f"Generated on {data.generated_on.isoformat()}. This document is system-generated and "
        f"carries the seal of {data.university_name}.",
        styles["Italic"],
    ))

    doc.build(elements)
    return buffer.getvalue()
