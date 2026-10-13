# Standard libraries
import os
import shutil
from typing import Optional

# Third-party library
import pytest

# Local libraries
from src.explaining.computing.neighborhood.facts import ExplanationFacts, ExplanationOutcomes
from src.explaining.exporting.explanation import (
    define_multiple_contrastive_explanations_json_file_name, define_single_free_text_explanation_json_file_name
)
from src.explaining.explanation.free.explanation import FreeTextExplanation
from src.explaining.explanation.predefined.explanation import (
    NonImprovingNegativeExplanation, PositiveExplanation, SkillNegativeExplanation, TimeNegativeExplanation
)
from src.explaining.interacting.configuration import ExplainerConfiguration, FreeTextExplanationModes, Pipelines
from src.explaining.interacting.counter import QuestionType
from src.explaining.interacting.explainer import Explainer
from src.explaining.modeling.instance import EditableInstance
from src.explaining.neighborhood.assembler import Assembler
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.neighborhood.neighborhood import Neighborhood, NeighborhoodExtractionModes
from src.explaining.neighborhood.operator import TaskInsertion
from src.explaining.neighborhood.restriction import PrecedenceChain
from src.explaining.neighborhood.bridge.mapper import Mapper
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
                    using_cached_contrastive_explanations_enabled: bool = False,
                    activated_question_template_ids: Optional[list[str]] = None,
                    writer_model: Optional[str] = None, free_text_explanation_mode: Optional[str] = None,
                    counterfactual_explanations_enabled: bool = False) -> Explainer:
    """
    Returns an Explainer with every optional behaviour switched off, so a test turns on only what it exercises.

    history_enabled, using_cached_contrastive_explanations_enabled and activated_question_template_ids are fixed
    at construction, so a test needing any of them other than their default must ask for it here rather than
    changing it afterward.

    Args:
        solution: The solution to explain.
        extractor_model: The extractor model string, for the tests asking a free-text question.
        writer_model: The writer model string, for the tests asking a free-text question in written mode.
        free_text_explanation_mode: How a free-text question's explanation is worded, or None for the default.
        counterfactual_explanations_enabled: Whether to allow counterfactual follow-up questions.
        history_enabled: Whether to keep every solution asked about or saved.
        using_cached_contrastive_explanations_enabled: Whether to reuse cached contrastive explanations
            instead of recomputing them.
        activated_question_template_ids: Ids of the question templates to activate,
            or None to activate every available one.

    Returns:
        The hermetic Explainer: no history, no scenario or counterfactual questions, no cache, no export
        unless explicitly asked for above.
    """
    configuration = ExplainerConfiguration(
        history_enabled=history_enabled,
        neighborhood_llm_model=extractor_model,
        explanation_writing_llm_model=writer_model,
        free_text_explanation_mode=free_text_explanation_mode,
        activated_question_template_ids=activated_question_template_ids,
        scenario_explanations_enabled=False,
        counterfactual_explanations_enabled=counterfactual_explanations_enabled,
        using_cached_contrastive_explanations_enabled=using_cached_contrastive_explanations_enabled,
        exporting_each_contrastive_explanation_automatically_enabled=False
    )
    return Explainer(solution, configuration)


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
    assert explainer.explanation_counter.get_count(QuestionType.CONTRASTIVE, WHY_NOT_INS_1) == 0
    for fields_values in FIELDS_VALUES_BY_EXPLANATION_TYPE.values():
        explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert explainer.explanation_counter.get_count(QuestionType.CONTRASTIVE, WHY_NOT_INS_1) == \
           len(FIELDS_VALUES_BY_EXPLANATION_TYPE)
    explainer.explanation_counter.reset()
    assert explainer.explanation_counter.get_count(QuestionType.CONTRASTIVE, WHY_NOT_INS_1) == 0


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
    explainer = build_explainer(demo_solution, using_cached_contrastive_explanations_enabled=True)
    fields_values = FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation]
    first = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    second = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert first is second


