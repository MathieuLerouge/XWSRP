# Standard library
import json

# Third-party library
import pytest

# Local libraries
from src.explaining.computing.neighborhood.exceptions import UnattributableFeasibilityShortfallException
from src.explaining.computing.neighborhood.extractor import ConflictExtractor
from src.explaining.computing.neighborhood.facts import (
    HOME, ExplanationFacts, ExplanationFactsBuilder, ExplanationOutcomes, SkillConflictFacts, TimeConflictFacts,
    UnattributedTimeConflictFacts
)
from src.explaining.explanation.predefined.explanation import create_explanation
from src.explaining.neighborhood.templates.mapper import Mapper
from src.explaining.question.free.question import FreeTextQuestion
from src.explaining.question.predefined.bank import (
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)
from src.explaining.question.predefined.question import ContrastiveQuestion
from tests.explaining.computing.helpers import (
    build_austria_solution, get_explanation_facts, get_neighborhood_computation_pipeline_result
)

# The cases of test_explanation_parity.py, plus the ones settling on an outcome none of them does.
_CASES: list[tuple[str, list[str]]] = [
    (WHY_NOT_INS_1, ["Ellen", "T27", "T17"]),
    (WHY_NOT_INS_1, ["Alexander", "T3", "T20"]),
    (WHY_NOT_INS_2A, ["Ellen", "T27"]),
    (WHY_NOT_INS_2A, ["Fabian", "T5"]),
    (WHY_NOT_INS_2B, ["Ellen"]),
    (WHY_NOT_INS_2C, ["T27"]),
    (WHY_NOT_INS_3, ["Ellen", "T27"]),
    (WHY_NOT_SWP_1, ["Ellen", "T27", "T17"]),
    (WHY_NOT_SWP_2A, ["Ellen", "T27"]),
    (WHY_NOT_SWP_2B, ["Ellen"]),
    (WHY_NOT_SWP_2C, ["T27"]),
    (WHY_NOT_SWP_3, ["Ellen", "T27"]),
    (WHY_NOT_ORD_LAT_1, ["Ellen", "T30", "T26"]),
    (WHY_NOT_ORD_EAR_1, ["Ellen", "T26", "T7"]),
    (WHY_NOT_ORD_LAT_2, ["Ellen", "T3"]),
    (WHY_NOT_ORD_EAR_2, ["Ellen", "T3"]),
    (WHY_NOT_ORD_2, ["Ellen", "T1"]),
    (WHY_NOT_ORD_3, ["Carlotta"]),
]


def build_facts(template_id: str, fields_values: list[str]) -> ExplanationFacts:
    """Return the facts of the given templated question, run through the template-free pipeline."""
    _, facts, _ = get_explanation_facts(template_id, fields_values)
    return facts


#########
# Tests #
#########

@pytest.mark.parametrize("template_id,fields_values", _CASES, ids=[f"{case[0]}-{case[1]}" for case in _CASES])
def test_the_verdict_agrees_with_the_predefined_pipeline(template_id, fields_values):
    """
    The facts call positive, and feasible, exactly what the predefined explanation of the same question does:
    "positive" keeps its predefined meaning, a feasible support solution strictly better than the current one.
    """
    facts = build_facts(template_id, fields_values)
    predefined_explanation = create_explanation(
        *get_neighborhood_computation_pipeline_result(build_austria_solution(), template_id, fields_values)
    )
    assert facts.is_positive == predefined_explanation.is_positive()
    assert facts.support_solution_is_feasible == predefined_explanation.support_solution_is_feasible


@pytest.mark.parametrize("template_id,fields_values", _CASES, ids=[f"{case[0]}-{case[1]}" for case in _CASES])
def test_the_facts_survive_a_json_round_trip(template_id, fields_values):
    facts = build_facts(template_id, fields_values)
    assert ExplanationFacts.from_dict(json.loads(json.dumps(facts.to_dict()))) == facts


