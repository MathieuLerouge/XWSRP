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
or `TaskRelocation` (move a single target task from an origin employee's sequence to a destination one). \
Its `scope` is its own candidate employees/tasks (or, for `TaskRelocation`, its origin/destination employees and target task).

A `Restriction` (`restriction.py`) narrows freedom already granted elsewhere: 
`SequenceOrderFixed` keeps the relative order of a given, explicit, ordered list of tasks unchanged 
(only tasks in scope may be added/removed/repositioned), 
and `ImmediatePrecedence` pins one activity to occur immediately after another, 
regardless of which employee ends up performing them 
— that's left to whatever else (typically an operator) constrains it.

Restrictions are composable: an employee's tasks may be covered by several of them at once 
(e.g. `SequenceOrderFixed` together with one or more `ImmediatePrecedence`).

The `templates` subpackage maps a `Question` to the `Neighborhood` it induces: `Mapper` (`mapper.py`)
dispatches on the question's template id to a dedicated mapping function, implemented per question family
(`insertion.py` for the `(Ins,*)` family — see section 3).


# 2. Description of the files

`primitive.py` contains `Primitive`, the common, otherwise-empty base shared by operators and restrictions.

`operator.py` contains `Operator` and its subclasses: 
`TaskInsertion`, `TaskDeletion` and `TaskRelocation`, described above.

`restriction.py` contains `Restriction` and its subclasses: 
`SequenceOrderFixed` and `ImmediatePrecedence`, described above.

`neighborhood.py` contains `Neighborhood`, described above.

`templates` is the subpackage mapping questions to neighborhoods:

- `mapper.py` contains `Mapper`, 
whose `map(question)` method dispatches a `ContrastiveQuestion` to its matching neighborhood-mapping function.
- `insertion.py` contains the mapping functions for the `(Ins,*)` template family.

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

| Scope Restriction                             | Description                                                                                        | Symbols                                    | Constraint                                                             |
|-----------------------------------------------|----------------------------------------------------------------------------------------------------|--------------------------------------------|------------------------------------------------------------------------|
| `ImmediatePrecedence(predecessor, successor)` | Pins successor to occur immediately after predecessor, regardless of which employee performs them. | $p :=$ predecessor, $s :=$ successor       | $\sum_{e} U_{e,\,p,\,s} = 1$                                           |
| `SequenceOrderFixed(tasks)`                   | Keeps the relative order of a given, explicit, ordered list of tasks unchanged.                    | $\mathcal{S} :=$ tasks (an ordered list)   | $T_i + d_i \le T_j \quad \forall\, (i,j)$ consecutive in $\mathcal{S}$ |

## 3.2. `Operator` bank

| Operator                                                             | Description                                                                                       | Symbols                                                                 | Scope                          | Constraint                                                                                                                                             |
|----------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| `TaskInsertion(candidate_employees, candidate_tasks)`                | Inserts a candidate task into a candidate employee's sequence.                                    | $\mathcal{E} :=$ candidate_employees, $\mathcal{J} :=$ candidate_tasks  | $\mathcal{E} \cup \mathcal{J}$ | $\sum_{j \in \mathcal{J}} X_j = 1 \ \ \forall\, j \in \mathcal{J}$, $\sum_{e \in \mathcal{E},\,k} U_{e,\,j,\,k} = X_j \ \ \forall\, j \in \mathcal{J}$ |
| `TaskDeletion(candidate_employees, candidate_tasks)`                 | Removes a candidate task from a candidate employee's sequence.                                    | $\mathcal{E} :=$ candidate_employees, $\mathcal{J} :=$ candidate_tasks  | $\mathcal{E} \cup \mathcal{J}$ | not yet implemented in `NeighborhoodFeasibilityMILP`                                                                                                   |
| `TaskRelocation(origin_employee, destination_employee, target_task)` | Moves the target task from the origin employee's sequence to the destination employee's sequence. | $o :=$ origin_employee, $d :=$ destination_employee, $t :=$ target_task | $\{o,\, d,\, t\}$              | not yet implemented in `NeighborhoodFeasibilityMILP`                                                                                                   |

WIP: `TaskDeletion` and `TaskRelocation` exist as vocabulary — their `scope` is fully defined and already used by
`Neighborhood.scope` — but have no MILP formulation yet (see `src/explaining/README.md` section 1.2's
"Next steps").

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

**Design only — not yet implemented.**

WIP
