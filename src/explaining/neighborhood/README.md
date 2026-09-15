# Description of the `neighborhood` module

This module implements a vocabulary for describing a search space around a solution: a `Neighborhood`.
It is as an alternative to `computing/templates`' per-template tailored transformation functions. \
It backs `computing/model.py`'s `NeighborhoodModel`, which turns a `Neighborhood` into a solvable MILP.


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
`TaskDeletion` (remove between a minimum and a maximum number of candidate tasks, freeing the other 
already-performed tasks of a given set of employees to shift in time/order to close the gap left behind), 
`TaskRelocation` (move a single target task from an origin employee's sequence to a destination one), 
`TaskRepositioning` (the same-employee special case of `TaskRelocation`), 
or `SequenceReordering` (free an employee's entire sequence to be reordered, without adding, removing or 
reassigning any of their tasks). \
Its `scope` is its own candidate employees/tasks (`TaskDeletion`'s freed_employees for the employee half; 
or, for `TaskRelocation`, its origin/destination employees and target task; for `TaskRepositioning`/
`SequenceReordering`, just its employee, plus the target task for the former).

A `Restriction` (`restriction.py`) narrows freedom already granted elsewhere: 
`PrecedenceChain` keeps the relative order of a given, explicit, ordered list of tasks unchanged 
(only tasks in scope may be added/removed/repositioned; every listed task is assumed to stay performed), 
`ImmediatePrecedence` pins one activity to occur immediately after another, 
regardless of which employee ends up performing them 
— that's left to whatever else (typically an operator) constrains it, 
`Precedence` requires one task to finish no later than another starts, without pinning adjacency, 
`ForbiddenSequence` forbids a specific employee's sequence from containing a given, 
explicit, ordered chain of activities as a contiguous run, 
and `ForbiddenBackwardSubsequence` requires a specific employee's route to never travel from a later task 
to an earlier one within a given, explicit, ordered list of tasks — keeping whichever of them remain 
performed in their original relative order, while allowing any of them to become unperformed 
(unlike `PrecedenceChain`, which assumes every listed task stays performed).

Restrictions are composable: an employee's tasks may be covered by several of them at once 
(e.g. `PrecedenceChain` together with one or more `ImmediatePrecedence`).

The `templates` subpackage maps a `Question` to the `Neighborhood` it induces: `Mapper` (`mapper.py`)
dispatches on the question's template id to a dedicated mapping function, implemented per question family
(`insertion.py` for the `(Ins,*)` family — see section 3).


# 2. Description of the files

`primitive.py` contains `Primitive`, the common, otherwise-empty base shared by operators and restrictions.

`operator.py` contains `Operator` and its subclasses: 
`TaskInsertion`, `TaskDeletion`, `TaskRelocation`, `TaskRepositioning` and `SequenceReordering`, described above.

`restriction.py` contains `Restriction` and its subclasses: 
`PrecedenceChain`, `ImmediatePrecedence`, `Precedence`, `ForbiddenSequence` and
`ForbiddenBackwardSubsequence`, described above.

`neighborhood.py` contains `Neighborhood`, described above.

`templates` is the subpackage mapping questions to neighborhoods:

- `mapper.py` contains `Mapper`, 
whose `map(question)` method dispatches a `ContrastiveQuestion` to its matching neighborhood-mapping function.
- `insertion.py` contains the mapping functions for the `(Ins,*)` template family.
- `swap.py` contains the mapping functions for the `(Swp,*)` template family.
- `reordering.py` contains the mapping functions for the `(Ord,*)` template family.


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
- $e^0(j)$ is the employee assigned to task $j$ in the given solution.


## 3.1. `Restriction` bank

| Scope Restriction                               | Description                                                                                                                                                                                            | Symbols                                                                                  | Constraint                                                              |
|-------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| `ImmediatePrecedence(predecessor, successor)`   | Pins successor to occur immediately after predecessor, regardless of which employee performs them.                                                                                                     | $p :=$ predecessor, $s :=$ successor                                                     | $\sum_{e} U_{e,\,p,\,s} = 1$                                            |
| `Precedence(predecessor, successor)`            | Requires successor to start no earlier than predecessor finishes, without pinning adjacency.                                                                                                           | $p :=$ predecessor, $s :=$ successor                                                     | $T_p + d_p \le T_s$                                                     |
| `PrecedenceChain(tasks)`                        | Keeps the relative order of a given, explicit, ordered list of tasks unchanged. Every listed task is assumed to stay performed.                                                                        | $\mathcal{T} :=$ tasks (an ordered list)                                                 | $T_i + d_i \le T_j \quad \forall\, (i,j)$ consecutive in $\mathcal{T}$  |
| `ForbiddenSequence(employee, activities)`       | Forbids employee's sequence from containing activities as a contiguous run.                                                                                                                            | $e :=$ employee, $\mathcal{S} :=$ activities (an ordered list, $n := \| \mathcal{S} \|$) | $\sum_{k=1}^{n-1} U_{e,\,a_k,\,a_{k+1}} \le n - 2$                      |
| `ForbiddenBackwardSubsequence(employee, tasks)` | Requires employee's route to never travel from a later task to an earlier one within tasks: whichever of them remain performed keep their original relative order, any of them may become unperformed. | $e :=$ employee, $\mathcal{T} :=$ tasks (an ordered list)                                | $U_{e,\,t_j,\,t_i} = 0 \quad \forall\, 1 \le i < j \le \|\mathcal{T}\|$ |


## 3.2. `Operator` bank

| Operator                                                                               | Description                                                                                                                                                                          | Symbols                                                                                                                | Scope                          | Constraint                                                                                                                                             | Comments                                                                                                                                                                                                              |
|----------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `TaskInsertion(candidate_employees, candidate_tasks)`                                  | Inserts a candidate task into a candidate employee's sequence.                                                                                                                       | $\mathcal{E} :=$ candidate_employees, $\mathcal{J} :=$ candidate_tasks                                                 | $\mathcal{E} \cup \mathcal{J}$ | $\sum_{j \in \mathcal{J}} X_j = 1 \ \ \forall\, j \in \mathcal{J}$, $\sum_{e \in \mathcal{E},\,k} U_{e,\,j,\,k} = X_j \ \ \forall\, j \in \mathcal{J}$ | —                                                                                                                                                                                                                     |
| `TaskDeletion(freed_employees, candidate_tasks, min_nb_removals=1, max_nb_removals=1)` | Removes between `min_nb_removals` and `max_nb_removals` candidate tasks from a candidate employee's sequence, freeing `freed_employees`' other tasks to shift in time/get reordered. | $\mathcal{E} :=$ freed_employees, $\mathcal{J} :=$ candidate_tasks, $n^- :=$ min_nb_removals, $n^+ :=$ max_nb_removals | $\mathcal{E} \cup \mathcal{J}$ | $n^- \le \|\mathcal{J}\| - \sum_{j \in \mathcal{J}} X_j \le n^+$, $\sum_{k} U_{e^0(j),\,j,\,k} = X_j \ \ \forall\, j \in \mathcal{J}$                  | Never gets slack variables of its own. `NeighborhoodModel` only accepts `TaskDeletion` paired with a feasibility-shortfall operator (`TaskInsertion`/`TaskRepositioning`/`SequenceReordering`).                       |
| `TaskRelocation(origin_employee, destination_employee, target_task)`                   | Moves the target task from the origin employee's sequence to the destination employee's sequence.                                                                                    | $o :=$ origin_employee, $d :=$ destination_employee, $t :=$ target_task                                                | $\{o,\, d,\, t\}$              | not yet implemented in `NeighborhoodModel`                                                                                        v                    | —                                                                                                                                                                                                                     |
| `TaskRepositioning(employee, target_task)`                                             | Moves the target task to a different position within employee's own sequence. The special case of `TaskRelocation` where origin and destination are the same.                        | $e :=$ employee, $t :=$ target_task                                                                                    | $\{e,\, t\}$                   | $X_t = 1$, $\sum_{k} U_{e,\,t,\,k} = 1$                                                                                                                | Must always be paired with a Restriction that pins a new position (e.g. `Precedence`/`ImmediatePrecedence`), otherwise the solver may trivially reproduce the given solution's sequence unchanged.                    |
| `SequenceReordering(employee)`                                                         | Frees employee's entire sequence to be reordered, without adding, removing or reassigning any of their tasks.                                                                        | $e :=$ employee                                                                                                        | $\{e\}$                        | none — achieved entirely by the generic freeze mechanism (an employee in scope already frees the timing/order of their given-solution tasks)           | Must always be paired with a `ForbiddenSequence` (typically forbidding employee's own original sequence as one contiguous run), otherwise the solver may trivially reproduce the given solution's sequence unchanged. |

