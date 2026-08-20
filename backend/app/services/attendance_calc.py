"""
Pure attendance-percentage functions — no DB, no FastAPI. Mirrors the
same "pure function" pattern as services/grading.py, per Part 0's
testability standard.
"""
from dataclasses import dataclass


@dataclass
class AttendanceTally:
    total_classes: int
    present_count: int  # PRESENT and LATE both count as "attended"; EXCUSED counts as neither present nor absent


def calculate_attendance_percentage(tally: AttendanceTally) -> float:
    """Returns 0-100. If there are no classes recorded yet, returns 100.0
    (an empty record isn't "failing" attendance — there's simply nothing
    to be low on yet)."""
    if tally.total_classes == 0:
        return 100.0
    return round((tally.present_count / tally.total_classes) * 100, 2)


def is_below_threshold(percentage: float, threshold_percent: float) -> bool:
    return percentage < threshold_percent


def tally_from_statuses(statuses: list[str]) -> AttendanceTally:
    """
    Converts a raw list of attendance_status values (as strings, e.g.
    from a DB query) into a tally. PRESENT and LATE count toward
    `present_count`; EXCUSED is removed from `total_classes` entirely
    (an excused absence shouldn't drag the percentage down); ABSENT
    counts toward total_classes but not present_count.
    """
    total = 0
    present = 0
    for status in statuses:
        if status == "excused":
            continue
        total += 1
        if status in ("present", "late"):
            present += 1
    return AttendanceTally(total_classes=total, present_count=present)
