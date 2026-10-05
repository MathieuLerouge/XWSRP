# Third-party library
import pytest
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import to_plain_text

# Local libraries
from src.explaining.interacting.configuration import ExplainerConfiguration
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.cli.cli import ExplainerCLI
from src.explaining.interacting.interface.cli.commands import LLMModels
from src.explaining.interacting.interface.cli.completer import (
    PREVIEW_FIELD_STYLE, PREVIEW_STYLE, ExplainerCLICompleter
)
from src.explaining.processes import get_demo_solution
from src.explaining.question.predefined.bank import QUESTIONS_TEMPLATES
from src.explaining.question.predefined.constants import WHY_NOT_INS_1, WHY_NOT_INS_3, WHY_NOT_SWP_1
from src.modeling.solution import Solution
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY


def complete(completer: ExplainerCLICompleter, text: str) -> list[str]:
    """Return the completion texts for text, with the cursor placed at the end of it."""
    document = Document(text=text, cursor_position=len(text))
    return [completion.text for completion in completer.get_completions(document, None)]


def complete_with_meta(completer: ExplainerCLICompleter, text: str) -> dict[str, str]:
    """Return each completion text mapped to its menu meta as plain text, with the cursor at the end of text."""
    document = Document(text=text, cursor_position=len(text))
    return {
        completion.text: to_plain_text(completion.display_meta)
        for completion in completer.get_completions(document, None)
    }


def expected_question(template_id: str, fields_values: list[str]) -> str:
    """Return the template's English text, with its first fields replaced by the given values."""
    template = QUESTIONS_TEMPLATES[template_id]
    text = template.all_texts[LANGUAGE_ENGLISH_KEY]
    for field_key, value in zip(template.fields_keys, fields_values):
        text = text.replace(field_key, value, 1)
    return text


@pytest.fixture(scope="module")
def demo_solution() -> Solution:
    """The demo solution every test here completes against."""
    return get_demo_solution()


@pytest.fixture
def cli(demo_solution: Solution) -> ExplainerCLI:
    """An ExplainerCLI with history enabled, so instance/solution-name completion has data to draw from."""
    explainer = Explainer(demo_solution, ExplainerConfiguration(history_enabled=True))
    return ExplainerCLI(demo_solution, explainer)


@pytest.fixture
def completer(cli: ExplainerCLI) -> ExplainerCLICompleter:
    """The completer under test, bound to the history-enabled cli fixture."""
    return ExplainerCLICompleter(cli)


@pytest.fixture
def cli_without_history(demo_solution: Solution) -> ExplainerCLI:
    """An ExplainerCLI with history disabled, still seeded with the root instance/solution."""
    explainer = Explainer(demo_solution, ExplainerConfiguration(history_enabled=False))
    return ExplainerCLI(demo_solution, explainer)


@pytest.fixture
def completer_without_history(cli_without_history: ExplainerCLI) -> ExplainerCLICompleter:
    """The completer under test, bound to the history-disabled cli_without_history fixture."""
    return ExplainerCLICompleter(cli_without_history)


def test_empty_input_offers_all_command_names(completer: ExplainerCLICompleter):
    results = complete(completer, "")
    assert "/contrastive" in results
    assert "/help" in results
    assert "/quit" in results


def test_command_name_prefix_completion(completer: ExplainerCLICompleter):
    assert complete(completer, "/con") == ["/contrastive"]


def test_unknown_command_offers_no_argument_completions(completer: ExplainerCLICompleter):
    assert complete(completer, "/not-a-command ") == []


def test_contrastive_template_id_completion(completer: ExplainerCLICompleter):
    results = complete(completer, f"/contrastive {WHY_NOT_INS_1[:-2]}")
    assert WHY_NOT_INS_1 in results


def test_contrastive_invalid_template_id_offers_no_field_completions(completer: ExplainerCLICompleter):
    assert complete(completer, "/contrastive NOT_A_TEMPLATE ") == []


def test_contrastive_first_field_value_completion(completer: ExplainerCLICompleter):
    results = complete(completer, f"/contrastive {WHY_NOT_INS_1} ")
    assert "Ellen" in results


def test_contrastive_second_field_value_narrowed_by_first(completer: ExplainerCLICompleter):
    # (Swp,1)'s second field is a task not performed by the employee given as the first field; the demo
    # solution has Ellen performing T1, so T1 must appear for Carlotta's set but not for Ellen's.
    results_for_ellen = complete(completer, f"/contrastive {WHY_NOT_SWP_1} Ellen ")
    results_for_carlotta = complete(completer, f"/contrastive {WHY_NOT_SWP_1} Carlotta ")
    assert "T1" not in results_for_ellen
    assert "T1" in results_for_carlotta


