# Third-party libraries
import pytest
from instructor import Mode

# Local library
from src.utils.llm import get_default_mode


@pytest.mark.parametrize("model, expected", [
    ("ollama/qwen2.5:7b", Mode.MD_JSON),
    ("anthropic/claude-sonnet-5", None),
    ("mistral/mistral-small-latest", None),
])
def test_the_default_mode_is_set_only_for_the_providers_needing_one(model, expected):
    assert get_default_mode(model) is expected
