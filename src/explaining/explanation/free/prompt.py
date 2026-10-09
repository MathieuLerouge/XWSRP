# Standard library
import json
from typing import Any, Optional

# Local libraries
from src.explaining.computing.neighborhood.facts import (
    HOME, ConflictFacts, ExplanationFacts, ExplanationOutcomes, KPIFacts, RouteFacts, SkillConflictFacts,
    TimeConflictFacts, UnattributedTimeConflictFacts
)
from src.modeling.solution import Solution
from src.utils.language import check_if_language_is_english, check_if_language_is_french
from src.utils.time import convert_nb_minutes_to_time_string, get_hour_format_associated_with_language

SYSTEM_PROMPT = """
You explain, to the planner of a workforce scheduling and routing solution, the answer to a question they asked
about it. Employees leave home, perform tasks in a given order within each task's time window, and come back home
within their own availability. Every task requires a skill level that its employee must reach.

The answer has already been worked out by an optimization engine, and is given to you as a set of FACTS (JSON).
Your only job is to word it. You must return a WrittenExplanation.

RULES
- State only what the FACTS say. Never compute, estimate or round a time, a duration or any other number yourself:
  every time and number you write must appear in the FACTS, spelled the same way, and be used in the role its key
  gives it (an "earliest end time" is never a deadline, a "latest start time" is never an end time).
- Write every employee and task name exactly as the FACTS spell it, even in another language: never translate,
  respell or abbreviate a name. Name only employees and tasks the FACTS name. "home" is the employee's home.
- Keep the roles the question gives to the tasks and employees it names: if it asks why T2 is not done rather than
  T1, do not answer about T1 rather than T2.
- The verdict is given ("verdict" and "outcome"): never contradict it, never hedge on it.
- Write in the language given by "answer language", whatever the language of the question.
- Plain text only: no markdown, no bullet points, no headings. Between 3 and 6 sentences.
- Never mention the engine, the solver, a model, a "neighborhood", "facts", "JSON", slacks or any other technical term:
  talk about employees, tasks, routes, times and durations.
- Call the solution the question is about "the current solution", and the one found to answer it "the new solution".

STRUCTURE
1. Answer the question directly, in one sentence that echoes it.
2. Describe the new solution: what changes with respect to the current one (see "route changes").
3. Give the reason, following the guidance for the outcome below.
4. Conclude in one sentence.

GUIDANCE PER OUTCOME
- "feasible improving": what the question asks about is possible, and the new solution is better than the current
  one, which is therefore not optimal. Use "KPIs comparison": a longer total working duration is better, and only
  when it is equal in both solutions does a shorter total traveling duration make a solution better.
- "feasible non improving": what the question asks about is possible, but the new solution is not better than the
  current one. Use "KPIs comparison" as above, to show why it is not better.
- "skill blocked": the employee's skill level is below the level the task requires, so the employee can never
  perform it. Give both levels.
- "time infeasible": the new solution does not respect the time constraints. Explain the conflict at the task,
  from its "conflicting side" only:
  - "the route before the task": by performing the activities from the "upstream binding activity" up to the task
    as early as possible, the employee can end the task at the earliest at "earliest end time", whereas the task
    must be ended by "task time window end";
  - "the route after the task": the employee can start the task at the earliest at "earliest start time", whereas
    it must be started at the latest at "latest start time", so that the employee can then end the "downstream
    binding activity" by "downstream binding time" (or, when it is home, be back home by "downstream binding time").
- "infeasible unattributed": the new solution does not respect the time constraints, the task missing its time
  constraints by "feasibility shortfall"; state it without inventing a more detailed cause.

EXAMPLE (the names, times and values below are illustrative, not the ones of the actual question)
FACTS: outcome "time infeasible", task T5 inserted just after T2 in Alice's route, conflicting side "the route
before the task", upstream binding activity T1, earliest end time 05:10PM, task time window end 04:30PM.
-> "Alice cannot perform T5 just after T2 because of time constraints. Consider the new solution obtained by
   inserting T5 just after T2 in Alice's route. By performing the tasks from T1 to T5 as early as possible, Alice
   can end T5 at the earliest at 05:10PM. However, T5 must be ended by 04:30PM. Thus, Alice performing T5 just after
   T2 is impossible."
""".strip()

_OUTCOME_VERDICTS = {
    ExplanationOutcomes.SKILL_BLOCKED: "negative: what the question asks about is impossible",
    ExplanationOutcomes.TIME_INFEASIBLE: "negative: what the question asks about is impossible",
    ExplanationOutcomes.INFEASIBLE_UNATTRIBUTED: "negative: what the question asks about is impossible",
    ExplanationOutcomes.FEASIBLE_IMPROVING: "positive: what the question asks about is possible, and better",
    ExplanationOutcomes.FEASIBLE_NON_IMPROVING: "negative: what the question asks about is possible, but not better",
}


def _get_language_name(language: str) -> str:
    """
    Return the English name of the language of the given key, as the LLM is told to answer in.

    Raises:
        NotImplementedError: if the language has no name here.
    """
    if check_if_language_is_english(language):
        return "English"
    if check_if_language_is_french(language):
        return "French"
    raise NotImplementedError(f"Non-supported language {language}")


def _format_time(nb_minutes: Optional[int], hour_format: str) -> Optional[str]:
    """Return the given time spelled in the given hour format, or None if there is no time."""
    return convert_nb_minutes_to_time_string(nb_minutes, hour_format) if nb_minutes is not None else None


def _format_duration(nb_minutes: int) -> str:
    """Return the given duration spelled in minutes."""
    return f"{nb_minutes} min"


