# Third-party library
import pytest

# Local libraries
from src.explaining.explanation.free.exceptions import ExplanationWritingError
from src.explaining.interacting.configuration import (
    ExplainerConfiguration, FreeTextExplanationModes, Pipelines, TemplateComputationModes
)
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.cli.cli import ExplainerCLI
from src.explaining.interacting.interface.cli.commands import (
    AskTemplateTargets, ClearTargets, DisplayModes, ListTargets, LLMModelTargets, SetTargets, ShowTargets,
    SolvingTimeLimitTargets, SwitchTargets
)
from src.explaining.neighborhood.neighborhood import NeighborhoodExtractionModes
from src.explaining.processes import get_demo_solution
from src.explaining.question.predefined.constants import WHY_NOT_INS_1, WHY_NOT_INS_2C
from src.modeling.solution import Solution
from src.utils.language import LANGUAGE_FRENCH_KEY
from tests.explaining.interacting.test_explainer import (
    StubWriter, build_covered_neighborhood, give_explainer_a_stub_extractor
)


@pytest.fixture(scope="module")
def demo_solution() -> Solution:
    """The demo solution every test here runs the CLI on."""
    return get_demo_solution()


def ask_contrastive(cli: ExplainerCLI, *args: str) -> str:
    """Return the result of /ask-template contrastive with the given arguments."""
    return cli.handle_ask_template([AskTemplateTargets.CONTRASTIVE.value, *args])


def build_cli(solution: Solution, llm_model=None, writer_model=None) -> ExplainerCLI:
    """Return an ExplainerCLI over an explainer built with the given extraction and writer LLM models, if any."""
    return ExplainerCLI(solution, Explainer(solution, ExplainerConfiguration(
        neighborhood_llm_model=llm_model, explanation_writing_llm_model=writer_model
    )))


def set_neighborhood_extraction_mode(cli: ExplainerCLI, *args: str) -> str:
    """Return the result of /set neighborhood-extraction-mode with the given arguments."""
    return cli.handle_set([SetTargets.NEIGHBORHOOD_EXTRACTION_MODE.value, *args])


def set_free_text_explanation_writing_mode(cli: ExplainerCLI, *args: str) -> str:
    """Return the result of /set free-text-explanation-writing-mode with the given arguments."""
    return cli.handle_set([SetTargets.FREE_TEXT_EXPLANATION_WRITING_MODE.value, *args])


def test_llm_neighborhood_extraction_mode_is_refused_without_an_llm_model(demo_solution):
    cli = build_cli(demo_solution)
    result = set_neighborhood_extraction_mode(cli, NeighborhoodExtractionModes.LLM.value)
    assert "No LLM model configured" in result
    assert cli.explainer.configuration.neighborhood_extraction_mode == NeighborhoodExtractionModes.TAILORED.value


def test_llm_neighborhood_extraction_mode_sets_up_the_extractor_when_an_llm_model_is_given(demo_solution, monkeypatch):
    cli = build_cli(demo_solution, llm_model="stub/model")
    prepare_calls = []
    monkeypatch.setattr(cli.explainer, "prepare_extractor", lambda: prepare_calls.append(True))
    set_neighborhood_extraction_mode(cli, NeighborhoodExtractionModes.LLM.value)
    assert prepare_calls == [True]
    assert cli.explainer.configuration.neighborhood_extraction_mode == NeighborhoodExtractionModes.LLM.value


def test_llm_neighborhood_extraction_mode_is_left_unchanged_when_the_extractor_cannot_be_set_up(
        demo_solution, monkeypatch):
    cli = build_cli(demo_solution, llm_model="stub/model")

    def fail_to_prepare_extractor():
        raise RuntimeError("missing API key")

    monkeypatch.setattr(cli.explainer, "prepare_extractor", fail_to_prepare_extractor)
    result = set_neighborhood_extraction_mode(cli, NeighborhoodExtractionModes.LLM.value)
    assert "missing API key" in result
    assert cli.explainer.configuration.neighborhood_extraction_mode == NeighborhoodExtractionModes.TAILORED.value


