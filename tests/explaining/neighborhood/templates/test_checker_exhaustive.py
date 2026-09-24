# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.templates.checker import (
    INSERTION_FAMILY, REORDERING_FAMILY, SWAP_FAMILY, TemplateComplianceChecker
)
from src.explaining.neighborhood.templates.mapper import Mapper
from src.explaining.questioning.question import ContrastiveQuestion
from src.explaining.questioning.questions_templates_bank import (
    QUESTIONS_TEMPLATES, WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)
from src.modeling.solution import Solution
from tests.importing.helpers import build_solution

# Global variable
_EXPECTED_FAMILY_BY_TEMPLATE_ID: dict[str, str] = {
    WHY_NOT_INS_1: INSERTION_FAMILY,
    WHY_NOT_INS_2A: INSERTION_FAMILY,
    WHY_NOT_INS_2B: INSERTION_FAMILY,
    WHY_NOT_INS_2C: INSERTION_FAMILY,
    WHY_NOT_INS_3: INSERTION_FAMILY,
    WHY_NOT_SWP_1: SWAP_FAMILY,
    WHY_NOT_SWP_2A: SWAP_FAMILY,
    WHY_NOT_SWP_2B: SWAP_FAMILY,
    WHY_NOT_SWP_2C: SWAP_FAMILY,
    WHY_NOT_SWP_3: SWAP_FAMILY,
    WHY_NOT_ORD_LAT_1: REORDERING_FAMILY,
    WHY_NOT_ORD_EAR_1: REORDERING_FAMILY,
    WHY_NOT_ORD_LAT_2: REORDERING_FAMILY,
    WHY_NOT_ORD_EAR_2: REORDERING_FAMILY,
    WHY_NOT_ORD_2: REORDERING_FAMILY,
    WHY_NOT_ORD_3: REORDERING_FAMILY,
}


###########
# Helpers #
###########


@pytest.fixture(scope="module")
def get_text_solution() -> Solution:
    """The tests' data directory's reference solution, with its KPIs computed."""
    reference_solution = build_solution()
    reference_solution.compute_kpis()
    return reference_solution


def assert_every_mapped_neighborhood_matches(solution: Solution, template_id: str):
    """
    Check that every neighborhood Mapper induces for the given template is template-compliant,
    and matched as that template's own family, over every valid field-value combination
    - not just the handful test_checker's own round-trip samples.

    Args:
        solution: The solution the questions are asked about.
        template_id: The identifier of the question template to enumerate and map.

    Raises:
        AssertionError: if the template has no valid field-value combination at all for solution,
            or if any mapped neighborhood is matched as another family, or not matched at all.
    """
    expected_family = _EXPECTED_FAMILY_BY_TEMPLATE_ID[template_id]
    all_fields_values = QUESTIONS_TEMPLATES[template_id].compute_all_fields_valid_values(solution)
    assert len(all_fields_values) > 0, f"No valid field-value combination found for template {template_id}"
    for fields_values in all_fields_values:
        neighborhood = Mapper.map(ContrastiveQuestion(solution, template_id, fields_values))
        assert TemplateComplianceChecker.match(neighborhood) == expected_family, (
            f"Template {template_id} maps {fields_values} to a neighborhood of another family"
        )
        assert TemplateComplianceChecker.is_compliant(neighborhood)


#########
# Tests #
#########


def test_ins_1_compliance_over_all_valid_fields_values(get_text_solution):
    """(Ins,1), over every valid (Employee, Task, Activity) combination:
    why is {Employee} not performing {Task} just after {Activity}?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_INS_1)


def test_ins_2a_compliance_over_all_valid_fields_values(get_text_solution):
    """(Ins,2a), over every valid (Employee, Task) combination:
    why is {Employee} not performing {Task} between two consecutive activities of their route?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_INS_2A)


def test_ins_2b_compliance_over_all_valid_fields_values(get_text_solution):
    """(Ins,2b), over every valid Employee:
    why is {Employee} not performing any non-performed task between two consecutive activities of
    their route?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_INS_2B)


def test_ins_2c_compliance_over_all_valid_fields_values(get_text_solution):
    """(Ins,2c), over every valid Task:
    why is any employee not performing {Task} between two consecutive activities of their route?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_INS_2C)


def test_ins_3_compliance_over_all_valid_fields_values(get_text_solution):
    """(Ins,3), over every valid (Employee, Task) combination:
    why is {Employee} not performing {Task} in addition to their already-performed activities
    (even if it means changing their order)?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_INS_3)


def test_swp_1_compliance_over_all_valid_fields_values(get_text_solution):
    """(Swp,1), over every valid (Employee, Task1, Task2) combination:
    why is {Employee} not performing {Task1} rather than {Task2}?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_SWP_1)


def test_swp_2a_compliance_over_all_valid_fields_values(get_text_solution):
    """(Swp,2a), over every valid (Employee, Task) combination:
    why is {Employee} not performing {Task} rather than any of their already-performed tasks?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_SWP_2A)


def test_swp_2b_compliance_over_all_valid_fields_values(get_text_solution):
    """(Swp,2b), over every valid Employee:
    why is {Employee} not performing any non-performed task rather than any of their already-performed
    tasks?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_SWP_2B)


def test_swp_2c_compliance_over_all_valid_fields_values(get_text_solution):
    """(Swp,2c), over every valid Task:
    why is any employee not performing {Task} rather than any of their already-performed tasks?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_SWP_2C)


def test_swp_3_compliance_over_all_valid_fields_values(get_text_solution):
    """(Swp,3), over every valid (Employee, Task) combination:
    why is {Employee} not performing {Task} rather than any of their already-performed tasks (even if it
    means changing their order)?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_SWP_3)


def test_ord_1a_compliance_over_all_valid_fields_values(get_text_solution):
    """(Ord,1a), over every valid (Employee, Task1, Task2) combination:
    why is {Employee} not performing {Task1} later in their planning, just after {Task2}?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_ORD_LAT_1)


def test_ord_1b_compliance_over_all_valid_fields_values(get_text_solution):
    """(Ord,1b), over every valid (Employee, Task1, Task2) combination:
    why is {Employee} not performing {Task1} earlier in their planning, just before {Task2}?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_ORD_EAR_1)


def test_ord_2a_compliance_over_all_valid_fields_values(get_text_solution):
    """(Ord,2a), over every valid (Employee, Task) combination:
    why is {Employee} not performing {Task} at a later stage of their planning?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_ORD_LAT_2)


def test_ord_2b_compliance_over_all_valid_fields_values(get_text_solution):
    """(Ord,2b), over every valid (Employee, Task) combination:
    why is {Employee} not performing {Task} at an earlier stage of their planning?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_ORD_EAR_2)


def test_ord_2c_compliance_over_all_valid_fields_values(get_text_solution):
    """(Ord,2c), over every valid (Employee, Task) combination:
    why is {Employee} not performing {Task} at any another stage in their planning?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_ORD_2)


def test_ord_3_compliance_over_all_valid_fields_values(get_text_solution):
    """(Ord,3), over every valid Employee:
    why is {Employee} not performing the activities of their route in another order?"""
    assert_every_mapped_neighborhood_matches(get_text_solution, WHY_NOT_ORD_3)
