"""
Pure grading/aggregation functions — no DB session, no FastAPI dependency.
These are the functions the "Testability" standard from Part 0 asks for:
unit-testable in isolation (see tests/test_grading.py).
"""
from dataclasses import dataclass


@dataclass
class GradableAnswer:
    """Minimal view of one exam_answer row needed to aggregate a score."""
    marks_possible: float
    score: float | None  # None means "not yet graded"


def is_fully_graded(answers: list[GradableAnswer]) -> bool:
    """An exam submission is fully graded only when every answer has a
    non-null score (MCQ answers get scored automatically at submit time;
    the rest need a teacher's grade first)."""
    return all(a.score is not None for a in answers)


def calculate_total_score(answers: list[GradableAnswer]) -> float | None:
    """
    Sums per-question scores into the submission's total_score.
    Returns None (not a partial number) if grading isn't complete yet —
    a partial sum would be misleading as a "final" score on a dashboard.
    """
    if not answers:
        return None
    if not is_fully_graded(answers):
        return None
    return round(sum(a.score for a in answers), 2)


def grade_mcq_answer(selected_option_is_correct: bool | None, question_marks: float) -> float:
    """
    Auto-grade a single MCQ answer.
    - Correct option selected -> full marks
    - Wrong option selected -> 0
    - No option selected (student skipped it) -> 0
    """
    if selected_option_is_correct:
        return question_marks
    return 0.0