def test_an_explanation_is_recomputed_once_the_cache_is_cleared(demo_solution):
    explainer = build_explainer(demo_solution, using_cached_contrastive_explanations_enabled=True)
    fields_values = FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation]
    first = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert explainer.clear_cached_contrastive_explanations() == 1
    assert explainer.cached_contrastive_explanations == []
    second = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert first is not second
    assert first.text == second.text


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
            using_cached_contrastive_explanations_enabled=True,
            contrastive_explanation_input_directory_relative_path=inputs_directory_relative_path
        ))
        assert len(explainer.cached_contrastive_explanations) > 0
        explanation = explainer.get_contrastive_explanation(
            WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
        assert explanation in explainer.cached_contrastive_explanations
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
    with pytest.raises(ValueError, match="no neighborhood_llm_model"):
        explainer.get_free_text_explanation("Why isn't Ellen doing T2 right after leaving home?")


def test_a_free_text_question_the_catalogue_covers_is_answered(demo_solution):
    explainer = build_explainer(demo_solution, extractor_model="stub/model",
                                free_text_explanation_mode=FreeTextExplanationModes.TEMPLATED.value)
    covered_neighborhood = Mapper.map(ContrastiveQuestion(
        explainer.current_solution, WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation]))
    give_explainer_a_stub_extractor(explainer, covered_neighborhood)
    explanation = explainer.get_free_text_explanation("Why isn't Ellen doing T2 right after leaving home?")
    assert isinstance(explanation, TimeNegativeExplanation)
    assert explanation.text
    # A free-text answer is a contrastive one, so scenario and counterfactual follow-ups can build on it.
    assert explainer.last_contrastive_explanation is explanation


def test_a_free_text_explanation_keeps_the_neighborhood_it_was_found_in(demo_solution):
    """
    The CLI's developer output reads the explanation's neighborhood, so the free-text route must keep it too.
    """
    explainer = build_explainer(demo_solution, extractor_model="stub/model",
                                free_text_explanation_mode=FreeTextExplanationModes.TEMPLATED.value)
    covered_neighborhood = Mapper.map(ContrastiveQuestion(
        explainer.current_solution, WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation]))
    give_explainer_a_stub_extractor(explainer, covered_neighborhood)
    explanation = explainer.get_free_text_explanation("Why isn't Ellen doing T2 right after leaving home?")
    assert explanation.neighborhood is covered_neighborhood


def test_a_template_question_in_llm_extraction_mode_has_its_neighborhood_extracted_by_the_extractor(demo_solution):
    explainer = build_explainer(demo_solution, extractor_model="stub/model")
    explainer.configuration.neighborhood_extraction_mode = NeighborhoodExtractionModes.LLM.value
    fields_values = FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation]
    extracted_neighborhood = Mapper.map(ContrastiveQuestion(explainer.current_solution, WHY_NOT_INS_1, fields_values))
    give_explainer_a_stub_extractor(explainer, extracted_neighborhood)
    explanation = explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert explanation.neighborhood is extracted_neighborhood
    assert isinstance(explanation, TimeNegativeExplanation)


def test_a_template_question_in_tailored_extraction_mode_has_its_neighborhood_mapped(demo_solution):
    # NB: Building with a model is what switches the template computation mode to neighborhood.
    explainer = build_explainer(demo_solution, extractor_model="stub/model")
    explanation = explainer.get_contrastive_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    assert explanation.neighborhood.extraction_mode == NeighborhoodExtractionModes.TAILORED.value


def test_a_neighborhood_explanation_keeps_the_statistics_of_the_milp_solved(demo_solution):
    """The CLI's developer output reads the explanation's MILP statistics, so the neighborhood route must keep them."""
    explainer = build_explainer(demo_solution, extractor_model="stub/model")
    explanation = explainer.get_contrastive_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    assert explanation.milp_statistics.nb_objectives == 3
    assert explanation.milp_statistics.solve_time > 0


