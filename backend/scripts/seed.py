"""
Seed script — bootstraps the ONE thing the API genuinely cannot create
on its own: the first admin account.

Why this is necessary (flagged gap): every account-creation endpoint in
this system (POST /users/students, POST /users/teachers) requires an
already-authenticated Admin. On a freshly migrated, empty database there
is no admin to log in as, and there is no self-registration endpoint
(deliberately — see Part 3's design notes on why accounts are
centrally issued, not self-registered). Without this script, the system
is unbootable. Run this exactly once per new university deployment,
right after `alembic upgrade head`.

Usage:
    cd backend
    python -m scripts.seed
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.models.academic import Department
from app.models.profiles import Admin
from app.models.university import University
from app.models.user import User


DEFAULT_ADMIN_EMAIL = "admin@university.edu"
DEFAULT_ADMIN_PASSWORD = "AdminPassword123!"  # CHANGE THIS IMMEDIATELY after first login


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.query(University).first()
        if existing is not None:
            print(f"A university already exists (id={existing.id}, name='{existing.name}'). "
                  f"Seed script is a no-op to avoid creating duplicates. Exiting.")
            return

        university = University(
            name="Demo University",
            slug="demo-university",
            contact_email="registrar@university.edu",
        )
        db.add(university)
        db.flush()

        department = Department(
            university_id=university.id,
            name="Computer Science & Engineering",
            code="CSE",
        )
        db.add(department)
        db.flush()

        admin_user = User(
            university_id=university.id,
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin_user)
        db.flush()

        admin_profile = Admin(
            university_id=university.id,
            user_id=admin_user.id,
            full_name="System Administrator",
        )
        db.add(admin_profile)

        db.commit()

        print("Seed complete.")
        print(f"  University: {university.name} (id={university.id})")
        print(f"  Department: {department.name} ({department.code})")
        print(f"  Admin login: {DEFAULT_ADMIN_EMAIL} / {DEFAULT_ADMIN_PASSWORD}")
        print("  >>> Log in and change this password immediately via PUT /auth/password. <<<")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
