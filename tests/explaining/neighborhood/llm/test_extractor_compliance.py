# Standard libraries
import os
import random

# Third-party libraries
import pytest
from instructor import Mode

# Local libraries
from src.explaining.neighborhood.llm.exceptions import NeighborhoodExtractionError
from src.explaining.neighborhood.llm.extractor import Extractor
from src.explaining.neighborhood.templates.checker import (
    INSERTION_FAMILY, REORDERING_FAMILY, SWAP_FAMILY, TemplateComplianceChecker
)
from src.explaining.questioning.questions_templates_bank import (
    QUESTIONS_TEMPLATES,
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)
from src.modeling.solution import Solution
from tests.importing.helpers import build_solution

# Global variables
# The backend defaults to a free local Ollama model rather than main_configuration.EXTRACTOR_MODEL,
# so these tests don't silently start hitting a paid provider if that configuration ever changes.
# Set _MODEL_ENV_VAR to an instructor "provider/model-name" string to compare another backend,
# e.g. XWSRP_EXTRACTOR_TEST_MODEL=mistral/mistral-medium-latest pytest -m llm
_MODEL_ENV_VAR = "XWSRP_EXTRACTOR_TEST_MODEL"
_DEFAULT_MODEL = "ollama/qwen2.5:7b"
_MODEL = os.environ.get(_MODEL_ENV_VAR, _DEFAULT_MODEL)
# NB: Ollama's tool-calling support isn't reliable enough for instructor's default mode, so it needs MD_JSON.
# Hosted providers do tool calling properly, so they are left on their own per-provider default.
_MODE = Mode.MD_JSON if _MODEL.startswith("ollama/") else None
_RANDOM_SEED = 42
_MAX_SAMPLES_PER_TEMPLATE = 3

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
def get_test_solution() -> Solution:
    """The tests' data directory's reference solution, with its KPIs computed."""
    reference_solution = build_solution()
    reference_solution.compute_kpis()
    return reference_solution


@pytest.fixture
def prepare_extractor(get_test_solution) -> Extractor:
    """An Extractor asking the local model about the reference solution."""
    return Extractor(get_test_solution, _MODEL, mode=_MODE)


def assert_every_extracted_neighborhood_matches_its_family(
        extractor: Extractor, solution: Solution, template_id: str
):
    """
    Check that the LLM pipeline turns the given template's own wording into a Neighborhood that is
    template-compliant and matched as that template's own family,
    over up to _MAX_SAMPLES_PER_TEMPLATE of its valid field-value combinations.

    Matching the family is required, not merely being compliant somewhere in the catalogue:
    a question worded as (Ord,2c) answered with a compliant (Ins,*) shape has been misread.

    An extraction failure counts as a miss rather than a case to skip.
    The question text comes verbatim from a template the catalogue covers.
    So the LLM reporting it as not coverable is the pipeline getting it wrong.

    Args:
        extractor: The Extractor to ask, already bound to solution.
        solution: The solution the questions are asked about.
        template_id: The identifier of the question template to render and extract.

    Raises:
        AssertionError: if the template has no valid field-value combination at all for solution,
            if extraction fails outright on a sampled question, or if an extracted neighborhood is
            matched as another family, or not matched at all.
    """
    expected_family = _EXPECTED_FAMILY_BY_TEMPLATE_ID[template_id]
    template = QUESTIONS_TEMPLATES[template_id]
    all_fields_values = template.compute_all_fields_valid_values(solution)
    assert len(all_fields_values) > 0, f"No valid field-value combination found for template {template_id}"
    random.Random(_RANDOM_SEED).shuffle(all_fields_values)
    
    for fields_values in all_fields_values[:_MAX_SAMPLES_PER_TEMPLATE]:
        question_text = template.complete_text_with_fields_values(fields_values)
        try:
            neighborhood = extractor.extract(question_text)
        except NeighborhoodExtractionError as error:
            raise AssertionError(f"Extraction failed for {question_text!r}") from error
        assert TemplateComplianceChecker.match(neighborhood) == expected_family, (
            f"The neighborhood extracted from {question_text!r} is not a {expected_family} one "
            f"the question catalogue produces"
        )
        assert TemplateComplianceChecker.is_compliant(neighborhood)


#########
# Tests #
#########


