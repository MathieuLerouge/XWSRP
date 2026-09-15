# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import TaskDeletion, TaskInsertion
from src.explaining.neighborhood.restriction import ImmediatePrecedence, PrecedenceChain
from src.modeling.solution import Solution
from tests.modeling.helpers import build_employee, build_instance, build_task


def test_neighborhood_with_no_operators_and_no_restrictions_raises():
    instance = build_instance()
    solution = Solution(instance)
    with pytest.raises(ValueError):
        Neighborhood(solution=solution, operators=[])


def test_neighborhood_with_employee_carrying_several_restrictions_is_accepted():
    instance = build_instance()
    solution = Solution(instance)
    predecessor = build_task(instance, 0)
    successor = build_task(instance, 1)
    restrictions = [PrecedenceChain([]), ImmediatePrecedence(predecessor, successor)]
    neighborhood = Neighborhood(solution=solution, operators=[], restrictions=restrictions)
    assert neighborhood.restrictions == restrictions


def test_neighborhood_with_operator_on_order_fixed_employee_is_accepted():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
    neighborhood = Neighborhood(solution=solution, operators=[operator],
                                restrictions=[PrecedenceChain([])])
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


def test_neighborhood_scope_is_deduced_from_operators_only():
    # A Restriction has no scope of its own (see Restriction's docstring): even one naming a task the
    # operator doesn't, like task_2 below, must not affect Neighborhood.scope.
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance)
    task_1 = build_task(instance, 0)
    task_2 = build_task(instance, 1)
    operator = TaskInsertion(frozenset({employee}), frozenset({task_1}))
    neighborhood = Neighborhood(solution=solution, operators=[operator],
                                restrictions=[PrecedenceChain([task_1, task_2])])
    assert neighborhood.scope == operator.scope
