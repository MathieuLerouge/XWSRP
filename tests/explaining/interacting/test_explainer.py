# Standard libraries
import os
import shutil

# Third-party library
import pytest

# Local libraries
from src.explaining.exporting.explanation import define_multiple_contrastive_explanations_json_file_name
from src.explaining.explanation.predefined.explanation import (
    NonImprovingNegativeExplanation, PositiveExplanation, SkillNegativeExplanation, TimeNegativeExplanation
)
from src.explaining.interacting.explainer import Explainer
from src.explaining.modeling.instance import EditableInstance
from src.explaining.processes import get_demo_solution
from src.explaining.question.predefined.bank import QUESTIONS_TEMPLATES
from src.explaining.question.predefined.constants import WHY_NOT_INS_1
from src.modeling.solution import Solution
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY

# Global variables
# Field values of the (Ins,1) template on the demo solution, one per kind of explanation it can produce.
# Picked by asking every one of that template's 806 valid combinations and grouping the answers,
# so that each branch of create_explanation is covered by a case that actually reaches it.
FIELDS_VALUES_BY_EXPLANATION_TYPE = {
    TimeNegativeExplanation: ['Ellen', 'T2', 'Start'],
    SkillNegativeExplanation: ['Ellen', 'T6', 'Start'],
    PositiveExplanation: ['Alexander', 'T22', 'T6'],
    NonImprovingNegativeExplanation: ['Adam', 'T1', 'T24'],
}
STORED_DEMO_EXPLANATIONS_PATH = "data/demo/explanations/explanations_solution_demo.json"


@pytest.fixture(autouse=True)
def restore_the_question_bank_language():
    """
    Puts the question catalogue back into English after each test.

    QUESTIONS_TEMPLATES holds module-level singletons and Explainer.set_language mutates them in place,
    so a test asking in French would otherwise leave every later test asking in French too.
    """
    yield
    for question_template in QUESTIONS_TEMPLATES.values():
        question_template.set_language(LANGUAGE_ENGLISH_KEY)


@pytest.fixture(scope="module")
def demo_solution() -> Solution:
    """The demo solution every test here questions."""
    return get_demo_solution()


def build_explainer(solution: Solution) -> Explainer:
    """
    Returns an Explainer with every optional behaviour switched off, so a test turns on only what it exercises.

    Args:
        solution: The solution to explain.

    Returns:
        The hermetic Explainer: no history, no scenario or counterfactual questions, no cache, no export.
    """
    explainer = Explainer(solution)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    return explainer


##########################
# Contrastive questions #
##########################

@pytest.mark.parametrize("expected_type,fields_values", list(FIELDS_VALUES_BY_EXPLANATION_TYPE.items()))
def test_contrastive_explanation_has_the_kind_its_transformation_calls_for(demo_solution, expected_type, fields_values):
    explainer = build_explainer(demo_solution)
    explanation = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert type(explanation) is expected_type
    assert explanation.text
    assert explanation.support_solution is not None
    assert explanation.question.fields_values == fields_values


def test_positive_and_negative_agree_with_the_solution_ordering(demo_solution):
    """
    is_positive() must match the comparison create_explanation classifies on, for every kind.
    """
    explainer = build_explainer(demo_solution)
    for expected_type, fields_values in FIELDS_VALUES_BY_EXPLANATION_TYPE.items():
        explanation = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
        if explanation.support_solution_is_feasible:
            improves = explanation.support_solution > explanation.question.solution
            assert explanation.is_positive() is improves, expected_type
        else:
            assert explanation.is_negative(), expected_type


def test_asking_an_unactivated_template_is_refused(demo_solution):
    explainer = build_explainer(demo_solution)
    explainer.deactivate_question_template(WHY_NOT_INS_1)
    with pytest.raises(ValueError, match="not handled by this explainer"):
        explainer.get_contrastive_explanation(WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[PositiveExplanation])


def test_asking_counts_are_tracked_per_template(demo_solution):
    explainer = build_explainer(demo_solution)
    assert explainer.get_contrastive_questions_asked_count(WHY_NOT_INS_1) == 0
    for fields_values in FIELDS_VALUES_BY_EXPLANATION_TYPE.values():
        explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert explainer.get_contrastive_questions_asked_count(WHY_NOT_INS_1) == \
        len(FIELDS_VALUES_BY_EXPLANATION_TYPE)
    explainer.reset_questions_asked_counts()
    assert explainer.get_contrastive_questions_asked_count(WHY_NOT_INS_1) == 0


def test_the_last_contrastive_explanation_is_the_one_just_asked(demo_solution):
    explainer = build_explainer(demo_solution)
    with pytest.raises(PermissionError):
        _ = explainer.last_contrastive_explanation
    explanation = explainer.get_contrastive_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    assert explainer.last_contrastive_explanation is explanation


###########
# Caching #
###########

def test_an_explanation_asked_twice_is_served_from_memory(demo_solution):
    """
    With the cache on, the second ask must hand back the very object the first one produced.
    """
    explainer = build_explainer(demo_solution)
    explainer.enable_using_already_computed_contrastive_explanations()
    fields_values = FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation]
    first = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    second = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert first is second


def test_an_explanation_is_not_reused_when_the_cache_is_off(demo_solution):
    explainer = build_explainer(demo_solution)
    fields_values = FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation]
    first = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    second = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert first is not second
    assert first.text == second.text


