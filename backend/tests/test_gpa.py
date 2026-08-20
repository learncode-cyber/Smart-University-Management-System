import pytest

from app.services.gpa import percentage_to_grade, calculate_gpa, CourseResult


def test_percentage_to_grade_a_plus():
    assert percentage_to_grade(85) == ("A+", 4.00)


def test_percentage_to_grade_boundary_exact():
    assert percentage_to_grade(80) == ("A+", 4.00)
    assert percentage_to_grade(79.99) == ("A", 3.75)


def test_percentage_to_grade_fail():
    assert percentage_to_grade(39.99) == ("F", 0.00)


def test_percentage_to_grade_zero():
    assert percentage_to_grade(0) == ("F", 0.00)


def test_percentage_to_grade_out_of_range_raises():
    with pytest.raises(ValueError):
        percentage_to_grade(101)
    with pytest.raises(ValueError):
        percentage_to_grade(-1)


def test_calculate_gpa_single_course():
    assert calculate_gpa([CourseResult(grade_point=4.00, credit_hours=3)]) == 4.00


def test_calculate_gpa_weighted_average():
    courses = [
        CourseResult(grade_point=4.00, credit_hours=3),  # 12.00
        CourseResult(grade_point=3.00, credit_hours=3),  # 9.00
        CourseResult(grade_point=2.00, credit_hours=2),  # 4.00
    ]
    # total credits = 8, weighted sum = 25.00 -> 3.125 -> rounds to 3.12 or 3.13
    assert calculate_gpa(courses) == round(25 / 8, 2)


def test_calculate_gpa_empty_list_returns_none():
    assert calculate_gpa([]) is None


def test_calculate_gpa_zero_credit_courses_returns_none():
    assert calculate_gpa([CourseResult(grade_point=4.00, credit_hours=0)]) is None
