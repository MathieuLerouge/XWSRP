# Local libraries
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.sequence import Sequence
from src.modeling.step import Step
from tests.modeling.helpers import build_employee, build_instance, build_sequence, build_task


###########
# __eq__  #
###########

def test_sequence_eq_with_identical_steps_returns_true():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    sequence_1 = build_sequence(instance, employee, [(task, 500)])
    sequence_2 = build_sequence(instance, employee, [(task, 500)])
    assert sequence_1 == sequence_2


def test_sequence_eq_with_different_employee_returns_false():
    instance = build_instance()
    employee_1 = build_employee(instance, 0)
    employee_2 = build_employee(instance, 1)
    task = build_task(instance)
    # The only difference between the two sequences is the employee.
    steps_1 = [Step(Departure(employee_1), 480, 480, 480), Step(task, 500, 500, 500 + task.duration),
              Step(ComeBack(employee_1), 560, 560, 560)]
    steps_2 = [Step(Departure(employee_2), 480, 480, 480), Step(task, 500, 500, 500 + task.duration),
              Step(ComeBack(employee_2), 560, 560, 560)]
    sequence_1 = Sequence(instance, employee_1, steps_1)
    sequence_2 = Sequence(instance, employee_2, steps_2)
    assert sequence_1 != sequence_2


def test_sequence_eq_ignores_instance_identity():
    # Two separate loads of the same instance file:
    # same employee (by name) but not the same Employee/Instance objects.
    employee_1 = build_employee(build_instance())
    employee_2 = build_employee(build_instance())
    task = build_task(build_instance())
    sequence_1 = build_sequence(build_instance(), employee_1, [(task, 500)])
    sequence_2 = build_sequence(build_instance(), employee_2, [(task, 500)])
    assert sequence_1 == sequence_2


def test_sequence_eq_with_different_step_count_returns_false():
    instance = build_instance()
    employee = build_employee(instance)
    task_1, task_2 = build_task(instance, 0), build_task(instance, 1)
    sequence_1 = build_sequence(instance, employee, [(task_1, 500)])
    sequence_2 = build_sequence(instance, employee, [(task_1, 500), (task_2, 600)])
    assert sequence_1 != sequence_2


def test_sequence_eq_with_different_step_order_returns_false():
    instance = build_instance()
    employee = build_employee(instance)
    task_1, task_2 = build_task(instance, 0), build_task(instance, 1)
    sequence_1 = build_sequence(instance, employee, [(task_1, 500), (task_2, 600)])
    sequence_2 = build_sequence(instance, employee, [(task_2, 500), (task_1, 600)])
    assert sequence_1 != sequence_2


def test_sequence_eq_with_non_sequence_returns_false():
    instance = build_instance()
    employee = build_employee(instance)
    sequence = build_sequence(instance, employee, [])
    assert sequence != "not a sequence"
