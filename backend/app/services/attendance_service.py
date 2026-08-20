"""
Attendance service layer.

Design note on POST vs PUT semantics:
POST /attendance is CREATE-only — marking the same (course_section,
student, date) twice raises a conflict telling the caller to use
PUT /attendance/{id} instead. We deliberately don't silently overwrite,
because an accidental double-POST silently changing a student's
attendance with no audit trail would defeat the whole point of having a
separate, logged "correction" flow.
"""
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError
from app.models.academic import CourseSection
from app.models.attendance import AttendanceRecord
from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.profiles import Student, Teacher, Parent
from app.services.attendance_calc import calculate_attendance_percentage, is_below_threshold, tally_from_statuses


def _not_found(entity: str) -> AppError:
    return AppError(404, "NOT_FOUND", f"{entity} not found.")


def _forbidden(message: str) -> AppError:
    return AppError(403, "FORBIDDEN", message)


def _get_owned_section(db: Session, university_id: int, course_section_id: int, teacher_id: int) -> CourseSection:
    section = db.get(CourseSection, course_section_id)
    if section is None or section.university_id != university_id:
        raise _not_found("Course section")
    if section.teacher_id != teacher_id:
        raise _forbidden("You can only mark attendance for course sections you teach.")
    return section


def _percentage_for_student_in_section(db: Session, student_id: int, course_section_id: int) -> float:
    statuses = db.scalars(
        select(AttendanceRecord.status).where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.course_section_id == course_section_id,
        )
    ).all()
    tally = tally_from_statuses([s.value for s in statuses])
    return calculate_attendance_percentage(tally)


def _maybe_notify_low_attendance(db: Session, student: Student, course_section_id: int, percentage: float) -> None:
    if not is_below_threshold(percentage, settings.LOW_ATTENDANCE_THRESHOLD_PERCENT):
        return
    db.add(Notification(
        university_id=student.university_id,
        user_id=student.user_id,
        type=NotificationType.ATTENDANCE_WARNING,
        title="Low attendance warning",
        message=(
            f"Your attendance in course section {course_section_id} is {percentage}%, "
            f"below the required {settings.LOW_ATTENDANCE_THRESHOLD_PERCENT}%."
        ),
        related_entity_type="course_section",
        related_entity_id=course_section_id,
    ))


def bulk_mark_attendance(db: Session, university_id: int, teacher: Teacher, data) -> list[AttendanceRecord]:
    _get_owned_section(db, university_id, data.course_section_id, teacher.id)

    existing = db.scalars(
        select(AttendanceRecord).where(
            AttendanceRecord.course_section_id == data.course_section_id,
            AttendanceRecord.date == data.date,
        )
    ).all()
    if existing:
        raise AppError(
            409, "ALREADY_MARKED",
            "Attendance for this class and date has already been marked. "
            "Use PUT /attendance/{id} to correct an individual record.",
        )

    created: list[AttendanceRecord] = []
    for entry in data.entries:
        student = db.get(Student, entry.student_id)
        if student is None or student.university_id != university_id:
            raise _not_found(f"Student {entry.student_id}")

        record = AttendanceRecord(
            university_id=university_id,
            course_section_id=data.course_section_id,
            student_id=entry.student_id,
            date=data.date,
            status=entry.status,
            marked_by_teacher_id=teacher.id,
        )
        db.add(record)
        created.append(record)

    db.flush()  # so percentage calc below sees the just-inserted rows

    for entry in data.entries:
        pct = _percentage_for_student_in_section(db, entry.student_id, data.course_section_id)
        student = db.get(Student, entry.student_id)
        _maybe_notify_low_attendance(db, student, data.course_section_id, pct)

    db.commit()
    for r in created:
        db.refresh(r)
    return created


def correct_attendance_record(db: Session, university_id: int, teacher: Teacher, record_id: int, data) -> AttendanceRecord:
    record = db.get(AttendanceRecord, record_id)
    if record is None or record.university_id != university_id:
        raise _not_found("Attendance record")

    section = db.get(CourseSection, record.course_section_id)
    if section.teacher_id != teacher.id:
        raise _forbidden("You can only correct attendance for course sections you teach.")

    record.status = data.status
    record.corrected_by_teacher_id = teacher.id
    record.corrected_at = datetime.now(timezone.utc)
    record.correction_reason = data.correction_reason
    db.commit()
    db.refresh(record)

    pct = _percentage_for_student_in_section(db, record.student_id, record.course_section_id)
    student = db.get(Student, record.student_id)
    _maybe_notify_low_attendance(db, student, record.course_section_id, pct)
    db.commit()

    return record


