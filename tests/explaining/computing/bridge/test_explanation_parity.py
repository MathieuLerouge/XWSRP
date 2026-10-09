# Third-party library
import pytest

# Local libraries
from src.explaining.explanation.predefined.explanation import create_explanation
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.question.predefined.question import ContrastiveQuestion
from src.explaining.question.predefined.bank import (
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY
from tests.explaining.computing.helpers import (
    build_austria_solution, gap_from_conflict, get_neighborhood_computation_pipeline_result,
    get_tailored_computation_pipeline_result
)

# One curated case per template, using the field values test_parity.py's own cases use, so that the two
# files describe the same sixteen transformations.
_CASES: list[tuple[str, list[str]]] = [
    (WHY_NOT_INS_1, ["Ellen", "T27", "T17"]),
    (WHY_NOT_INS_2A, ["Ellen", "T27"]),
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

# The templates whose two pipelines are known to settle on the very same arrangement whenever they agree
# on the feasibility gap, and so are expected to word it identically. They are exactly the ones
# test_parity.py asserts identical KPIs for. The (Swp,*) family is left out on purpose: its two pipelines
# legitimately pick different tasks to swap - see assert_at_least_as_good_kpis's docstring in helpers.py -
# and a different swap has no reason to be described with the same sentence.
_TEMPLATES_SETTLING_ON_THE_SAME_ARRANGEMENT = (
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)


###########
# Helpers #
###########


def assert_describes_the_transformation(question: ContrastiveQuestion, result: TransformationResult):
    """
    Assert a transformation result carries a usable description in both languages, and yields a text.

    Args:
        question: The question the result answers.
        result: The result to check.

    Raises:
        AssertionError: if either language's description is missing or empty, or if the explanation
            built from the result has no text.
    """
    for language_key in (LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY):
        assert language_key in result.descriptions, f"No {language_key} description was built"
        assert result.descriptions[language_key] != "", f"The {language_key} description is empty"
    assert create_explanation(question, result).text != "", "The explanation built has no text"


###########
# Fixture #
###########


@pytest.fixture(scope="module")
def get_austria_solution():
    """The Austria reference solution, with its KPIs computed."""
    solution = build_austria_solution()
    solution.compute_kpis()
    return solution


#########
# Tests #
#########


@pytest.mark.parametrize("template_id,fields_values", _CASES, ids=[case[0] for case in _CASES])
def test_the_neighborhood_pipeline_explains_every_template(get_austria_solution, template_id, fields_values):
    """
    Every question template's neighborhood carries all the way to an explanation text.

    This is the bridge's own contract: the pipeline used to stop at a support solution and a conflict,
    with no description to build a TransformationResult - and so no explanation - from.
    """
    question, result = get_neighborhood_computation_pipeline_result(
        get_austria_solution, template_id, fields_values
    )
    assert question.template.id == template_id, "The neighborhood was recognized as another question"
    assert question.fields_values == fields_values
    assert_describes_the_transformation(question, result)


@pytest.mark.parametrize("template_id,fields_values", _CASES, ids=[case[0] for case in _CASES])
def test_both_pipelines_describe_the_transformation_the_same_way(
        get_austria_solution, template_id, fields_values):
    """
    The two pipelines word the same transformation identically, whenever they settle on the same one.

    Both descriptions come from TransformationDescriptionBuilder, so agreeing here is what shows the
    neighborhood pipeline reads the settled-on position and route correctly off its solved model rather
    than merely producing some sentence.
    """
    tailored_question, tailored_result = get_tailored_computation_pipeline_result(
        get_austria_solution, template_id, fields_values
    )
    neighborhood_question, neighborhood_result = get_neighborhood_computation_pipeline_result(
        get_austria_solution, template_id, fields_values
    )
    assert_describes_the_transformation(tailored_question, tailored_result)
    assert_describes_the_transformation(neighborhood_question, neighborhood_result)
    if template_id not in _TEMPLATES_SETTLING_ON_THE_SAME_ARRANGEMENT:
        return
    if gap_from_conflict(tailored_result.conflict) != gap_from_conflict(neighborhood_result.conflict):
        # A strictly smaller neighborhood gap means the two pipelines landed on different arrangements,
        # which have no reason to be worded the same - the rule test_parity.py applies to conflicts.
        return
    assert tailored_result.descriptions == neighborhood_result.descriptions, (
        f"The two pipelines word {template_id} differently: "
        f"tailored={tailored_result.descriptions}, neighborhood={neighborhood_result.descriptions}"
    )
    assert (create_explanation(tailored_question, tailored_result).text
            == create_explanation(neighborhood_question, neighborhood_result).text), (
        f"The two pipelines explain {template_id} with different texts"
    )
