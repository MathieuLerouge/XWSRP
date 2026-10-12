# Third-party library
import pytest

# Local libraries
from src.explaining.explanation.free.exceptions import ExplanationWritingError
from src.explaining.interacting.configuration import ExplainerConfiguration, FreeTextExplanationModes
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.cli.cli import ExplainerCLI
from src.explaining.interacting.interface.cli.commands import (
    ClearTargets, DisplayModes, ShowTargets, SwitchTargets
)
from src.explaining.neighborhood.neighborhood import NeighborhoodExtractionModes
from src.explaining.processes import get_demo_solution
from src.explaining.question.predefined.constants import WHY_NOT_INS_1
from src.modeling.solution import Solution
from tests.explaining.interacting.test_explainer import (
    StubWriter, build_covered_neighborhood, give_explainer_a_stub_extractor
)


@pytest.fixture(scope="module")
def demo_solution() -> Solution:
    """The demo solution every test here runs the CLI on."""
    return get_demo_solution()


def build_cli(solution: Solution, llm_model=None, writer_model=None) -> ExplainerCLI:
    """Return an ExplainerCLI over an explainer built with the given extraction and writer LLM models, if any."""
    return ExplainerCLI(solution, Explainer(solution, ExplainerConfiguration(
        neighborhood_llm_model=llm_model, explanation_writing_llm_model=writer_model
    )))


def test_llm_extraction_mode_is_refused_without_an_llm_model(demo_solution):
    cli = build_cli(demo_solution)
    result = cli.handle_neighborhood_extraction_mode([NeighborhoodExtractionModes.LLM.value])
    assert "No LLM model configured" in result
    assert cli.explainer.configuration.neighborhood_extraction_mode == NeighborhoodExtractionModes.TAILORED.value


def test_llm_extraction_mode_sets_up_the_extractor_when_an_llm_model_is_given(demo_solution, monkeypatch):
    cli = build_cli(demo_solution, llm_model="stub/model")
    prepare_calls = []
    monkeypatch.setattr(cli.explainer, "prepare_extractor", lambda: prepare_calls.append(True))
    cli.handle_neighborhood_extraction_mode([NeighborhoodExtractionModes.LLM.value])
    assert prepare_calls == [True]
    assert cli.explainer.configuration.neighborhood_extraction_mode == NeighborhoodExtractionModes.LLM.value


def test_llm_extraction_mode_is_left_unchanged_when_the_extractor_cannot_be_set_up(demo_solution, monkeypatch):
    cli = build_cli(demo_solution, llm_model="stub/model")

    def fail_to_prepare_extractor():
        raise RuntimeError("missing API key")

    monkeypatch.setattr(cli.explainer, "prepare_extractor", fail_to_prepare_extractor)
    result = cli.handle_neighborhood_extraction_mode([NeighborhoodExtractionModes.LLM.value])
    assert "missing API key" in result
    assert cli.explainer.configuration.neighborhood_extraction_mode == NeighborhoodExtractionModes.TAILORED.value


def test_an_invalid_extraction_mode_shows_the_usage(demo_solution):
    cli = build_cli(demo_solution)
    assert "Usage" in cli.handle_neighborhood_extraction_mode(["magic"])


def test_clear_without_a_known_target_shows_the_usage(demo_solution):
    cli = build_cli(demo_solution)
    assert "Usage" in cli.handle_clear([])
    assert "Usage" in cli.handle_clear(["everything"])


def test_clearing_cached_explanations_is_refused_when_the_cache_is_off(demo_solution):
    cli = build_cli(demo_solution)
    assert "disabled" in cli.handle_clear([ClearTargets.CACHED_EXPLANATIONS.value])


