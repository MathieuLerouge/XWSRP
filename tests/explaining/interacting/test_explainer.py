# Standard libraries
import os
import shutil
from typing import Optional

# Third-party library
import pytest

# Local libraries
from src.explaining.exporting.explanation import define_multiple_contrastive_explanations_json_file_name
from src.explaining.explanation.predefined.explanation import (
    NonImprovingNegativeExplanation, PositiveExplanation, SkillNegativeExplanation, TimeNegativeExplanation
)
from src.explaining.interacting.configuration import ExplainerConfiguration
from src.explaining.interacting.explainer import Explainer
from src.explaining.modeling.instance import EditableInstance
from src.explaining.neighborhood.assembler import Assembler
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import TaskInsertion
from src.explaining.neighborhood.restriction import PrecedenceChain
from src.explaining.neighborhood.templates.mapper import Mapper
from src.explaining.processes import get_demo_solution
from src.explaining.question.free.question import FreeTextQuestion
from src.explaining.question.predefined.bank import QUESTIONS_TEMPLATES
from src.explaining.question.predefined.constants import WHY_NOT_INS_1, WHY_NOT_SWP_1
from src.explaining.question.predefined.question import (
    ContrastiveQuestion, CounterfactualQuestion, ScenarioQuestion
)
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


def build_explainer(solution: Solution, extractor_model: Optional[str] = None, history_enabled: bool = False,
                    using_already_computed_contrastive_explanations_enabled: bool = False,
                    activated_question_template_ids: Optional[list[str]] = None) -> Explainer:
    """
    Returns an Explainer with every optional behaviour switched off, so a test turns on only what it exercises.

    history_enabled, using_already_computed_contrastive_explanations_enabled and
    activated_question_template_ids are fixed at construction, so a test needing any of them other than
    their default must ask for it here rather than changing it afterward.

    Args:
        solution: The solution to explain.
        extractor_model: The extractor model string, for the tests asking a free-text question.
        history_enabled: Whether to keep every solution asked about or saved.
        using_already_computed_contrastive_explanations_enabled: Whether to reuse already computed
            contrastive explanations instead of recomputing them.
        activated_question_template_ids: Ids of the question templates to activate,
            or None to activate every available one.

    Returns:
        The hermetic Explainer: no history, no scenario or counterfactual questions, no cache, no export
        unless explicitly asked for above.
    """
    return Explainer(solution, ExplainerConfiguration(
        extractor_model=extractor_model, history_enabled=history_enabled,
        activated_question_template_ids=activated_question_template_ids,
        scenario_explanations_enabled=False, counterfactual_explanations_enabled=False,
        using_already_computed_contrastive_explanations_enabled=(
            using_already_computed_contrastive_explanations_enabled
        ),
        exporting_each_contrastive_explanation_automatically_enabled=False
    ))


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
    explainer = build_explainer(demo_solution, activated_question_template_ids=[WHY_NOT_SWP_1])
    with pytest.raises(ValueError, match="not handled by this explainer"):
        explainer.get_contrastive_explanation(WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[PositiveExplanation])


def test_asking_counts_are_tracked_per_template(demo_solution):
    explainer = build_explainer(demo_solution)
    assert explainer.get_asked_contrastive_question_count(WHY_NOT_INS_1) == 0
    for fields_values in FIELDS_VALUES_BY_EXPLANATION_TYPE.values():
        explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert explainer.get_asked_contrastive_question_count(WHY_NOT_INS_1) == \
           len(FIELDS_VALUES_BY_EXPLANATION_TYPE)
    explainer.reset_asked_predefined_question_counts()
    assert explainer.get_asked_contrastive_question_count(WHY_NOT_INS_1) == 0


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
    explainer = build_explainer(demo_solution, using_already_computed_contrastive_explanations_enabled=True)
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
        explainer = Explainer(demo_solution, ExplainerConfiguration.batch(
            using_already_computed_contrastive_explanations_enabled=True,
            contrastive_explanation_input_directory_relative_path=inputs_directory_relative_path
        ))
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
    explainer.configuration.scenario_explanations_enabled = True
    with pytest.raises(PermissionError):
        explainer.compute_scenario_explanation(EditableInstance.from_Instance(explainer.current_instance))


