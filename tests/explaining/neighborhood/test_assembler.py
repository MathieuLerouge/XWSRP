# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.assembler import Assembler
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import TaskInsertion
from src.explaining.neighborhood.restriction import ImmediatePrecedence
from tests.explaining.neighborhood.helpers import build_solution_with_task_performances
from tests.modeling.helpers import build_instance


def _build_solution():
    instance = build_instance()
    solution = build_solution_with_task_performances(instance, "solution", {"T1": ("Valentin", 480)})
    return instance, solution


def test_assemble_returns_a_neighborhood_for_a_supported_case():
    instance, solution = _build_solution()
    employee = instance.get_employee_by_name("Valentin")
    task = instance.get_task_by_name("T4")
    operators = [TaskInsertion(frozenset({employee}), frozenset({task}))]
    neighborhood = Assembler.assemble(operators, [], solution)
    assert isinstance(neighborhood, Neighborhood)
    assert neighborhood.solution == solution
    assert neighborhood.operators == operators
    assert neighborhood.restrictions == []


def test_assemble_raises_when_operators_and_restrictions_are_both_empty():
    _, solution = _build_solution()
    with pytest.raises(NeighborhoodError):
        Assembler.assemble([], [], solution)


def test_assemble_raises_on_immediate_precedence_with_multi_candidate_operator():
    instance, solution = _build_solution()
    valentin = instance.get_employee_by_name("Valentin")
    ambre = instance.get_employee_by_name("Ambre")
    task = instance.get_task_by_name("T4")
    t1 = instance.get_task_by_name("T1")
    operators = [TaskInsertion(frozenset({valentin, ambre}), frozenset({task}))]
    restrictions = [ImmediatePrecedence(t1, task)]
    with pytest.raises(NeighborhoodError):
        Assembler.assemble(operators, restrictions, solution)


def test_assemble_raises_on_lunch_break_instance():
    instance, solution = _build_solution()
    instance.set_lunch_break(lunch_break_lower_bound=660, lunch_break_upper_bound=780, lunch_break_duration=30)
    employee = instance.get_employee_by_name("Valentin")
    task = instance.get_task_by_name("T4")
    operators = [TaskInsertion(frozenset({employee}), frozenset({task}))]
    with pytest.raises(NeighborhoodError):
        Assembler.assemble(operators, [], solution)
