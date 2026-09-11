# Description of the `neighborhood` module

This module implements a vocabulary for describing a search space around a solution: a `Neighborhood`.
It is as an alternative to `computing/templates`' per-template tailored transformation functions. \
It backs `computing/model.py`'s `NeighborhoodFeasibilityMILP`, which turns a `Neighborhood` into a solvable MILP.


# 1. Overview of the neighborhood abstraction

A `Neighborhood` (`neighborhood.py`) is defined by three things: 
the `employees` whose sequences are in scope, the `operators` that may transform those sequences, 
and the `constraints` that restrict how. \
`operators` and `constraints` are both built out of `NeighborhoodPrimitive` (`primitive.py`), the common
base exposing which `employees` a primitive concerns.

A `NeighborhoodOperator` (`operator.py`) is an elementary transformation: 
`TaskInsertion` (insert a candidate task into a candidate employee's sequence), 
`TaskDeletion` (remove a candidate task from a candidate employee's sequence), 
or `TaskRelocation` (move a single target task from an origin employee's sequence to a destination one).

A `NeighborhoodConstraint` (`constraint.py`) restricts a single employee's sequence: 
`SequenceOrderFixed` keeps the relative order of their already-performed tasks unchanged 
(only tasks targeted by an operator may be added/removed/repositioned), 
while `SequenceFixed` pins their sequence entirely. 
An in-scope employee carrying neither constraint has their sequence fully free to be reordered. 
An employee not listed in `employees` at all is out of scope and reproduced unchanged.

The `templates` subpackage maps a `Question` to the `Neighborhood` it induces: `Mapper` (`mapper.py`)
dispatches on the question's template id to a dedicated mapping function, implemented per question family
(`insertion.py` for the `(Ins,*)` family — see section 3).


# 2. Description of the files

`primitive.py` contains `NeighborhoodPrimitive`, the abstract base shared by operators and constraints.

`operator.py` contains `NeighborhoodOperator` and its subclasses: 
`TaskInsertion`, `TaskDeletion` and `TaskRelocation`, described above.

`constraint.py` contains `NeighborhoodConstraint` and its subclasses: 
`SequenceOrderFixed` and `SequenceFixed`, described above.

`neighborhood.py` contains `Neighborhood`, described above.

`templates` is the subpackage mapping questions to neighborhoods:

- `mapper.py` contains `Mapper`, 
whose `map(question)` method dispatches a `ContrastiveQuestion` to its matching neighborhood-mapping function.
- `insertion.py` contains the mapping functions for the `(Ins,*)` template family.


# 3. Mapping the `(Ins,*)` contrastive questions to neighborhoods

Each `(Ins,*)` question asks why a task isn't inserted somewhere. 
Every mapping below therefore induces a `Neighborhood` with a single `TaskInsertion` operator, 
differing in which employees are in scope, what the operator's candidates are, whether the insertion point is anchored, 
and which `SequenceOrderFixed` constraints keep the rest of each in-scope employee's sequence untouched.

| Template   | Question (English)                                                                                                     | Mapping function | Employees in scope | `TaskInsertion` candidates                              | Anchor                          | Constraints                                    |
|------------|-------------------------------------------------------------------------------------------------------------------------|-------------------|--------------------|-----------------------------------------------------------|----------------------------------|-------------------------------------------------|
| `(Ins,1)`  | Why is employee {Employee} not performing task {Task} just after activity {Activity}?                                  | `map_ins_1`       | `{employee}`       | employees: `{employee}`; tasks: `{task}`                  | just after `{activity}`         | `SequenceOrderFixed({employee})`                 |
| `(Ins,2a)` | Why is employee {Employee} not performing task {Task} between two consecutive activities of their route?               | `map_ins_2a`      | `{employee}`       | employees: `{employee}`; tasks: `{task}`                  | none (anywhere in the sequence) | `SequenceOrderFixed({employee})`                 |
| `(Ins,2b)` | Why is employee {Employee} not performing any non-performed task between two consecutive activities of their route?    | `map_ins_2b`      | `{employee}`       | employees: `{employee}`; tasks: every non-performed task   | none                             | `SequenceOrderFixed({employee})`                 |
| `(Ins,2c)` | Why is any employee not performing task {Task} between two consecutive activities of their route?                      | `map_ins_2c`      | every employee     | employees: every employee; tasks: `{task}`                 | none                             | `SequenceOrderFixed(e)` for every employee `e`   |
| `(Ins,3)`  | Why is employee {Employee} not performing task {Task} in addition to their already-performed activities (even if it means changing their order)? | `map_ins_3`       | `{employee}`       | employees: `{employee}`; tasks: `{task}`                  | none                             | none — order left free                           |

`(Ins,2b)` additionally raises `ImpossibleTransformationException` when the solution already performs every task, 
since there is then no non-performed task left to offer as a candidate.