def test_a_scenario_explanation_answers_the_last_contrastive_question(demo_solution):
    explainer = build_explainer(demo_solution)
    explainer.configuration.scenario_explanations_enabled = True
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
    explainer.configuration.counterfactual_explanations_enabled = True
    with pytest.raises(ValueError, match="both None or both not None"):
        explainer.compute_counterfactual_explanation(WHY_NOT_INS_1)


def test_a_counterfactual_explanation_is_built_from_a_given_question(demo_solution):
    explainer = build_explainer(demo_solution)
    explainer.configuration.counterfactual_explanations_enabled = True
    explanation = explainer.compute_counterfactual_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    assert explanation.is_counterfactual
    assert explanation.text
    assert explainer.last_counterfactual_explanation is explanation


def test_a_counterfactual_explanation_falls_back_on_the_last_contrastive_question(demo_solution):
    explainer = build_explainer(demo_solution)
    explainer.configuration.counterfactual_explanations_enabled = True
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
    assert not explainer.configuration.history_enabled
    with pytest.raises(PermissionError, match="Historizing is disabled"):
        explainer.store_solution(demo_solution)


def test_enabling_history_works_on_a_renamed_copy_of_the_root_solution(demo_solution):
    """
    Enabling history must leave the root solution alone and question a renamed copy of it instead.

    history_enabled is fixed at construction, so the with/without comparison is across two separate
    Explainers rather than one toggled on then off.
    """
    root_explainer = build_explainer(demo_solution)
    root_solution_name = root_explainer.current_solution.name

    history_explainer = build_explainer(demo_solution, history_enabled=True)
    assert history_explainer.configuration.history_enabled
    assert history_explainer.current_solution.name != root_solution_name
    assert history_explainer.current_solution.name in history_explainer.history.solutions_names
    assert history_explainer.history.nb_instances == 1

    assert not root_explainer.configuration.history_enabled
    assert root_explainer.current_solution.name == root_solution_name


def test_a_stored_solution_is_reachable_by_name(demo_solution):
    explainer = build_explainer(demo_solution, history_enabled=True)
    support_solution = explainer.get_contrastive_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[PositiveExplanation]).support_solution
    explainer.store_solution(support_solution)
    assert support_solution.name in explainer.history.solutions_names
    assert explainer.history.get_solution_by_name(support_solution.name).name == support_solution.name


############################
# Routing by question kind #
############################

class StubExtractor:
    """
    Stands in for the llm Extractor, handing back a prepared neighborhood instead of calling a model.

    It lets the free-text route be tested down to the explanation without an LLM backend:
    everything past the extraction - solving, recognizing, phrasing - is the code under test.
    """

    def __init__(self, neighborhood):
        """
        Args:
            neighborhood: The neighborhood every extraction returns.
        """
        self._neighborhood = neighborhood

    def extract(self, question: FreeTextQuestion) -> Neighborhood:
        """Returns the prepared neighborhood, whatever the question."""
        return self._neighborhood


def give_explainer_a_stub_extractor(explainer: Explainer, neighborhood: Neighborhood):
    """
    Plants a StubExtractor in the explainer, as though the LLM had extracted the given neighborhood.

    Args:
        explainer: The explainer to plant it in.
        neighborhood: The neighborhood the extraction is to yield.
    """
    explainer._extractor = StubExtractor(neighborhood)
    explainer._solution_the_extractor_was_built_for = explainer.current_solution


