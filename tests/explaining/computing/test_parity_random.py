# Standard library
import random

# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.operator import TaskInsertion, TaskRepositioning
from src.explaining.neighborhood.templates.mapper import Mapper
from src.explaining.questioning.question import ContrastiveQuestion
from src.explaining.questioning.questions_templates_bank import (
    QUESTIONS_TEMPLATES, WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)
from src.modeling.solution import Solution
from tests.explaining.computing.helpers import (
    assert_at_least_as_good_kpis, build_austria_solution, get_neighborhood_computation_pipeline_gap_and_solution,
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

    NB: The neighborhood gap is asserted <= the tailored gap, not ==.
    The tailored pipeline's reordering examinations (examine_moving_after_a_task/examine_moving_before_a_task)
    bound each candidate slot's feasibility using the original sequence's precomputed BTS/FTS slack,
    which goes stale once the relative order actually changes
    - understating how much room a joint reoptimization of every now-reordered task's time can find.
    The neighborhood MILP re-solves all of them together, so it can only find an equal or smaller gap.

    WIP: A combination is skipped rather than checked when none of the neighborhood's TaskInsertion (or
    TaskRepositioning) candidate employees is skilled for any of its candidate tasks, since skill
    mismatches aren't handled by the neighborhood computation pipeline yet. A neighborhood with neither
    (e.g. a lone SequenceReordering) is never skipped this way, since it never reassigns anyone.

    KPIs (when the tailored pipeline is feasible) are checked with assert_at_least_as_good_kpis rather
    than requiring an exact match: for candidate-set questions the neighborhood pipeline's exhaustive
    MILP search can legitimately find a strictly better swap than the tailored pipeline's heuristic, not
    just an equally good one (see that helper's docstring).

    Raises:
        AssertionError: if the template has no valid field-value combination at all for solution,
            or if a sampled combination's neighborhood gap exceeds its tailored gap, or (when the
            tailored pipeline is feasible) the neighborhood pipeline's KPIs are worse.
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
        candidate_employees, candidate_tasks = frozenset(), frozenset()
        for operator in neighborhood.operators:
            if isinstance(operator, TaskInsertion):
                candidate_employees, candidate_tasks = operator.candidate_employees, operator.candidate_tasks
                break
            elif isinstance(operator, TaskRepositioning):
                candidate_employees = frozenset({operator.employee})
                candidate_tasks = frozenset({operator.target_task})
                break
        if candidate_tasks and not any(
                employee.is_capable_of_performing(task)
                for employee in candidate_employees for task in candidate_tasks):
            continue

        tailored_gap, tailored_solution = get_tailored_computation_pipeline_gap_and_solution(
            solution, template_id, fields_values
        )
        neighborhood_gap, neighborhood_solution = get_neighborhood_computation_pipeline_gap_and_solution(
            solution, template_id, fields_values
        )

        assert neighborhood_gap <= tailored_gap, f"Neighborhood gap exceeds tailored gap for {fields_values}"
        if tailored_gap == 0:
            assert_at_least_as_good_kpis(tailored_solution, neighborhood_solution)


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


@pytest.mark.slow
def test_swp_1_parity_over_random_samples():
    """(Swp,1), over random (Employee, Task1, Task2) samples:
    why is {Employee} not performing {Task1} rather than {Task2}?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_SWP_1)


@pytest.mark.slow
def test_swp_2a_parity_over_random_samples():
    """(Swp,2a), over random (Employee, Task) samples:
    why is {Employee} not performing {Task} rather than any of their already-performed tasks?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_SWP_2A)


@pytest.mark.slow
def test_swp_2b_parity_over_random_samples():
    """(Swp,2b), over random Employee samples:
    why is {Employee} not performing any non-performed task rather than any of their already-performed
    tasks?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_SWP_2B)


@pytest.mark.slow
def test_swp_2c_parity_over_random_samples():
    """(Swp,2c), over random Task samples:
    why is any employee not performing {Task} rather than any of their already-performed tasks?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_SWP_2C)


@pytest.mark.slow
def test_swp_3_parity_over_random_samples():
    """(Swp,3), over random (Employee, Task) samples:
    why is {Employee} not performing {Task} rather than any of their already-performed tasks (even if it
    means changing their order)?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_SWP_3)


@pytest.mark.slow
def test_ord_1a_parity_over_random_samples():
    """(Ord,1a), over random (Employee, Task1, Task2) samples:
    why is {Employee} not performing {Task1} later in their planning, just after {Task2}?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_ORD_LAT_1)


@pytest.mark.slow
def test_ord_1b_parity_over_random_samples():
    """(Ord,1b), over random (Employee, Task1, Task2) samples:
    why is {Employee} not performing {Task1} earlier in their planning, just before {Task2}?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_ORD_EAR_1)


@pytest.mark.slow
def test_ord_2a_parity_over_random_samples():
    """(Ord,2a), over random (Employee, Task) samples:
    why is {Employee} not performing {Task} at a later stage of their planning?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_ORD_LAT_2)


@pytest.mark.slow
def test_ord_2b_parity_over_random_samples():
    """(Ord,2b), over random (Employee, Task) samples:
    why is {Employee} not performing {Task} at an earlier stage of their planning?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_ORD_EAR_2)


@pytest.mark.slow
def test_ord_2c_parity_over_random_samples():
    """(Ord,2c), over random (Employee, Task) samples:
    why is {Employee} not performing {Task} at any another stage in their planning?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_ORD_2)


@pytest.mark.slow
def test_ord_3_parity_over_random_samples():
    """(Ord,3), over random Employee samples:
    why is {Employee} not performing the activities of their route in another order?"""
    assert_parity_over_random_samples(build_austria_solution(), WHY_NOT_ORD_3)