def test_clearing_cached_explanations_empties_the_cache(demo_solution):
    explainer = Explainer(
        demo_solution, ExplainerConfiguration(using_already_computed_contrastive_explanations_enabled=True)
    )
    cli = ExplainerCLI(demo_solution, explainer)
    cli.handle_contrastive([WHY_NOT_INS_1, "Ellen", "T2", "Start"])
    result = cli.handle_clear([ClearTargets.CACHED_EXPLANATIONS.value])
    assert "Cleared 1 cached contrastive explanation" in result
    assert explainer.already_computed_contrastive_explanations == []


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
    cli.handle_contrastive([WHY_NOT_INS_1, "Alexander", "T22", "T6"])
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
    cli.handle_contrastive([WHY_NOT_INS_1, "Ellen", "T2", "Start"])
    assert "not feasible" in cli.handle_switch([SwitchTargets.LAST_SUPPORT_SOLUTION.value])
    assert cli.explainer.current_solution is current_solution


def test_switch_to_last_support_instance(demo_solution):
    cli = build_cli_with_history(demo_solution)
    cli.handle_contrastive([WHY_NOT_INS_1, "Alexander", "T22", "T6"])
    support_instance_name = cli.explainer.last_contrastive_explanation.support_solution.instance.name
    assert "Switched to instance" in cli.handle_switch([SwitchTargets.LAST_SUPPORT_INSTANCE.value])
    assert cli.explainer.current_instance.name == support_instance_name


def test_saving_the_same_support_solution_twice_reports_it_is_already_saved(demo_solution):
    cli = build_cli_with_history(demo_solution)
    cli.handle_contrastive([WHY_NOT_INS_1, "Alexander", "T22", "T6"])
    first_result = cli.handle_save_solution([])
    nb_solutions = len(cli.explainer.history.solutions)
    second_result = cli.handle_save_solution([])
    assert first_result.startswith("Support solution saved as")
    assert second_result == first_result.replace("saved as", "already saved as")
    assert len(cli.explainer.history.solutions) == nb_solutions


def test_saving_after_asking_the_same_question_again_reports_the_first_saved_name(demo_solution):
    cli = build_cli_with_history(demo_solution)
    question = [WHY_NOT_INS_1, "Alexander", "T22", "T6"]
    cli.handle_contrastive(question)
    first_result = cli.handle_save_solution([])
    nb_solutions = len(cli.explainer.history.solutions)
    cli.handle_contrastive(question)
    assert cli.handle_save_solution([]) == first_result.replace("saved as", "already saved as")
    assert len(cli.explainer.history.solutions) == nb_solutions


def test_switching_after_asking_the_same_question_again_switches_to_the_first_saved_solution(demo_solution):
    cli = build_cli_with_history(demo_solution)
    question = [WHY_NOT_INS_1, "Alexander", "T22", "T6"]
    cli.handle_contrastive(question)
    cli.handle_switch([SwitchTargets.LAST_SUPPORT_SOLUTION.value])
    first_saved_solution = cli.explainer.current_solution
    nb_solutions = len(cli.explainer.history.solutions)
    cli.handle_contrastive(question)
    cli.handle_switch([SwitchTargets.LAST_SUPPORT_SOLUTION.value])
    assert cli.explainer.current_solution is first_saved_solution
    assert len(cli.explainer.history.solutions) == nb_solutions


###############################################
# Free-text questions - Writer and their mode #
###############################################

def test_writer_llm_model_without_a_model_shows_the_usage(demo_solution):
    cli = build_cli(demo_solution)
    assert "Usage" in cli.handle_writer_llm_model([])
    assert "Invalid model format" in cli.handle_writer_llm_model(["qwen"])


def test_writer_llm_model_sets_the_model_and_sets_up_the_writer(demo_solution, monkeypatch):
    cli = build_cli(demo_solution)
    prepare_calls = []
    monkeypatch.setattr(cli.explainer, "prepare_writer", lambda: prepare_calls.append(True))
    assert cli.handle_writer_llm_model(["stub/model"]) == "Writer LLM model set to stub/model"
    assert cli.explainer.explanation_writing_llm_model == "stub/model"
    assert prepare_calls == [True]


