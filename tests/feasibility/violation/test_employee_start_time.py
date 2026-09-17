# Local libraries
from src.feasibility.violation.employee_start_time import EmployeeStartTimeViolation
from src.utils.timeset import TimeInterval, convert_nb_minutes_to_time_string
from tests.feasibility.helpers import build_employee, build_task


def test_employee_start_time_violation_text_reports_the_employee_start_time_lb():
    task = build_task()
    employee = build_employee(start_time_lb=480)
    violation = EmployeeStartTimeViolation(task, employee, start_time=400, end_time=430)
    assert violation.text == (
        f"Task {task.name} is supposed to be performed over "
        f"{TimeInterval(400, 430)} by employee {employee.name} while he/she must start working at "
        f"{convert_nb_minutes_to_time_string(employee.start_time_lb)}."
    )


def test_employee_start_time_violation_properties_return_constructor_arguments():
    task = build_task()
    employee = build_employee()
    violation = EmployeeStartTimeViolation(task, employee, start_time=400, end_time=430)
    assert violation.task is task
    assert violation.employee is employee
    assert violation.start_time == 400
    assert violation.end_time == 430
