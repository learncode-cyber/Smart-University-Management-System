from app.services.attendance_calc import (
    AttendanceTally, calculate_attendance_percentage, is_below_threshold, tally_from_statuses,
)


def test_percentage_full_attendance():
    assert calculate_attendance_percentage(AttendanceTally(10, 10)) == 100.0


def test_percentage_zero_attendance():
    assert calculate_attendance_percentage(AttendanceTally(10, 0)) == 0.0


def test_percentage_partial():
    assert calculate_attendance_percentage(AttendanceTally(8, 6)) == 75.0


def test_percentage_no_classes_yet_defaults_to_100():
    assert calculate_attendance_percentage(AttendanceTally(0, 0)) == 100.0


def test_is_below_threshold_true():
    assert is_below_threshold(70.0, 75.0) is True


def test_is_below_threshold_false():
    assert is_below_threshold(80.0, 75.0) is False


def test_is_below_threshold_exact_boundary_not_below():
    assert is_below_threshold(75.0, 75.0) is False


def test_tally_from_statuses_counts_present_and_late():
    statuses = ["present", "present", "late", "absent"]
    tally = tally_from_statuses(statuses)
    assert tally.total_classes == 4
    assert tally.present_count == 3


def test_tally_from_statuses_excludes_excused_from_total():
    statuses = ["present", "excused", "absent"]
    tally = tally_from_statuses(statuses)
    assert tally.total_classes == 2  # excused day doesn't count toward total
    assert tally.present_count == 1
