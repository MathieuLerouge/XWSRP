# Local libraries
from src.feasibility.violation.task_time_window import TaskTimeWindowViolation
from src.utils.timeset import TimeInterval
from tests.feasibility.helpers import build_employee, build_task


def test_task_time_window_violation_text_reports_performed_and_available_windows():
    task = build_task(start_time_lb=480, end_time_ub=600)
    employee = build_employee()
    violation = TaskTimeWindowViolation(task, employee, start_time=550, end_time=580)
    assert violation.text == (
        f"Task {task.name} is supposed to be performed over "
        f"{TimeInterval(550, 580)} while it is available only over {task.time_windows.as_string()}."
    )


def test_task_time_window_violation_properties_return_constructor_arguments():
    task = build_task()
    employee = build_employee()
    violation = TaskTimeWindowViolation(task, employee, start_time=500, end_time=530)
    assert violation.task is task
    assert violation.employee is employee
    assert violation.start_time == 500
    assert violation.end_time == 530
