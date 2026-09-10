# Standard library
import random

# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.templates.mapper import Mapper
from src.explaining.questioning.question import ContrastiveQuestion
from src.explaining.questioning.questions_templates_bank import (
    QUESTIONS_TEMPLATES, WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3
)
from src.modeling.solution import Solution
from tests.explaining.computing.helpers import (
    assert_same_kpis, build_austria_solution, get_neighborhood_computation_pipeline_gap_and_solution,
    get_tailored_computation_pipeline_gap_and_solution
)

# Global variables
_RANDOM_SEED = 42
_MAX_SAMPLES_PER_TEMPLATE = 10


def assert_parity_over_random_samples(solution: Solution, template_id: str,
                                      max_samples: int = _MAX_SAMPLES_PER_TEMPLATE):
    """
    Check tailored/neighborhood computation pipeline parity over up to max_samples random valid
    field-value combinations for the given template (fewer if fewer valid combinations exist).

    WIP: A combination is skipped rather than checked when none of its operator's candidate employees
    is skilled for any of its candidate tasks, since skill mismatches aren't handled by the neighborhood
    computation pipeline yet. A combination with at least one skill-compatible (employee, task) pair
    among its candidates is still checked even if some other candidates aren't skill-compatible, since
    the neighborhood computation pipeline's hard skill constraint already keeps it from ever choosing an
    incompatible one on its own (verified directly for (Ins,2c), whose candidate employees are a mix of
    skill-compatible and skill-incompatible ones).

    Raises:
        AssertionError: if the template has no valid field-value combination at all for solution,
            or if a sampled combination's gap or (when both are feasible) KPIs disagree between pipelines.
    """
    # compute_all_fields_valid_values needs solution.nb_non_performed_tasks for some templates (e.g.
    # (Ins,2b)'s "no candidate task at all" special case), which itself needs KPIs to have been computed.
    solution.compute_kpis()
    template = QUESTIONS_TEMPLATES[template_id]
    all_fields_values = template.compute_all_fields_valid_values(solution)
    assert len(all_fields_values) > 0, f"No valid field-value combination found for template {template_id}"
    random.Random(_RANDOM_SEED).shuffle(all_fields_values)

    for fields_values in all_fields_values[:max_samples]:
        neighborhood = Mapper.map(ContrastiveQuestion(solution, template_id, fields_values))
        operator = neighborhood.operators[0]
        if not any(employee.is_capable_of_performing(task)
                  for employee in operator.candidate_employees for task in operator.candidate_tasks):
            continue

        tailored_gap, tailored_solution = get_tailored_computation_pipeline_gap_and_solution(
            solution, template_id, fields_values
        )
        neighborhood_gap, neighborhood_solution = get_neighborhood_computation_pipeline_gap_and_solution(
            solution, template_id, fields_values
        )

        assert tailored_gap == neighborhood_gap, f"Gap mismatch for fields_values={fields_values}"
        if tailored_gap == 0:
            assert_same_kpis(tailored_solution, neighborhood_solution)


@pytest.mark.slow
def test_ins_1_parity_over_random_samples():
    """(Ins,1), over random (Employee, Task, Activity) samples:
    why is {Employee} not performing {Task} just after {Activity}?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_INS_1)


@pytest.mark.slow
def test_ins_2a_parity_over_random_samples():
    """(Ins,2a), over random (Employee, Task) samples:
    why is {Employee} not performing {Task} between two consecutive activities of their route?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_INS_2A)


@pytest.mark.slow
def test_ins_2b_parity_over_random_samples():
    """(Ins,2b), over random Employee samples:
    why is {Employee} not performing any non-performed task between two consecutive activities of
    their route?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_INS_2B)


@pytest.mark.slow
def test_ins_2c_parity_over_random_samples():
    """(Ins,2c), over random Task samples:
    why is any employee not performing {Task} between two consecutive activities of their route?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_INS_2C)


@pytest.mark.slow
def test_ins_3_parity_over_random_samples():
    """(Ins,3), over random (Employee, Task) samples:
    why is {Employee} not performing {Task} in addition to their already-performed activities
    (even if it means changing their order)?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_INS_3)