def test_stored_explanations_are_loaded_and_served_from_disk(demo_solution, tmp_path):
    """
    Enabling the cache must import the stored multi-explanation file and answer from it without recomputing.

    NB: the file has to be named as define_multiple_contrastive_explanations_json_file_name derives it,
    and to sit inside the project, since the inputs directory is a project-relative path.
    """
    inputs_directory_relative_path = f"outputs/{tmp_path.name}"
    inputs_directory_path = os.path.join(os.getcwd(), inputs_directory_relative_path)
    os.makedirs(inputs_directory_path, exist_ok=True)
    try:
        shutil.copy(
            STORED_DEMO_EXPLANATIONS_PATH,
            os.path.join(inputs_directory_path,
                         define_multiple_contrastive_explanations_json_file_name(demo_solution))
        )
        explainer = build_explainer(demo_solution)
        explainer.contrastive_explanations_inputs_directory_relative_path = inputs_directory_relative_path
        explainer.enable_using_already_computed_contrastive_explanations()
        assert len(explainer.already_computed_contrastive_explanations) > 0
        explanation = explainer.get_contrastive_explanation(
            WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
        assert explanation in explainer.already_computed_contrastive_explanations
        assert explanation.text
    finally:
        shutil.rmtree(inputs_directory_path, ignore_errors=True)


############
# Scenario #
############

def test_a_scenario_question_needs_scenario_explanations_enabled(demo_solution):
    explainer = build_explainer(demo_solution)
    explainer.get_contrastive_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    with pytest.raises(PermissionError, match="Scenario explanations are not enabled"):
        explainer.compute_scenario_explanation(EditableInstance.from_Instance(explainer.current_instance))


def test_a_scenario_question_needs_a_contrastive_one_before_it(demo_solution):
    explainer = build_explainer(demo_solution)
    explainer.enable_scenario_explanations()
    with pytest.raises(PermissionError):
        explainer.compute_scenario_explanation(EditableInstance.from_Instance(explainer.current_instance))


def test_a_scenario_explanation_answers_the_last_contrastive_question(demo_solution):
    explainer = build_explainer(demo_solution)
    explainer.enable_scenario_explanations()
    contrastive_explanation = explainer.get_contrastive_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    scenario_explanation = explainer.compute_scenario_explanation(
        EditableInstance.from_Instance(explainer.current_instance))
    assert scenario_explanation.is_scenario
    assert scenario_explanation.text
    assert scenario_explanation.question.fields_values == contrastive_explanation.question.fields_values
    assert explainer.last_scenario_explanation is scenario_explanation


##################
# Counterfactual #
##################

def test_a_counterfactual_question_needs_counterfactual_explanations_enabled(demo_solution):
    explainer = build_explainer(demo_solution)
    with pytest.raises(PermissionError, match="Counterfactual explanations are not enabled"):
        explainer.compute_counterfactual_explanation(
            WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])


def test_a_counterfactual_question_refuses_half_of_a_question(demo_solution):
    explainer = build_explainer(demo_solution)
    explainer.enable_counterfactual_explanations()
    with pytest.raises(ValueError, match="both None or both not None"):
        explainer.compute_counterfactual_explanation(WHY_NOT_INS_1)


def test_a_counterfactual_explanation_is_built_from_a_given_question(demo_solution):
    explainer = build_explainer(demo_solution)
    explainer.enable_counterfactual_explanations()
    explanation = explainer.compute_counterfactual_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    assert explanation.is_counterfactual
    assert explanation.text
    assert explainer.last_counterfactual_explanation is explanation


def test_a_counterfactual_explanation_falls_back_on_the_last_contrastive_question(demo_solution):
    explainer = build_explainer(demo_solution)
    explainer.enable_counterfactual_explanations()
    contrastive_explanation = explainer.get_contrastive_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    explanation = explainer.compute_counterfactual_explanation()
    assert explanation.is_counterfactual
    assert explanation.question.fields_values == contrastive_explanation.question.fields_values


###########
# History #
###########

def test_storing_a_solution_needs_history_enabled(demo_solution):
    explainer = build_explainer(demo_solution)
    assert explainer.history_is_disabled
    with pytest.raises(PermissionError, match="Historizing is disabled"):
        explainer.store_solution(demo_solution)


def test_enabling_history_works_on_a_renamed_copy_of_the_root_solution(demo_solution):
    """
    Enabling history must leave the root solution alone and question a renamed copy of it instead.
    """
    explainer = build_explainer(demo_solution)
    root_solution_name = explainer.current_solution.name
    explainer.enable_history()
    assert explainer.history_is_enabled
    assert explainer.current_solution.name != root_solution_name
    assert explainer.current_solution.name in explainer.solutions_names
    assert explainer.nb_instances == 1
    explainer.disable_history()
    assert explainer.history_is_disabled
    assert explainer.current_solution.name == root_solution_name


def test_a_stored_solution_is_reachable_by_name(demo_solution):
    explainer = build_explainer(demo_solution)
    explainer.enable_history()
    support_solution = explainer.get_contrastive_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[PositiveExplanation]).support_solution
    explainer.store_solution(support_solution)
    assert support_solution.name in explainer.solutions_names
    assert explainer.get_solution_by_name(support_solution.name).name == support_solution.name


############
# Language #
############

def test_the_language_reaches_the_explanation_text(demo_solution):
    explainer = build_explainer(demo_solution)
    fields_values = FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation]
    english_explanation = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert english_explanation.language_is_english
    explainer.set_language(LANGUAGE_FRENCH_KEY)
    assert explainer.language_is_french
    french_explanation = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert french_explanation.language_is_french
    assert french_explanation.text != english_explanation.text
