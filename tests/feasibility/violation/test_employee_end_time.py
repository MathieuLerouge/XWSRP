# Local libraries
from src.feasibility.violation.employee_end_time import EmployeeEndTimeViolation
from src.utils.timeset import TimeInterval, convert_nb_minutes_to_time_string
from tests.feasibility.helpers import build_employee, build_task


def test_employee_end_time_violation_text_reports_the_employee_end_time_ub():
    task = build_task()
    employee = build_employee(end_time_ub=1020)
    violation = EmployeeEndTimeViolation(task, employee, start_time=1030, end_time=1060)
    assert violation.text == (
        f"Task {task.name} is supposed to be performed over "
        f"{TimeInterval(1030, 1060)} by employee {employee.name} while he/she must end working at "
        f"{convert_nb_minutes_to_time_string(employee.end_time_ub)}."
    )


def test_employee_end_time_violation_properties_return_constructor_arguments():
    task = build_task()
    employee = build_employee()
    violation = EmployeeEndTimeViolation(task, employee, start_time=1030, end_time=1060)
    assert violation.task is task
    assert violation.employee is employee
    assert violation.start_time == 1030
    assert violation.end_time == 1060