def test_an_invalid_neighborhood_extraction_mode_shows_the_usage(demo_solution):
    cli = build_cli(demo_solution)
    assert "Usage" in set_neighborhood_extraction_mode(cli, "magic")


def test_clear_without_a_known_target_shows_the_usage(demo_solution):
    cli = build_cli(demo_solution)
    assert "Usage" in cli.handle_clear([])
    assert "Usage" in cli.handle_clear(["everything"])


def test_clearing_cached_explanations_is_refused_when_the_cache_is_off(demo_solution):
    cli = build_cli(demo_solution)
    assert "disabled" in cli.handle_clear([ClearTargets.CACHED_EXPLANATIONS.value])


def test_clearing_cached_explanations_empties_the_cache(demo_solution):
    explainer = Explainer(
        demo_solution, ExplainerConfiguration(using_cached_contrastive_explanations_enabled=True)
    )
    cli = ExplainerCLI(demo_solution, explainer)
    ask_contrastive(cli, WHY_NOT_INS_1, "Ellen", "T2", "Start")
    result = cli.handle_clear([ClearTargets.CACHED_EXPLANATIONS.value])
    assert "Cleared 1 cached contrastive explanation" in result
    assert explainer.cached_contrastive_explanations == []


def test_show_current_solution_and_instance_need_no_name(demo_solution):
    cli = build_cli(demo_solution)
    assert cli.explainer.current_solution.name in cli.handle_show([ShowTargets.CURRENT_SOLUTION.value])
    assert cli.explainer.current_instance.name in cli.handle_show([ShowTargets.CURRENT_INSTANCE.value])


def test_show_solution_and_instance_by_name(demo_solution):
    cli = build_cli(demo_solution)
    solution_name, instance_name = cli.explainer.current_solution.name, cli.explainer.current_instance.name
    assert f"Solution: {solution_name}" in cli.handle_show([ShowTargets.SOLUTION.value, solution_name])
    assert f"Instance: {instance_name}" in cli.handle_show([ShowTargets.INSTANCE.value, instance_name])


def test_show_solution_and_instance_report_an_unknown_or_missing_name(demo_solution):
    cli = build_cli(demo_solution)
    assert "not found" in cli.handle_show([ShowTargets.SOLUTION.value, "nope"])
    assert "not found" in cli.handle_show([ShowTargets.INSTANCE.value, "nope"])
    assert "Usage" in cli.handle_show([ShowTargets.SOLUTION.value])
    assert "Usage" in cli.handle_show([ShowTargets.INSTANCE.value])


def build_cli_with_history(solution: Solution) -> ExplainerCLI:
    """Return an ExplainerCLI over a history-enabled explainer, so support solutions can be saved and switched to."""
    return ExplainerCLI(solution, Explainer(solution, ExplainerConfiguration(history_enabled=True)))


def test_switch_solution_and_instance_by_name(demo_solution):
    cli = build_cli(demo_solution)
    solution_name, instance_name = cli.explainer.current_solution.name, cli.explainer.current_instance.name
    assert "Switched to solution" in cli.handle_switch([SwitchTargets.SOLUTION.value, solution_name])
    assert "Switched to instance" in cli.handle_switch([SwitchTargets.INSTANCE.value, instance_name])


def test_switch_reports_an_unknown_or_missing_name_or_target(demo_solution):
    cli = build_cli(demo_solution)
    assert "not found" in cli.handle_switch([SwitchTargets.SOLUTION.value, "nope"])
    assert "not found" in cli.handle_switch([SwitchTargets.INSTANCE.value, "nope"])
    assert "Usage" in cli.handle_switch([SwitchTargets.SOLUTION.value])
    assert "Usage" in cli.handle_switch([SwitchTargets.INSTANCE.value])
    assert "Usage" in cli.handle_switch([])
    assert "Unknown target" in cli.handle_switch(["elsewhere"])