def build_uncovered_neighborhood(solution: Solution) -> Neighborhood:
    """
    Builds a neighborhood NeighborhoodModel can solve but no question template's shape matches.

    Offering several non-performed tasks without offering every one of them is no template's shape,
    which is the case the free-text route cannot phrase an answer for.

    Args:
        solution: The solution the neighborhood is built around.

    Returns:
        The solvable but unrecognizable neighborhood.
    """
    instance = solution.instance
    employee = instance.get_employee_by_name("Ellen")
    some_non_performed_tasks_names = solution.non_performed_tasks_names[:2]
    operator = TaskInsertion(
        frozenset({employee}),
        frozenset(instance.get_task_by_name(name) for name in some_non_performed_tasks_names)
    )
    performed_tasks = list(solution.get_sequence(employee).get_contained_tasks())
    return Assembler.assemble([operator], [PrecedenceChain(performed_tasks)], solution)


def test_a_contrastive_question_is_answered_the_same_whichever_entry_point_asks_it(demo_solution):
    explainer = build_explainer(demo_solution)
    fields_values = FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation]
    through_the_question = explainer.get_explanation(
        ContrastiveQuestion(explainer.current_solution, WHY_NOT_INS_1, fields_values))
    through_the_template = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert type(through_the_question) is type(through_the_template)
    assert through_the_question.text == through_the_template.text


@pytest.mark.parametrize("build_follow_up_question,expected_method_name", [
    (lambda explainer, contrastive_question: ScenarioQuestion(
        contrastive_question, EditableInstance.from_Instance(explainer.current_instance)),
     "compute_scenario_explanation"),
    (lambda explainer, contrastive_question: CounterfactualQuestion(contrastive_question),
     "compute_counterfactual_explanation"),
])
def test_a_follow_up_question_is_refused_with_the_method_that_asks_it(
        demo_solution, build_follow_up_question, expected_method_name):
    """
    Scenario and counterfactual questions are follow-ups with their own entry points, not get_explanation's job.
    """
    explainer = build_explainer(demo_solution)
    contrastive_question = ContrastiveQuestion(
        explainer.current_solution, WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    with pytest.raises(TypeError, match=expected_method_name):
        explainer.get_explanation(build_follow_up_question(explainer, contrastive_question))


def test_something_that_is_not_a_question_is_refused(demo_solution):
    explainer = build_explainer(demo_solution)
    with pytest.raises(TypeError, match="not handled by this explainer"):
        explainer.get_explanation("Why isn't Ellen doing T2?")


def test_a_free_text_question_needs_an_extractor_model(demo_solution):
    """
    An explainer built without a model must say so, rather than fail somewhere inside the llm package.
    """
    explainer = build_explainer(demo_solution)
    with pytest.raises(ValueError, match="no extractor model"):
        explainer.get_free_text_explanation("Why isn't Ellen doing T2 right after leaving home?")


def test_a_free_text_question_the_catalogue_covers_is_answered(demo_solution):
    explainer = build_explainer(demo_solution, extractor_model="stub/model")
    covered_neighborhood = Mapper.map(ContrastiveQuestion(
        explainer.current_solution, WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation]))
    give_explainer_a_stub_extractor(explainer, covered_neighborhood)
    explanation = explainer.get_free_text_explanation("Why isn't Ellen doing T2 right after leaving home?")
    assert isinstance(explanation, TimeNegativeExplanation)
    assert explanation.text
    # A free-text answer is a contrastive one, so scenario and counterfactual follow-ups can build on it.
    assert explainer.last_contrastive_explanation is explanation


def test_a_free_text_question_the_catalogue_does_not_cover_says_so(demo_solution):
    """
    A question that is understood and solved but matches no template must fail saying exactly that.
    """
    explainer = build_explainer(demo_solution, extractor_model="stub/model")
    give_explainer_a_stub_extractor(explainer, build_uncovered_neighborhood(explainer.current_solution))
    with pytest.raises(NeighborhoodError, match="matches no question template"):
        explainer.get_free_text_explanation("Why isn't Ellen doing one of those two tasks?")


############
# Language #
############

