# Standard library
from typing import Optional

# Third-party library
import pytest

# Local libraries
from src.explaining.computing.conflict.conflict import SkillConflict, TimeConflict
from src.explaining.computing.conflict.extractor import ConflictExtractor
from src.explaining.computing.model import NeighborhoodModel
from src.explaining.computing.templates.transformation import \
    apply_transformation_induced_by_contrastive_or_scenario_question
from src.explaining.modeling.solution import EditableSolution
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import TaskRelocation
from src.explaining.neighborhood.templates.mapper import Mapper
from src.explaining.questioning.question import ContrastiveQuestion
from src.explaining.questioning.questions_templates_bank import (
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_ORD_3, WHY_NOT_SWP_1, WHY_NOT_SWP_2A
)
from src.modeling.solution import Solution
from tests.explaining.computing.helpers import build_austria_solution


#####################
# NeighborhoodModel #
#####################

def solve_neighborhood(solution: Solution, template_id: str, fields_values: list[str]) -> NeighborhoodModel:
    """
    Map the given question to a neighborhood, solve its NeighborhoodModel and return it.

    Raises:
        AssertionError: if the MILP finds no incumbent, which it should always do by construction.
    """
    model = NeighborhoodModel(Mapper.map(ContrastiveQuestion(solution, template_id, fields_values)))
    outcome = model.solve(mute=True)
    assert outcome.has_incumbent, "The neighborhood computation pipeline's MILP should be feasible by construction"
    return model


def assert_conflict_describes_shortfall(model: NeighborhoodModel, conflict: Optional[TimeConflict]):
    """
    Assert the given TimeConflict is internally consistent with the model it was derived from.

    This is what can be checked for the neighborhood shapes the tailored pipeline has no counterpart for -
    a TaskInsertion with several candidate tasks or employees, or one paired with a TaskDeletion - where
    there is nothing to compare against field for field (that comparison is test_parity's job).

    Checks that a zero shortfall yields no conflict and a strictly positive one does; that the
    conflicting pair is one the solution actually realizes; that the two start-time bounds are exactly the
    shortfall apart; and that each of the two feasibility flags agrees with its own bound being inside the
    conflicting task's time window.
    """
    if model.feasibility_shortfall == 0:
        assert conflict is None, "A zero feasibility shortfall should yield no conflict"
        return

    assert conflict is not None, "A strictly positive feasibility shortfall should yield a conflict"
    conflicting_task = conflict.conflicting_task
    assert model.solution.get_task_performance_status(conflicting_task), \
        f"{conflicting_task.name} is reported as conflicting but is not performed"
    assert model.solution.get_task_assignee(conflicting_task) == conflict.conflicting_employee, \
        f"{conflicting_task.name} is not performed by the employee reported as conflicting"

    earliest = conflict.earliest_upstream_feasible_start_time_of_conflicting_task
    latest = conflict.latest_downstream_feasible_start_time_of_conflicting_task
    assert earliest - latest == model.feasibility_shortfall, \
        f"The two start-time bounds are {earliest - latest} apart, not the shortfall {model.feasibility_shortfall}"
    assert conflict.is_upstream_feasible == \
        (earliest + conflicting_task.duration <= conflicting_task.end_time_ub), \
        "The upstream feasibility flag disagrees with the earliest start time fitting the task's time window"
    assert conflict.is_downstream_feasible == (latest >= conflicting_task.start_time_lb), \
        "The downstream feasibility flag disagrees with the latest start time fitting the task's time window"

    upstream_binding_step_index = conflict.upstream_binding_step_index
    downstream_binding_step_index = conflict.downstream_binding_step_index
    nb_steps = len(model.solution.get_sequence(conflict.conflicting_employee))
    assert 0 <= upstream_binding_step_index < downstream_binding_step_index <= nb_steps, \
        f"The binding step indices {upstream_binding_step_index, downstream_binding_step_index} do not "\
        f"bracket a position of a {nb_steps}-step route"


def test_no_conflict_when_the_solution_found_is_feasible():
    """(Ins,1): Alexander can perform T3 just after T20, so there is nothing to report."""
    model = solve_neighborhood(build_austria_solution(), WHY_NOT_INS_1, ["Alexander", "T3", "T20"])
    assert model.feasibility_shortfall == 0
    assert ConflictExtractor.extract_from_solved_model(model) is None


def test_conflict_is_refused_before_solving():
    """Extraction needs a solved model, like every other result NeighborhoodModel exposes."""
    solution = build_austria_solution()
    model = NeighborhoodModel(Mapper.map(ContrastiveQuestion(solution, WHY_NOT_INS_1, ["Ellen", "T18", "T1"])))
    with pytest.raises(AttributeError):
        _ = ConflictExtractor.extract_from_solved_model(model)


@pytest.mark.parametrize("template_id, fields_values", [
    (WHY_NOT_INS_2B, ["Ellen"]),
    (WHY_NOT_INS_2C, ["T27"]),
])
def test_conflict_describes_shortfall_for_several_candidates(template_id, fields_values):
    """
    (Ins,2b)/(Ins,2c): the candidate task (resp. employee) is not named, so the neighborhood carries
    several of them and the tailored pipeline's heuristic choice is not the one to compare against.
    """
    model = solve_neighborhood(build_austria_solution(), template_id, fields_values)
    assert_conflict_describes_shortfall(model, ConflictExtractor.extract_from_solved_model(model))