def test_a_neighborhood_explanation_settled_by_a_skill_conflict_has_no_milp_statistics(demo_solution):
    explainer = build_explainer(demo_solution, extractor_model="stub/model")
    explanation = explainer.get_contrastive_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[SkillNegativeExplanation])
    assert explanation.milp_statistics is None


def test_a_tailored_explanation_has_no_milp_statistics(demo_solution):
    explainer = build_explainer(demo_solution)
    explanation = explainer.get_contrastive_explanation(
        WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    assert explanation.milp_statistics is None


def test_a_templated_free_text_explanation_keeps_the_statistics_of_the_milp_solved(demo_solution):
    explainer = build_explainer(demo_solution, extractor_model="stub/model",
                                free_text_explanation_mode=FreeTextExplanationModes.TEMPLATED.value)
    give_explainer_a_stub_extractor(explainer, build_covered_neighborhood(explainer.current_solution))
    explanation = explainer.get_free_text_explanation("Why isn't Ellen doing T2 right after leaving home?")
    assert explanation.milp_statistics.nb_objectives == 3


def test_an_invalid_neighborhood_extraction_mode_is_refused(demo_solution):
    explainer = build_explainer(demo_solution)
    with pytest.raises(ValueError, match="Invalid neighborhood extraction mode"):
        explainer.configuration.neighborhood_extraction_mode = "magic"


def test_a_free_text_question_the_catalogue_does_not_cover_says_so(demo_solution):
    """
    A question that is understood and solved but matches no template must fail saying exactly that.
    """
    explainer = build_explainer(demo_solution, extractor_model="stub/model",
                                free_text_explanation_mode=FreeTextExplanationModes.TEMPLATED.value)
    give_explainer_a_stub_extractor(explainer, build_uncovered_neighborhood(explainer.current_solution))
    with pytest.raises(NeighborhoodError, match="matches no question template"):
        explainer.get_free_text_explanation("Why isn't Ellen doing one of those two tasks?")



###########################################
# Free-text questions - Written by an LLM #
###########################################

##############
# StubWriter #
##############

class StubWriter:
    """
    Stands in for the ExplanationWriter, wording every explanation with the same text instead of calling a model.

    Everything before the wording - extracting aside, solving and reading the facts off - is the code under test.
    """

    TEXT = "A stub explanation."

    def write(self, question: FreeTextQuestion, facts: ExplanationFacts, support_solution: Solution,
              computation_mode: Optional[str] = None,
              computation_time: Optional[float] = None) -> FreeTextExplanation:
        """Returns the explanation the real writer would, but with the stub text."""
        return FreeTextExplanation(question, support_solution, facts, self.TEXT, "stub/model",
                                   computation_mode, computation_time)


def build_written_mode_explainer(solution: Solution, neighborhood_builder,
                                 counterfactual_explanations_enabled: bool = False) -> Explainer:
    """
    Returns an explainer answering free-text questions in written mode, with a stub extractor and a stub writer.

    Args:
        solution: The solution to explain.
        neighborhood_builder: Builds, from the explainer's current solution, the neighborhood the extraction yields.
        counterfactual_explanations_enabled: Whether to allow counterfactual follow-up questions.
    """
    explainer = build_explainer(solution, extractor_model="stub/model", writer_model="stub/model",
                                counterfactual_explanations_enabled=counterfactual_explanations_enabled)
    give_explainer_a_stub_extractor(explainer, neighborhood_builder(explainer.current_solution))
    explainer._writer = StubWriter()
    return explainer


def build_covered_neighborhood(solution: Solution) -> Neighborhood:
    """Builds the neighborhood of the (Ins,1) question the demo solution answers with a time conflict."""
    return Mapper.map(ContrastiveQuestion(
        solution, WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation]))