def test_switch_to_last_support_needs_a_question_first(demo_solution):
    cli = build_cli(demo_solution)
    assert "Ask a question first" in cli.handle_switch([SwitchTargets.LAST_SUPPORT_SOLUTION.value])
    assert "Ask a question first" in cli.handle_switch([SwitchTargets.LAST_SUPPORT_INSTANCE.value])


def test_switch_to_last_support_solution_saves_it_once_and_makes_it_current(demo_solution):
    cli = build_cli_with_history(demo_solution)
    # A positive explanation's support solution is feasible, so it can be saved.
    ask_contrastive(cli, WHY_NOT_INS_1, "Alexander", "T22", "T6")
    support_solution = cli.explainer.last_contrastive_explanation.support_solution
    nb_solutions_before = len(cli.explainer.history.solutions)
    assert "saved to history" in cli.handle_switch([SwitchTargets.LAST_SUPPORT_SOLUTION.value])
    assert cli.explainer.current_solution is support_solution
    assert len(cli.explainer.history.solutions) == nb_solutions_before + 1
    assert "saved to history" not in cli.handle_switch([SwitchTargets.LAST_SUPPORT_SOLUTION.value])
    assert len(cli.explainer.history.solutions) == nb_solutions_before + 1


def test_switch_to_an_infeasible_last_support_solution_is_refused(demo_solution):
    cli = build_cli_with_history(demo_solution)
    current_solution = cli.explainer.current_solution
    # A negative explanation's support solution is infeasible, so it cannot be saved.
    ask_contrastive(cli, WHY_NOT_INS_1, "Ellen", "T2", "Start")
    assert "not feasible" in cli.handle_switch([SwitchTargets.LAST_SUPPORT_SOLUTION.value])
    assert cli.explainer.current_solution is current_solution


def test_switch_to_last_support_instance(demo_solution):
    cli = build_cli_with_history(demo_solution)
    ask_contrastive(cli, WHY_NOT_INS_1, "Alexander", "T22", "T6")
    support_instance_name = cli.explainer.last_contrastive_explanation.support_solution.instance.name
    assert "Switched to instance" in cli.handle_switch([SwitchTargets.LAST_SUPPORT_INSTANCE.value])
    assert cli.explainer.current_instance.name == support_instance_name


def test_saving_the_same_support_solution_twice_reports_it_is_already_saved(demo_solution):
    cli = build_cli_with_history(demo_solution)
    ask_contrastive(cli, WHY_NOT_INS_1, "Alexander", "T22", "T6")
    first_result = cli.handle_save_solution([])
    nb_solutions = len(cli.explainer.history.solutions)
    second_result = cli.handle_save_solution([])
    assert first_result.startswith("Support solution saved as")
    assert second_result == first_result.replace("saved as", "already saved as")
    assert len(cli.explainer.history.solutions) == nb_solutions


def test_saving_after_asking_the_same_question_again_reports_the_first_saved_name(demo_solution):
    cli = build_cli_with_history(demo_solution)
    question = [WHY_NOT_INS_1, "Alexander", "T22", "T6"]
    ask_contrastive(cli, *question)
    first_result = cli.handle_save_solution([])
    nb_solutions = len(cli.explainer.history.solutions)
    ask_contrastive(cli, *question)
    assert cli.handle_save_solution([]) == first_result.replace("saved as", "already saved as")
    assert len(cli.explainer.history.solutions) == nb_solutions


def test_switching_after_asking_the_same_question_again_switches_to_the_first_saved_solution(demo_solution):
    cli = build_cli_with_history(demo_solution)
    question = [WHY_NOT_INS_1, "Alexander", "T22", "T6"]
    ask_contrastive(cli, *question)
    cli.handle_switch([SwitchTargets.LAST_SUPPORT_SOLUTION.value])
    first_saved_solution = cli.explainer.current_solution
    nb_solutions = len(cli.explainer.history.solutions)
    ask_contrastive(cli, *question)
    cli.handle_switch([SwitchTargets.LAST_SUPPORT_SOLUTION.value])
    assert cli.explainer.current_solution is first_saved_solution
    assert len(cli.explainer.history.solutions) == nb_solutions


