"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-21

NOTE: hand-written to match app/models/*.py exactly, table-by-table in FK
dependency order (parents before children). This sandbox has no network
access to install SQLAlchemy/Alembic/Postgres, so this could not be
verified end-to-end with `alembic revision --autogenerate` here. Before
your first real run:
    pip install -r requirements.txt
    createdb ums_db   # or update DATABASE_URL in .env
    alembic upgrade head
If autogenerate against a real Postgres instance produces any diff
against this file, that's a signal to review — but the model files are
the source of truth either way, so trust `alembic revision --autogenerate
--autogenerate -m "sync"` if this ever drifts.
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------------- #
    # 1. universities — root tenant table, no FKs
    # ---------------------------------------------------------------- #
    op.create_table(
        "universities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("contact_email", sa.String(255)),
        sa.Column("address", sa.String(500)),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("primary_color", sa.String(20)),
        sa.Column("secondary_color", sa.String(20)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # ---------------------------------------------------------------- #
    # 2. users — auth identity, depends on universities
    # ---------------------------------------------------------------- #
    user_role_enum = sa.Enum("student", "teacher", "admin", "parent", name="user_role")
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("university_id", "email", name="uq_users_university_email"),
    )
    op.create_index("ix_users_university_id", "users", ["university_id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_university_role", "users", ["university_id", "role"])

    # ---------------------------------------------------------------- #
    # 3. departments — depends on universities
    # ---------------------------------------------------------------- #
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("university_id", "code", name="uq_department_university_code"),
    )
    op.create_index("ix_departments_university_id", "departments", ["university_id"])

    # ---------------------------------------------------------------- #
    # 4. students — depends on users, departments
    # ---------------------------------------------------------------- #
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("roll_number", sa.String(30), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("phone", sa.String(30)),
        sa.Column("address", sa.String(500)),
        sa.Column("profile_photo_url", sa.String(500)),
        sa.Column("enrollment_year", sa.Integer(), nullable=False),
        sa.Column("current_semester", sa.String(20)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("university_id", "roll_number", name="uq_student_university_roll"),
    )
    op.create_index("ix_students_university_id", "students", ["university_id"])
    op.create_index("ix_students_department_id", "students", ["department_id"])

    # ---------------------------------------------------------------- #
    # 5. teachers — depends on users, departments
    # ---------------------------------------------------------------- #
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("employee_id", sa.String(30), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("designation", sa.String(100)),
        sa.Column("phone", sa.String(30)),
        sa.Column("profile_photo_url", sa.String(500)),
        sa.Column("joined_at", sa.Date()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("university_id", "employee_id", name="uq_teacher_university_employee"),
    )
    op.create_index("ix_teachers_university_id", "teachers", ["university_id"])
    op.create_index("ix_teachers_department_id", "teachers", ["department_id"])

    # ---------------------------------------------------------------- #
    # 6. admins — depends on users
    # ---------------------------------------------------------------- #
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(30)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_admins_university_id", "admins", ["university_id"])

    # ---------------------------------------------------------------- #
    # 7. parents — depends on users
    # ---------------------------------------------------------------- #
    op.create_table(
        "parents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(30)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_parents_university_id", "parents", ["university_id"])

    # ---------------------------------------------------------------- #
    # 8. parent_student_links — depends on parents, students
    # ---------------------------------------------------------------- #
    parent_relationship_enum = sa.Enum("father", "mother", "guardian", "other", name="parent_relationship")
    op.create_table(
        "parent_student_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("parents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", parent_relationship_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("parent_id", "student_id", name="uq_parent_student"),
    )
    op.create_index("ix_parent_student_links_parent_id", "parent_student_links", ["parent_id"])
    op.create_index("ix_parent_student_student", "parent_student_links", ["student_id"])

    # ---------------------------------------------------------------- #
    # 9. courses — depends on departments
    # ---------------------------------------------------------------- #
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("credit_hours", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("university_id", "code", name="uq_course_university_code"),
    )
    op.create_index("ix_courses_university_id", "courses", ["university_id"])
    op.create_index("ix_courses_department_id", "courses", ["department_id"])

    # ---------------------------------------------------------------- #
    # 10. course_sections — depends on courses, teachers
    # ---------------------------------------------------------------- #
    op.create_table(
        "course_sections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("section_name", sa.String(20), nullable=False, server_default="A"),
        sa.Column("semester", sa.String(20), nullable=False),
        sa.Column("academic_year", sa.String(9), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_course_sections_university_id", "course_sections", ["university_id"])
    op.create_index("ix_course_sections_course_id", "course_sections", ["course_id"])
    op.create_index("ix_course_sections_teacher_id", "course_sections", ["teacher_id"])
    op.create_index(
        "ix_course_sections_teacher_semester", "course_sections",
        ["teacher_id", "semester", "academic_year"],
    )

    # ---------------------------------------------------------------- #
    # 11. enrollments — depends on students, course_sections
    # ---------------------------------------------------------------- #
    op.create_table(
        "enrollments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("course_section_id", sa.Integer(), sa.ForeignKey("course_sections.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("student_id", "course_section_id", name="uq_enrollment_student_section"),
    )
    op.create_index("ix_enrollments_university_id", "enrollments", ["university_id"])
    op.create_index("ix_enrollment_section", "enrollments", ["course_section_id"])

    # ---------------------------------------------------------------- #
    # 12. exams — depends on course_sections, teachers
    # ---------------------------------------------------------------- #
    exam_status_enum = sa.Enum(
        "draft", "scheduled", "open", "closed", "grading_done", "published", name="exam_status"
    )
    op.create_table(
        "exams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("course_section_id", sa.Integer(), sa.ForeignKey("course_sections.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_by_teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", exam_status_enum, nullable=False, server_default="draft"),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("total_marks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_exams_university_id", "exams", ["university_id"])
    op.create_index("ix_exams_course_section_id", "exams", ["course_section_id"])
    op.create_index("ix_exams_status", "exams", ["status"])
    op.create_index("ix_exams_section_status", "exams", ["course_section_id", "status"])

    # ---------------------------------------------------------------- #
    # 13. exam_questions — depends on exams
    # ---------------------------------------------------------------- #
    question_type_enum = sa.Enum("mcq", "short_answer", "descriptive", "coding", name="question_type")
    op.create_table(
        "exam_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_type", question_type_enum, nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("marks", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("starter_code", sa.Text()),
        sa.Column("expected_output", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_exam_questions_exam", "exam_questions", ["exam_id", "order_index"])

    # ---------------------------------------------------------------- #
    # 14. exam_options — depends on exam_questions
    # ---------------------------------------------------------------- #
    op.create_table(
        "exam_options",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("exam_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_exam_options_question_id", "exam_options", ["question_id"])

    # ---------------------------------------------------------------- #
    # 15. exam_submissions — depends on exams, students
    # ---------------------------------------------------------------- #
    submission_status_enum = sa.Enum("in_progress", "submitted", "graded", name="submission_status")
    op.create_table(
        "exam_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exams.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", submission_status_enum, nullable=False, server_default="in_progress"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("submitted_at", sa.DateTime()),
        sa.Column("total_score", sa.Numeric(6, 2)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("exam_id", "student_id", name="uq_submission_exam_student"),
    )
    op.create_index("ix_exam_submissions_university_id", "exam_submissions", ["university_id"])
    op.create_index("ix_exam_submissions_exam_id", "exam_submissions", ["exam_id"])
    op.create_index("ix_exam_submissions_student_id", "exam_submissions", ["student_id"])

    # ---------------------------------------------------------------- #
    # 16. exam_answers — depends on exam_submissions, exam_questions, exam_options, teachers
    # ---------------------------------------------------------------- #
    op.create_table(
        "exam_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("exam_submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("exam_questions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("selected_option_id", sa.Integer(), sa.ForeignKey("exam_options.id", ondelete="SET NULL")),
        sa.Column("answer_text", sa.Text()),
        sa.Column("score", sa.Numeric(6, 2)),
        sa.Column("feedback", sa.Text()),
        sa.Column("graded_by_teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="SET NULL")),
        sa.Column("graded_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("submission_id", "question_id", name="uq_answer_submission_question"),
    )
    op.create_index("ix_exam_answers_submission_id", "exam_answers", ["submission_id"])

    # ---------------------------------------------------------------- #
    # 17. attendance_records — depends on course_sections, students, teachers
    # ---------------------------------------------------------------- #
    attendance_status_enum = sa.Enum("present", "absent", "late", "excused", name="attendance_status")
    op.create_table(
        "attendance_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("course_section_id", sa.Integer(), sa.ForeignKey("course_sections.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", attendance_status_enum, nullable=False),
        sa.Column("marked_by_teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("corrected_by_teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="SET NULL")),
        sa.Column("corrected_at", sa.DateTime()),
        sa.Column("correction_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("course_section_id", "student_id", "date", name="uq_attendance_section_student_date"),
    )
    op.create_index("ix_attendance_university_id", "attendance_records", ["university_id"])
    op.create_index("ix_attendance_student_date", "attendance_records", ["student_id", "date"])
    op.create_index("ix_attendance_section_date", "attendance_records", ["course_section_id", "date"])

    # ---------------------------------------------------------------- #
    # 18. results — depends on students, course_sections, teachers, admins
    # ---------------------------------------------------------------- #
    result_status_enum = sa.Enum("draft", "submitted", "approved", "published", "rejected", name="result_status")
    op.create_table(
        "results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("course_section_id", sa.Integer(), sa.ForeignKey("course_sections.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("total_marks_obtained", sa.Numeric(6, 2), nullable=False),
        sa.Column("total_marks_possible", sa.Numeric(6, 2), nullable=False),
        sa.Column("grade_letter", sa.String(2)),
        sa.Column("grade_point", sa.Numeric(3, 2)),
        sa.Column("status", result_status_enum, nullable=False, server_default="draft"),
        sa.Column("submitted_by_teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="SET NULL")),
        sa.Column("submitted_at", sa.DateTime()),
        sa.Column("approved_by_admin_id", sa.Integer(), sa.ForeignKey("admins.id", ondelete="SET NULL")),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column("rejection_reason", sa.String(1000)),
        sa.Column("published_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("student_id", "course_section_id", name="uq_result_student_section"),
    )
    op.create_index("ix_results_university_id", "results", ["university_id"])
    op.create_index("ix_results_student_status", "results", ["student_id", "status"])

    # ---------------------------------------------------------------- #
    # 19. semester_gpas — depends on students
    # ---------------------------------------------------------------- #
    op.create_table(
        "semester_gpas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("semester", sa.String(20), nullable=False),
        sa.Column("academic_year", sa.String(9), nullable=False),
        sa.Column("semester_gpa", sa.Numeric(3, 2), nullable=False),
        sa.Column("cumulative_gpa", sa.Numeric(3, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("student_id", "semester", "academic_year", name="uq_semester_gpa_student_period"),
    )
    op.create_index("ix_semester_gpas_university_id", "semester_gpas", ["university_id"])
    op.create_index("ix_semester_gpas_student_id", "semester_gpas", ["student_id"])

    # ---------------------------------------------------------------- #
    # 20. fee_structures — depends on departments
    # ---------------------------------------------------------------- #
    op.create_table(
        "fee_structures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id", ondelete="RESTRICT")),
        sa.Column("fee_type", sa.String(100), nullable=False),
        sa.Column("semester", sa.String(20), nullable=False),
        sa.Column("academic_year", sa.String(9), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_fee_structures_university_id", "fee_structures", ["university_id"])

    # ---------------------------------------------------------------- #
    # 21. invoices — depends on students, fee_structures
    # ---------------------------------------------------------------- #
    invoice_status_enum = sa.Enum("pending", "partial", "paid", "overdue", "waived", name="invoice_status")
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("fee_structure_id", sa.Integer(), sa.ForeignKey("fee_structures.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount_due", sa.Numeric(10, 2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", invoice_status_enum, nullable=False, server_default="pending"),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_invoices_university_id", "invoices", ["university_id"])
    op.create_index("ix_invoices_student_status", "invoices", ["student_id", "status"])
    op.create_index("ix_invoices_due_date_status", "invoices", ["due_date", "status"])

    # ---------------------------------------------------------------- #
    # 22. fee_payments — depends on invoices, admins
    # ---------------------------------------------------------------- #
    payment_method_enum = sa.Enum("cash", "bank_transfer", "mobile_banking", "card", "other", name="payment_method")
    op.create_table(
        "fee_payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("method", payment_method_enum, nullable=False),
        sa.Column("transaction_ref", sa.String(100)),
        sa.Column("paid_at", sa.DateTime(), nullable=False),
        sa.Column("recorded_by_admin_id", sa.Integer(), sa.ForeignKey("admins.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_fee_payments_invoice_id", "fee_payments", ["invoice_id"])

    # ---------------------------------------------------------------- #
    # 23. class_schedules — depends on course_sections, teachers
    # ---------------------------------------------------------------- #
    day_of_week_enum = sa.Enum(
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", name="day_of_week"
    )
    op.create_table(
        "class_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("course_section_id", sa.Integer(), sa.ForeignKey("course_sections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("day_of_week", day_of_week_enum, nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("room", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_class_schedules_university_id", "class_schedules", ["university_id"])
    op.create_index("ix_schedule_room_day", "class_schedules", ["room", "day_of_week"])
    op.create_index("ix_schedule_teacher_day", "class_schedules", ["teacher_id", "day_of_week"])

    # ---------------------------------------------------------------- #
    # 24. notifications — depends on users
    # ---------------------------------------------------------------- #
    notification_type_enum = sa.Enum(
        "exam_published", "result_published", "attendance_warning",
        "fee_due", "fee_overdue", "schedule_change", "general",
        name="notification_type",
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", notification_type_enum, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("related_entity_type", sa.String(50)),
        sa.Column("related_entity_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_university_id", "notifications", ["university_id"])
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "is_read", "created_at"])


def downgrade() -> None:
    # drop in reverse dependency order
    op.drop_table("notifications")
    op.drop_table("class_schedules")
    op.drop_table("fee_payments")
    op.drop_table("invoices")
    op.drop_table("fee_structures")
    op.drop_table("semester_gpas")
    op.drop_table("results")
    op.drop_table("attendance_records")
    op.drop_table("exam_answers")
    op.drop_table("exam_submissions")
    op.drop_table("exam_options")
    op.drop_table("exam_questions")
    op.drop_table("exams")
    op.drop_table("enrollments")
    op.drop_table("course_sections")
    op.drop_table("courses")
    op.drop_table("parent_student_links")
    op.drop_table("parents")
    op.drop_table("admins")
    op.drop_table("teachers")
    op.drop_table("students")
    op.drop_table("departments")
    op.drop_table("users")
    op.drop_table("universities")

    # drop enum types (postgres requires explicit drop; SQLAlchemy's
    # Enum.drop() handles the `DROP TYPE IF EXISTS ...` for us)
    for enum_name in [
        "notification_type", "day_of_week", "payment_method", "invoice_status",
        "result_status", "attendance_status", "submission_status",
        "question_type", "exam_status", "parent_relationship", "user_role",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