WIP: `TaskRelocation` exists as vocabulary, but has no MILP formulation yet.


# 4. Mapping the tailored contrastive questions to neighborhoods

## 4.1. `(Ins,*)` contrastive questions

Each `(Ins,*)` question asks why a task isn't inserted somewhere. 
Every mapping below therefore induces a `Neighborhood` with a `TaskInsertion` operator, 
differing in which employee(s) it targets, what the operator's candidates are, 
and which restrictions keep the rest of each targeted employee's sequence untouched.

| Template   | Question                                                                                                                                         | Operator                                         | Restrictions                                                                  |
|------------|--------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|-------------------------------------------------------------------------------|
| `(Ins,1)`  | Why is employee {Employee} not performing task {Task} just after activity {Activity}?                                                            | `TaskInsertion({employee}, {task})`              | `PrecedenceChain(employee_tasks)`, `ImmediatePrecedence({activity}, {task})`  |
| `(Ins,2a)` | Why is employee {Employee} not performing task {Task} between two consecutive activities of their route?                                         | `TaskInsertion({employee}, {task})`              | `PrecedenceChain(employee_tasks)`                                             |
| `(Ins,2b)` | Why is employee {Employee} not performing any non-performed task between two consecutive activities of their route?                              | `TaskInsertion({employee}, non_performed_tasks)` | `PrecedenceChain(employee_tasks)`                                             |
| `(Ins,2c)` | Why is any employee not performing task {Task} between two consecutive activities of their route?                                                | `TaskInsertion(employees, {task})`               | `PrecedenceChain(employee_tasks)` for every employee                          |
| `(Ins,3)`  | Why is employee {Employee} not performing task {Task} in addition to their already-performed activities (even if it means changing their order)? | `TaskInsertion({employee}, {task})`              | none — order left free                                                        |