###############################################
# Free-text questions - Writer and their mode #
###############################################

def set_explanation_writing_llm_model(cli: ExplainerCLI, *args: str) -> str:
    """Return the result of /set llm-model explanation-writing with the given arguments."""
    return cli.handle_set([SetTargets.LLM_MODEL.value, LLMModelTargets.EXPLANATION_WRITING.value, *args])


def test_set_explanation_writing_llm_model_without_a_model_shows_the_usage(demo_solution):
    cli = build_cli(demo_solution)
    assert "Usage" in set_explanation_writing_llm_model(cli)
    assert "Invalid model format" in set_explanation_writing_llm_model(cli, "qwen")


def test_set_explanation_writing_llm_model_sets_the_model_and_sets_up_the_writer(demo_solution, monkeypatch):
    cli = build_cli(demo_solution)
    prepare_calls = []
    monkeypatch.setattr(cli.explainer, "prepare_writer", lambda: prepare_calls.append(True))
    assert set_explanation_writing_llm_model(cli, "stub/model") == "Explanation writing LLM model set to stub/model"
    assert cli.explainer.explanation_writing_llm_model == "stub/model"
    assert prepare_calls == [True]


def test_set_explanation_writing_llm_model_reports_a_writer_that_cannot_be_set_up(demo_solution, monkeypatch):
    cli = build_cli(demo_solution)

    def fail_to_prepare_writer():
        raise RuntimeError("missing API key")

    monkeypatch.setattr(cli.explainer, "prepare_writer", fail_to_prepare_writer)
    result = set_explanation_writing_llm_model(cli, "stub/model")
    assert "could not be set up: missing API key" in result
    assert cli.explainer.explanation_writing_llm_model == "stub/model"


def test_written_free_text_explanation_writing_mode_is_refused_without_a_writer_model(demo_solution):
    cli = build_cli(demo_solution)
    cli.explainer.configuration.free_text_explanation_mode = FreeTextExplanationModes.TEMPLATED.value
    result = set_free_text_explanation_writing_mode(cli, FreeTextExplanationModes.WRITTEN.value)
    assert "No writer LLM model configured" in result
    assert cli.explainer.configuration.free_text_explanation_mode == FreeTextExplanationModes.TEMPLATED.value


def test_written_free_text_explanation_writing_mode_is_left_unchanged_when_the_writer_cannot_be_set_up(
        demo_solution, monkeypatch):
    cli = build_cli(demo_solution, writer_model="stub/model")
    cli.explainer.configuration.free_text_explanation_mode = FreeTextExplanationModes.TEMPLATED.value

    def fail_to_prepare_writer():
        raise RuntimeError("missing API key")

    monkeypatch.setattr(cli.explainer, "prepare_writer", fail_to_prepare_writer)
    result = set_free_text_explanation_writing_mode(cli, FreeTextExplanationModes.WRITTEN.value)
    assert "missing API key" in result
    assert cli.explainer.configuration.free_text_explanation_mode == FreeTextExplanationModes.TEMPLATED.value


def test_free_text_explanation_writing_mode_switches_between_written_and_templated(demo_solution, monkeypatch):
    cli = build_cli(demo_solution, writer_model="stub/model")
    monkeypatch.setattr(cli.explainer, "prepare_writer", lambda: None)
    set_free_text_explanation_writing_mode(cli, FreeTextExplanationModes.TEMPLATED.value)
    assert cli.explainer.configuration.free_text_explanation_mode == FreeTextExplanationModes.TEMPLATED.value
    set_free_text_explanation_writing_mode(cli, FreeTextExplanationModes.WRITTEN.value)
    assert cli.explainer.configuration.free_text_explanation_mode == FreeTextExplanationModes.WRITTEN.value
    assert "Usage" in set_free_text_explanation_writing_mode(cli, "magic")
    assert "Usage" in set_free_text_explanation_writing_mode(cli)


