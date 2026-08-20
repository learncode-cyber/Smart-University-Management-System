"""
Users & Profiles service layer.

Creating a student/teacher account is a two-step DB write (a `users` row
+ the role-specific profile row) that must succeed or fail together —
both inserts happen in the same DB session before a single commit, so a
failure partway (e.g. duplicate roll_number) rolls back the user row too
and we never end up with an orphaned login with no profile.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.academic import Department
from app.models.profiles import Student, Teacher, Admin, Parent
from app.models.user import User


def _conflict(field: str) -> AppError:
    return AppError(409, "ALREADY_EXISTS", f"A record with this {field} already exists.")


def _not_found(entity: str) -> AppError:
    return AppError(404, "NOT_FOUND", f"{entity} not found.")


def _check_department(db: Session, university_id: int, department_id: int) -> None:
    dept = db.get(Department, department_id)
    if dept is None or dept.university_id != university_id:
        raise _not_found("Department")


# ---- /users/me ----

def get_own_profile_merged(db: Session, user: User) -> dict:
    """Merges auth-identity fields with role-specific personal fields so
    the frontend has one 'my profile' shape regardless of role."""
    base = {"id": user.id, "email": user.email, "role": user.role, "is_active": user.is_active}

    if user.role == UserRole.STUDENT:
        profile = db.scalar(select(Student).where(Student.user_id == user.id))
    elif user.role == UserRole.TEACHER:
        profile = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
    elif user.role == UserRole.ADMIN:
        profile = db.scalar(select(Admin).where(Admin.user_id == user.id))
    else:
        profile = db.scalar(select(Parent).where(Parent.user_id == user.id))

    if profile is None:
        return base

    base["full_name"] = getattr(profile, "full_name", None)
    base["phone"] = getattr(profile, "phone", None)
    base["address"] = getattr(profile, "address", None)  # only Student has this; None otherwise
    base["profile_photo_url"] = getattr(profile, "profile_photo_url", None)  # Student/Teacher only
    return base


def update_own_profile(db: Session, user: User, data) -> dict:
    """Updates email on `users` and whatever personal fields exist on the
    caller's role-specific profile table. Administrative fields
    (roll_number, department_id, employee_id, enrollment_year) are
    intentionally NOT editable here — see UserMeUpdateRequest docstring."""
    update_own_email(db, user, data.email)

    if user.role == UserRole.STUDENT:
        profile = db.scalar(select(Student).where(Student.user_id == user.id))
    elif user.role == UserRole.TEACHER:
        profile = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
    elif user.role == UserRole.ADMIN:
        profile = db.scalar(select(Admin).where(Admin.user_id == user.id))
    else:
        profile = db.scalar(select(Parent).where(Parent.user_id == user.id))

    if profile is not None:
        if data.full_name is not None:
            profile.full_name = data.full_name
        if data.phone is not None:
            profile.phone = data.phone
        if data.address is not None and hasattr(profile, "address"):
            profile.address = data.address
        if data.profile_photo_url is not None and hasattr(profile, "profile_photo_url"):
            profile.profile_photo_url = data.profile_photo_url
        db.commit()

    return get_own_profile_merged(db, user)
    if new_email is None or new_email == user.email:
        return user

    existing = db.scalar(
        select(User).where(User.university_id == user.university_id, User.email == new_email)
    )
    if existing is not None:
        raise _conflict("email")

    user.email = new_email
    db.commit()
    db.refresh(user)
    return user


# ---- Students ----

def create_student(db: Session, university_id: int, data) -> Student:
    _check_department(db, university_id, data.department_id)

    existing_email = db.scalar(
        select(User).where(User.university_id == university_id, User.email == data.email)
    )
    if existing_email is not None:
        raise _conflict("email")

    existing_roll = db.scalar(
        select(Student).where(Student.university_id == university_id, Student.roll_number == data.roll_number)
    )
    if existing_roll is not None:
        raise _conflict("roll number")

    user = User(
        university_id=university_id,
        email=data.email,
        password_hash=hash_password(data.initial_password),
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add(user)
    db.flush()  # assigns user.id without committing, so we can attach the student row in the same transaction

    student = Student(
        university_id=university_id,
        user_id=user.id,
        department_id=data.department_id,
        roll_number=data.roll_number,
        full_name=data.full_name,
        date_of_birth=data.date_of_birth,
        phone=data.phone,
        address=data.address,
        enrollment_year=data.enrollment_year,
        current_semester=data.current_semester,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def list_students(db: Session, university_id: int, skip: int = 0, limit: int = 50) -> list[Student]:
    stmt = (
        select(Student)
        .where(Student.university_id == university_id)
        .order_by(Student.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def get_student(db: Session, university_id: int, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None or student.university_id != university_id:
        raise _not_found("Student")
    return student


def update_student(db: Session, university_id: int, student_id: int, data) -> Student:
    student = get_student(db, university_id, student_id)

    if data.department_id is not None:
        _check_department(db, university_id, data.department_id)
        student.department_id = data.department_id
    if data.full_name is not None:
        student.full_name = data.full_name
    if data.date_of_birth is not None:
        student.date_of_birth = data.date_of_birth
    if data.phone is not None:
        student.phone = data.phone
    if data.address is not None:
        student.address = data.address
    if data.current_semester is not None:
        student.current_semester = data.current_semester

    db.commit()
    db.refresh(student)
    return student


def deactivate_student(db: Session, university_id: int, student_id: int) -> None:
    """
    Soft-delete: flips users.is_active to False. We NEVER hard-delete a
    student row, because attendance/results/exam_submissions all hold
    RESTRICT foreign keys pointing at students.id — a hard delete would
    be rejected by the database anyway, but more importantly a deactivated
    student's historical academic record must remain intact and queryable
    (e.g. for a transcript request after graduation/withdrawal).
    """
    student = get_student(db, university_id, student_id)
    user = db.get(User, student.user_id)
    user.is_active = False
    db.commit()


# ---- Teachers ----

def create_teacher(db: Session, university_id: int, data) -> Teacher:
    _check_department(db, university_id, data.department_id)

    existing_email = db.scalar(
        select(User).where(User.university_id == university_id, User.email == data.email)
    )
    if existing_email is not None:
        raise _conflict("email")

    existing_emp = db.scalar(
        select(Teacher).where(Teacher.university_id == university_id, Teacher.employee_id == data.employee_id)
    )
    if existing_emp is not None:
        raise _conflict("employee ID")

    user = User(
        university_id=university_id,
        email=data.email,
        password_hash=hash_password(data.initial_password),
        role=UserRole.TEACHER,
        is_active=True,
    )
    db.add(user)
    db.flush()

    teacher = Teacher(
        university_id=university_id,
        user_id=user.id,
        department_id=data.department_id,
        employee_id=data.employee_id,
        full_name=data.full_name,
        designation=data.designation,
        phone=data.phone,
        joined_at=data.joined_at,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def list_teachers(db: Session, university_id: int, skip: int = 0, limit: int = 50) -> list[Teacher]:
    stmt = (
        select(Teacher)
        .where(Teacher.university_id == university_id)
        .order_by(Teacher.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def update_teacher(db: Session, university_id: int, teacher_id: int, data) -> Teacher:
    teacher = db.get(Teacher, teacher_id)
    if teacher is None or teacher.university_id != university_id:
        raise _not_found("Teacher")

    if data.department_id is not None:
        _check_department(db, university_id, data.department_id)
        teacher.department_id = data.department_id
    if data.full_name is not None:
        teacher.full_name = data.full_name
    if data.designation is not None:
        teacher.designation = data.designation
    if data.phone is not None:
        teacher.phone = data.phone

    db.commit()
    db.refresh(teacher)
    return teacher