NB: `(Ins,2b)` additionally raises `ImpossibleTransformationException` when the solution already performs every task, 
since there is then no non-performed task left to offer as a candidate.


## 4.2. `(Swp,*)` contrastive questions to neighborhoods

Each `(Swp,*)` question asks why a task isn't performed instead of one the employee already performs.
Every mapping below therefore pairs a `TaskDeletion` (removing the outgoing task) with a `TaskInsertion`
(adding the incoming one) on the same employee(s), differing in whether the outgoing/incoming task is
named or left for the solver to choose among a candidate set, and whether order is kept fixed.

`(Swp,1)`'s outgoing task is named, so `PrecedenceChain`'s `tasks` parameter already provides the right mechanism: 
the Mapper just excludes it from `tasks` (keeping the rest in their original relative order), 
so it isn't wrongly re-pinned by the very restriction meant to keep everything else in place.

For `(Swp,2a)`/`(Swp,2b)`/`(Swp,2c)`, the outgoing task is known once the solver picks one,
among several `TaskDeletion` candidates. 
For that reason, the Mapper cannot use a `PrecedenceChain` restriction.
Instead, it can use `ForbiddenBackwardSubsequence` restriction: it constrains arcs ($U$), not times ($T$).
Whichever candidate ends up removed has no arcs at all, 
and the solver bridges directly between its former neighbors with the shorter direct travel time between them.