def test_ask_in_written_mode_needs_a_writer_model(demo_solution):
    """Said up front, with both ways out, rather than surfacing the Explainer's own ValueError."""
    cli = build_cli(demo_solution, llm_model="stub/model")
    result = cli.handle_ask(["Why", "not?"])
    assert "No writer LLM model configured" in result
    assert FreeTextExplanationModes.TEMPLATED.value in result


def build_cli_answering_with_stubs(solution: Solution) -> ExplainerCLI:
    """Return an ExplainerCLI whose explainer extracts and writes with stubs, in written free-text mode."""
    cli = build_cli(solution, llm_model="stub/model", writer_model="stub/model")
    give_explainer_a_stub_extractor(cli.explainer, build_covered_neighborhood(cli.explainer.current_solution))
    cli.explainer._writer = StubWriter()
    return cli


def test_ask_in_written_mode_shows_the_written_explanation(demo_solution):
    cli = build_cli_answering_with_stubs(demo_solution)
    result = cli.handle_ask(["Why", "isn't", "Ellen", "doing", "T2", "right", "after", "leaving", "home?"])
    assert StubWriter.TEXT in result
    assert "Outcome" not in result, "The facts' outcome is developer output only"
    cli.handle_set([SetTargets.DISPLAY_MODE.value, DisplayModes.DEVELOPER.value])
    developer_result = cli.handle_ask(["Why", "isn't", "Ellen", "doing", "T2", "right", "after", "leaving", "home?"])
    assert "Free-text explanation writing mode: written" in developer_result
    assert "Explanation writing LLM model: stub/model" in developer_result
    assert "Outcome: time infeasible" in developer_result


def test_developer_mode_shows_the_statistics_of_the_milp_solved(demo_solution):
    # NB: Building with an LLM model is what switches the template computation mode to neighborhood.
    cli = build_cli(demo_solution, llm_model="stub/model")
    assert "MILP" not in ask_contrastive(cli, WHY_NOT_INS_1, "Ellen", "T2", "Start"), "Developer output only"
    cli.handle_set([SetTargets.DISPLAY_MODE.value, DisplayModes.DEVELOPER.value])
    result = ask_contrastive(cli, WHY_NOT_INS_1, "Ellen", "T2", "Start")
    assert "MILP variables:" in result
    assert "MILP constraints:" in result
    assert "  NeighborhoodSameAssigneeConstraint: " in result
    assert "MILP objectives: 3" in result
    assert "MILP build time:" in result
    assert "MILP solve time:" in result


def test_developer_mode_says_no_milp_was_solved_when_a_skill_conflict_settles_the_question(demo_solution):
    cli = build_cli(demo_solution, llm_model="stub/model")
    cli.handle_set([SetTargets.DISPLAY_MODE.value, DisplayModes.DEVELOPER.value])
    assert "MILP: none solved" in ask_contrastive(cli, WHY_NOT_INS_1, "Ellen", "T6", "Start")


def test_ask_reports_an_explanation_that_could_not_be_written(demo_solution, monkeypatch):
    cli = build_cli_answering_with_stubs(demo_solution)

    def fail_to_write(*args, **kwargs):
        raise ExplanationWritingError()

    monkeypatch.setattr(cli.explainer._writer, "write", fail_to_write)
    assert cli.handle_ask(["Why", "not?"]).startswith("Error: No explanation could be worded")


def test_show_config_lists_both_llm_models_and_the_free_text_explanation_mode(demo_solution):
    result = build_cli(demo_solution, llm_model="stub/extractor", writer_model="stub/writer").handle_show(
        [ShowTargets.CONFIG.value])
    assert "Neighborhood Extraction LLM Model: stub/extractor" in result
    assert "Explanation Writing LLM Model: stub/writer" in result
    assert f"Free-Text Explanation Writing Mode: {FreeTextExplanationModes.WRITTEN.value}" in result