@pytest.mark.parametrize("template_id, fields_values", [
    (WHY_NOT_SWP_1, ["Alexander", "T13", "T28"]),
    (WHY_NOT_SWP_2A, ["Ellen", "T13"]),
])
def test_conflict_describes_shortfall_when_paired_with_a_deletion(template_id, fields_values):
    """
    (Swp,1)/(Swp,2a): a TaskInsertion paired with a TaskDeletion, so the conflicting task's neighbors are
    whoever the deletion left adjacent to it rather than whoever the given solution had there.
    """
    model = solve_neighborhood(build_austria_solution(), template_id, fields_values)
    assert_conflict_describes_shortfall(model, ConflictExtractor.extract_from_solved_model(model))


################
# Neighborhood #
################

# NB: In the Austria instance, Fabian and Carlotta are the two skill-level-1 employees, while every
# non-performed task (T5, T12, T15, T27, T31) requires level 2 - so Fabian is blocked from all of them.

def map_neighborhood(solution: Solution, template_id: str, fields_values: list[str]):
    """Map the given question to the neighborhood it induces, without building any model for it."""
    return Mapper.map(ContrastiveQuestion(solution, template_id, fields_values))


def test_no_skill_conflict_when_one_candidate_pairing_is_skill_feasible():
    """
    (Ins,2c) on T27: a level-2 task offered to every employee. Fabian and Carlotta cannot perform it, but
    the three level-2 employees can, so the model still has an arrangement to search and nothing is blocked.
    """
    neighborhood = map_neighborhood(build_austria_solution(), WHY_NOT_INS_2C, ["T27"])
    assert ConflictExtractor.extract_from_neighborhood(neighborhood) is None


def test_no_skill_conflict_when_no_operator_opens_a_pairing():
    """(Ord,3): a lone SequenceReordering hands nobody a task they don't already perform."""
    neighborhood = map_neighborhood(build_austria_solution(), WHY_NOT_ORD_3, ["Fabian"])
    assert ConflictExtractor.extract_from_neighborhood(neighborhood) is None


def test_skill_conflict_when_the_only_candidate_pairing_is_blocked():
    """
    (Ins,2a): Fabian is offered T5 alone and is not skilled for it, so the one pairing on offer is blocked.
    Being the single-pairing case, it is also the one where the tailored pipeline reports a skill conflict
    of its own, which this asserts the neighborhood pipeline agrees with field for field.
    """
    solution = build_austria_solution()
    solution.compute_kpis()
    conflict = ConflictExtractor.extract_from_neighborhood(
        map_neighborhood(solution, WHY_NOT_INS_2A, ["Fabian", "T5"])
    )
    assert isinstance(conflict, SkillConflict)
    assert conflict.conflicting_employee.name == "Fabian"
    assert conflict.conflicting_task.name == "T5"

    editable_solution = EditableSolution.from_solution(solution)
    tailored_result = apply_transformation_induced_by_contrastive_or_scenario_question(
        editable_solution, ContrastiveQuestion(editable_solution, WHY_NOT_INS_2A, ["Fabian", "T5"])
    )
    assert conflict.to_dict() == tailored_result.conflict.to_dict()


def test_skill_conflict_when_every_candidate_pairing_is_blocked():
    """
    (Ins,2b): Fabian is offered every non-performed task at once, and is skilled for none of them.
    Which of them gets named is settled by sorting rather than by frozenset iteration order,
    so the conflict reported is the same from one run to the next.
    """
    neighborhood = map_neighborhood(build_austria_solution(), WHY_NOT_INS_2B, ["Fabian"])
    conflict = ConflictExtractor.extract_from_neighborhood(neighborhood)
    assert isinstance(conflict, SkillConflict)
    assert conflict.conflicting_employee.name == "Fabian"
    assert conflict.conflicting_task.name == "T12"
    assert ConflictExtractor.extract_from_neighborhood(neighborhood).to_dict() == conflict.to_dict()


def test_a_blocked_neighborhood_leaves_the_model_nothing_to_solve():
    """
    Why the skill check has to run before the model rather than on a solved one: NeighborhoodModel never
    relaxes a skill constraint, so a blocked neighborhood's MILP has no incumbent to extract anything from.
    """
    neighborhood = map_neighborhood(build_austria_solution(), WHY_NOT_INS_2A, ["Fabian", "T5"])
    assert ConflictExtractor.extract_from_neighborhood(neighborhood) is not None
    outcome = NeighborhoodModel(neighborhood).solve(mute=True)
    assert not outcome.has_incumbent


@pytest.mark.parametrize("destination_employee_name, expects_conflict", [
    ("Fabian", True),
    ("Adam", False),
])
def test_skill_conflict_of_a_relocation_depends_on_its_destination(destination_employee_name, expects_conflict):
    """
    A TaskRelocation of the level-2 task T6 away from Alexander: only the destination employee is a pairing
    the given solution has not already vouched for, so relocating to Fabian is blocked and to Adam is not.

    NB: Built by hand rather than through Mapper, which no question maps to a TaskRelocation yet, and never
    handed to NeighborhoodModel, which has no MILP formulation for one - neither of which stops the pairing
    it opens from being readable off the operator itself.
    """
    solution = build_austria_solution()
    solution.compute_kpis()
    instance = solution.instance
    operator = TaskRelocation(
        instance.get_employee_by_name("Alexander"),
        instance.get_employee_by_name(destination_employee_name),
        instance.get_task_by_name("T6")
    )
    conflict = ConflictExtractor.extract_from_neighborhood(Neighborhood(solution, [operator]))
    if not expects_conflict:
        assert conflict is None
        return
    assert isinstance(conflict, SkillConflict)
    assert conflict.conflicting_employee.name == destination_employee_name
    assert conflict.conflicting_task.name == "T6"