@pytest.mark.llm
def test_ins_1_llm_compliance(prepare_extractor, get_test_solution):
    """(Ins,1), over sampled (Employee, Task, Activity) combinations:
    why is employee {Employee} not performing task {Task} just after activity {Activity}?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_INS_1)


@pytest.mark.llm
def test_ins_2a_llm_compliance(prepare_extractor, get_test_solution):
    """(Ins,2a), over sampled (Employee, Task) combinations:
    why is employee {Employee} not performing task {Task} between two consecutive activities of
    their route?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_INS_2A)


@pytest.mark.llm
def test_ins_2b_llm_compliance(prepare_extractor, get_test_solution):
    """(Ins,2b), over sampled Employees:
    why is employee {Employee} not performing any non-performed task between two consecutive
    activities of their route?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_INS_2B)


@pytest.mark.llm
def test_ins_2c_llm_compliance(prepare_extractor, get_test_solution):
    """(Ins,2c), over sampled Tasks:
    why is any employee not performing task {Task} between two consecutive activities of their route?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_INS_2C)


@pytest.mark.llm
def test_ins_3_llm_compliance(prepare_extractor, get_test_solution):
    """(Ins,3), over sampled (Employee, Task) combinations:
    why is employee {Employee} not performing task {Task} in addition to their already-performed
    activities (even if it means changing their order)?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_INS_3)


@pytest.mark.llm
def test_swp_1_llm_compliance(prepare_extractor, get_test_solution):
    """(Swp,1), over sampled (Employee, Task1, Task2) combinations:
    why is employee {Employee} not performing task {Task1} rather than task {Task2}?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_SWP_1)


@pytest.mark.llm
def test_swp_2a_llm_compliance(prepare_extractor, get_test_solution):
    """(Swp,2a), over sampled (Employee, Task) combinations:
    why is employee {Employee} not performing task {Task} rather than any of their already-performed
    tasks?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_SWP_2A)


@pytest.mark.llm
def test_swp_2b_llm_compliance(prepare_extractor, get_test_solution):
    """(Swp,2b), over sampled Employees:
    why is employee {Employee} not performing any non-performed task rather than any of their
    already-performed tasks?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_SWP_2B)


@pytest.mark.llm
def test_swp_2c_llm_compliance(prepare_extractor, get_test_solution):
    """(Swp,2c), over sampled Tasks:
    why is any employee not performing task {Task} rather than any of their already-performed tasks?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_SWP_2C)


@pytest.mark.llm
def test_swp_3_llm_compliance(prepare_extractor, get_test_solution):
    """(Swp,3), over sampled (Employee, Task) combinations:
    why is employee {Employee} not performing task {Task} rather than any of their already-performed
    tasks (even if it means changing their order)?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_SWP_3)


@pytest.mark.llm
def test_ord_1a_llm_compliance(prepare_extractor, get_test_solution):
    """(Ord,1a), over sampled (Employee, Task1, Task2) combinations:
    why is employee {Employee} not performing task {Task1} later in their planning, just after
    task {Task2}?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_ORD_LAT_1)


@pytest.mark.llm
def test_ord_1b_llm_compliance(prepare_extractor, get_test_solution):
    """(Ord,1b), over sampled (Employee, Task1, Task2) combinations:
    why is employee {Employee} not performing task {Task1} earlier in their planning, just before
    task {Task2}?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_ORD_EAR_1)


@pytest.mark.llm
def test_ord_2a_llm_compliance(prepare_extractor, get_test_solution):
    """(Ord,2a), over sampled (Employee, Task) combinations:
    why is employee {Employee} not performing task {Task} at a later stage of their planning?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_ORD_LAT_2)


@pytest.mark.llm
def test_ord_2b_llm_compliance(prepare_extractor, get_test_solution):
    """(Ord,2b), over sampled (Employee, Task) combinations:
    why is employee {Employee} not performing task {Task} at an earlier stage of their planning?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_ORD_EAR_2)


@pytest.mark.llm
def test_ord_2c_llm_compliance(prepare_extractor, get_test_solution):
    """(Ord,2c), over sampled (Employee, Task) combinations:
    why is employee {Employee} not performing task {Task} at any another stage in their planning?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_ORD_2)


@pytest.mark.llm
def test_ord_3_llm_compliance(prepare_extractor, get_test_solution):
    """(Ord,3), over sampled Employees:
    why is employee {Employee} not performing the activities of their route in another order?"""
    assert_every_extracted_neighborhood_matches_its_family(prepare_extractor, get_test_solution, WHY_NOT_ORD_3)