#######
# Set #
#######

def test_set_without_a_known_target_shows_the_usage(demo_solution):
    cli = build_cli(demo_solution)
    assert "Usage" in cli.handle_set([])
    assert "Unknown target" in cli.handle_set(["everything"])
    assert "Unknown target" in cli.handle_set([SetTargets.LLM_MODEL.value, "everything", "stub/model"])
    assert "Unknown target" in cli.handle_set([SetTargets.SOLVING_TIME_LIMIT.value, "everything", "30"])


def test_set_language(demo_solution):
    cli = build_cli(demo_solution)
    assert cli.handle_set([SetTargets.LANGUAGE.value, "fr"]) == f"Language set to {LANGUAGE_FRENCH_KEY}"
    assert cli.explainer.language == LANGUAGE_FRENCH_KEY
    cli.handle_set([SetTargets.LANGUAGE.value, "en"])
    assert "Usage" in cli.handle_set([SetTargets.LANGUAGE.value, "de"])


def test_set_solving_time_limit(demo_solution):
    cli = build_cli(demo_solution)
    configuration = cli.explainer.configuration
    cli.handle_set([SetTargets.SOLVING_TIME_LIMIT.value, SolvingTimeLimitTargets.CONTRASTIVE.value, "30"])
    assert configuration.time_limit_for_contrastive_explanation_milp_computation == 30
    cli.handle_set([SetTargets.SOLVING_TIME_LIMIT.value, SolvingTimeLimitTargets.COUNTERFACTUAL.value, "60"])
    assert configuration.time_limit_for_counterfactual_explanation_milp_computation == 60
    assert "non-negative" in cli.handle_set(
        [SetTargets.SOLVING_TIME_LIMIT.value, SolvingTimeLimitTargets.CONTRASTIVE.value, "-1"])
    assert "must be an integer" in cli.handle_set(
        [SetTargets.SOLVING_TIME_LIMIT.value, SolvingTimeLimitTargets.CONTRASTIVE.value, "soon"])
    assert "Usage" in cli.handle_set([SetTargets.SOLVING_TIME_LIMIT.value, SolvingTimeLimitTargets.CONTRASTIVE.value])
    assert configuration.time_limit_for_contrastive_explanation_milp_computation == 30


def test_set_display_mode(demo_solution):
    cli = build_cli(demo_solution)
    assert cli.handle_set([SetTargets.DISPLAY_MODE.value, DisplayModes.DEVELOPER.value]) == \
        "Display mode set to developer"
    assert "Usage" in cli.handle_set([SetTargets.DISPLAY_MODE.value, "magic"])
    assert "Usage" in cli.handle_set([SetTargets.DISPLAY_MODE.value])


def test_set_template_computation_mode(demo_solution):
    cli = build_cli(demo_solution)
    cli.handle_set([SetTargets.TEMPLATE_COMPUTATION_MODE.value, TemplateComputationModes.NEIGHBORHOOD.value])
    assert cli.explainer.configuration.template_computation_mode == TemplateComputationModes.NEIGHBORHOOD.value
    assert "Usage" in cli.handle_set([SetTargets.TEMPLATE_COMPUTATION_MODE.value, "magic"])
    assert "Usage" in cli.handle_set([SetTargets.TEMPLATE_COMPUTATION_MODE.value])


def test_neighborhood_extraction_mode_points_at_the_template_computation_mode_when_it_does_not_apply(
        demo_solution, monkeypatch):
    """Building with an LLM model switches to neighborhood computation, so it is switched back to tailored first."""
    cli = build_cli(demo_solution, llm_model="stub/model")
    cli.explainer.configuration.template_computation_mode = TemplateComputationModes.TAILORED.value
    monkeypatch.setattr(cli.explainer, "prepare_extractor", lambda: None)
    result = set_neighborhood_extraction_mode(cli, NeighborhoodExtractionModes.LLM.value)
    assert "/set template-computation-mode" in result


