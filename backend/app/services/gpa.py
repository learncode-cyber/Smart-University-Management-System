"""
Pure GPA/grade functions — no DB, no FastAPI. Grade scale used here is
the common Bangladeshi university 4.00-point scale.
"""
from dataclasses import dataclass

_GRADE_TABLE = [
    (80, "A+", 4.00),
    (75, "A", 3.75),
    (70, "A-", 3.50),
    (65, "B+", 3.25),
    (60, "B", 3.00),
    (55, "B-", 2.75),
    (50, "C+", 2.50),
    (45, "C", 2.25),
    (40, "D", 2.00),
    (0, "F", 0.00),
]


def percentage_to_grade(percentage: float) -> tuple[str, float]:
    """Returns (letter_grade, grade_point) for a given percentage (0-100)."""
    if percentage < 0 or percentage > 100:
        raise ValueError("percentage must be between 0 and 100")
    for cutoff, letter, point in _GRADE_TABLE:
        if percentage >= cutoff:
            return letter, point
    return "F", 0.00  # unreachable given the 0-cutoff row, kept for safety


@dataclass
class CourseResult:
    grade_point: float
    credit_hours: int


def calculate_gpa(courses: list[CourseResult]) -> float | None:
    """
    Credit-weighted GPA: sum(grade_point * credit_hours) / sum(credit_hours).
    Returns None for an empty course list rather than dividing by zero —
    "no courses yet" is not the same as "GPA of 0.00".
    """
    total_credits = sum(c.credit_hours for c in courses)
    if total_credits == 0:
        return None
    weighted_sum = sum(c.grade_point * c.credit_hours for c in courses)
    return round(weighted_sum / total_credits, 2)
