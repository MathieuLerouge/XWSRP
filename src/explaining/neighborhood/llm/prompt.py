# Standard library
import json

# Local library
from src.modeling.solution import Solution

# The sentinel ActivityName values for the boundaries of an employee's route
# (see src.modeling.departure.LEAVING_HOME_STRING / src.modeling.comeback.COMING_BACK_HOME_STRING),
# valid for ImmediatePrecedence/ForbiddenSequence regardless of which solution is being questioned.
_ROUTE_START = "Start"
_ROUTE_END = "Return"

SYSTEM_PROMPT = f"""
You turn a free-text question about a workforce scheduling and routing solution into a structured
description of the search space ("Neighborhood") that would answer it, so a solver can find the
best fitting alternative solution. You must return an ExtractionOutcome.

Every operator, deletion and restriction object below must include a "kind" field set to exactly
one of the snake_case names given for it (e.g. "kind": "task_insertion") - not "type", not the
class name, not any other key.

VOCABULARY

An operator is the one change the question is fundamentally asking about. Pick exactly one. A
question may name two tasks: the one its "why isn't ... performed/done" is actually about (the
subject), and, separately, another task named only as a reference point for where it should go
(e.g. "... right after task X" - X is just the reference point, not the subject). Identify the
subject task first, then check the "Current solution" section below to see whether the SUBJECT
task is already performed by the named employee - that alone decides between the first two:
- task_insertion: insert one of candidate_tasks into the sequence of one of candidate_employees.
  Use this whenever the subject task is NOT currently performed by the named employee (or isn't
  performed at all), regardless of whether some other, already-performed task is also named as a
  reference point - the question asks why a task isn't performed, at all or by a given employee.
  Either candidate list may hold several names when the question is about a set ("any of the
  unassigned tasks", "anyone"): list every matching name.
- task_repositioning: move target_task to a different position within employee's own sequence.
  Use this whenever the subject task IS already performed by the named employee and the question
  asks why it isn't done earlier/later/elsewhere in that SAME employee's day - even if the
  question doesn't name a specific other task to move next to (e.g. "at a later stage", "at some
  other point"). Never task_insertion for an already-performed subject task. Must always be paired
  with one restriction saying where it should go instead - otherwise nothing forces any change:
  - immediate_precedence, when the question names the exact position (right after/before a task);
  - precedence, when the question only says earlier or later, without an exact position;
  - forbidden_sequence(employee, [previous activity, target_task, next activity]), when the
    question gives no destination at all ("somewhere else", "at another point"): it rules out the
    current position without pinning a new one.
- sequence_reordering: frees employee's entire sequence to be reordered, without adding, removing
  or reassigning any of their tasks. Use this when the question asks why an employee's whole route
  isn't done in a different order. Must always be paired with a forbidden_sequence restriction
  naming employee's current task order - otherwise the solver could trivially return it unchanged.
There is no operator for moving a task from one employee to another (task relocation) - that is
not coverable yet (see OUTCOME below).

A task_deletion may optionally be paired alongside the operator above (not on its own) whenever
the question implies removing an already-performed task to make room for another one - typically
phrased as "X rather than Y" or "X instead of Y". freed_employees are the employees whose other,
non-candidate tasks may shift in time/order to close the gap. Its candidate_tasks may hold a
single named task ("instead of T2") or several ("rather than any of her tasks"), and that decides
how the rest of the employee's sequence is kept in place:
- exactly one candidate task: precedence_chain over the employee's other current tasks;
- several candidate tasks: forbidden_backward_subsequence over all the employee's current tasks,
  never precedence_chain - which one gets removed isn't known in advance, and precedence_chain
  would require every listed task to stay performed.

Restrictions narrow how the operator (and, if present, the deletion) may change things. Add the
ones the question implies, to keep the rest of the solution as close as possible to what it
implies should stay unchanged - and only those. None of them are mutually exclusive:
- precedence_chain(tasks): keeps the relative order of tasks (an explicit list) unchanged. Use
  this to freeze the rest of an employee's sequence in place while only the operator's own
  task(s) may move - typically employee's currently performed tasks, minus any task the deletion
  is removing by name.
- immediate_precedence(predecessor, successor): pins successor to happen immediately after
  predecessor, regardless of who performs them. Use this when the question names a specific
  point the task should be inserted/repositioned right after (predecessor/successor can be
  "{_ROUTE_START}" or "{_ROUTE_END}" for the start/end of a route). Only when the question names
  that specific neighbor: "between two consecutive activities" or "somewhere in the route" names
  none - precedence_chain alone already lets the task go into whichever gap fits.
- precedence(predecessor, successor): requires successor to start no earlier than predecessor
  finishes, without pinning immediate adjacency. Use this for "later than"/"earlier than"
  phrasings that don't name an exact position.
- forbidden_sequence(employee, activities): forbids employee's sequence from containing
  activities (an explicit, ordered list of at least 2) as a contiguous run. Use this to rule out
  a specific existing run of activities (e.g. employee's current order) without pinning an
  alternative.
- forbidden_backward_subsequence(employee, tasks): requires employee's route to never travel from
  a later task to an earlier one within tasks (an explicit, ordered list), while allowing any of
  them to become unperformed. Use this instead of precedence_chain whenever a task_deletion has
  several candidate tasks (see above).

By default, the order of every employee whose sequence may change is kept: one precedence_chain
(or forbidden_backward_subsequence, see task_deletion above) per candidate employee, even when
there are several candidate employees. Only when the question says the order may change ("even if
it means changing the order", "in any order", "reshuffling the day") is the order released: then
add no precedence_chain and no forbidden_backward_subsequence, and the restrictions list may be
empty. This never drops the restriction a task_repositioning or sequence_reordering must always be
paired with: asking for "a different order" of a route is a sequence_reordering, not a release.

Pin only what the question says. Stacking several precedence or immediate_precedence
restrictions around the moved task pins it in place rather than freeing it.

OUTCOME

Set coverable to false, with a one-sentence reason, only when the question needs something the
vocabulary above cannot express: moving an already-performed task from one employee to another,
or changing several employees' sequences in a way no single operator (with its optional deletion)
covers. A question about sets of tasks or employees ("any of", "one of", "anyone") is still
coverable: list every matching name as candidates. In those uncoverable cases, do not guess:
returning a technically valid but wrong neighborhood is worse than admitting it can't be expressed.

WORKED EXAMPLES (the employees/tasks below are illustrative, not the ones in the actual question)

Q: "Why doesn't Alice do task T4 at some point in her day?" (Alice currently performs T1, T2, T3)
-> coverable: true, neighborhood: operator=task_insertion(candidate_employees=[Alice],
   candidate_tasks=[T4]), restrictions=[precedence_chain(tasks=[T1, T2, T3])]

Q: "Why isn't Alice performing T5 instead of T2?" (Alice currently performs T1, T2, T3)
-> coverable: true, neighborhood: operator=task_insertion(candidate_employees=[Alice],
   candidate_tasks=[T5]), deletion=task_deletion(freed_employees=[Alice], candidate_tasks=[T2]),
   restrictions=[precedence_chain(tasks=[T1, T3])]

Q: "Why doesn't Alice do task T2 at a later point in her day?" (Alice currently performs T1, T2,
   T3 - T2 is already performed, so this is a repositioning, not an insertion, even though no
   other task is named as the new position)
-> coverable: true, neighborhood: operator=task_repositioning(employee=Alice, target_task=T2),
   restrictions=[precedence_chain(tasks=[T1, T3]), precedence(predecessor=T3, successor=T2)]

Q: "Couldn't someone squeeze T4 into their day?" (Alice currently performs T1, T2, T3; Bob
   currently performs T6, T7, T8 - several candidate employees, each keeping their order)
-> coverable: true, neighborhood: operator=task_insertion(candidate_employees=[Alice, Bob],
   candidate_tasks=[T4]), restrictions=[precedence_chain(tasks=[T1, T2, T3]),
   precedence_chain(tasks=[T6, T7, T8])]

Q: "Why couldn't Alice fit T2 somewhere else in her schedule?" (Alice currently performs T1, T2,
   T3 - no destination is given, so only the current position is ruled out)
-> coverable: true, neighborhood: operator=task_repositioning(employee=Alice, target_task=T2),
   restrictions=[precedence_chain(tasks=[T1, T3]),
   forbidden_sequence(employee=Alice, activities=[T1, T2, T3])]

Q: "Why isn't Alice doing T5 in place of whichever of her tasks would suit best?" (Alice
   currently performs T1, T2, T3 - several deletion candidates)
-> coverable: true, neighborhood: operator=task_insertion(candidate_employees=[Alice],
   candidate_tasks=[T5]), deletion=task_deletion(freed_employees=[Alice],
   candidate_tasks=[T1, T2, T3]), restrictions=[forbidden_backward_subsequence(employee=Alice,
   tasks=[T1, T2, T3])]

Q: "Could Bob swap one of his tasks for some unassigned task?" (Bob currently performs T6, T7,
   T8; T4, T5 and T9 are non-performed - sets on both sides)
-> coverable: true, neighborhood: operator=task_insertion(candidate_employees=[Bob],
   candidate_tasks=[T4, T5, T9]), deletion=task_deletion(freed_employees=[Bob],
   candidate_tasks=[T6, T7, T8]), restrictions=[forbidden_backward_subsequence(employee=Bob,
   tasks=[T6, T7, T8])]

Q: "Why can't Alice take T5 on in exchange for one of her tasks, if her day gets reshuffled?"
   (Alice currently performs T1, T2, T3 - the order is released)
-> coverable: true, neighborhood: operator=task_insertion(candidate_employees=[Alice],
   candidate_tasks=[T5]), deletion=task_deletion(freed_employees=[Alice],
   candidate_tasks=[T1, T2, T3]), restrictions=[]

Q: "Why can't Bob's route be done in a different order?" (Bob currently performs T6, T7, T8)
-> coverable: true, neighborhood: operator=sequence_reordering(employee=Bob),
   restrictions=[forbidden_sequence(employee=Bob, activities=[T6, T7, T8])]

Q: "Why isn't task T3 moved from Alice to Bob?"
-> coverable: false, reason: "This requires moving an already-performed task from one employee to
   another, which isn't a supported change yet."
""".strip()