def test_ask_hint_names_the_set_free_text_explanation_writing_mode_command(demo_solution):
    cli = build_cli(demo_solution, llm_model="stub/model")
    result = cli.handle_ask(["Why", "not?"])
    assert "/set free-text-explanation-writing-mode" in result
    assert result.endswith(f" {FreeTextExplanationModes.TEMPLATED.value}.")


def test_set_neighborhood_extraction_llm_model(demo_solution):
    cli = build_cli(demo_solution)
    result = cli.handle_set(
        [SetTargets.LLM_MODEL.value, LLMModelTargets.NEIGHBORHOOD_EXTRACTION.value, "stub/model"])
    assert result == "Neighborhood extraction LLM model set to stub/model"
    assert cli.explainer.neighborhood_extraction_llm_model == "stub/model"


def test_hints_name_the_set_llm_model_command(demo_solution):
    cli = build_cli(demo_solution)
    assert "/set llm-model neighborhood-extraction" in cli.handle_ask(["Why", "not?"])
    cli = build_cli(demo_solution, llm_model="stub/model")
    assert "/set llm-model explanation-writing" in cli.handle_ask(["Why", "not?"])


########
# List #
########

def test_list_each_target(demo_solution):
    cli = build_cli(demo_solution)
    assert "Available templates:" in cli.handle_list([ListTargets.TEMPLATE_QUESTIONS.value])
    assert cli.explainer.current_instance.name in cli.handle_list([ListTargets.INSTANCES.value])
    assert cli.explainer.current_solution.name in cli.handle_list([ListTargets.SOLUTIONS.value])


def test_list_without_a_known_target_shows_the_usage(demo_solution):
    cli = build_cli(demo_solution)
    assert "Usage" in cli.handle_list([])
    assert "Unknown target" in cli.handle_list(["everything"])


def test_unknown_names_point_at_the_list_command(demo_solution):
    cli = build_cli(demo_solution)
    assert "/list solutions" in cli.handle_switch([SwitchTargets.SOLUTION.value, "nope"])
    assert "/list instances" in cli.handle_switch([SwitchTargets.INSTANCE.value, "nope"])
    assert "/list template-questions" in ask_contrastive(cli, "nope")


############
# Pipeline #
############

def set_pipeline(cli: ExplainerCLI, *args: str) -> str:
    """Return the result of /set pipeline with the given arguments."""
    return cli.handle_set([SetTargets.PIPELINE.value, *args])


def test_set_pipeline_tailored(demo_solution):
    cli = build_cli(demo_solution, llm_model="stub/model")
    result = set_pipeline(cli, Pipelines.TAILORED.value)
    assert result.startswith("Pipeline set to tailored:")
    assert "LLM model" not in result
    assert cli.explainer.configuration.pipeline == Pipelines.TAILORED.value


def test_set_pipeline_llm_with_one_model_for_both(demo_solution, monkeypatch):
    cli = build_cli(demo_solution)
    monkeypatch.setattr(cli.explainer, "prepare_extractor", lambda: None)
    monkeypatch.setattr(cli.explainer, "prepare_writer", lambda: None)
    result = set_pipeline(cli, Pipelines.LLM.value, "stub/model")
    assert "Neighborhood extraction LLM model: stub/model" in result
    assert "Explanation writing LLM model: stub/model" in result
    assert cli.explainer.configuration.pipeline == Pipelines.LLM.value


def test_set_pipeline_llm_without_any_model_is_refused(demo_solution):
    cli = build_cli(demo_solution)
    assert set_pipeline(cli, Pipelines.LLM.value).startswith("Error:")
    assert cli.explainer.configuration.pipeline is None