def test_the_language_reaches_the_explanation_text(demo_solution):
    explainer = build_explainer(demo_solution)
    fields_values = FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation]
    english_explanation = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert english_explanation.language_is_english
    explainer.language = LANGUAGE_FRENCH_KEY
    assert explainer.language_is_french
    french_explanation = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert french_explanation.language_is_french
    assert french_explanation.text != english_explanation.text


##########
# Counts #
##########

def test_a_template_that_was_never_asked_has_a_count_of_zero(demo_solution):
    """
    A count must read zero for a template nobody asked, rather than raising.

    The web UI reads this straight into the contrastive tab's statistics text.
    """
    explainer = build_explainer(demo_solution)
    explainer.reset_asked_predefined_question_counts()
    assert explainer.get_asked_contrastive_question_count(WHY_NOT_SWP_1) == 0


def test_a_question_built_outside_the_activated_set_is_still_counted(demo_solution):
    """
    get_explanation takes a question already built, so its template need not be an activated one.
    """
    explainer = build_explainer(demo_solution, activated_question_template_ids=[])
    question = ContrastiveQuestion(
        explainer.current_solution, WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    assert explainer.get_explanation(question).text
    assert explainer.get_asked_contrastive_question_count(WHY_NOT_INS_1) == 1


###################################
# Naming a saved support solution #
###################################

def test_a_saved_scenario_support_solution_is_named_after_a_new_instance(demo_solution):
    explainer = build_explainer(demo_solution, history_enabled=True)
    explainer.configuration.scenario_explanations_enabled = True
    root_solution_name, root_instance_name = explainer.current_solution.name, explainer.current_instance.name
    explainer.get_contrastive_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    explainer.compute_scenario_explanation(EditableInstance.from_Instance(explainer.current_instance))
    if explainer.last_scenario_explanation.support_solution_is_feasible:
        explainer.save_last_scenario_support_solution()
        saved = explainer.last_scenario_explanation.support_solution
        assert saved.instance.name == f"{root_instance_name.rsplit('.', 1)[0]}.2"
        assert saved.name == f"{root_solution_name.rsplit('.', 2)[0]}.2.1"


def test_a_saved_counterfactual_support_solution_is_named_the_same_way(demo_solution):
    """
    A counterfactual save names its solution exactly as a scenario save does: both alter the instance.
    """
    explainer = build_explainer(demo_solution, history_enabled=True)
    explainer.configuration.counterfactual_explanations_enabled = True
    root_solution_name, root_instance_name = explainer.current_solution.name, explainer.current_instance.name
    explainer.compute_counterfactual_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    if explainer.last_counterfactual_explanation.support_solution_is_feasible:
        explainer.save_last_counterfactual_support_solution()
        saved = explainer.last_counterfactual_explanation.support_solution
        assert saved.instance.name == f"{root_instance_name.rsplit('.', 1)[0]}.2"
        assert saved.name == f"{root_solution_name.rsplit('.', 2)[0]}.2.1"


#####################
# Exporting in bulk #
#####################

def test_exporting_every_computed_explanation_honours_the_configured_directory(demo_solution, tmp_path):
    """
    The bulk export must write where the explainer was configured to write, as the single one does.

    It used to pass its own None straight through, letting the exporter fall back to the default
    outputs directory and silently ignore the configured one.
    """
    outputs_directory_relative_path = f"outputs/{tmp_path.name}"
    outputs_directory_path = os.path.join(os.getcwd(), outputs_directory_relative_path)
    os.makedirs(outputs_directory_path, exist_ok=True)
    try:
        explainer = build_explainer(demo_solution, using_already_computed_contrastive_explanations_enabled=True)
        explainer.configuration.contrastive_explanation_output_directory_relative_path = outputs_directory_relative_path
        explainer.get_contrastive_explanation(
            WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
        explainer.export_all_already_computed_contrastive_explanations()
        assert os.listdir(outputs_directory_path), "the bulk export wrote nothing into the configured directory"
    finally:
        shutil.rmtree(outputs_directory_path, ignore_errors=True)
