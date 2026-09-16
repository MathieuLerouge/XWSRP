# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.llm.extractor import Extractor
from tests.explaining.neighborhood.helpers import build_solution_with_task_performances
from tests.modeling.helpers import build_instance


def _build_solution():
    instance = build_instance()
    return build_solution_with_task_performances(instance, "solution", {"T1": ("Valentin", 480)})


def test_construction_succeeds_for_ollama_without_any_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    solution = _build_solution()
    Extractor(solution, "ollama/llama3.2")


def test_construction_raises_when_anthropic_api_key_is_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    solution = _build_solution()
    with pytest.raises(RuntimeError):
        Extractor(solution, "anthropic/claude-sonnet-5")


def test_construction_succeeds_when_anthropic_api_key_is_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")
    solution = _build_solution()
    Extractor(solution, "anthropic/claude-sonnet-5")
