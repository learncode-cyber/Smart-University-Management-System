from datetime import time

from app.services.schedule_calc import (
    ScheduleSlot, times_overlap, slots_conflict, find_conflicts_for_new_slot, find_all_conflicts,
)


def test_times_overlap_true():
    assert times_overlap(time(10, 0), time(11, 0), time(10, 30), time(11, 30)) is True


def test_times_overlap_false_back_to_back():
    assert times_overlap(time(10, 0), time(11, 0), time(11, 0), time(12, 0)) is False


def test_times_overlap_false_no_overlap():
    assert times_overlap(time(9, 0), time(10, 0), time(11, 0), time(12, 0)) is False


def test_slots_conflict_same_room_different_teacher():
    a = ScheduleSlot(1, "monday", time(10, 0), time(11, 0), "Room-101", teacher_id=1)
    b = ScheduleSlot(2, "monday", time(10, 30), time(11, 30), "Room-101", teacher_id=2)
    assert slots_conflict(a, b) == "room"


def test_slots_conflict_same_teacher_different_room():
    a = ScheduleSlot(1, "monday", time(10, 0), time(11, 0), "Room-101", teacher_id=5)
    b = ScheduleSlot(2, "monday", time(10, 30), time(11, 30), "Room-202", teacher_id=5)
    assert slots_conflict(a, b) == "teacher"


def test_slots_conflict_different_day_no_conflict():
    a = ScheduleSlot(1, "monday", time(10, 0), time(11, 0), "Room-101", teacher_id=5)
    b = ScheduleSlot(2, "tuesday", time(10, 0), time(11, 0), "Room-101", teacher_id=5)
    assert slots_conflict(a, b) is None


def test_slots_conflict_no_overlap_no_conflict():
    a = ScheduleSlot(1, "monday", time(9, 0), time(10, 0), "Room-101", teacher_id=5)
    b = ScheduleSlot(2, "monday", time(10, 0), time(11, 0), "Room-101", teacher_id=5)
    assert slots_conflict(a, b) is None


def test_find_conflicts_for_new_slot_excludes_self():
    candidate = ScheduleSlot(1, "monday", time(10, 0), time(11, 0), "Room-101", teacher_id=1)
    existing = [candidate]  # updating itself shouldn't self-conflict
    assert find_conflicts_for_new_slot(candidate, existing) == []


def test_find_all_conflicts_full_scan():
    slots = [
        ScheduleSlot(1, "monday", time(10, 0), time(11, 0), "Room-101", teacher_id=1),
        ScheduleSlot(2, "monday", time(10, 30), time(11, 30), "Room-101", teacher_id=2),
        ScheduleSlot(3, "tuesday", time(9, 0), time(10, 0), "Room-202", teacher_id=3),
    ]
    conflicts = find_all_conflicts(slots)
    assert len(conflicts) == 1
    assert conflicts[0].reason == "room"
