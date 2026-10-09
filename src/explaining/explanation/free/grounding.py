# Standard libraries
import re
from typing import Optional

# Times as convert_nb_minutes_to_time_string spells them in every hour format ("04:37PM", "16h37", "16:37"),
# and as an LLM may respell them ("4:37 pm", "4:37 p.m.", "16h").
_TWELVE_HOURS_TIME_PATTERN = re.compile(r"\b(\d{1,2}):(\d{2})\s*([AaPp])\.?\s*[Mm]\b\.?")
_TWENTY_FOUR_HOURS_TIME_PATTERN = re.compile(r"\b(\d{1,2})(?::(\d{2})|h(\d{2})?)(?!\d)(?!\s*[AaPp]\.?\s*[Mm]\b)")


def find_times(text: str) -> list[set[int]]:
    """
    Return the times the given text states, each as the set of minutes since midnight it may stand for.

    A 12-hour time without its AM/PM marker is ambiguous, and so stands for both of its readings.

    Args:
        text: The text to read the times off.

    Returns:
        One set of candidate minutes per time stated, in order of appearance.
    """
    times = []
    for match in _TWELVE_HOURS_TIME_PATTERN.finditer(text):
        hours, minutes = int(match.group(1)) % 12, int(match.group(2))
        if match.group(3).lower() == "p":
            hours += 12
        times.append({60 * hours + minutes})
    for match in _TWENTY_FOUR_HOURS_TIME_PATTERN.finditer(text):
        hours = int(match.group(1))
        minutes = int(match.group(2) or match.group(3) or 0)
        candidates = {60 * hours + minutes}
        if hours < 12:
            candidates.add(60 * (hours + 12) + minutes)
        times.append(candidates)
    return times


def find_names(text: str, names: set[str]) -> set[str]:
    """
    Return which of the given names the given text mentions, as whole words.

    Args:
        text: The text to look the names up in.
        names: The names to look up.

    Returns:
        The names mentioned.
    """
    return {name for name in names if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text)}


def find_ungrounded_mentions(text: str, allowed_times: set[int], allowed_names: set[str],
                             known_names: set[str], required_names: Optional[set[str]] = None) -> list[str]:
    """
    Return the times and names the given text states that the facts it was worded from do not hold,
    and the names it should state but does not.

    Args:
        text: The worded explanation.
        allowed_times: The times, in minutes since midnight, the facts hold.
        allowed_names: The employee and task names the facts hold.
        known_names: Every employee and task name of the instance, the ones to look for in text.
        required_names: The names text must state, spelled exactly as given (typically the ones the question names),
            or None if there is none.

    Returns:
        A description of each ungrounded or missing mention, empty if there is none.
    """
    ungrounded_mentions = []
    for name in sorted((required_names or set()) - find_names(text, required_names or set())):
        ungrounded_mentions.append(f"missing name {name} (to be spelled exactly so)")
    for candidates in find_times(text):
        if candidates.isdisjoint(allowed_times):
            ungrounded_mentions.append(f"time {sorted(candidates)} (in minutes since midnight)")
    for name in sorted(find_names(text, known_names) - allowed_names):
        ungrounded_mentions.append(f"name {name}")
    return ungrounded_mentions