def test_a_free_text_question_is_written_by_default(demo_solution):
    explainer = build_written_mode_explainer(demo_solution, build_covered_neighborhood)
    explanation = explainer.get_free_text_explanation("Why isn't Ellen doing T2 right after leaving home?")
    assert isinstance(explanation, FreeTextExplanation)
    assert explanation.text == StubWriter.TEXT
    assert explanation.facts.outcome is ExplanationOutcomes.TIME_INFEASIBLE
    assert explanation.is_negative()
    assert explanation.mode == "neighborhood"
    assert explanation.neighborhood is explainer._extractor._neighborhood
    assert explanation.milp_statistics.nb_objectives == 3
    assert explainer.last_contrastive_explanation is explanation


def test_a_free_text_question_outside_the_catalogue_is_written_too(demo_solution):
    """What templated mode refuses (see above) is answered once the explanation is written from the facts."""
    explainer = build_written_mode_explainer(demo_solution, build_uncovered_neighborhood)
    explanation = explainer.get_free_text_explanation("Why isn't Ellen doing one of those two tasks?")
    assert isinstance(explanation, FreeTextExplanation)
    assert explanation.facts.question == "Why isn't Ellen doing one of those two tasks?"


def test_a_written_free_text_question_needs_a_writer_model(demo_solution):
    """The missing model is reported before any LLM is called, naming the setting and the templated way out."""
    explainer = build_explainer(demo_solution, extractor_model="stub/model")
    give_explainer_a_stub_extractor(explainer, build_covered_neighborhood(explainer.current_solution))
    with pytest.raises(ValueError, match="explanation_writing_llm_model"):
        explainer.get_free_text_explanation("Why isn't Ellen doing T2 right after leaving home?")


def test_a_follow_up_of_a_written_free_text_question_is_refused(demo_solution):
    """A counterfactual follow-up needs a question template, which a written free-text answer has none of."""
    explainer = build_written_mode_explainer(demo_solution, build_covered_neighborhood,
                                             counterfactual_explanations_enabled=True)
    explainer.get_free_text_explanation("Why isn't Ellen doing T2 right after leaving home?")
    with pytest.raises(PermissionError, match="free-text"):
        explainer.compute_counterfactual_explanation()


def test_the_llm_pipeline_sets_up_its_extractor_and_writer(demo_solution, monkeypatch):
    explainer = build_explainer(demo_solution)
    prepare_calls = []
    monkeypatch.setattr(explainer, "prepare_extractor", lambda: prepare_calls.append("extractor"))
    monkeypatch.setattr(explainer, "prepare_writer", lambda: prepare_calls.append("writer"))
    explainer.set_pipeline(Pipelines.LLM.value, "stub/model")
    assert prepare_calls == ["extractor", "writer"]
    assert explainer.configuration.pipeline == Pipelines.LLM.value


def test_the_llm_pipeline_is_all_or_nothing(demo_solution, monkeypatch):
    """A writer that cannot be set up leaves every setting, models included, exactly as it was."""
    explainer = build_explainer(demo_solution)
    configuration = explainer.configuration
    settings_before = (configuration.template_computation_mode, configuration.neighborhood_extraction_mode,
                       configuration.free_text_explanation_mode, configuration.neighborhood_extraction_llm_model,
                       configuration.explanation_writing_llm_model)

    def fail_to_prepare_writer():
        raise RuntimeError("missing API key")

    monkeypatch.setattr(explainer, "prepare_extractor", lambda: None)
    monkeypatch.setattr(explainer, "prepare_writer", fail_to_prepare_writer)
    with pytest.raises(RuntimeError, match="missing API key"):
        explainer.set_pipeline(Pipelines.LLM.value, "stub/model")
    assert (configuration.template_computation_mode, configuration.neighborhood_extraction_mode,
            configuration.free_text_explanation_mode, configuration.neighborhood_extraction_llm_model,
            configuration.explanation_writing_llm_model) == settings_before


def test_the_tailored_pipeline_sets_up_no_llm_backend(demo_solution, monkeypatch):
    explainer = build_explainer(demo_solution)
    monkeypatch.setattr(explainer, "prepare_extractor", lambda: pytest.fail("No extractor is needed"))
    explainer.set_pipeline(Pipelines.TAILORED.value)
    assert explainer.configuration.pipeline == Pipelines.TAILORED.value


