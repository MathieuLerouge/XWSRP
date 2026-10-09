# Standard library
import os

# Third-party library
import pytest
from instructor import Mode

# Local libraries
from src.explaining.computing.neighborhood.facts import ExplanationOutcomes
from src.explaining.explanation.free.writer import ExplanationWriter
from src.explaining.question.predefined.bank import WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_ORD_LAT_1, WHY_NOT_SWP_1
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY
from tests.explaining.computing.helpers import get_explanation_facts

# Real-model quality checks, one question per outcome, in both languages.
# Run against a free, local Ollama model by default (overridable with XWSRP_WRITER_TEST_MODEL),
# so that these tests never silently start hitting a paid provider.
# Grounding (no invented time or name) is already enforced by the writer itself, so a text coming back at all
# means it passed; what is asserted on top is that it names the conflict's employee and task.
_MODEL = os.environ.get("XWSRP_WRITER_TEST_MODEL", "ollama/qwen2.5:7b")
_MODE = Mode.MD_JSON if _MODEL.startswith("ollama/") else None

_CASES = [
    (WHY_NOT_INS_1, ["Ellen", "T27", "T17"], ExplanationOutcomes.TIME_INFEASIBLE),
    (WHY_NOT_ORD_LAT_1, ["Ellen", "T30", "T26"], ExplanationOutcomes.TIME_INFEASIBLE),
    (WHY_NOT_INS_2A, ["Fabian", "T5"], ExplanationOutcomes.SKILL_BLOCKED),
    (WHY_NOT_INS_1, ["Alexander", "T3", "T20"], ExplanationOutcomes.FEASIBLE_NON_IMPROVING),
    (WHY_NOT_SWP_1, ["Ellen", "T27", "T17"], ExplanationOutcomes.FEASIBLE_IMPROVING),
]


@pytest.fixture(scope="module")
def writer():
    return ExplanationWriter(_MODEL, mode=_MODE)


@pytest.mark.llm
@pytest.mark.parametrize("language", [LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY])
@pytest.mark.parametrize("template_id, fields_values, expected_outcome", _CASES,
                         ids=[f"{case[0]}-{case[1]}" for case in _CASES])
def test_the_written_explanation_names_who_and_what_it_is_about(writer, template_id, fields_values,
                                                                  expected_outcome, language):
    question, facts, support_solution = get_explanation_facts(template_id, fields_values, language)
    assert facts.outcome is expected_outcome
    explanation = writer.write(question, facts, support_solution)
    print(f"\n[{language}] {question.text}\n{explanation.text}")
    for name in (fields_values[0], fields_values[1]):
        assert name in explanation.text, f"{name} is not mentioned in: {explanation.text}"
