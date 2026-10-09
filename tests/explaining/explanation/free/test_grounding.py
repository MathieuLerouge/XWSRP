# Third-party library
import pytest
from pydantic import ValidationError

# Local libraries
from src.explaining.explanation.free.grounding import find_names, find_times, find_ungrounded_mentions
from src.explaining.explanation.free.written_explanation import (
    ALLOWED_NAMES_KEY, ALLOWED_TIMES_KEY, KNOWN_NAMES_KEY, WrittenExplanation
)

_KNOWN_NAMES = {"Ellen", "Fabian", "T1", "T17", "T27"}
_CONTEXT = {ALLOWED_TIMES_KEY: {16 * 60 + 37, 15 * 60}, ALLOWED_NAMES_KEY: {"Ellen", "T17", "T27"},
            KNOWN_NAMES_KEY: _KNOWN_NAMES}


@pytest.mark.parametrize("text, expected_minutes", [
    ("at 04:37PM", {16 * 60 + 37}),
    ("at 4:37 pm", {16 * 60 + 37}),
    ("at 4:37 p.m.", {16 * 60 + 37}),
    ("at 12:00AM", {0}),
    ("à 16h37", {16 * 60 + 37}),
    ("à 16h", {16 * 60}),
    ("at 16:37", {16 * 60 + 37}),
    ("at 04:37", {4 * 60 + 37, 16 * 60 + 37}),
])
def test_a_time_is_read_whichever_way_it_is_spelled(text, expected_minutes):
    assert find_times(text) == [expected_minutes]


def test_task_names_and_durations_are_not_read_as_times():
    assert find_times("T17 lasts 40 min, and T27 97min") == []


def test_names_are_matched_as_whole_words():
    assert find_names("T17 then T1.", _KNOWN_NAMES) == {"T17", "T1"}


def test_a_text_stating_only_the_facts_is_grounded():
    text = "Ellen can end T27 at the earliest at 04:37PM, whereas it must end by 3:00 pm, after T17 (16h37)."
    assert find_ungrounded_mentions(text, _CONTEXT[ALLOWED_TIMES_KEY], _CONTEXT[ALLOWED_NAMES_KEY],
                                    _KNOWN_NAMES) == []


def test_an_invented_time_or_name_is_reported():
    text = "Fabian could end T27 at 04:12PM."
    assert find_ungrounded_mentions(text, _CONTEXT[ALLOWED_TIMES_KEY], _CONTEXT[ALLOWED_NAMES_KEY],
                                    _KNOWN_NAMES) == ["time [972] (in minutes since midnight)", "name Fabian"]


def test_the_written_explanation_rejects_an_ungrounded_text_only_when_given_a_context():
    text = "Fabian could end T27 at 04:12PM."
    assert WrittenExplanation.model_validate({"text": text}).text == text
    with pytest.raises(ValidationError, match="Fabian"):
        WrittenExplanation.model_validate({"text": text}, context=_CONTEXT)


def test_the_written_explanation_rejects_an_empty_text():
    with pytest.raises(ValidationError):
        WrittenExplanation.model_validate({"text": "  "})
