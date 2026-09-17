# Local libraries
from src.feasibility.violation.covering import CoveringViolation
from tests.feasibility.helpers import build_task


def test_covering_violation_text_names_the_unperformed_task():
    task = build_task()
    violation = CoveringViolation(task)
    assert violation.text == f"Task {task.name} is not performed while all tasks must be performed."


def test_covering_violation_task_property_returns_the_task():
    task = build_task()
    violation = CoveringViolation(task)
    assert violation.task is task