def test_set_pipeline_llm_reports_a_backend_that_cannot_be_set_up_and_changes_nothing(demo_solution, monkeypatch):
    cli = build_cli(demo_solution)

    def fail_to_prepare_extractor():
        raise RuntimeError("missing API key")

    monkeypatch.setattr(cli.explainer, "prepare_extractor", fail_to_prepare_extractor)
    assert set_pipeline(cli, Pipelines.LLM.value, "stub/model") == "Error: missing API key"
    assert cli.explainer.neighborhood_extraction_llm_model is None
    assert cli.explainer.configuration.pipeline is None


def test_set_pipeline_shows_the_usage_or_refuses_a_bad_model(demo_solution):
    cli = build_cli(demo_solution)
    assert "Usage" in set_pipeline(cli)
    assert "Usage" in set_pipeline(cli, "magic")
    assert "Invalid model format" in set_pipeline(cli, Pipelines.LLM.value, "qwen")


def test_show_config_names_the_pipeline(demo_solution):
    cli = build_cli(demo_solution)
    assert "Pipeline: custom" in cli.handle_show([ShowTargets.CONFIG.value])
    set_pipeline(cli, Pipelines.TAILORED.value)
    assert "Pipeline: tailored" in cli.handle_show([ShowTargets.CONFIG.value])


################
# Ask template #
################

def build_cli_with_follow_ups(solution: Solution) -> ExplainerCLI:
    """Return an ExplainerCLI whose explainer allows scenario and counterfactual follow-up questions."""
    return ExplainerCLI(solution, Explainer(solution, ExplainerConfiguration(
        scenario_explanations_enabled=True, counterfactual_explanations_enabled=True
    )))


def test_ask_template_usage_lists_only_the_activated_kinds(demo_solution):
    assert build_cli(demo_solution).handle_ask_template([]).endswith("where kind is: contrastive")
    assert build_cli_with_follow_ups(demo_solution).handle_ask_template([]).endswith(
        "where kind is: contrastive, scenario, counterfactual")
    assert "Unknown target" in build_cli(demo_solution).handle_ask_template(["everything"])


def test_help_lists_only_the_activated_kinds(demo_solution):
    assert "Ask a template-based question (contrastive)" in build_cli(demo_solution).handle_help([])
    assert "(contrastive, scenario, counterfactual)" in build_cli_with_follow_ups(demo_solution).handle_help([])


def test_a_kind_of_question_not_activated_points_at_enable(demo_solution):
    result = build_cli(demo_solution).handle_ask_template([AskTemplateTargets.COUNTERFACTUAL.value])
    assert result.startswith("Counterfactual questions are not activated.")
    assert "/enable counterfactual" in result


def test_scenario_questions_cannot_be_asked_from_the_cli_yet(demo_solution):
    result = build_cli_with_follow_ups(demo_solution).handle_ask_template([AskTemplateTargets.SCENARIO.value])
    assert result == "Scenario questions cannot be asked from the CLI yet."


def test_a_counterfactual_question_needs_a_contrastive_one_first(demo_solution):
    result = build_cli_with_follow_ups(demo_solution).handle_ask_template([AskTemplateTargets.COUNTERFACTUAL.value])
    assert result.startswith("Error:")


def test_a_counterfactual_question_turns_the_last_contrastive_one_around(demo_solution):
    cli = build_cli_with_follow_ups(demo_solution)
    ask_contrastive(cli, WHY_NOT_INS_1, "Ellen", "T2", "Start")
    result = cli.handle_ask_template([AskTemplateTargets.COUNTERFACTUAL.value])
    assert result.startswith("Question:")
    assert cli.explainer.last_counterfactual_explanation is not None


def test_a_counterfactual_question_refuses_a_template_that_cannot_be_turned_around(demo_solution):
    cli = build_cli_with_follow_ups(demo_solution)
    assert "Unknown template ID" in cli.handle_ask_template(
        [AskTemplateTargets.COUNTERFACTUAL.value, WHY_NOT_INS_2C, "T27"])
    assert "requires 3 values" in cli.handle_ask_template(
        [AskTemplateTargets.COUNTERFACTUAL.value, WHY_NOT_INS_1, "Ellen"])
