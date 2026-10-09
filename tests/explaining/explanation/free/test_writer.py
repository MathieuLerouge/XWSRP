# Standard library
import json
from types import SimpleNamespace

# Third-party library
import pytest
from instructor.core import InstructorRetryException

# Local libraries
from src.explaining.explanation.free.exceptions import ExplanationWritingError
from src.explaining.explanation.free.explanation import FreeTextExplanation
from src.explaining.explanation.free.prompt import SYSTEM_PROMPT, build_facts_document, build_user_prompt
from src.explaining.explanation.free.writer import ExplanationWriter
from src.explaining.explanation.free.written_explanation import WrittenExplanation
from src.explaining.question.free.question import FreeTextQuestion
from src.explaining.question.predefined.bank import WHY_NOT_INS_1, WHY_NOT_SWP_1
from src.utils.language import LANGUAGE_FRENCH_KEY
from tests.explaining.computing.helpers import get_explanation_facts

_MODEL = "ollama/qwen2.5:7b"
_GROUNDED_TEXT = (
    "Ellen cannot perform T27 just after T17 because of time constraints. By performing the tasks from T26 to T27 "
    "as early as possible, Ellen can end T27 at the earliest at 04:37PM. However, T27 must be ended by 03:00PM."
)


###########
# Helpers #
###########

####################
# _FakeCompletions #
####################

class _FakeCompletions:
    """Stands for instructor's chat.completions, validating the given answers the way instructor does."""

    def __init__(self, texts: list[str]):
        self._texts = texts
        self.calls: list[dict] = []

    def create(self, **kwargs) -> WrittenExplanation:
        """Return the first of its answers that validates, or raise as instructor does once none does."""
        self.calls.append(kwargs)
        for text in self._texts[:kwargs["max_retries"] + 1]:
            try:
                return WrittenExplanation.model_validate({"text": text}, context=kwargs["context"])
            except ValueError:
                continue
        raise InstructorRetryException(n_attempts=kwargs["max_retries"] + 1, total_usage=0)


def build_writer(*texts: str, with_json_context: bool = False) -> tuple[ExplanationWriter, _FakeCompletions]:
    """Return a writer answering with the given texts in turn, and the fake completions recording its calls."""
    completions = _FakeCompletions(list(texts))
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return ExplanationWriter(_MODEL, with_json_context=with_json_context, client=client), completions


#########
# Tests #
#########

def test_the_explanation_carries_the_written_text_and_the_verdict_of_the_facts():
    question, facts, support_solution = get_explanation_facts(WHY_NOT_INS_1, ["Ellen", "T27", "T17"])
    writer, completions = build_writer(_GROUNDED_TEXT)
    explanation = writer.write(question, facts, support_solution)
    assert isinstance(explanation, FreeTextExplanation)
    assert explanation.text == _GROUNDED_TEXT
    assert explanation.is_negative() and not explanation.is_positive()
    assert not explanation.support_solution_is_feasible
    assert explanation.conflict == facts.conflict
    assert explanation.llm_model == _MODEL
    assert completions.calls[0]["messages"][0]["content"] == SYSTEM_PROMPT


def test_the_verdict_does_not_depend_on_the_text():
    """A text claiming the opposite of the facts does not turn a positive explanation into a negative one."""
    question, facts, support_solution = get_explanation_facts(WHY_NOT_SWP_1, ["Ellen", "T27", "T17"])
    writer, _ = build_writer("Ellen cannot perform T27 in place of T17.")
    assert writer.write(question, facts, support_solution).is_positive()


def test_an_ungrounded_text_is_retried():
    question, facts, support_solution = get_explanation_facts(WHY_NOT_INS_1, ["Ellen", "T27", "T17"])
    writer, _ = build_writer("Fabian can end T27 at 04:12PM.", _GROUNDED_TEXT)
    assert writer.write(question, facts, support_solution).text == _GROUNDED_TEXT


def test_exhausting_the_retries_raises_a_writing_error():
    question, facts, support_solution = get_explanation_facts(WHY_NOT_INS_1, ["Ellen", "T27", "T17"])
    writer, _ = build_writer("Fabian can end T27 at 04:12PM.")
    with pytest.raises(ExplanationWritingError):
        writer.write(question, facts, support_solution)


def test_facts_read_off_another_question_are_refused():
    question, facts, support_solution = get_explanation_facts(WHY_NOT_INS_1, ["Ellen", "T27", "T17"])
    writer, _ = build_writer(_GROUNDED_TEXT)
    with pytest.raises(ValueError):
        writer.write(FreeTextQuestion(question.solution, "Another question?"), facts, support_solution)


def test_the_explanation_survives_a_json_round_trip():
    question, facts, support_solution = get_explanation_facts(WHY_NOT_INS_1, ["Ellen", "T27", "T17"])
    writer, _ = build_writer(_GROUNDED_TEXT)
    explanation = writer.write(question, facts, support_solution, computation_time=1.5)
    rebuilt = FreeTextExplanation.from_dict(json.loads(json.dumps(explanation.to_dict())), question.solution)
    assert rebuilt.to_dict() == explanation.to_dict()
    assert rebuilt.question.text == question.text and rebuilt.facts == facts


@pytest.mark.parametrize("with_json_context", [False, True])
def test_the_user_prompt_carries_the_facts_and_optionally_the_json_context(with_json_context):
    question, facts, _ = get_explanation_facts(WHY_NOT_INS_1, ["Ellen", "T27", "T17"])
    user_prompt = build_user_prompt(build_facts_document(facts), question.solution, with_json_context)
    assert '"earliest end time": "04:37PM"' in user_prompt
    assert ("Instance (JSON" in user_prompt) == with_json_context


def test_the_facts_document_spells_times_in_the_language_of_the_question():
    _, facts, _ = get_explanation_facts(WHY_NOT_INS_1, ["Ellen", "T27", "T17"], LANGUAGE_FRENCH_KEY)
    document = build_facts_document(facts)
    assert document["answer language"] == "French"
    assert document["conflict"]["earliest end time"] == "16h37"


def test_a_missing_api_key_fails_at_construction(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MISTRAL_API_KEY"):
        ExplanationWriter("mistral/mistral-small-latest")


@pytest.mark.parametrize("model, expected", [("ollama/qwen2.5:7b", False), ("anthropic/claude-sonnet-5", True)])
def test_the_json_context_defaults_per_provider(model, expected):
    client = SimpleNamespace(chat=SimpleNamespace(completions=_FakeCompletions([])))
    assert ExplanationWriter(model, client=client).with_json_context is expected
