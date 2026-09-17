# Local libraries
from src.feasibility.violation.employee_unavailability import EmployeeUnavailabilityViolation
from src.modeling.unavailability import Unavailability
from src.utils.location import Location
from src.utils.timeset import TimeInterval
from tests.feasibility.helpers import build_employee, build_task


def test_employee_unavailability_violation_text_reports_the_unavailability():
    task = build_task()
    employee = build_employee()
    unavailability = Unavailability(employee, name="U1", start_time=500, end_time=520, location=Location(0, 0))
    violation = EmployeeUnavailabilityViolation(task, employee, start_time=505, end_time=515,
                                                unavailability=unavailability)
    assert violation.text == (
        f"Task {task.name} is supposed to be performed "
        f"over {TimeInterval(505, 515)} by employee {employee.name} "
        f"while he/she is unavailable over {unavailability.time_windows[0]} "
        f"due to his/her unavailability {unavailability.name}."
    )


def test_employee_unavailability_violation_properties_return_constructor_arguments():
    task = build_task()
    employee = build_employee()
    unavailability = Unavailability(employee, name="U1", start_time=500, end_time=520, location=Location(0, 0))
    violation = EmployeeUnavailabilityViolation(task, employee, start_time=505, end_time=515,
                                                unavailability=unavailability)
    assert violation.task is task
    assert violation.employee is employee
    assert violation.start_time == 505
    assert violation.end_time == 515
    assert violation.unavailability is unavailability
