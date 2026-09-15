# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.llm.exceptions import NeighborhoodExtractionError
from src.explaining.neighborhood.llm.neighborhood import ExtractedNeighborhood
from src.explaining.neighborhood.llm.grounder import Grounder
from src.explaining.neighborhood.operator import (
    SequenceReordering, TaskDeletion, TaskInsertion, TaskRepositioning
)
from src.explaining.neighborhood.restriction import (
    ForbiddenBackwardSubsequence, ForbiddenSequence, ImmediatePrecedence, Precedence, PrecedenceChain
)
from tests.explaining.neighborhood.helpers import build_solution_with_task_performances
from tests.modeling.helpers import build_instance


def _build_solution_with_valentin_and_ambre_performing_tasks():
    # Valentin performs T1, T2, T3 in order; Ambre performs T6. Times are spaced generously,
    # feasibility of the resulting schedule doesn't matter here - Grounder never solves or checks
    # it, it only builds Operator/Restriction objects out of the given names.
    instance = build_instance()
    solution = build_solution_with_task_performances(instance, "solution", {
        "T1": ("Valentin", 480), "T2": ("Valentin", 602), "T3": ("Valentin", 680),
        "T6": ("Ambre", 480),
    })
    return instance, solution


def test_ground_task_insertion():
    instance, solution = _build_solution_with_valentin_and_ambre_performing_tasks()
    extracted = ExtractedNeighborhood.model_validate({
        "operator": {"kind": "task_insertion", "candidate_employees": ["Valentin"], "candidate_tasks": ["T4"]},
    })
    operators, restrictions = Grounder.ground(extracted, solution)
    assert len(operators) == 1 and restrictions == []
    operator = operators[0]
    assert isinstance(operator, TaskInsertion)
    assert operator.candidate_employees == frozenset({instance.get_employee_by_name("Valentin")})
    assert operator.candidate_tasks == frozenset({instance.get_task_by_name("T4")})


def test_ground_task_repositioning():
    instance, solution = _build_solution_with_valentin_and_ambre_performing_tasks()
    extracted = ExtractedNeighborhood.model_validate({
        "operator": {"kind": "task_repositioning", "employee": "Valentin", "target_task": "T2"},
    })
    operators, _ = Grounder.ground(extracted, solution)
    operator = operators[0]
    assert isinstance(operator, TaskRepositioning)
    assert operator.employee == instance.get_employee_by_name("Valentin")
    assert operator.target_task == instance.get_task_by_name("T2")


def test_ground_sequence_reordering_with_forbidden_sequence():
    instance, solution = _build_solution_with_valentin_and_ambre_performing_tasks()
    extracted = ExtractedNeighborhood.model_validate({
        "operator": {"kind": "sequence_reordering", "employee": "Valentin"},
        "restrictions": [{"kind": "forbidden_sequence", "employee": "Valentin", "activities": ["T1", "T2", "T3"]}],
    })
    operators, restrictions = Grounder.ground(extracted, solution)
    operator = operators[0]
    assert isinstance(operator, SequenceReordering)
    assert operator.employee == instance.get_employee_by_name("Valentin")
    assert len(restrictions) == 1
    restriction = restrictions[0]
    assert isinstance(restriction, ForbiddenSequence)
    assert restriction.employee == instance.get_employee_by_name("Valentin")
    assert restriction.activities == [instance.get_task_by_name(name) for name in ["T1", "T2", "T3"]]


def test_ground_task_deletion_paired_with_operator():
    instance, solution = _build_solution_with_valentin_and_ambre_performing_tasks()
    extracted = ExtractedNeighborhood.model_validate({
        "operator": {"kind": "task_insertion", "candidate_employees": ["Valentin"], "candidate_tasks": ["T5"]},
        "deletion": {"kind": "task_deletion", "freed_employees": ["Valentin"], "candidate_tasks": ["T2"]},
    })
    operators, _ = Grounder.ground(extracted, solution)
    assert len(operators) == 2
    insertion, deletion = operators[0], operators[1]
    assert isinstance(insertion, TaskInsertion)
    assert isinstance(deletion, TaskDeletion)
    assert deletion.freed_employees == frozenset({instance.get_employee_by_name("Valentin")})
    assert deletion.candidate_tasks == frozenset({instance.get_task_by_name("T2")})
    assert deletion.min_nb_removals == 1 and deletion.max_nb_removals == 1


def test_ground_precedence_chain():
    instance, solution = _build_solution_with_valentin_and_ambre_performing_tasks()
    extracted = ExtractedNeighborhood.model_validate({
        "operator": {"kind": "task_insertion", "candidate_employees": ["Valentin"], "candidate_tasks": ["T4"]},
        "restrictions": [{"kind": "precedence_chain", "tasks": ["T1", "T2", "T3"]}],
    })
    _, restrictions = Grounder.ground(extracted, solution)
    assert len(restrictions) == 1
    restriction = restrictions[0]
    assert isinstance(restriction, PrecedenceChain)
    assert restriction.tasks == [instance.get_task_by_name(name) for name in ["T1", "T2", "T3"]]


