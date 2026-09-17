# Local libraries
from src.feasibility.violation.sequence_end import SequenceEndViolation
from src.modeling.comeback import ComeBack
from src.modeling.step import Step
from src.utils.timeset import convert_nb_minutes_to_time_string
from tests.feasibility.helpers import build_employee, build_task


def test_sequence_end_violation_text_reports_the_employee_end_time_ub():
    employee = build_employee(end_time_ub=1020)
    task = build_task()
    last_step = Step(task, start_time=990, end_time=1020)
    comeback_step = Step(ComeBack(employee), arrival_time=1040, start_time=1040, end_time=1040)
    violation = SequenceEndViolation(employee, last_step, comeback_step)
    assert violation.text == (
        f"{employee.name} is supposed perform "
        f"{task.name} at {convert_nb_minutes_to_time_string(last_step.start_time)} "
        f"and then go to his/her final location, "
        f"which means that he/she is supposed to be at his/her final location at "
        f"{convert_nb_minutes_to_time_string(comeback_step.arrival_time)}. "
        f"However, {employee.name} must end to work no later than "
        f"{convert_nb_minutes_to_time_string(employee.end_time_ub)}."
    )


def test_sequence_end_violation_properties_return_constructor_arguments():
    employee = build_employee()
    last_step = Step(build_task(), start_time=990, end_time=1020)
    comeback_step = Step(ComeBack(employee), arrival_time=1040, start_time=1040, end_time=1040)
    violation = SequenceEndViolation(employee, last_step, comeback_step)
    assert violation.employee is employee
    assert violation.last_step is last_step
    assert violation.comeback_step is comeback_step
