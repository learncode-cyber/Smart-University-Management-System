"""
Academic structure service layer — thin CRUD, Admin-only, backing the
department/course/course_section/enrollment tables added in Part 1.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.academic import Department, Course, CourseSection, Enrollment
from app.models.profiles import Teacher, Student


def _not_found(entity: str) -> AppError:
    return AppError(404, "NOT_FOUND", f"{entity} not found.")


# ---- Departments ----

def create_department(db: Session, university_id: int, name: str, code: str) -> Department:
    dept = Department(university_id=university_id, name=name, code=code)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


def list_departments(db: Session, university_id: int) -> list[Department]:
    stmt = select(Department).where(Department.university_id == university_id)
    return list(db.scalars(stmt))


# ---- Courses ----

def create_course(db: Session, university_id: int, department_id: int, code: str,
                   title: str, credit_hours: int) -> Course:
    dept = db.get(Department, department_id)
    if dept is None or dept.university_id != university_id:
        raise _not_found("Department")

    course = Course(
        university_id=university_id, department_id=department_id,
        code=code, title=title, credit_hours=credit_hours,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def list_courses(db: Session, university_id: int, department_id: int | None = None) -> list[Course]:
    stmt = select(Course).where(Course.university_id == university_id)
    if department_id is not None:
        stmt = stmt.where(Course.department_id == department_id)
    return list(db.scalars(stmt))


# ---- Course Sections ----

def _enrich_course_section(db: Session, section: CourseSection) -> dict:
    course = db.get(Course, section.course_id)
    return {
        "id": section.id, "course_id": section.course_id,
        "course_code": course.code, "course_title": course.title,
        "teacher_id": section.teacher_id, "section_name": section.section_name,
        "semester": section.semester, "academic_year": section.academic_year,
    }


def create_course_section(db: Session, university_id: int, course_id: int, teacher_id: int,
                           section_name: str, semester: str, academic_year: str) -> dict:
    course = db.get(Course, course_id)
    if course is None or course.university_id != university_id:
        raise _not_found("Course")

    teacher = db.get(Teacher, teacher_id)
    if teacher is None or teacher.university_id != university_id:
        raise _not_found("Teacher")

    section = CourseSection(
        university_id=university_id, course_id=course_id, teacher_id=teacher_id,
        section_name=section_name, semester=semester, academic_year=academic_year,
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return _enrich_course_section(db, section)


def list_course_sections(db: Session, university_id: int, teacher_id: int | None = None) -> list[dict]:
    stmt = select(CourseSection).where(CourseSection.university_id == university_id)
    if teacher_id is not None:
        stmt = stmt.where(CourseSection.teacher_id == teacher_id)
    sections = list(db.scalars(stmt))
    return [_enrich_course_section(db, s) for s in sections]


# ---- Enrollments ----

def create_enrollment(db: Session, university_id: int, student_id: int, course_section_id: int) -> Enrollment:
    student = db.get(Student, student_id)
    if student is None or student.university_id != university_id:
        raise _not_found("Student")

    section = db.get(CourseSection, course_section_id)
    if section is None or section.university_id != university_id:
        raise _not_found("Course section")

    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_section_id == course_section_id,
        )
    )
    if existing is not None:
        raise AppError(409, "ALREADY_ENROLLED", "This student is already enrolled in this course section.")

    enrollment = Enrollment(
        university_id=university_id, student_id=student_id, course_section_id=course_section_id
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def list_enrolled_students(db: Session, university_id: int, course_section_id: int) -> list[dict]:
    """The class roster — flagged addition. Needed for the Teacher
    Attendance Marker screen (and would help the Exam Builder too), but
    the original spec never defined a way to list who's enrolled in a
    section, only how to enroll one student at a time."""
    section = db.get(CourseSection, course_section_id)
    if section is None or section.university_id != university_id:
        raise _not_found("Course section")

    stmt = select(Enrollment).where(Enrollment.course_section_id == course_section_id)
    enrollments = list(db.scalars(stmt))
    students = []
    for e in enrollments:
        student = db.get(Student, e.student_id)
        students.append({"student_id": student.id, "full_name": student.full_name, "roll_number": student.roll_number})
    return sorted(students, key=lambda s: s["roll_number"])