def test_an_invalid_free_text_explanation_mode_is_refused():
    with pytest.raises(ValueError, match="Invalid free-text explanation mode"):
        ExplainerConfiguration(free_text_explanation_mode="magic")


def test_a_free_text_explanation_is_exported_under_a_name_of_its_own(demo_solution):
    """No template id nor field values to name the file after: it is named after the question's text instead."""
    question = FreeTextQuestion(demo_solution, "Why isn't Ellen doing T2 right after leaving home?")
    file_name = define_single_free_text_explanation_json_file_name(question)
    assert file_name.startswith(f"explanation_{demo_solution.core_name}_free-text_")
    assert file_name == define_single_free_text_explanation_json_file_name(
        FreeTextQuestion(demo_solution, question.text))
    assert file_name != define_single_free_text_explanation_json_file_name(
        FreeTextQuestion(demo_solution, "Another question?"))


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
    explainer.explanation_counter.reset()
    assert explainer.explanation_counter.get_count(QuestionType.CONTRASTIVE, WHY_NOT_SWP_1) == 0


def test_a_question_built_outside_the_activated_set_is_still_counted(demo_solution):
    """
    get_explanation takes a question already built, so its template need not be an activated one.
    """
    explainer = build_explainer(demo_solution, activated_question_template_ids=[])
    question = ContrastiveQuestion(
        explainer.current_solution, WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
    assert explainer.get_explanation(question).text
    assert explainer.explanation_counter.get_count(QuestionType.CONTRASTIVE, WHY_NOT_INS_1) == 1


###################################
# Naming a saved support solution #
###################################

def test_a_contrastive_support_solution_saved_twice_is_stored_and_named_once(demo_solution):
    explainer = build_explainer(demo_solution, history_enabled=True)
    explainer.get_contrastive_explanation(WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[PositiveExplanation])
    support_solution = explainer.last_contrastive_explanation.support_solution
    assert explainer.save_last_contrastive_support_solution() is True
    saved_name, nb_solutions = support_solution.name, len(explainer.history.solutions)
    assert explainer.save_last_contrastive_support_solution() is False
    assert support_solution.name == saved_name
    assert len(explainer.history.solutions) == nb_solutions


def test_a_contrastive_support_solution_recomputed_by_asking_again_is_not_saved_again(demo_solution):
    """
    With the cache off, asking again recomputes a distinct support solution object with the same content,
    which must be recognized as already saved.
    """
    explainer = build_explainer(demo_solution, history_enabled=True)
    fields_values = FIELDS_VALUES_BY_EXPLANATION_TYPE[PositiveExplanation]
    explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    assert explainer.save_last_contrastive_support_solution() is True
    first_support_solution = explainer.last_contrastive_explanation.support_solution
    nb_solutions = len(explainer.history.solutions)
    explainer.get_contrastive_explanation(WHY_NOT_INS_1, fields_values)
    second_support_solution = explainer.last_contrastive_explanation.support_solution
    assert second_support_solution is not first_support_solution
    assert explainer.save_last_contrastive_support_solution() is False
    assert len(explainer.history.solutions) == nb_solutions
    assert explainer.find_stored_solution_with_same_content(second_support_solution) is first_support_solution


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
        explainer = build_explainer(demo_solution, using_cached_contrastive_explanations_enabled=True)
        explainer.configuration.contrastive_explanation_output_directory_relative_path = outputs_directory_relative_path
        explainer.get_contrastive_explanation(
            WHY_NOT_INS_1, FIELDS_VALUES_BY_EXPLANATION_TYPE[TimeNegativeExplanation])
        explainer.export_all_cached_contrastive_explanations()
        assert os.listdir(outputs_directory_path), "the bulk export wrote nothing into the configured directory"
    finally:
        shutil.rmtree(outputs_directory_path, ignore_errors=True)
