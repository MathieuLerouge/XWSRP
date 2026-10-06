# Third-party library
import pytest

# Local libraries
from src.explaining.interacting.configuration import ExplainerConfiguration
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.cli.cli import ExplainerCLI
from src.explaining.interacting.interface.cli.commands import ClearTargets
from src.explaining.neighborhood.neighborhood import NeighborhoodExtractionModes
from src.explaining.processes import get_demo_solution
from src.explaining.question.predefined.constants import WHY_NOT_INS_1
from src.modeling.solution import Solution


@pytest.fixture(scope="module")
def demo_solution() -> Solution:
    """The demo solution every test here runs the CLI on."""
    return get_demo_solution()


def build_cli(solution: Solution, llm_model=None) -> ExplainerCLI:
    """Return an ExplainerCLI over an explainer built with the given LLM model, if any."""
    return ExplainerCLI(solution, Explainer(solution, ExplainerConfiguration(neighborhood_llm_model=llm_model)))


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
