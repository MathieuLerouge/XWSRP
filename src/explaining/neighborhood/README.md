# Description of the `neighborhood` module

This module implements a vocabulary for describing a search space around a solution: a `Neighborhood`.
It is as an alternative to `computing/templates`' per-template tailored transformation functions. \
It backs `computing/model.py`'s `NeighborhoodFeasibilityMILP`, which turns a `Neighborhood` into a solvable MILP.


# 1. Overview of the neighborhood abstraction

A `Neighborhood` (`neighborhood.py`) is defined by two things: 
the `operators` that may transform its scope's sequences, and the `constraints` that restrict how. \
Its `scope` — the employees and tasks it frees from being fixed to their current state — 
is entirely deduced from its operators' and constraints' own `scope`. \
`operators` and `constraints` are both built out of `NeighborhoodPrimitive` (`primitive.py`), 
the common base exposing each primitive's own `scope`.

A `NeighborhoodOperator` (`operator.py`) is an elementary transformation: 
`TaskInsertion` (insert a candidate task into a candidate employee's sequence), 
`TaskDeletion` (remove a candidate task from a candidate employee's sequence), 
or `TaskRelocation` (move a single target task from an origin employee's sequence to a destination one). \
Its `scope` is its own candidate employees/tasks (or, for `TaskRelocation`, its origin/destination employees and target task).

A `NeighborhoodConstraint` (`constraint.py`) restricts a single employee's sequence: 
`SequenceOrderFixed` keeps the relative order of their already-performed tasks unchanged 
(only tasks in scope may be added/removed/repositioned), `SequenceFixed` pins their sequence entirely, 
and `ImmediatePrecedence` pins one activity to occur immediately after another 
(its `scope` is just the restricted `employee`, not the referenced `predecessor`/`successor`, 
which it constrains rather than frees). \
An in-`scope` employee carrying none of these has their sequence fully free to be reordered. 
An employee or task not in `scope` is fixed and reproduced unchanged 
— for an out-of-scope employee, their entire sequence; for a task belonging to one, its assignment and timing.

Constraints are composable: an employee may carry several of them at once 
(e.g. `SequenceOrderFixed` together with one or more `ImmediatePrecedence`), 
except that `SequenceFixed` must be an employee's only constraint, 
since it already pins their sequence entirely.

The `templates` subpackage maps a `Question` to the `Neighborhood` it induces: `Mapper` (`mapper.py`)
dispatches on the question's template id to a dedicated mapping function, implemented per question family
(`insertion.py` for the `(Ins,*)` family — see section 3).


# 2. Description of the files

`primitive.py` contains `NeighborhoodPrimitive`, the abstract base shared by operators and constraints.

`operator.py` contains `NeighborhoodOperator` and its subclasses: 
`TaskInsertion`, `TaskDeletion` and `TaskRelocation`, described above.

`constraint.py` contains `NeighborhoodConstraint` and its subclasses: 
`SequenceOrderFixed`, `SequenceFixed` and `ImmediatePrecedence`, described above.

`neighborhood.py` contains `Neighborhood`, described above.

`templates` is the subpackage mapping questions to neighborhoods:

- `mapper.py` contains `Mapper`, 
whose `map(question)` method dispatches a `ContrastiveQuestion` to its matching neighborhood-mapping function.
- `insertion.py` contains the mapping functions for the `(Ins,*)` template family.


# 3. Mapping the `(Ins,*)` contrastive questions to neighborhoods

Each `(Ins,*)` question asks why a task isn't inserted somewhere. 
Every mapping below therefore induces a `Neighborhood` with a `TaskInsertion` operator, 
differing in which employee(s) it targets, what the operator's candidates are, 
and which constraints keep the rest of each targeted employee's sequence untouched — 
`(Ins,1)` additionally pins the insertion point via an `ImmediatePrecedence` constraint. \
In every row, the resulting `Neighborhood.scope` is exactly the operator's own candidate employees and candidate tasks 
— the constraints listed restrict how that scope may vary, they don't add to it.

| Template   | Question                                                                                                                                         | Operator                                         | Constraints                                                                             |
|------------|--------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|-----------------------------------------------------------------------------------------|
| `(Ins,1)`  | Why is employee {Employee} not performing task {Task} just after activity {Activity}?                                                            | `TaskInsertion({employee}, {task})`              | `SequenceOrderFixed({employee})`, `ImmediatePrecedence({employee}, {activity}, {task})` |
| `(Ins,2a)` | Why is employee {Employee} not performing task {Task} between two consecutive activities of their route?                                         | `TaskInsertion({employee}, {task})`              | `SequenceOrderFixed({employee})`                                                        |
| `(Ins,2b)` | Why is employee {Employee} not performing any non-performed task between two consecutive activities of their route?                              | `TaskInsertion({employee}, non_performed_tasks)` | `SequenceOrderFixed({employee})`                                                        |
| `(Ins,2c)` | Why is any employee not performing task {Task} between two consecutive activities of their route?                                                | `TaskInsertion(employees, {task})`               | `SequenceOrderFixed(employees)`                                                         |
| `(Ins,3)`  | Why is employee {Employee} not performing task {Task} in addition to their already-performed activities (even if it means changing their order)? | `TaskInsertion({employee}, {task})`              | none — order left free                                                                  |

`(Ins,2b)` additionally raises `ImpossibleTransformationException` when the solution already performs every task, 
since there is then no non-performed task left to offer as a candidate.


# 4. Mapping the `(Swp,*)` contrastive questions to neighborhoods

WIP


# 5. Mapping the `(Ord,*)` contrastive questions to neighborhoods

WIP