| Template   | Question                                                                                                                                        | Operators                                                                                              | Restrictions                                                                  |
|------------|-------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `(Swp,1)`  | Why is employee {Employee} not performing task {Task1} rather than task {Task2}?                                                                | `TaskDeletion({employee}, {task2})`, `TaskInsertion({employee}, {task1})`                              | `PrecedenceChain(employee_tasks - {task2})`                                   |
| `(Swp,2a)` | Why is employee {Employee} not performing task {Task} rather than any of their already-performed tasks?                                         | `TaskDeletion({employee}, employee_performed_tasks)`, `TaskInsertion({employee}, {task})`              | `ForbiddenBackwardSubsequence({employee}, employee_tasks)`                    |
| `(Swp,2b)` | Why is employee {Employee} not performing any non-performed task rather than any of their already-performed tasks?                              | `TaskDeletion({employee}, employee_performed_tasks)`, `TaskInsertion({employee}, non_performed_tasks)` | `ForbiddenBackwardSubsequence({employee}, employee_tasks)`                    |
| `(Swp,2c)` | Why is any employee not performing task {Task} rather than any of their already-performed tasks?                                                | `TaskDeletion(employees, performed_tasks)`, `TaskInsertion(employees, {task})`                         | `ForbiddenBackwardSubsequence({employee}, employee_tasks)` for every employee |
| `(Swp,3)`  | Why is employee {Employee} not performing task {Task} rather than any of their already-performed tasks (even if it means changing their order)? | `TaskDeletion({employee}, employee_performed_tasks)`, `TaskInsertion({employee}, {task})`              | none — order left free                                                        |


## 4.3. Mapping the `(Ord,*)` contrastive questions to neighborhoods

Each `(Ord,*)` mapping below uses a single Operator (`TaskRepositioning` or `SequenceReordering`)
along with precedence-related or sequence-related Restrictions 
(`ImmediatePrecedence,`, `Precedence`, `ForbiddenSequence`).

| Template   | Question                                                                                                    | Operator                                 | Restrictions                                                                                              |
|------------|-------------------------------------------------------------------------------------------------------------|------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| `(Ord,1a)` | Why is employee {Employee} not performing task {Task1} later in their planning, just after task {Task2}?    | `TaskRepositioning({employee}, {task1})` | `PrecedenceChain(employee_tasks - {task1})`, `ImmediatePrecedence({task2}, {task1})`                      |
| `(Ord,1b)` | Why is employee {Employee} not performing task {Task1} earlier in their planning, just before task {Task2}? | `TaskRepositioning({employee}, {task1})` | `PrecedenceChain(employee_tasks - {task1})`, `ImmediatePrecedence({task1}, {task2})`                      |
| `(Ord,2a)` | Why is employee {Employee} not performing task {Task} at a later stage of their planning?                   | `TaskRepositioning({employee}, {task})`  | `PrecedenceChain(employee_tasks - {task})`, `Precedence(next_task, task)`                                 |
| `(Ord,2b)` | Why is employee {Employee} not performing task {Task} at an earlier stage of their planning?                | `TaskRepositioning({employee}, {task})`  | `PrecedenceChain(employee_tasks - {task})`, `Precedence(task, prev_task)`                                 |
| `(Ord,2c)` | Why is employee {Employee} not performing task {Task} at any another stage in their planning?               | `TaskRepositioning({employee}, {task})`  | `PrecedenceChain(employee_tasks - {task})`, `ForbiddenSequence({employee}, [prev_task, task, next_task])` |
| `(Ord,3)`  | Why is employee {Employee} not performing the activities of their route in another order?                   | `SequenceReordering({employee})`         | `ForbiddenSequence({employee}, employee_tasks)`                                                           |

NB: Parity with the tailored pipeline holds for every `(Ord,*)` mapping below, with one caveat: 
the neighborhood pipeline's feasibility shortfall is only guaranteed to be at or below the tailored pipeline's, 
not exactly equal to it.
The tailored pipeline's reordering examinations bound each candidate position's feasibility 
using the original sequence's precomputed slack, which goes stale once the relative order actually changes.
The neighborhood MILP jointly re-optimizes every reordered task's time instead, 
so it can only find an equal or smaller shortfall. 
Both pipelines agree exactly whenever either finds a fully feasible (feasibility shortfall 0) arrangement.