# Third-party library
import pytest

# Local libraries
from src.explaining.computing.neighborhood.checker import ModelCompatibilityChecker
from src.explaining.computing.neighborhood.model import NeighborhoodModel
from src.explaining.neighborhood.assembler import Assembler
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import (
    SequenceReordering, TaskDeletion, TaskInsertion, TaskRelocation, TaskRepositioning
)
from src.explaining.neighborhood.restriction import ForbiddenSequence, ImmediatePrecedence, PrecedenceChain
from tests.explaining.neighborhood.helpers import build_solution_with_task_performances
from tests.modeling.helpers import build_instance

# Global variables
# Valentin performs T1, T2, T3, T4 in order; Ambre performs T6, T7 in order; T5, T8-T14 stay non-performed.
_TASK_PERFORMANCES = {
    "T1": ("Valentin", 480), "T2": ("Valentin", 560), "T3": ("Valentin", 640), "T4": ("Valentin", 720),
    "T6": ("Ambre", 480), "T7": ("Ambre", 560),
}


@pytest.fixture(scope="module")
def instance():
    return build_instance()


@pytest.fixture(scope="module")
def solution(instance):
    return build_solution_with_task_performances(instance, "solution", _TASK_PERFORMANCES)


@pytest.fixture
def own_instance():
    """A freshly read instance, for the tests that alter it rather than only reading it."""
    return build_instance()


@pytest.fixture
def own_solution(own_instance):
    """A solution over own_instance, so that altering it cannot leak into any other test."""
    return build_solution_with_task_performances(own_instance, "solution", _TASK_PERFORMANCES)


def build_compatible_neighborhood(solution, instance) -> Neighborhood:
    """Build the simplest neighborhood NeighborhoodModel supports: inserting one task for one employee."""
    return Neighborhood(
        solution,
        [TaskInsertion(frozenset({instance.get_employee_by_name("Valentin")}),
                       frozenset({instance.get_task_by_name("T5")}))],
        []
    )


#########################
# Compatible neighborhood #
#########################

def test_a_supported_neighborhood_is_compatible(solution, instance):
    """The simplest supported shape runs into none of the model's limits, so there is nothing to report."""
    neighborhood = build_compatible_neighborhood(solution, instance)

    assert ModelCompatibilityChecker.unsupported_reason(neighborhood) is None
    assert ModelCompatibilityChecker.is_compatible(neighborhood)


###################
# Instance limits #
###################

def test_a_lunch_break_makes_the_neighborhood_incompatible(own_solution, own_instance):
    """A lunch break is a limit of the model rather than of the neighborhood, but it stops it all the same."""
    own_instance.set_lunch_break(720, 840, 60)
    neighborhood = build_compatible_neighborhood(own_solution, own_instance)

    assert ModelCompatibilityChecker.unsupported_reason(neighborhood) == \
        "NeighborhoodModel does not support instances with a lunch break"


def test_having_to_cover_all_tasks_makes_the_neighborhood_incompatible(own_solution, own_instance):
    """Mandatory coverage is the other instance-level limit, and it is read from the instance too."""
    own_instance.must_cover_all_tasks = True
    neighborhood = build_compatible_neighborhood(own_solution, own_instance)

    assert ModelCompatibilityChecker.unsupported_reason(neighborhood) == \
        "NeighborhoodModel does not support instances whose tasks must all be covered"


#######################
# Operator-set limits #
#######################

def test_more_than_two_operators_is_incompatible(solution, instance):
    """The model formulates one feasibility-shortfall operator and at most one deletion, so no more than two."""
    employee = instance.get_employee_by_name("Valentin")
    neighborhood = Neighborhood(
        solution,
        [TaskInsertion(frozenset({employee}), frozenset({instance.get_task_by_name("T5")})),
         TaskDeletion(frozenset({employee}), frozenset({instance.get_task_by_name("T1")})),
         TaskRepositioning(employee, instance.get_task_by_name("T2"))],
        []
    )

    assert ModelCompatibilityChecker.unsupported_reason(neighborhood) == \
        "NeighborhoodModel currently only supports a neighborhood with one or two operators"


def test_no_operator_at_all_is_incompatible(solution, instance):
    """Restrictions alone narrow a freedom nothing granted, so there is no shortfall operator to formulate."""
    neighborhood = Neighborhood(
        solution, [],
        [ForbiddenSequence(instance.get_employee_by_name("Valentin"),
                           [instance.get_task_by_name("T1"), instance.get_task_by_name("T2")])]
    )

    assert ModelCompatibilityChecker.unsupported_reason(neighborhood) == \
        "NeighborhoodModel currently only supports a neighborhood with one or two operators"


def test_two_deletions_is_incompatible(solution, instance):
    """Only one TaskDeletion gets deletion constraints, so a second one would be silently ignored."""
    employee = instance.get_employee_by_name("Valentin")
    neighborhood = Neighborhood(
        solution,
        [TaskDeletion(frozenset({employee}), frozenset({instance.get_task_by_name("T1")})),
         TaskDeletion(frozenset({employee}), frozenset({instance.get_task_by_name("T2")}))],
        []
    )

    assert ModelCompatibilityChecker.unsupported_reason(neighborhood) == \
        "NeighborhoodModel does not support more than one TaskDeletion operator"


