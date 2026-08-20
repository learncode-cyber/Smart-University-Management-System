"""
Pure schedule conflict-detection — no DB, no FastAPI. O(n) per new-slot
check against existing slots; O(n^2) for a full conflict scan (fine at
university-department scale — a few hundred slots, not millions).
"""
from dataclasses import dataclass
from datetime import time


@dataclass
class ScheduleSlot:
    id: int | None  # None for a not-yet-created candidate slot
    day_of_week: str
    start_time: time
    end_time: time
    room: str
    teacher_id: int


@dataclass
class ScheduleConflict:
    slot_a_id: int | None
    slot_b_id: int | None
    reason: str  # "room" or "teacher"


def times_overlap(start1: time, end1: time, start2: time, end2: time) -> bool:
    """Standard interval-overlap check. Back-to-back classes (one ends
    exactly when the other starts) are NOT a conflict."""
    return start1 < end2 and start2 < end1


def slots_conflict(a: ScheduleSlot, b: ScheduleSlot) -> str | None:
    """Returns 'room', 'teacher', or None. If both room AND teacher
    collide, 'room' is reported first (arbitrary but deterministic)."""
    if a.day_of_week != b.day_of_week:
        return None
    if not times_overlap(a.start_time, a.end_time, b.start_time, b.end_time):
        return None
    if a.room == b.room:
        return "room"
    if a.teacher_id == b.teacher_id:
        return "teacher"
    return None


def find_conflicts_for_new_slot(candidate: ScheduleSlot, existing: list[ScheduleSlot]) -> list[ScheduleConflict]:
    """Used by the create/update endpoint to block a conflicting slot
    BEFORE it's saved."""
    conflicts = []
    for other in existing:
        if other.id == candidate.id:
            continue  # don't compare a slot against itself when checking an update
        reason = slots_conflict(candidate, other)
        if reason:
            conflicts.append(ScheduleConflict(slot_a_id=candidate.id, slot_b_id=other.id, reason=reason))
    return conflicts


def find_all_conflicts(slots: list[ScheduleSlot]) -> list[ScheduleConflict]:
    """Full pairwise scan — used by GET /schedule/conflicts to audit the
    entire schedule for any conflicts, e.g. after a bulk import."""
    conflicts = []
    for i in range(len(slots)):
        for j in range(i + 1, len(slots)):
            reason = slots_conflict(slots[i], slots[j])
            if reason:
                conflicts.append(ScheduleConflict(slot_a_id=slots[i].id, slot_b_id=slots[j].id, reason=reason))
    return conflicts
