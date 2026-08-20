"""
Unit tests for app/services/grading.py — pure functions, no DB needed.
Run with: pytest tests/test_grading.py
"""
from app.services.grading import (
    GradableAnswer, is_fully_graded, calculate_total_score, grade_mcq_answer,
)


def test_grade_mcq_answer_correct():
    assert grade_mcq_answer(selected_option_is_correct=True, question_marks=5) == 5


def test_grade_mcq_answer_incorrect():
    assert grade_mcq_answer(selected_option_is_correct=False, question_marks=5) == 0


def test_grade_mcq_answer_unanswered():
    assert grade_mcq_answer(selected_option_is_correct=None, question_marks=5) == 0


def test_is_fully_graded_true_when_all_scored():
    answers = [GradableAnswer(marks_possible=5, score=5), GradableAnswer(marks_possible=10, score=7)]
    assert is_fully_graded(answers) is True


def test_is_fully_graded_false_when_one_ungraded():
    answers = [GradableAnswer(marks_possible=5, score=5), GradableAnswer(marks_possible=10, score=None)]
    assert is_fully_graded(answers) is False


def test_calculate_total_score_sums_correctly():
    answers = [
        GradableAnswer(marks_possible=5, score=5),
        GradableAnswer(marks_possible=10, score=7.5),
        GradableAnswer(marks_possible=3, score=0),
    ]
    assert calculate_total_score(answers) == 12.5


def test_calculate_total_score_none_when_incomplete():
    answers = [GradableAnswer(marks_possible=5, score=5), GradableAnswer(marks_possible=10, score=None)]
    assert calculate_total_score(answers) is None


def test_calculate_total_score_none_when_empty():
    assert calculate_total_score([]) is None


def test_calculate_total_score_rounds_to_two_decimals():
    answers = [GradableAnswer(marks_possible=3, score=1.005), GradableAnswer(marks_possible=3, score=1.001)]
    assert calculate_total_score(answers) == 2.01
