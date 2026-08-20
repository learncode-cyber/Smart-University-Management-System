"""
Scheduling service layer. Every create/update runs the candidate slot
against all existing slots for the university BEFORE saving — see the
conflict-detection design note above.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.academic import CourseSection, Enrollment
from app.models.schedule import ClassSchedule
from app.services.schedule_calc import ScheduleSlot, find_conflicts_for_new_slot, find_all_conflicts


def _not_found(entity: str) -> AppError:
    return AppError(404, "NOT_FOUND", f"{entity} not found.")


def _existing_slots(db: Session, university_id: int) -> list[ScheduleSlot]:
    stmt = select(ClassSchedule).where(ClassSchedule.university_id == university_id)
    rows = db.scalars(stmt)
    return [
        ScheduleSlot(
            id=r.id, day_of_week=r.day_of_week.value, start_time=r.start_time,
            end_time=r.end_time, room=r.room, teacher_id=r.teacher_id,
        )
        for r in rows
    ]


def _conflict_error(conflicts) -> AppError:
    reasons = ", ".join(sorted({c.reason for c in conflicts}))
    return AppError(
        409, "SCHEDULE_CONFLICT",
        f"This time slot conflicts with an existing schedule entry ({reasons} double-booked).",
    )


def enrich_schedule(db: Session, s: ClassSchedule) -> dict:
    from app.models.academic import Course
    from app.models.profiles import Teacher
    section = db.get(CourseSection, s.course_section_id)
    course = db.get(Course, section.course_id)
    teacher = db.get(Teacher, s.teacher_id)
    return {
        "id": s.id, "course_section_id": s.course_section_id,
        "course_code": course.code, "course_title": course.title,
        "teacher_id": s.teacher_id, "teacher_name": teacher.full_name,
        "day_of_week": s.day_of_week, "start_time": s.start_time, "end_time": s.end_time, "room": s.room,
    }


def create_schedule(db: Session, university_id: int, data) -> ClassSchedule:
    section = db.get(CourseSection, data.course_section_id)
    if section is None or section.university_id != university_id:
        raise _not_found("Course section")

    candidate = ScheduleSlot(
        id=None, day_of_week=data.day_of_week.value, start_time=data.start_time,
        end_time=data.end_time, room=data.room, teacher_id=section.teacher_id,
    )
    conflicts = find_conflicts_for_new_slot(candidate, _existing_slots(db, university_id))
    if conflicts:
        raise _conflict_error(conflicts)

    schedule = ClassSchedule(
        university_id=university_id, course_section_id=data.course_section_id, teacher_id=section.teacher_id,
        day_of_week=data.day_of_week, start_time=data.start_time, end_time=data.end_time, room=data.room,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def update_schedule(db: Session, university_id: int, schedule_id: int, data) -> ClassSchedule:
    schedule = db.get(ClassSchedule, schedule_id)
    if schedule is None or schedule.university_id != university_id:
        raise _not_found("Schedule entry")

    new_day = data.day_of_week or schedule.day_of_week  # DayOfWeek enum member either way
    candidate = ScheduleSlot(
        id=schedule.id,
        day_of_week=new_day.value,
        start_time=data.start_time or schedule.start_time,
        end_time=data.end_time or schedule.end_time,
        room=data.room or schedule.room,
        teacher_id=schedule.teacher_id,
    )
    others = [s for s in _existing_slots(db, university_id) if s.id != schedule.id]
    conflicts = find_conflicts_for_new_slot(candidate, others)
    if conflicts:
        raise _conflict_error(conflicts)

    if data.day_of_week is not None:
        schedule.day_of_week = data.day_of_week
    if data.start_time is not None:
        schedule.start_time = data.start_time
    if data.end_time is not None:
        schedule.end_time = data.end_time
    if data.room is not None:
        schedule.room = data.room

    db.commit()
    db.refresh(schedule)
    return schedule


def delete_schedule(db: Session, university_id: int, schedule_id: int) -> None:
    schedule = db.get(ClassSchedule, schedule_id)
    if schedule is None or schedule.university_id != university_id:
        raise _not_found("Schedule entry")
    db.delete(schedule)
    db.commit()


def get_schedule_for_student(db: Session, university_id: int, student_id: int) -> list[ClassSchedule]:
    section_ids = db.scalars(select(Enrollment.course_section_id).where(Enrollment.student_id == student_id)).all()
    if not section_ids:
        return []
    stmt = select(ClassSchedule).where(
        ClassSchedule.university_id == university_id, ClassSchedule.course_section_id.in_(section_ids)
    )
    return list(db.scalars(stmt))


def get_schedule_for_parent(db: Session, university_id: int, parent_id: int) -> list[ClassSchedule]:
    """
    Union of all linked children's timetables. NOTE (flagged
    simplification): for a parent with more than one child at this
    university, entries from different children are not distinguished
    in this response — a future iteration should tag each entry with
    which child it belongs to. Covers the common single-child case
    cleanly; multi-child parents get a merged (still correct, just
    unlabeled) timetable for now.
    """
    from app.models.profiles import ParentStudentLink
    links = db.scalars(select(ParentStudentLink).where(ParentStudentLink.parent_id == parent_id)).all()
    all_schedules: list[ClassSchedule] = []
    seen_ids: set[int] = set()
    for link in links:
        for sched in get_schedule_for_student(db, university_id, link.student_id):
            if sched.id not in seen_ids:
                seen_ids.add(sched.id)
                all_schedules.append(sched)
    return all_schedules


def get_schedule_for_teacher(db: Session, university_id: int, teacher_id: int) -> list[ClassSchedule]:
    stmt = select(ClassSchedule).where(ClassSchedule.university_id == university_id, ClassSchedule.teacher_id == teacher_id)
    return list(db.scalars(stmt))


def list_all_schedule(db: Session, university_id: int) -> list[ClassSchedule]:
    """Admin-facing: every schedule entry university-wide, for the
    Timetable Control screen. Flagged addition — the original spec's
    /schedule endpoints only covered create/update/delete/conflicts,
    with no way to list existing entries to manage them."""
    stmt = select(ClassSchedule).where(ClassSchedule.university_id == university_id)
    return list(db.scalars(stmt))


def detect_all_conflicts(db: Session, university_id: int) -> list[dict]:
    slots = _existing_slots(db, university_id)
    conflicts = find_all_conflicts(slots)
    return [{"slot_a_id": c.slot_a_id, "slot_b_id": c.slot_b_id, "reason": c.reason} for c in conflicts]
