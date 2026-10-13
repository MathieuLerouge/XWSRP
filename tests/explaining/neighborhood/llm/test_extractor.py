# Third-party libraries
import pytest
from instructor import Mode

# Local libraries
from src.explaining.neighborhood.llm.extractor import Extractor
from tests.explaining.neighborhood.helpers import build_solution_with_task_performances
from tests.modeling.helpers import build_instance


def _build_solution():
    instance = build_instance()
    return build_solution_with_task_performances(instance, "solution", {"T1": ("Valentin", 480)})


def test_construction_succeeds_for_ollama_without_any_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    solution = _build_solution()
    Extractor(solution, "ollama/llama3.2")


def test_construction_raises_when_anthropic_api_key_is_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    solution = _build_solution()
    with pytest.raises(RuntimeError):
        Extractor(solution, "anthropic/claude-sonnet-5")


def test_construction_succeeds_when_anthropic_api_key_is_set(monkeypatch):
    # NB: anthropic is an optional dependency (requirements_anthropic.in), without which construction fails
    pytest.importorskip("anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")
    solution = _build_solution()
    Extractor(solution, "anthropic/claude-sonnet-5")


def test_construction_raises_when_mistral_api_key_is_missing(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    solution = _build_solution()
    with pytest.raises(RuntimeError):
        Extractor(solution, "mistral/mistral-small-latest")


def test_construction_succeeds_when_mistral_api_key_is_set(monkeypatch):
    # NB: mistral is an optional dependency (requirements_mistral.in), without which construction fails
    pytest.importorskip("mistralai")
    monkeypatch.setenv("MISTRAL_API_KEY", "fake-key-for-test")
    solution = _build_solution()
    Extractor(solution, "mistral/mistral-small-latest")


@pytest.mark.parametrize("model, with_json_context, expected", [
    ("ollama/llama3.2", None, False),
    ("mistral/mistral-small-latest", None, True),
    ("ollama/llama3.2", True, True),
    ("mistral/mistral-small-latest", False, False),
])
def test_json_context_defaults_per_provider_unless_overridden(monkeypatch, model, with_json_context, expected):
    monkeypatch.setenv("MISTRAL_API_KEY", "fake-key-for-test")
    extractor = Extractor(_build_solution(), model, with_json_context=with_json_context)
    assert extractor._with_json_context is expected


@pytest.mark.parametrize("model, mode, expected", [
    ("ollama/llama3.2", None, Mode.MD_JSON),
    ("mistral/mistral-small-latest", None, None),
    ("ollama/llama3.2", Mode.JSON, Mode.JSON),
])
def test_the_mode_defaults_per_provider_unless_overridden(monkeypatch, model, mode, expected):
    """Ollama answers in plain text too often for instructor's TOOLS mode, so it defaults to MD_JSON."""
    monkeypatch.setenv("MISTRAL_API_KEY", "fake-key-for-test")
    modes_asked_for = []
    monkeypatch.setattr("src.explaining.neighborhood.llm.extractor.instructor.from_provider",
                        lambda model_name, mode=None: modes_asked_for.append(mode))
    Extractor(_build_solution(), model, mode=mode)
    assert modes_asked_for == [expected]