def test_a_feasible_but_worse_alternative_is_not_improving():
    """(Ins,1): Alexander can perform T3 just after T20, but it travels more for the same working duration."""
    facts = build_facts(WHY_NOT_INS_1, ["Alexander", "T3", "T20"])
    assert facts.outcome is ExplanationOutcomes.FEASIBLE_NON_IMPROVING
    assert facts.conflict is None
    assert facts.support_kpis.total_working_duration == facts.current_kpis.total_working_duration
    assert facts.support_kpis.total_traveling_duration > facts.current_kpis.total_traveling_duration
    alexander_change = next(change for change in facts.route_changes if change.employee == "Alexander")
    assert alexander_change.added_tasks == ("T3",)
    assert all(step.start_time is not None for step in alexander_change.support_route.steps), \
        "A feasible support route's times are meaningful, and so stated"


def test_a_better_alternative_is_improving():
    """(Swp,1): Ellen performing T27 in place of T17 increases the total working duration."""
    facts = build_facts(WHY_NOT_SWP_1, ["Ellen", "T27", "T17"])
    assert facts.outcome is ExplanationOutcomes.FEASIBLE_IMPROVING
    assert facts.newly_performed_tasks == ("T27",)
    assert facts.no_longer_performed_tasks == ("T17",)


def test_a_skill_blocked_neighborhood_names_both_skill_levels():
    """(Ins,2a): Fabian (level 1) is offered T5 alone, which requires level 2."""
    facts = build_facts(WHY_NOT_INS_2A, ["Fabian", "T5"])
    assert facts.outcome is ExplanationOutcomes.SKILL_BLOCKED
    assert facts.conflict == SkillConflictFacts("Fabian", "T5", employee_skill_level=1, task_skill_level=2)
    assert facts.route_changes == ()
    assert facts.support_kpis is None


def test_a_time_conflict_names_the_activities_its_step_indices_point_at():
    """
    (Ins,1): T27 cannot end by 03:00PM once inserted just after T17, the route being held back from T26 on
    - the facts the predefined TimeNegativeExplanation words as "by performing all the tasks from T26 to T27
    at the earliest possible time, Ellen can end T27 at the earliest at 04:37PM".
    """
    facts = build_facts(WHY_NOT_INS_1, ["Ellen", "T27", "T17"])
    assert facts.outcome is ExplanationOutcomes.TIME_INFEASIBLE
    conflict = facts.conflict
    assert isinstance(conflict, TimeConflictFacts)
    assert (conflict.employee, conflict.task) == ("Ellen", "T27")
    assert not conflict.is_upstream_feasible
    assert conflict.upstream_binding_activity == "T26"
    assert conflict.earliest_end_time == 16 * 60 + 37
    assert conflict.task_time_window_end == 15 * 60
    assert (conflict.activity_before, conflict.activity_after) == ("T17", "T8")
    assert conflict.downstream_binding_activity == HOME
    assert conflict.earliest_start_time - conflict.latest_start_time == conflict.feasibility_shortfall
    (ellen_change,) = facts.route_changes
    assert ellen_change.added_tasks == ("T27",)
    assert ellen_change.support_route.activities == ("T7", "T30", "T3", "T26", "T1", "T17", "T27", "T8")
    assert all(step.start_time is None for step in ellen_change.support_route.steps), \
        "An infeasible support route's times are inconsistent, and so left out"
    assert facts.support_kpis is None


def test_an_unattributable_shortfall_is_still_reported(monkeypatch):
    """When ConflictExtractor cannot attribute the shortfall, its size and task are still stated."""
    def raise_unattributable(model):
        raise UnattributableFeasibilityShortfallException()
    monkeypatch.setattr(ConflictExtractor, "extract_from_solved_model", staticmethod(raise_unattributable))
    facts = build_facts(WHY_NOT_INS_1, ["Ellen", "T27", "T17"])
    assert facts.outcome is ExplanationOutcomes.INFEASIBLE_UNATTRIBUTED
    assert facts.conflict == UnattributedTimeConflictFacts("Ellen", "T27", feasibility_shortfall=97)
    assert not facts.is_positive


def test_exactly_one_of_a_model_and_a_skill_conflict_is_required():
    solution = build_austria_solution()
    neighborhood = Mapper.map(ContrastiveQuestion(solution, WHY_NOT_INS_1, ["Ellen", "T27", "T17"]))
    with pytest.raises(ValueError):
        ExplanationFactsBuilder.build(FreeTextQuestion(solution, "Why?"), neighborhood, None, None)