def test_two_feasibility_shortfall_operators_is_incompatible(solution, instance):
    """Only one operator gets slack variables, so a second one would have no shortfall of its own."""
    employee = instance.get_employee_by_name("Valentin")
    neighborhood = Neighborhood(
        solution,
        [TaskInsertion(frozenset({employee}), frozenset({instance.get_task_by_name("T5")})),
         TaskRepositioning(employee, instance.get_task_by_name("T1"))],
        []
    )

    assert ModelCompatibilityChecker.unsupported_reason(neighborhood) == \
        "NeighborhoodModel does not support more than one TaskInsertion, " \
        "TaskRepositioning or SequenceReordering operator"


def test_an_operator_with_no_formulation_is_incompatible(solution, instance):
    """TaskRelocation exists as vocabulary but has no MILP formulation yet."""
    neighborhood = Neighborhood(
        solution,
        [TaskRelocation(instance.get_employee_by_name("Valentin"),
                        instance.get_employee_by_name("Ambre"),
                        instance.get_task_by_name("T1"))],
        []
    )

    assert ModelCompatibilityChecker.unsupported_reason(neighborhood) == \
        "NeighborhoodModel currently only supports TaskInsertion, TaskDeletion, " \
        "TaskRepositioning or SequenceReordering operators"


def test_a_deletion_on_its_own_is_incompatible(solution, instance):
    """A deletion never has a "does it fit" question of its own, so it needs an operator that does."""
    neighborhood = Neighborhood(
        solution,
        [TaskDeletion(frozenset({instance.get_employee_by_name("Valentin")}),
                      frozenset({instance.get_task_by_name("T1")}))],
        []
    )

    assert ModelCompatibilityChecker.unsupported_reason(neighborhood) == \
        "NeighborhoodModel requires a TaskInsertion, TaskRepositioning or " \
        "SequenceReordering operator alongside TaskDeletion"


############################
# Restriction interactions #
############################

def test_an_immediate_precedence_over_open_candidates_is_incompatible(solution, instance):
    """
    An ImmediatePrecedence pins one specific task's insertion point, so it has to line up with a pairing the
    operator has already narrowed to one.
    """
    neighborhood = Neighborhood(
        solution,
        [TaskInsertion(frozenset(instance.employees), frozenset({instance.get_task_by_name("T5")}))],
        [ImmediatePrecedence(instance.get_task_by_name("T1"), instance.get_task_by_name("T5"))]
    )

    assert ModelCompatibilityChecker.unsupported_reason(neighborhood) == \
        "NeighborhoodModel does not support an ImmediatePrecedence restriction together " \
        "with more than one candidate employee or candidate task"


def test_an_immediate_precedence_over_a_narrowed_pairing_is_compatible(solution, instance):
    """The same restriction is supported once the operator names one employee and one task."""
    employee = instance.get_employee_by_name("Valentin")
    neighborhood = Neighborhood(
        solution,
        [TaskInsertion(frozenset({employee}), frozenset({instance.get_task_by_name("T5")}))],
        [PrecedenceChain([instance.get_task_by_name(name) for name in ("T1", "T2", "T3", "T4")]),
         ImmediatePrecedence(instance.get_task_by_name("T1"), instance.get_task_by_name("T5"))]
    )

    assert ModelCompatibilityChecker.is_compatible(neighborhood)


def test_an_immediate_precedence_beside_a_reordering_is_compatible(solution, instance):
    """
    A SequenceReordering has a single pivot task chosen for it rather than a candidate set, so it never
    trips the open-candidates limit.
    """
    employee = instance.get_employee_by_name("Valentin")
    neighborhood = Neighborhood(
        solution, [SequenceReordering(employee)],
        [ImmediatePrecedence(instance.get_task_by_name("T1"), instance.get_task_by_name("T2"))]
    )

    assert ModelCompatibilityChecker.is_compatible(neighborhood)


###############################################
# Both consumers report the checker's verdict #
###############################################

def test_the_model_raises_the_checker_s_own_reason(solution, instance):
    """
    NeighborhoodModel doesn't restate the limits, it reports whatever the checker found - so that widening
    one widens the other.
    """
    neighborhood = Neighborhood(
        solution,
        [TaskRelocation(instance.get_employee_by_name("Valentin"),
                        instance.get_employee_by_name("Ambre"),
                        instance.get_task_by_name("T1"))],
        []
    )
    unsupported_reason = ModelCompatibilityChecker.unsupported_reason(neighborhood)

    with pytest.raises(NotImplementedError) as raised:
        NeighborhoodModel(neighborhood)

    assert str(raised.value) == unsupported_reason


def test_the_assembler_raises_the_checker_s_own_reason(solution, instance):
    """Assembler reports the same reason, rather than building a whole model to find out there is one."""
    operators = [TaskDeletion(frozenset({instance.get_employee_by_name("Valentin")}),
                              frozenset({instance.get_task_by_name("T1")}))]

    with pytest.raises(NeighborhoodError) as raised:
        Assembler.assemble(operators, [], solution)

    assert str(raised.value) == ModelCompatibilityChecker.unsupported_reason(
        Neighborhood(solution, operators, [])
    )