def test_ground_precedence():
    instance, solution = _build_solution_with_valentin_and_ambre_performing_tasks()
    extracted = ExtractedNeighborhood.model_validate({
        "operator": {"kind": "task_repositioning", "employee": "Valentin", "target_task": "T3"},
        "restrictions": [{"kind": "precedence", "predecessor": "T2", "successor": "T3"}],
    })
    _, restrictions = Grounder.ground(extracted, solution)
    assert len(restrictions) == 1
    restriction = restrictions[0]
    assert isinstance(restriction, Precedence)
    assert restriction.predecessor == instance.get_task_by_name("T2")
    assert restriction.successor == instance.get_task_by_name("T3")


def test_ground_immediate_precedence_with_task_names_anchored_via_singleton_operator_employee():
    instance, solution = _build_solution_with_valentin_and_ambre_performing_tasks()
    extracted = ExtractedNeighborhood.model_validate({
        "operator": {"kind": "task_insertion", "candidate_employees": ["Valentin"], "candidate_tasks": ["T4"]},
        "restrictions": [{"kind": "immediate_precedence", "predecessor": "T1", "successor": "T4"}],
    })
    _, restrictions = Grounder.ground(extracted, solution)
    assert len(restrictions) == 1
    restriction = restrictions[0]
    assert isinstance(restriction, ImmediatePrecedence)
    assert restriction.predecessor == instance.get_task_by_name("T1")
    assert restriction.successor == instance.get_task_by_name("T4")


def test_ground_immediate_precedence_with_route_boundary_sentinel_anchored_via_task_repositioning():
    instance, solution = _build_solution_with_valentin_and_ambre_performing_tasks()
    extracted = ExtractedNeighborhood.model_validate({
        "operator": {"kind": "task_repositioning", "employee": "Valentin", "target_task": "T2"},
        "restrictions": [{"kind": "immediate_precedence", "predecessor": "Start", "successor": "T2"}],
    })
    _, restrictions = Grounder.ground(extracted, solution)
    restriction = restrictions[0]
    assert isinstance(restriction, ImmediatePrecedence)
    predecessor = restriction.predecessor
    assert predecessor.name == "Start"
    assert predecessor == instance.get_hypothetical_activity_by_names("Start", "Valentin")
    assert restriction.successor == instance.get_task_by_name("T2")


def test_ground_forbidden_backward_subsequence():
    instance, solution = _build_solution_with_valentin_and_ambre_performing_tasks()
    extracted = ExtractedNeighborhood.model_validate({
        "operator": {"kind": "task_insertion", "candidate_employees": ["Valentin"], "candidate_tasks": ["T4"]},
        "deletion": {"kind": "task_deletion", "freed_employees": ["Valentin"], "candidate_tasks": ["T1", "T2", "T3"]},
        "restrictions": [
            {"kind": "forbidden_backward_subsequence", "employee": "Valentin", "tasks": ["T1", "T2", "T3"]}
        ],
    })
    _, restrictions = Grounder.ground(extracted, solution)
    assert len(restrictions) == 1
    restriction = restrictions[0]
    assert isinstance(restriction, ForbiddenBackwardSubsequence)
    assert restriction.employee == instance.get_employee_by_name("Valentin")
    assert restriction.tasks == [instance.get_task_by_name(name) for name in ["T1", "T2", "T3"]]


def test_ground_raises_on_unresolvable_employee_name():
    _, solution = _build_solution_with_valentin_and_ambre_performing_tasks()
    extracted = ExtractedNeighborhood.model_validate({
        "operator": {"kind": "task_insertion", "candidate_employees": ["Ghost"], "candidate_tasks": ["T4"]},
    })
    with pytest.raises(NeighborhoodExtractionError):
        Grounder.ground(extracted, solution)


def test_ground_raises_on_unresolvable_task_name():
    _, solution = _build_solution_with_valentin_and_ambre_performing_tasks()
    extracted = ExtractedNeighborhood.model_validate({
        "operator": {"kind": "task_insertion", "candidate_employees": ["Valentin"], "candidate_tasks": ["T999"]},
    })
    with pytest.raises(NeighborhoodExtractionError):
        Grounder.ground(extracted, solution)


def test_ground_raises_on_ambiguous_immediate_precedence_anchor():
    _, solution = _build_solution_with_valentin_and_ambre_performing_tasks()
    extracted = ExtractedNeighborhood.model_validate({
        "operator": {
            "kind": "task_insertion", "candidate_employees": ["Valentin", "Ambre"], "candidate_tasks": ["T4"]
        },
        "restrictions": [{"kind": "immediate_precedence", "predecessor": "Start", "successor": "T4"}],
    })
    with pytest.raises(NeighborhoodExtractionError):
        Grounder.ground(extracted, solution)
