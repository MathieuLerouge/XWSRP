# Description of the `neighborhood` module

This module implements a vocabulary for describing a search space around a solution: a `Neighborhood`.
It is as an alternative to `computing/templates`' per-template tailored transformation functions. \
It backs `computing/model.py`'s `NeighborhoodFeasibilityMILP`, which turns a `Neighborhood` into a solvable MILP.


# 1. Overview of the neighborhood abstraction

A `Neighborhood` (`neighborhood.py`) is defined by two things: 
the `operators` that may transform its scope's sequences, and the `restrictions` that narrow how. \
Its `scope` — the employees and tasks it frees from being fixed to their current state — 
is deduced from its operators' own `scope` alone; restrictions never contribute to it. \
`operators` and `restrictions` are both built out of `Primitive` (`primitive.py`), 
the common base marking what compose a `Neighborhood`.

Scope grants two different kinds of freedom, not one uniform kind — this is easy to misread, so worth
stating precisely: 
- a **task** in scope (an operator's own candidate) is fully free: its performance status and its
  assignee may both change, on top of its timing and position; 
- an **employee** in scope only frees the *timing and relative order* of their already-performed,
  not-separately-scoped tasks (subject to whatever `Restriction` narrows that further) — their task set
  and assignee stay exactly as given, unconditionally, regardless of the employee being in scope.

An `Operator` (`operator.py`) is an elementary transformation: 
`TaskInsertion` (insert a candidate task into a candidate employee's sequence), 
`TaskDeletion` (remove a candidate task from a candidate employee's sequence), 
`TaskRelocation` (move a single target task from an origin employee's sequence to a destination one), 
`TaskRepositioning` (the same-employee special case of `TaskRelocation`), 
or `SequenceReordering` (free an employee's entire sequence to be reordered, without adding, removing or 
reassigning any of their tasks). \
Its `scope` is its own candidate employees/tasks (or, for `TaskRelocation`, its origin/destination employees 
and target task; for `TaskRepositioning`/`SequenceReordering`, just its employee, plus the target task for 
the former).

A `Restriction` (`restriction.py`) narrows freedom already granted elsewhere: 
`SequenceOrderFixed` keeps the relative order of a given, explicit, ordered list of tasks unchanged 
(only tasks in scope may be added/removed/repositioned), 
`ImmediatePrecedence` pins one activity to occur immediately after another, 
regardless of which employee ends up performing them 
— that's left to whatever else (typically an operator) constrains it, 
`Precedence` requires one task to finish no later than another starts, without pinning adjacency, 
and `ForbiddenSequence` forbids a specific employee's sequence from containing a given, 
explicit, ordered chain of activities as a contiguous run.

Restrictions are composable: an employee's tasks may be covered by several of them at once 
(e.g. `SequenceOrderFixed` together with one or more `ImmediatePrecedence`).

The `templates` subpackage maps a `Question` to the `Neighborhood` it induces: `Mapper` (`mapper.py`)
dispatches on the question's template id to a dedicated mapping function, implemented per question family
(`insertion.py` for the `(Ins,*)` family — see section 3).


# 2. Description of the files

`primitive.py` contains `Primitive`, the common, otherwise-empty base shared by operators and restrictions.

`operator.py` contains `Operator` and its subclasses: 
`TaskInsertion`, `TaskDeletion`, `TaskRelocation`, `TaskRepositioning` and `SequenceReordering`, described above.

`restriction.py` contains `Restriction` and its subclasses: 
`SequenceOrderFixed`, `ImmediatePrecedence`, `Precedence` and `ForbiddenSequence`, described above.

`neighborhood.py` contains `Neighborhood`, described above.

`templates` is the subpackage mapping questions to neighborhoods:

- `mapper.py` contains `Mapper`, 
whose `map(question)` method dispatches a `ContrastiveQuestion` to its matching neighborhood-mapping function.
- `insertion.py` contains the mapping functions for the `(Ins,*)` template family.
- `repositioning.py` contains the mapping functions for the `(Ord,*)` template family.

# 3. `Primitive` bank

Let's introduce a few notations.

#### Parameters:
- $d_i$ is task $i$'s duration.

#### Decision variables: 
- $T_i$ is task $i$'s start time;
- $X_i$ is 1 if task $i$ is performed (0 otherwise); 
- $U_{e,i,j}$ is 1 if employee $e$ travels directly from activity $i$ to activity $j$ in their route.

#### Original solution:
- A superscript $^0$ denotes the decision variable's value in the given solution.
- $\mathcal{T}^0(e)$ is the set of tasks assigned to employee $e$ in the given solution.

## 3.1. `Restriction` bank

| Scope Restriction                             | Description                                                                                        | Symbols                                                                                  | Constraint                                                             |
|-----------------------------------------------|----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| `ImmediatePrecedence(predecessor, successor)` | Pins successor to occur immediately after predecessor, regardless of which employee performs them. | $p :=$ predecessor, $s :=$ successor                                                     | $\sum_{e} U_{e,\,p,\,s} = 1$                                           |
| `Precedence(predecessor, successor)`          | Requires successor to start no earlier than predecessor finishes, without pinning adjacency.       | $p :=$ predecessor, $s :=$ successor                                                     | $T_p + d_p \le T_s$                                                    |
| `SequenceOrderFixed(tasks)`                   | Keeps the relative order of a given, explicit, ordered list of tasks unchanged.                    | $\mathcal{S} :=$ tasks (an ordered list)                                                 | $T_i + d_i \le T_j \quad \forall\, (i,j)$ consecutive in $\mathcal{S}$ |
| `ForbiddenSequence(employee, activities)`     | Forbids employee's sequence from containing activities as a contiguous run.                        | $e :=$ employee, $\mathcal{A} :=$ activities (an ordered list, $n := \| \mathcal{A} \|$) | $\sum_{k=1}^{n-1} U_{e,\,a_k,\,a_{k+1}} \le n - 2$                     |

## 3.2. `Operator` bank

| Operator                                                             | Description                                                                                                                                                   | Symbols                                                                 | Scope                          | Constraint                                                                                                                                             | Comments                                                                                                                                                                                                                                                                                                   |
|----------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `TaskInsertion(candidate_employees, candidate_tasks)`                | Inserts a candidate task into a candidate employee's sequence.                                                                                                | $\mathcal{E} :=$ candidate_employees, $\mathcal{J} :=$ candidate_tasks  | $\mathcal{E} \cup \mathcal{J}$ | $\sum_{j \in \mathcal{J}} X_j = 1 \ \ \forall\, j \in \mathcal{J}$, $\sum_{e \in \mathcal{E},\,k} U_{e,\,j,\,k} = X_j \ \ \forall\, j \in \mathcal{J}$ | —                                                                                                                                                                                                                                                                                                          |
| `TaskDeletion(candidate_employees, candidate_tasks)`                 | Removes a candidate task from a candidate employee's sequence.                                                                                                | $\mathcal{E} :=$ candidate_employees, $\mathcal{J} :=$ candidate_tasks  | $\mathcal{E} \cup \mathcal{J}$ | not yet implemented in `NeighborhoodFeasibilityMILP`                                                                                                   | —                                                                                                                                                                                                                                                                                                          |
| `TaskRelocation(origin_employee, destination_employee, target_task)` | Moves the target task from the origin employee's sequence to the destination employee's sequence.                                                             | $o :=$ origin_employee, $d :=$ destination_employee, $t :=$ target_task | $\{o,\, d,\, t\}$              | not yet implemented in `NeighborhoodFeasibilityMILP`                                                                                                   | —                                                                                                                                                                                                                                                                                                          |
| `TaskRepositioning(employee, target_task)`                           | Moves the target task to a different position within employee's own sequence. The special case of `TaskRelocation` where origin and destination are the same. | $e :=$ employee, $t :=$ target_task                                     | $\{e,\, t\}$                   | $X_t = 1$, $\sum_{k} U_{e,\,t,\,k} = 1$                                                                                                                | Must always be paired with a Restriction that pins a new position (e.g. `Precedence`/`ImmediatePrecedence`); unlike `TaskRelocation` with distinct origin/destination, nothing here inherently forces a change, so without one the solver may trivially reproduce the given solution's sequence unchanged. |
| `SequenceReordering(employee)`                                       | Frees employee's entire sequence to be reordered, without adding, removing or reassigning any of their tasks.                                                 | $e :=$ employee                                                         | $\{e\}$                        | none — achieved entirely by the generic freeze mechanism (an employee in scope already frees the timing/order of their given-solution tasks)           | Must always be paired with a `ForbiddenSequence` (typically forbidding employee's own original route as one contiguous run), otherwise the solver may trivially reproduce it unchanged.                                                                                                                    |

WIP: `TaskDeletion` and `TaskRelocation` exist as vocabulary — their `scope` is fully defined and already
used by `Neighborhood.scope` — but have no MILP formulation yet. 
`TaskInsertion`, `TaskRepositioning` and `SequenceReordering` are fully implemented.

# 4. Mapping the tailored contrastive questions to neighborhoods

## 4.1. `(Ins,*)` contrastive questions

Each `(Ins,*)` question asks why a task isn't inserted somewhere. 
Every mapping below therefore induces a `Neighborhood` with a `TaskInsertion` operator, 
differing in which employee(s) it targets, what the operator's candidates are, 
and which restrictions keep the rest of each targeted employee's sequence untouched. \

| Template   | Question                                                                                                                                         | Operator                                         | Restrictions                                                                    |
|------------|--------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|---------------------------------------------------------------------------------|
| `(Ins,1)`  | Why is employee {Employee} not performing task {Task} just after activity {Activity}?                                                            | `TaskInsertion({employee}, {task})`              | `SequenceOrderFixed(employee_tasks)`, `ImmediatePrecedence({activity}, {task})` |
| `(Ins,2a)` | Why is employee {Employee} not performing task {Task} between two consecutive activities of their route?                                         | `TaskInsertion({employee}, {task})`              | `SequenceOrderFixed(employee_tasks)`                                            |
| `(Ins,2b)` | Why is employee {Employee} not performing any non-performed task between two consecutive activities of their route?                              | `TaskInsertion({employee}, non_performed_tasks)` | `SequenceOrderFixed(employee_tasks)`                                            |
| `(Ins,2c)` | Why is any employee not performing task {Task} between two consecutive activities of their route?                                                | `TaskInsertion(employees, {task})`               | `SequenceOrderFixed(employee_tasks)` for every employee                         |
| `(Ins,3)`  | Why is employee {Employee} not performing task {Task} in addition to their already-performed activities (even if it means changing their order)? | `TaskInsertion({employee}, {task})`              | none — order left free                                                          |

`(Ins,2b)` additionally raises `ImpossibleTransformationException` when the solution already performs every task, 
since there is then no non-performed task left to offer as a candidate.


## 4.2. `(Swp,*)` contrastive questions to neighborhoods

**Design only — not yet implemented.**
There is no `templates/swap.py` yet, and `NeighborhoodFeasibilityMILP`
currently only supports a `Neighborhood` targeted by a single `TaskInsertion` operator: wiring the mapping
below in also needs multi-operator support and a `TaskDeletion` MILP formulation (including one with a
non-singleton candidate-task set, for `(Swp,2a)`/`(Swp,2b)`/`(Swp,2c)`/`(Swp,3)`), neither of which exists
today. \
`SequenceOrderFixed`'s explicit `tasks` parameter (section 3.1) already provides the right mechanism for
`(Swp,1)`, where the outgoing task is named: the Mapper just excludes it from `tasks` (keeping the rest in
their original relative order), so it isn't wrongly re-pinned by the very restriction meant to keep
everything *else* in place. \
For `(Swp,2a)`/`(Swp,2b)`/`(Swp,2c)`/`(Swp,3)` the outgoing task is only known once the solver picks one
among several `TaskDeletion` candidates — which one to exclude from `tasks` can't be decided by the Mapper
upfront. That's a genuinely open modeling question (e.g. a conditional version of the pairwise constraint,
only active when both tasks end up performed), separate from — and not solved by — `SequenceOrderFixed`'s
explicit `tasks` parameter; the table below leaves those rows using the full, unexcluded `employee_tasks`
as a placeholder, not as a claimed-correct answer.

Each `(Swp,*)` question asks why a task isn't performed instead of one the employee already performs.
Every mapping below therefore pairs a `TaskDeletion` (removing the outgoing task) with a `TaskInsertion`
(adding the incoming one) on the same employee(s), differing in whether the outgoing/incoming task is
named or left for the solver to choose among a candidate set, and whether order is kept fixed. \
Matching the *tailored* pipeline's actual `(Swp,*)` behavior (`apply_swp_1` →
`Sequence.examine_replacing_task_with_another`, which only ever touches the named employee's own
sequence): the incoming task is not un-assigned from wherever it might currently be performed by someone
else — `(Swp,*)` never needs a second employee in scope, unlike a "true" cross-employee swap would.

| Template   | Question                                                                                                                                        | Operators                                                                                              | Restrictions                                                                      |
|------------|-------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `(Swp,1)`  | Why is employee {Employee} not performing task {Task1} rather than task {Task2}?                                                                | `TaskDeletion({employee}, {task2})`, `TaskInsertion({employee}, {task1})`                              | `SequenceOrderFixed(employee_tasks - {task2})`                                    |
| `(Swp,2a)` | Why is employee {Employee} not performing task {Task} rather than any of their already-performed tasks?                                         | `TaskDeletion({employee}, employee_performed_tasks)`, `TaskInsertion({employee}, {task})`              | `SequenceOrderFixed(employee_tasks)` — see open question above                    |
| `(Swp,2b)` | Why is employee {Employee} not performing any non-performed task rather than any of their already-performed tasks?                              | `TaskDeletion({employee}, employee_performed_tasks)`, `TaskInsertion({employee}, non_performed_tasks)` | `SequenceOrderFixed(employee_tasks)` — see open question above                    |
| `(Swp,2c)` | Why is any employee not performing task {Task} rather than any of their already-performed tasks?                                                | `TaskDeletion(employees, performed_tasks)`, `TaskInsertion(employees, {task})`                         | `SequenceOrderFixed(employee_tasks)` for every employee — see open question above |
| `(Swp,3)`  | Why is employee {Employee} not performing task {Task} rather than any of their already-performed tasks (even if it means changing their order)? | `TaskDeletion({employee}, employee_performed_tasks)`, `TaskInsertion({employee}, {task})`              | none — order left free                                                            |

Unlike every `(Ins,*)` mapping, `(Swp,2a)`/`(Swp,2b)`/`(Swp,2c)`/`(Swp,3)` give `TaskDeletion` a
multi-element `candidate_tasks` set (the employee's — or every candidate employee's — currently-performed
tasks): the outgoing task isn't named, only that it must already be performed by one of `candidate_employees`.
`(Swp,1)` is the exception where both operators are fully pinned (singleton candidates on both sides), the
same shape `(Ins,1)` already supports today.


## 4.3. Mapping the `(Ord,*)` contrastive questions to neighborhoods

Implemented in `templates/repositioning.py`, dispatched by `Mapper`. 
Each mapping below uses a single Operator. 
`TaskRepositioning` itself carries no direction, it is expressed entirely through `Precedence`: 
`next_task`/`prev_task` denote task's immediate successor/predecessor in `employee_tasks`, 
and requiring `Precedence(next_task, task)` (resp. `Precedence(task, prev_task)`) forces task past its former neighbor, 
i.e. to a strictly later (resp. earlier) position, without pinning it any more precisely than that. 
`(Ord,2c)` instead needs task to move to any different position: 
`ForbiddenSequence({employee}, [prev_task, task, next_task])` forbids only its exact original spot 
(dropping whichever neighbor doesn't exist if task was originally first/last), leaving every other position free. 
`(Ord,3)` reorders the whole route rather than one named task, via `SequenceReordering`; 
pairing it with `ForbiddenSequence({employee}, employee_tasks)` forbids the original order from being reproduced.

| Template   | Question                                                                                                    | Operator                                 | Restrictions                                                                                                  |
|------------|-------------------------------------------------------------------------------------------------------------|------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| `(Ord,1a)` | Why is employee {Employee} not performing task {Task1} later in their planning, just after task {Task2}?    | `TaskRepositioning({employee}, {task1})` | `SequenceOrderFixed(employee_tasks - {task1})`, `ImmediatePrecedence({task2}, {task1})`                       |
| `(Ord,1b)` | Why is employee {Employee} not performing task {Task1} earlier in their planning, just before task {Task2}? | `TaskRepositioning({employee}, {task1})` | `SequenceOrderFixed(employee_tasks - {task1})`, `ImmediatePrecedence({task1}, {task2})`                       |
| `(Ord,2a)` | Why is employee {Employee} not performing task {Task} at a later stage of their planning?                   | `TaskRepositioning({employee}, {task})`  | `SequenceOrderFixed(employee_tasks - {task})`, `Precedence(next_task, task)`                                  |
| `(Ord,2b)` | Why is employee {Employee} not performing task {Task} at an earlier stage of their planning?                | `TaskRepositioning({employee}, {task})`  | `SequenceOrderFixed(employee_tasks - {task})`, `Precedence(task, prev_task)`                                  |
| `(Ord,2c)` | Why is employee {Employee} not performing task {Task} at any another stage in their planning?               | `TaskRepositioning({employee}, {task})`  | `SequenceOrderFixed(employee_tasks - {task})`, `ForbiddenSequence({employee}, [prev_task, task, next_task])`  |
| `(Ord,3)`  | Why is employee {Employee} not performing the activities of their route in another order?                   | `SequenceReordering({employee})`         | `ForbiddenSequence({employee}, employee_tasks)`                                                               |