def test_contrastive_too_many_field_values_offers_nothing(completer: ExplainerCLICompleter):
    assert complete(completer, f"/contrastive {WHY_NOT_INS_1} Ellen T2 Start extra ") == []


def test_language_enum_completion(completer: ExplainerCLICompleter):
    assert complete(completer, "/language e") == ["en"]


def test_llm_model_completion_offers_every_suggested_model(completer: ExplainerCLICompleter):
    assert complete(completer, "/llm-model ") == LLMModels.list_values()


def test_llm_model_completion_narrows_by_provider(completer: ExplainerCLICompleter):
    assert complete(completer, "/llm-model ollama/") == ["ollama/llama3.2", "ollama/qwen2.5:7b"]


def test_llm_model_second_argument_offers_nothing(completer: ExplainerCLICompleter):
    assert complete(completer, "/llm-model ollama/llama3.2 ") == []


def test_neighborhood_extraction_mode_enum_completion(completer: ExplainerCLICompleter):
    assert complete(completer, "/neighborhood-extraction-mode l") == ["llm"]


def test_show_enum_completion(completer: ExplainerCLICompleter):
    assert complete(completer, "/show sol") == ["solution"]


def test_switch_instance_completion_from_history(completer: ExplainerCLICompleter, cli: ExplainerCLI):
    results = complete(completer, "/switch-instance ")
    assert set(results) == set(cli.explainer.history.instances_names)


def test_switch_solution_completion_from_history(completer: ExplainerCLICompleter, cli: ExplainerCLI):
    results = complete(completer, "/switch-solution ")
    assert set(results) == set(cli.explainer.history.solutions_names)


def test_history_disabled_still_completes_from_the_root_instance_and_solution(
        completer_without_history: ExplainerCLICompleter, cli_without_history: ExplainerCLI
):
    # Explainer.history always returns a History seeded with the root instance/solution, even when
    # history_enabled is False - disabling it only stops further solutions from being stored into it.
    instance_results = complete(completer_without_history, "/switch-instance ")
    solution_results = complete(completer_without_history, "/switch-solution ")
    assert set(instance_results) == set(cli_without_history.explainer.history.instances_names)
    assert set(solution_results) == set(cli_without_history.explainer.history.solutions_names)


def test_contrastive_template_id_candidates_preview_their_own_question(completer: ExplainerCLICompleter):
    metas = complete_with_meta(completer, "/contrastive WN-Ins")
    assert len(metas) > 1
    for template_id, meta in metas.items():
        assert meta == expected_question(template_id, [])


def test_contrastive_value_candidate_previews_the_question_filled_with_it(completer: ExplainerCLICompleter):
    metas = complete_with_meta(completer, f"/contrastive {WHY_NOT_INS_3} El")
    assert metas["Ellen"] == expected_question(WHY_NOT_INS_3, ["Ellen"])
    assert "{Task}" in metas["Ellen"]


def test_contrastive_value_candidate_preview_keeps_the_values_already_typed(completer: ExplainerCLICompleter):
    metas = complete_with_meta(completer, f"/contrastive {WHY_NOT_INS_1} Ellen ")
    assert metas
    for task_name, meta in metas.items():
        assert meta == expected_question(WHY_NOT_INS_1, ["Ellen", task_name])
        assert meta.endswith("{Activity}?")


def test_contrastive_preview_styles_values_and_placeholders_as_fields(completer: ExplainerCLICompleter):
    text = f"/contrastive {WHY_NOT_INS_3} El"
    document = Document(text=text, cursor_position=len(text))
    ellen = next(completion for completion in completer.get_completions(document, None) if completion.text == "Ellen")
    assert [text for style, text in ellen.display_meta if style == PREVIEW_FIELD_STYLE] == ["Ellen", "{Task}"]
    assert all(style in (PREVIEW_STYLE, PREVIEW_FIELD_STYLE) for style, _ in ellen.display_meta)


def test_non_contrastive_candidates_have_no_preview(completer: ExplainerCLICompleter):
    assert complete_with_meta(completer, "/language e") == {"en": ""}


def test_contrastive_preview_follows_the_template_language(completer: ExplainerCLICompleter):
    template = QUESTIONS_TEMPLATES[WHY_NOT_INS_3]
    template.set_language(LANGUAGE_FRENCH_KEY)
    try:
        metas = complete_with_meta(completer, f"/contrastive {WHY_NOT_INS_3} El")
        assert metas["Ellen"].startswith("Pourquoi est-ce que l'employé Ellen")
    finally:
        template.set_language(LANGUAGE_ENGLISH_KEY)
