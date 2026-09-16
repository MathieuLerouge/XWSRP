# Local library
from src.modeling.solution import Solution

# The sentinel ActivityName values for the boundaries of an employee's route (see
# src.modeling.departure.LEAVING_HOME_STRING / src.modeling.comeback.COMING_BACK_HOME_STRING),
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

An operator is the one change the question is fundamentally asking about. Pick exactly one:
- task_insertion: insert one of candidate_tasks into the sequence of one of candidate_employees.
  Use this whenever the question asks why a task isn't performed (at all, or by a given employee).
- task_repositioning: move target_task to a different position within employee's own sequence.
  Use this when the question asks why a task isn't done earlier/later/elsewhere in the SAME
  employee's day. Must always be paired with a restriction that pins where it should go instead
  (immediate_precedence or precedence) - otherwise there is nothing forcing any actual change.
- sequence_reordering: frees employee's entire sequence to be reordered, without adding, removing
  or reassigning any of their tasks. Use this when the question asks why an employee's whole route
  isn't done in a different order. Must always be paired with a forbidden_sequence restriction
  naming employee's current task order - otherwise the solver could trivially return it unchanged.
There is no operator for moving a task from one employee to another (task relocation) - that is
not coverable yet (see OUTCOME below).

A task_deletion may optionally be paired alongside the operator above (not on its own) whenever
the question implies removing an already-performed task to make room for another one - typically
phrased as "X rather than Y" or "X instead of Y". freed_employees are the employees whose other,
non-candidate tasks may shift in time/order to close the gap.

Restrictions narrow how the operator (and, if present, the deletion) may change things. Add as
many as needed to keep the rest of the solution as close as possible to what the question implies
should stay unchanged. None of them are mutually exclusive:
- precedence_chain(tasks): keeps the relative order of tasks (an explicit list) unchanged. Use
  this to freeze the rest of an employee's sequence in place while only the operator's own
  task(s) may move - typically employee's currently performed tasks, minus any task the deletion
  is removing by name.
- immediate_precedence(predecessor, successor): pins successor to happen immediately after
  predecessor, regardless of who performs them. Use this when the question names a specific
  point the task should be inserted/repositioned right after (predecessor/successor can be
  "{_ROUTE_START}" or "{_ROUTE_END}" for the start/end of a route).
- precedence(predecessor, successor): requires successor to start no earlier than predecessor
  finishes, without pinning immediate adjacency. Use this for "later than"/"earlier than"
  phrasings that don't name an exact position.
- forbidden_sequence(employee, activities): forbids employee's sequence from containing
  activities (an explicit, ordered list of at least 2) as a contiguous run. Use this to rule out
  a specific existing run of activities (e.g. employee's current order) without pinning an
  alternative.
- forbidden_backward_subsequence(employee, tasks): requires employee's route to never travel from
  a later task to an earlier one within tasks (an explicit, ordered list), while allowing any of
  them to become unperformed. Use this instead of precedence_chain when a task_deletion's
  candidate_tasks includes more than one task, since which one actually gets removed isn't known
  in advance.

OUTCOME

Set coverable to false, with a one-sentence reason, whenever the question needs something the
vocabulary above cannot express - most commonly relocating an already-performed task from one
employee to another, or changing more than one employee's sequence at once. Do not guess: return
a technically valid but wrong neighborhood is worse than admitting it can't be expressed.

WORKED EXAMPLES (the employees/tasks below are illustrative, not the ones in the actual question)

Q: "Why doesn't Alice do task T4 at some point in her day?" (Alice currently performs T1, T2, T3)
-> coverable: true, neighborhood: operator=task_insertion(candidate_employees=[Alice],
   candidate_tasks=[T4]), restrictions=[precedence_chain(tasks=[T1, T2, T3])]

Q: "Why isn't Alice performing T5 instead of T2?" (Alice currently performs T1, T2, T3)
-> coverable: true, neighborhood: operator=task_insertion(candidate_employees=[Alice],
   candidate_tasks=[T5]), deletion=task_deletion(freed_employees=[Alice], candidate_tasks=[T2]),
   restrictions=[precedence_chain(tasks=[T1, T3])]

Q: "Why can't Bob's route be done in a different order?" (Bob currently performs T6, T7, T8)
-> coverable: true, neighborhood: operator=sequence_reordering(employee=Bob),
   restrictions=[forbidden_sequence(employee=Bob, activities=[T6, T7, T8])]

Q: "Why isn't task T3 moved from Alice to Bob?"
-> coverable: false, reason: "This requires moving an already-performed task from one employee to
   another, which isn't a supported change yet."
""".strip()


def build_user_prompt(solution: Solution, question_text: str) -> str:
    """
    Builds the prompt embedding question_text together with solution's own employee/task vocabulary,
    so entity names the LLM extracts are ones the given solution actually recognizes.

    Args:
        solution: The solution the question is about.
        question_text: The free-text question.

    Returns:
        str: The user prompt to send alongside SYSTEM_PROMPT.
    """
    lines = [f'Question: "{question_text}"', "", "Current solution:"]
    for employee in solution.instance.employees:
        performed_tasks_names = [task.name for task in solution.get_tasks_performed_by(employee)]
        tasks_description = ", ".join(performed_tasks_names) if performed_tasks_names else "(none)"
        lines.append(f"- {employee.name} performs, in order: {tasks_description}")
    non_performed_tasks_names = solution.non_performed_tasks_names
    lines.append(
        "Non-performed tasks: " + (", ".join(non_performed_tasks_names) if non_performed_tasks_names else "(none)")
    )
    return "\n".join(lines)