def _describe_route(route: RouteFacts) -> list[str]:
    """
    Return the given route as the order of its activities, home included at both ends.

    Its times are left out on purpose: the reason an explanation gives is in the conflict and the KPIs,
    and a small LLM handed every time of every route tends to pick the wrong ones.
    """
    return [HOME, *route.activities, HOME]


def _describe_conflict(conflict: ConflictFacts, hour_format: str) -> dict[str, Any]:
    """
    Return the given conflict's facts, with its times and durations spelled out.

    A time conflict is told from one side only, the one TimeNegativeExplanation tells it from:
    the route before the task when that side alone already rules the task out, the route after it otherwise.
    Leaving the other side's values out keeps an LLM from building the reason on them.
    """
    description: dict[str, Any] = {"employee": conflict.employee, "task": conflict.task}
    if isinstance(conflict, SkillConflictFacts):
        description.update({"employee skill level": conflict.employee_skill_level,
                            "task required skill level": conflict.task_skill_level})
    elif isinstance(conflict, TimeConflictFacts):
        description.update({
            "task duration": _format_duration(conflict.task_duration),
            "task time window start": _format_time(conflict.task_time_window_start, hour_format),
            "task time window end": _format_time(conflict.task_time_window_end, hour_format),
            "activity before the task": conflict.activity_before,
            "activity after the task": conflict.activity_after,
        })
        if not conflict.is_upstream_feasible:
            description.update({
                "conflicting side": "the route before the task",
                "upstream binding activity": conflict.upstream_binding_activity,
                "earliest end time": _format_time(conflict.earliest_end_time, hour_format),
            })
        else:
            description.update({
                "conflicting side": "the route after the task",
                "earliest start time": _format_time(conflict.earliest_start_time, hour_format),
                "latest start time": _format_time(conflict.latest_start_time, hour_format),
                "downstream binding activity": conflict.downstream_binding_activity,
                "downstream binding time": _format_time(conflict.downstream_binding_time, hour_format),
            })
    elif isinstance(conflict, UnattributedTimeConflictFacts):
        description["feasibility shortfall"] = _format_duration(conflict.feasibility_shortfall)
    return description


def _compare(current_value: int, new_value: int, lower_word: str, higher_word: str) -> str:
    """Return how the new solution's value compares with the current solution's, in words."""
    if new_value < current_value:
        return f"{lower_word} in the new solution"
    if new_value > current_value:
        return f"{higher_word} in the new solution"
    return "equal in both solutions"


def _describe_kpis_comparison(current_kpis: KPIFacts, support_kpis: KPIFacts) -> dict[str, dict[str, str]]:
    """Return the two solutions' KPIs side by side, each with how they compare spelled out."""
    return {
        kpi_name: {"current solution": _format_duration(current_value), "new solution": _format_duration(new_value),
                   "comparison": _compare(current_value, new_value, "shorter", "longer")}
        for kpi_name, current_value, new_value in (
            ("total working duration", current_kpis.total_working_duration, support_kpis.total_working_duration),
            ("total traveling duration",
             current_kpis.total_traveling_duration, support_kpis.total_traveling_duration),
        )
    }


def build_facts_document(facts: ExplanationFacts) -> dict[str, Any]:
    """
    Return the facts as the document the LLM words the explanation from:
    times spelled in the hour format of the explanation's language, durations in minutes,
    values the wording needs but the facts only imply (the verdict, the earliest end time, how the KPIs compare)
    made explicit, and the side of a time conflict that does not explain it left out.

    Args:
        facts: The facts to describe.

    Returns:
        The document, JSON-serializable.
    """
    hour_format = get_hour_format_associated_with_language(facts.language)
    document: dict[str, Any] = {
        "question": facts.question,
        "answer language": _get_language_name(facts.language),
        "outcome": facts.outcome.value,
        "verdict": _OUTCOME_VERDICTS[facts.outcome],
        "explored change": {"operators": list(facts.operators), "restrictions": list(facts.restrictions)},
    }
    if facts.conflict is not None:
        document["conflict"] = _describe_conflict(facts.conflict, hour_format)
    document["route changes"] = [
        {"employee": route_change.employee,
         "current route": _describe_route(route_change.current_route),
         "new route": _describe_route(route_change.support_route),
         "added tasks": list(route_change.added_tasks), "removed tasks": list(route_change.removed_tasks)}
        for route_change in facts.route_changes
    ]
    document["newly performed tasks"] = list(facts.newly_performed_tasks)
    document["no longer performed tasks"] = list(facts.no_longer_performed_tasks)
    if facts.support_kpis is not None:
        document["KPIs comparison"] = _describe_kpis_comparison(facts.current_kpis, facts.support_kpis)
    return document


def build_user_prompt(facts_document: dict[str, Any], solution: Solution, with_json_context: bool = False) -> str:
    """
    Builds the prompt carrying the facts to word, and optionally the instance and the current solution as JSON.

    Args:
        facts_document: The facts, as built by build_facts_document.
        solution: The solution the question is about.
        with_json_context: If True, also describe the instance and the current solution as two JSON documents,
            for an LLM to draw context from (e.g. what a task is like).
            Only the FACTS are to be stated, whichever way.

    Returns:
        The user prompt to send alongside SYSTEM_PROMPT.
    """
    lines = ["FACTS (JSON):", json.dumps(facts_document, indent=2, ensure_ascii=False)]
    if with_json_context:
        solution_dictionary = solution.to_dict(
            with_tasks_performances=True, with_sequences=True, with_kpis=False, with_instance=False
        )
        lines += [
            "",
            "For context only - the explanation must still state only what the FACTS above say:",
            "Instance (JSON, times in minutes since midnight):",
            json.dumps(solution.instance.to_dict(), indent=2),
            "",
            "Current solution (JSON, \"start time\" values in minutes since midnight):",
            json.dumps(solution_dictionary, indent=2),
        ]
    return "\n".join(lines)
