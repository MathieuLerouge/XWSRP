# Standard library
from typing import Optional

# Local libraries
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.sequence import Sequence
from src.modeling.solution import Solution
from src.modeling.step import Step
from src.modeling.task import Task
from src.reading.instance import extract_instance_from_file

# Global variables
_SMALL_INSTANCE_PATH = "data/evaluation/instances/instance_evaluation_1.xlsx"


def build_instance() -> Instance:
    return extract_instance_from_file(_SMALL_INSTANCE_PATH, True, True, True)


def build_employee(instance: Instance, index: int = 0) -> Employee:
    return instance.employees[index]


def build_task(instance: Instance, index: int = 0) -> Task:
    return instance.tasks[index]


def build_departure_step(employee: Employee, time: Optional[int] = None) -> Step:
    """
    Args:
        employee: Employee leaving home.
        time: Arrival/start/end time of the step, in minutes since midnight.
            Defaults to the employee's start_time_lb.

    Returns:
        Step: A Departure step for the employee, with arrival, start, and end times all equal to time.
    """
    if time is None:
        time = employee.start_time_lb
    return Step(Departure(employee), time, time, time)


def build_comeback_step(employee: Employee, time: int) -> Step:
    """
    Returns:
        Step: A ComeBack step for the employee, with arrival, start, and end times all equal to time.
    """
    return Step(ComeBack(employee), time, time, time)


def build_task_step(task: Task, start_time: int) -> Step:
    """
    Returns:
        Step: A step performing task, arriving and starting at start_time and
            ending at start_time + task.duration.
    """
    return Step(task, start_time, start_time, start_time + task.duration)


def build_sequence(instance: Instance, employee: Employee, task_steps: list[tuple[Task, int]]) -> Sequence:
    """
    Builds a Sequence made of a Departure step, one step per (task, start_time) pair in task_steps
    (in the given order), and a ComeBack step starting right after the last task step.

    Args:
        instance: Instance the sequence belongs to.
        employee: Employee whose sequence this is.
        task_steps: Ordered (Task, start_time) pairs to turn into steps.

    Returns:
        Sequence: The built sequence.
    """
    steps = [build_departure_step(employee)]
    for task, start_time in task_steps:
        steps.append(build_task_step(task, start_time))
    steps.append(build_comeback_step(employee, steps[-1].end_time))
    return Sequence(instance, employee, steps)


def build_solution(instance: Instance, name: str, overrides: dict[str, Sequence]) -> Solution:
    """
    Builds a Solution over every employee of instance, defaulting each employee's sequence to an
    empty one (Departure/ComeBack only) except for the employee names in overrides, whose Sequence
    is used instead.

    Args:
        instance: Instance the solution belongs to.
        name: Name of the solution.
        overrides: Mapping from employee name to the Sequence to use for that employee, in place of
            the default empty one.

    Returns:
        Solution: The built solution.
    """
    sequences = {employee.name: Sequence(instance, employee) for employee in instance.employees}
    sequences.update(overrides)
    return Solution(instance, name=name, sequences=sequences)
