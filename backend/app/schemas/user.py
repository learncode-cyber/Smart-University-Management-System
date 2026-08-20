"""
Schemas for /api/v1/users/*. Separate Create/Update/Response shapes per
role, since a student create payload and a teacher create payload are
genuinely different data.
"""
from datetime import date

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


# ---- shared "me" (own profile) ----

class UserMeResponse(BaseModel):
    id: int
    email: str
    role: UserRole
    is_active: bool
    # merged in from the role-specific profile table (Student/Teacher/Admin/Parent)
    # so the frontend has one endpoint for "my profile" regardless of role
    full_name: str | None = None
    phone: str | None = None
    address: str | None = None  # students only
    profile_photo_url: str | None = None  # students/teachers only

    model_config = {"from_attributes": True}


class UserMeUpdateRequest(BaseModel):
    """
    Auth-identity fields (email) plus SELF-editable personal fields.
    Deliberately excludes administrative fields (roll_number,
    department_id, enrollment_year, employee_id) — those still require
    Admin action via /users/students/{id} or /users/teachers/{id}, since
    they're institutional record-keeping, not personal info.
    """
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    profile_photo_url: str | None = Field(default=None, max_length=500)


# ---- Students ----

class StudentCreateRequest(BaseModel):
    email: EmailStr
    # Admin sets an initial password when onboarding; we don't auto-generate
    # one here to keep this build phase simple — flagged as an assumption.
    # A production version would email a "set your password" link instead
    # of the admin ever seeing/choosing the student's password.
    initial_password: str = Field(min_length=8, max_length=128)

    department_id: int
    roll_number: str = Field(max_length=30)
    full_name: str = Field(max_length=255)
    date_of_birth: date | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    enrollment_year: int
    current_semester: str | None = Field(default=None, max_length=20)


class StudentUpdateRequest(BaseModel):
    department_id: int | None = None
    full_name: str | None = Field(default=None, max_length=255)
    date_of_birth: date | None = None
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    current_semester: str | None = Field(default=None, max_length=20)


class StudentResponse(BaseModel):
    id: int
    user_id: int
    email: str
    is_active: bool
    department_id: int
    roll_number: str
    full_name: str
    date_of_birth: date | None
    phone: str | None
    address: str | None
    enrollment_year: int
    current_semester: str | None

    model_config = {"from_attributes": True}


# ---- Teachers ----

class TeacherCreateRequest(BaseModel):
    email: EmailStr
    initial_password: str = Field(min_length=8, max_length=128)

    department_id: int
    employee_id: str = Field(max_length=30)
    full_name: str = Field(max_length=255)
    designation: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    joined_at: date | None = None


class TeacherUpdateRequest(BaseModel):
    department_id: int | None = None
    full_name: str | None = Field(default=None, max_length=255)
    designation: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=30)


class TeacherResponse(BaseModel):
    id: int
    user_id: int
    email: str
    is_active: bool
    department_id: int
    employee_id: str
    full_name: str
    designation: str | None
    phone: str | None
    joined_at: date | None

    model_config = {"from_attributes": True}
