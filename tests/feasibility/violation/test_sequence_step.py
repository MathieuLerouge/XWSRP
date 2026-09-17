# Local libraries
from src.feasibility.violation.sequence_step import SequenceStepViolation
from src.modeling.step import Step
from src.utils.timeset import convert_nb_minutes_to_time_string
from tests.feasibility.helpers import build_employee, build_task


def test_sequence_step_violation_text_without_lunch_break_performs_then_perform():
    employee = build_employee()
    previous_task = build_task(name="T1")
    task = build_task(name="T2")
    previous_step = Step(previous_task, start_time=500, end_time=530)
    step = Step(task, start_time=540, end_time=570)
    violation = SequenceStepViolation(employee, previous_step, step, crosses_lunch_break=False,
                                      allowed_traveling_duration=10, actual_traveling_duration=25)
    assert violation.text == (
        f"{employee.name} is supposed to perform "
        f"{previous_task.name} at {convert_nb_minutes_to_time_string(previous_step.start_time)}, "
        f"then perform {task.name} at {convert_nb_minutes_to_time_string(step.start_time)}. "
        f"It means that {employee.name} is supposed to travel from "
        f"{previous_task.name} to {task.name} in less than 10min. "
        f"However, such a travel takes 25min."
    )


def test_sequence_step_violation_text_with_lunch_break_mentions_the_lunch_break():
    employee = build_employee()
    previous_task = build_task(name="T1")
    task = build_task(name="T2")
    previous_step = Step(previous_task, start_time=500, end_time=530)
    step = Step(task, start_time=600, end_time=630)
    violation = SequenceStepViolation(employee, previous_step, step, crosses_lunch_break=True,
                                      allowed_traveling_duration=10, actual_traveling_duration=25)
    assert violation.text == (
        f"{employee.name} is supposed to perform "
        f"{previous_task.name} at {convert_nb_minutes_to_time_string(previous_step.start_time)}, "
        f"then have a lunch break and perform {task.name} at "
        f"{convert_nb_minutes_to_time_string(step.start_time)}. "
        f"It means that {employee.name} is supposed to travel from "
        f"{previous_task.name} to {task.name} in less than 10min. "
        f"However, such a travel takes 25min."
    )


def test_sequence_step_violation_properties_return_constructor_arguments():
    employee = build_employee()
    previous_step = Step(build_task(name="T1"), start_time=500, end_time=530)
    step = Step(build_task(name="T2"), start_time=540, end_time=570)
    violation = SequenceStepViolation(employee, previous_step, step, crosses_lunch_break=False,
                                      allowed_traveling_duration=10, actual_traveling_duration=25)
    assert violation.employee is employee
    assert violation.previous_step is previous_step
    assert violation.step is step
    assert violation.crosses_lunch_break is False
    assert violation.allowed_traveling_duration == 10
    assert violation.actual_traveling_duration == 25