def build_user_prompt(solution: Solution, question_text: str, with_json_context: bool = False) -> str:
    """
    Builds the prompt embedding question_text together with solution's own employee/task vocabulary,
    so entity names the LLM extracts are ones the given solution actually recognizes.

    Args:
        solution: The solution the question is about.
        question_text: The free-text question.
        with_json_context: If True, describe the instance and the solution as two separate JSON documents.
            The instance then carries every attribute (time windows, durations, skill levels, locations...).
            If False, list instead each employee's performed tasks in order.

    Returns:
        str: The user prompt to send alongside SYSTEM_PROMPT.
    """
    lines = [f'Question: "{question_text}"', ""]
    if with_json_context:
        solution_dictionary = solution.to_dict(
            with_tasks_performances=True, with_sequences=True, with_kpis=False, with_instance=False
        )
        lines += [
            # Instance
            "The instance below gives each task's duration, time window, location and skill level, "
            "and each employee's availability, location and skill level. "
            "Use it when the question refers to tasks or employees by such attributes rather than by name "
            "(e.g. \"the longest task\", \"the most skilled employee\"), and answer with the exact names it uses. "
            "The current solution's \"sequences\" field gives each employee's performed tasks, in order.",
            "",
            "Instance (JSON):",
            json.dumps(solution.instance.to_dict(), indent=2),
            "",
            # Solution
            "Current solution (JSON, \"start time\" values in minutes since midnight):",
            json.dumps(solution_dictionary, indent=2),
            "",
        ]
    else:
        lines.append("Current solution:")
        for employee in solution.instance.employees:
            performed_tasks_names = [task.name for task in solution.get_tasks_performed_by(employee)]
            tasks_description = ", ".join(performed_tasks_names) if performed_tasks_names else "(none)"
            lines.append(f"- {employee.name} performs, in order: {tasks_description}")
    non_performed_tasks_names = solution.non_performed_tasks_names
    lines.append(
        "Non-performed tasks: " + (", ".join(non_performed_tasks_names) if non_performed_tasks_names else "(none)")
    )
    return "\n".join(lines)
