# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.constraint import ImmediatePrecedence, SequenceFixed, SequenceOrderFixed
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import TaskDeletion, TaskInsertion
from src.modeling.solution import Solution
from tests.modeling.helpers import build_employee, build_instance, build_task


def test_neighborhood_with_no_operators_and_no_constraints_raises():
    instance = build_instance()
    solution = Solution(instance)
    with pytest.raises(ValueError):
        Neighborhood(solution=solution, operators=[])


def test_neighborhood_with_employee_carrying_sequence_fixed_and_another_constraint_raises():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance)
    with pytest.raises(ValueError):
        Neighborhood(solution=solution, operators=[],
                     constraints=[SequenceOrderFixed(employee), SequenceFixed(employee)])


def test_neighborhood_with_employee_carrying_several_non_sequence_fixed_constraints_is_accepted():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance)
    predecessor = build_task(instance, 0)
    successor = build_task(instance, 1)
    constraints = [SequenceOrderFixed(employee), ImmediatePrecedence(employee, predecessor, successor)]
    neighborhood = Neighborhood(solution=solution, operators=[], constraints=constraints)
    assert neighborhood.constraints == constraints


def test_neighborhood_with_operator_on_sequence_fixed_employee_raises():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
    with pytest.raises(ValueError):
        Neighborhood(solution=solution, operators=[operator], constraints=[SequenceFixed(employee)])


def test_neighborhood_with_operator_on_order_fixed_employee_is_accepted():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
    neighborhood = Neighborhood(solution=solution, operators=[operator],
                                constraints=[SequenceOrderFixed(employee)])
    assert neighborhood.employees == frozenset({employee})
    assert neighborhood.operators == [operator]


def test_neighborhood_target_tasks_aggregates_across_operators():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance)
    task_1 = build_task(instance, 0)
    task_2 = build_task(instance, 1)
    insertion = TaskInsertion(frozenset({employee}), frozenset({task_1}))
    deletion = TaskDeletion(frozenset({employee}), frozenset({task_2}))
    neighborhood = Neighborhood(solution=solution, operators=[insertion, deletion])
    assert neighborhood.target_tasks == frozenset({task_1, task_2})


def test_neighborhood_scope_is_deduced_from_operators_and_constraints():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance, 0)
    other_employee = build_employee(instance, 1)
    task = build_task(instance)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
    neighborhood = Neighborhood(solution=solution, operators=[operator],
                                constraints=[SequenceOrderFixed(other_employee)])
    assert neighborhood.scope == frozenset({employee, task, other_employee})
    assert neighborhood.employees == frozenset({employee, other_employee})
