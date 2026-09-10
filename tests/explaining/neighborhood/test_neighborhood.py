# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.constraint import SequenceFixed, SequenceOrderFixed
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import TaskDeletion, TaskInsertion
from src.modeling.solution import Solution
from tests.modeling.helpers import build_employee, build_instance, build_task


def test_neighborhood_with_empty_employees_raises():
    instance = build_instance()
    solution = Solution(instance)
    with pytest.raises(ValueError):
        Neighborhood(solution=solution, employees=[], operators=[])


def test_neighborhood_with_operator_on_employee_not_listed_raises():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance, 0)
    other_employee = build_employee(instance, 1)
    task = build_task(instance)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
    with pytest.raises(ValueError):
        Neighborhood(solution=solution, employees=[other_employee], operators=[operator])


def test_neighborhood_with_constraint_on_employee_not_listed_raises():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance, 0)
    other_employee = build_employee(instance, 1)
    with pytest.raises(ValueError):
        Neighborhood(solution=solution, employees=[other_employee], operators=[],
                     constraints=[SequenceOrderFixed(employee)])


def test_neighborhood_with_employee_carrying_two_constraints_raises():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance)
    with pytest.raises(ValueError):
        Neighborhood(solution=solution, employees=[employee], operators=[],
                     constraints=[SequenceOrderFixed(employee), SequenceFixed(employee)])


def test_neighborhood_with_operator_on_sequence_fixed_employee_raises():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
    with pytest.raises(ValueError):
        Neighborhood(solution=solution, employees=[employee], operators=[operator],
                     constraints=[SequenceFixed(employee)])


def test_neighborhood_with_operator_on_order_fixed_employee_is_accepted():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
    neighborhood = Neighborhood(solution=solution, employees=[employee], operators=[operator],
                                constraints=[SequenceOrderFixed(employee)])
    assert neighborhood.employees == frozenset({employee})
    assert neighborhood.operators == [operator]


def test_neighborhood_with_no_operators_and_no_constraints_is_accepted():
    # e.g. the "why not perform this route in another order" case: one employee in scope, nothing else.
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance)
    neighborhood = Neighborhood(solution=solution, employees=[employee], operators=[])
    assert neighborhood.employees == frozenset({employee})
    assert neighborhood.operators == []
    assert neighborhood.constraints == []
    assert neighborhood.target_tasks == frozenset()


def test_neighborhood_target_tasks_aggregates_across_operators():
    instance = build_instance()
    solution = Solution(instance)
    employee = build_employee(instance)
    task_1 = build_task(instance, 0)
    task_2 = build_task(instance, 1)
    insertion = TaskInsertion(frozenset({employee}), frozenset({task_1}))
    deletion = TaskDeletion(frozenset({employee}), frozenset({task_2}))
    neighborhood = Neighborhood(solution=solution, employees=[employee], operators=[insertion, deletion])
    assert neighborhood.target_tasks == frozenset({task_1, task_2})
