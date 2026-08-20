"""
Reusable auth dependencies — every protected endpoint in every future
part (Part 3 onward) depends on these two functions. This is the ONE
place RBAC is enforced; individual routers never re-implement
"is this user allowed to do this" logic.
"""
from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import token_expired, token_invalid, account_inactive, insufficient_permissions
from app.core.security import decode_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise token_invalid()
    return authorization.split(" ", 1)[1].strip()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    Decodes and verifies the access token, then loads the User row fresh
    from the DB (not just trusting the token payload) so that an admin
    deactivating an account takes effect immediately on the NEXT request
    — we don't want a deactivated user staying "logged in" for the
    remaining lifetime of a token they already hold.
    """
    raw_token = _extract_bearer_token(authorization)

    try:
        payload = decode_token(raw_token)
    except JWTError as exc:
        # jose raises the same JWTError subtype for "expired" as other
        # validation failures depending on version; we distinguish by
        # message where possible, otherwise fall back to generic invalid.
        if "expired" in str(exc).lower():
            raise token_expired() from exc
        raise token_invalid() from exc

    if payload.get("type") != "access":
        raise token_invalid()

    user_id = payload.get("sub")
    if user_id is None:
        raise token_invalid()

    user = db.get(User, int(user_id))
    if user is None:
        raise token_invalid()
    if not user.is_active:
        raise account_inactive()

    return user


def require_role(*allowed_roles: UserRole):
    """
    Dependency FACTORY — usage in a router:

        @router.get("/students")
        def list_students(user: User = Depends(require_role(UserRole.ADMIN))):
            ...

    Returns a dependency function (not a plain dependency) because the
    set of allowed roles differs per-endpoint and can't be hardcoded into
    a single reusable function signature.
    """

    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise insufficient_permissions()
        return user

    return _check


def get_current_student_profile(
    user: User = Depends(require_role(UserRole.STUDENT)),
    db: Session = Depends(get_db),
):
    """Resolves the logged-in user's Student profile row. Used by any
    endpoint that needs student-specific fields (e.g. student.id for
    enrollment/attendance/result lookups), not just the role check."""
    from app.models.profiles import Student  # local import avoids a circular import at module load time
    student = db.scalar(select(Student).where(Student.user_id == user.id))
    if student is None:
        raise token_invalid()  # a STUDENT-role user with no profile row is a data-integrity bug, not a normal 403
    return student


def get_current_teacher_profile(
    user: User = Depends(require_role(UserRole.TEACHER)),
    db: Session = Depends(get_db),
):
    """Resolves the logged-in user's Teacher profile row."""
    from app.models.profiles import Teacher
    teacher = db.scalar(select(Teacher).where(Teacher.user_id == user.id))
    if teacher is None:
        raise token_invalid()
    return teacher