def get_class_attendance(db: Session, university_id: int, requester_teacher_id: int | None,
                          course_section_id: int, is_admin: bool,
                          date_from: date | None = None, date_to: date | None = None) -> list[AttendanceRecord]:
    section = db.get(CourseSection, course_section_id)
    if section is None or section.university_id != university_id:
        raise _not_found("Course section")
    if not is_admin and section.teacher_id != requester_teacher_id:
        raise _forbidden("You can only view attendance for course sections you teach.")

    stmt = select(AttendanceRecord).where(AttendanceRecord.course_section_id == course_section_id)
    if date_from is not None:
        stmt = stmt.where(AttendanceRecord.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(AttendanceRecord.date <= date_to)
    return list(db.scalars(stmt))


def get_my_attendance_summary(db: Session, university_id: int, student: Student) -> list[dict]:
    """One summary row per course_section the student has ANY attendance
    records in."""
    section_ids = db.scalars(
        select(AttendanceRecord.course_section_id)
        .where(AttendanceRecord.student_id == student.id)
        .distinct()
    ).all()

    summaries = []
    for section_id in section_ids:
        pct = _percentage_for_student_in_section(db, student.id, section_id)
        statuses = db.scalars(
            select(AttendanceRecord.status).where(
                AttendanceRecord.student_id == student.id, AttendanceRecord.course_section_id == section_id
            )
        ).all()
        tally = tally_from_statuses([s.value for s in statuses])
        summaries.append({
            "course_section_id": section_id,
            "total_classes": tally.total_classes,
            "present_count": tally.present_count,
            "percentage": pct,
            "is_below_threshold": is_below_threshold(pct, settings.LOW_ATTENDANCE_THRESHOLD_PERCENT),
        })
    return summaries


def get_my_attendance_records(db: Session, student: Student, course_section_id: int | None,
                               date_from: date | None, date_to: date | None) -> list[AttendanceRecord]:
    stmt = select(AttendanceRecord).where(AttendanceRecord.student_id == student.id)
    if course_section_id is not None:
        stmt = stmt.where(AttendanceRecord.course_section_id == course_section_id)
    if date_from is not None:
        stmt = stmt.where(AttendanceRecord.date >= date_from)
    if date_to is not None:
        stmt = stmt.where(AttendanceRecord.date <= date_to)
    return list(db.scalars(stmt))


def get_attendance_status_for_student(db: Session, student: Student, course_section_id: int | None = None,
                                       date_from: date | None = None, date_to: date | None = None) -> dict:
    """Unified per-student shape used by both the Student and Parent
    paths of GET /attendance/me — see schemas/attendance.py docstring."""
    summaries = get_my_attendance_summary(db, student.university_id, student)
    records = []
    if course_section_id is not None or date_from is not None or date_to is not None:
        records = get_my_attendance_records(db, student, course_section_id, date_from, date_to)
    return {
        "student_id": student.id,
        "student_name": student.full_name,
        "summaries": summaries,
        "records": records,
    }


def get_attendance_status_for_parent(db: Session, parent: Parent) -> list[dict]:
    """One entry per linked child — reuses the same per-student logic
    as the Student path, just looped over ParentStudentLink rows."""
    from app.models.profiles import ParentStudentLink
    links = db.scalars(select(ParentStudentLink).where(ParentStudentLink.parent_id == parent.id)).all()
    return [get_attendance_status_for_student(db, link.student) for link in links]


def generate_attendance_report(db: Session, university_id: int, course_section_id: int | None = None) -> list[dict]:
    """Admin-only. One row per (student, course_section) with their
    computed percentage — the building block for the 'attendance reports'
    screen and for department/semester rollups the frontend can group."""
    stmt = select(AttendanceRecord.student_id, AttendanceRecord.course_section_id).where(
        AttendanceRecord.university_id == university_id
    ).distinct()
    if course_section_id is not None:
        stmt = stmt.where(AttendanceRecord.course_section_id == course_section_id)

    pairs = db.execute(stmt).all()
    rows = []
    for student_id, section_id in pairs:
        student = db.get(Student, student_id)
        pct = _percentage_for_student_in_section(db, student_id, section_id)
        statuses = db.scalars(
            select(AttendanceRecord.status).where(
                AttendanceRecord.student_id == student_id, AttendanceRecord.course_section_id == section_id
            )
        ).all()
        tally = tally_from_statuses([s.value for s in statuses])
        rows.append({
            "student_id": student_id,
            "student_name": student.full_name,
            "course_section_id": section_id,
            "total_classes": tally.total_classes,
            "present_count": tally.present_count,
            "percentage": pct,
            "is_below_threshold": is_below_threshold(pct, settings.LOW_ATTENDANCE_THRESHOLD_PERCENT),
        })
    return rows
