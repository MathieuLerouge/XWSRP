# Local libraries
from src.feasibility.violation.sequence_start import SequenceStartViolation
from src.modeling.departure import Departure
from src.modeling.step import Step
from src.utils.timeset import convert_nb_minutes_to_time_string
from tests.feasibility.helpers import build_employee, build_task


def test_sequence_start_violation_text_reports_the_employee_start_time_lb():
    employee = build_employee(start_time_lb=480)
    departure_step = Step(Departure(employee), start_time=450, end_time=450)
    task = build_task()
    first_step = Step(task, start_time=470, end_time=500)
    violation = SequenceStartViolation(employee, departure_step, first_step)
    assert violation.text == (
        f"{employee.name} is supposed to perform "
        f"task {task.name} at {convert_nb_minutes_to_time_string(first_step.start_time)}, "
        f"which means that he/she is supposed to leave their initial location at "
        f"{convert_nb_minutes_to_time_string(departure_step.start_time)}. "
        f"However, he/she must not start to work before "
        f"{convert_nb_minutes_to_time_string(employee.start_time_lb)}."
    )


def test_sequence_start_violation_properties_return_constructor_arguments():
    employee = build_employee()
    departure_step = Step(Departure(employee), start_time=450, end_time=450)
    first_step = Step(build_task(), start_time=470, end_time=500)
    violation = SequenceStartViolation(employee, departure_step, first_step)
    assert violation.employee is employee
    assert violation.departure_step is departure_step
    assert violation.first_step is first_step