def test_writer_llm_model_reports_a_writer_that_cannot_be_set_up(demo_solution, monkeypatch):
    cli = build_cli(demo_solution)

    def fail_to_prepare_writer():
        raise RuntimeError("missing API key")

    monkeypatch.setattr(cli.explainer, "prepare_writer", fail_to_prepare_writer)
    result = cli.handle_writer_llm_model(["stub/model"])
    assert "could not be set up: missing API key" in result
    assert cli.explainer.explanation_writing_llm_model == "stub/model"


def test_written_free_text_explanation_mode_is_refused_without_a_writer_model(demo_solution):
    cli = build_cli(demo_solution)
    cli.explainer.configuration.free_text_explanation_mode = FreeTextExplanationModes.TEMPLATED.value
    result = cli.handle_free_text_explanation_mode([FreeTextExplanationModes.WRITTEN.value])
    assert "No writer LLM model configured" in result
    assert cli.explainer.configuration.free_text_explanation_mode == FreeTextExplanationModes.TEMPLATED.value


def test_written_free_text_explanation_mode_is_left_unchanged_when_the_writer_cannot_be_set_up(
        demo_solution, monkeypatch):
    cli = build_cli(demo_solution, writer_model="stub/model")
    cli.explainer.configuration.free_text_explanation_mode = FreeTextExplanationModes.TEMPLATED.value

    def fail_to_prepare_writer():
        raise RuntimeError("missing API key")

    monkeypatch.setattr(cli.explainer, "prepare_writer", fail_to_prepare_writer)
    result = cli.handle_free_text_explanation_mode([FreeTextExplanationModes.WRITTEN.value])
    assert "missing API key" in result
    assert cli.explainer.configuration.free_text_explanation_mode == FreeTextExplanationModes.TEMPLATED.value


def test_free_text_explanation_mode_switches_between_written_and_templated(demo_solution, monkeypatch):
    cli = build_cli(demo_solution, writer_model="stub/model")
    monkeypatch.setattr(cli.explainer, "prepare_writer", lambda: None)
    cli.handle_free_text_explanation_mode([FreeTextExplanationModes.TEMPLATED.value])
    assert cli.explainer.configuration.free_text_explanation_mode == FreeTextExplanationModes.TEMPLATED.value
    cli.handle_free_text_explanation_mode([FreeTextExplanationModes.WRITTEN.value])
    assert cli.explainer.configuration.free_text_explanation_mode == FreeTextExplanationModes.WRITTEN.value
    assert "Usage" in cli.handle_free_text_explanation_mode(["magic"])
    assert "Usage" in cli.handle_free_text_explanation_mode([])


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
    cli.handle_display_mode([DisplayModes.DEVELOPER.value])
    developer_result = cli.handle_ask(["Why", "isn't", "Ellen", "doing", "T2", "right", "after", "leaving", "home?"])
    assert "Free-text explanation mode: written" in developer_result
    assert "Writer LLM model: stub/model" in developer_result
    assert "Outcome: time infeasible" in developer_result


def test_ask_reports_an_explanation_that_could_not_be_written(demo_solution, monkeypatch):
    cli = build_cli_answering_with_stubs(demo_solution)

    def fail_to_write(*args, **kwargs):
        raise ExplanationWritingError()

    monkeypatch.setattr(cli.explainer._writer, "write", fail_to_write)
    assert cli.handle_ask(["Why", "not?"]).startswith("Error: No explanation could be worded")


def test_show_config_lists_both_llm_models_and_the_free_text_explanation_mode(demo_solution):
    result = build_cli(demo_solution, llm_model="stub/extractor", writer_model="stub/writer").handle_show(
        [ShowTargets.CONFIG.value])
    assert "Extraction LLM Model: stub/extractor" in result
    assert "Writer LLM Model: stub/writer" in result
    assert f"Free-Text Explanation Mode: {FreeTextExplanationModes.WRITTEN.value}" in result
