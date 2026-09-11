# Standard library
from typing import Optional

# Local libraries
from src.explaining.neighborhood.constraint import NeighborhoodConstraint, SequenceFixed
from src.explaining.neighborhood.operator import NeighborhoodOperator
from src.modeling.employee import Employee
from src.modeling.solution import Solution


################
# Neighborhood #
################

class Neighborhood:
    """
    A search space around a solution, defined by:
    - the elementary operators that may transform its scope's employees' sequences;
    - and the elementary constraints that restrict how they may be transformed.

    The neighborhood's scope is deduced from the operators' and constraints' own scopes.
    An employee in scope has their sequence eligible to be modified by the model obtained from this Neighborhood;
    a task in scope is individually free to be added/removed/relocated,
    even if its current employee (if any) is not itself in scope.

    How much an in-scope employee's sequence can vary is governed by their own operators and constraints:
    • With no constraint (e.g. an employee solely targeted by a TaskInsertion/TaskDeletion/TaskRelocation operator),
      the sequence is fully free to be reordered;
    • Under SequenceOrderFixed, the sequence is order-preserving but open to the operators' insertions/deletions/relocations;
    • Under SequenceFixed, it is entirely pinned despite being in scope.

    An employee or task not in scope is fixed:
    • for an employee, their entire sequence, which tasks they perform, in what order, and at what times,
    is reproduced unchanged rather than searched at all;
    • for a task belonging to an out-of-scope employee, it stays exactly where and when it currently is.
    """

    def __init__(self, solution: Solution, operators: list[NeighborhoodOperator],
                 constraints: Optional[list[NeighborhoodConstraint]] = None):
        """
        Args:
            solution: The solution this neighborhood is defined relative to.
            operators: The elementary operators that may transform the in-scope sequences.
            constraints: The elementary constraints that restrict how the in-scope sequences may be transformed.

        Raises:
            ValueError: If operators and constraints are both empty (there would be nothing to deduce a scope from),
                if an employee targeted by an operator also carries a SequenceFixed constraint,
                or if an employee carrying a SequenceFixed constraint also carries another constraint.
        """
        if constraints is None:
            constraints = []
        if len(operators) == 0 and len(constraints) == 0:
            raise ValueError("operators and constraints must not both be empty")
        self._solution = solution
        self._operators: list[NeighborhoodOperator] = operators
        self._constraints: list[NeighborhoodConstraint] = constraints
        self._check_consistency()

    def _check_consistency(self):
        """
        Check that:
        - no employee carrying a SequenceFixed constraint also carries another constraint,
          since SequenceFixed already pins their sequence entirely;
        - and that no employee is both targeted by an operator and restricted by a SequenceFixed constraint.
        Constraints are otherwise composable: an employee may carry any number of them
        (e.g. one SequenceOrderFixed together with one or more ImmediatePrecedence).

        Raises:
            ValueError: If any of the above checks fails.
        """
        constraints_by_employee: dict[Employee, list[NeighborhoodConstraint]] = dict()
        for constraint in self._constraints:
            constraints_by_employee.setdefault(constraint.employee, []).append(constraint)
        for employee, employee_constraints in constraints_by_employee.items():
            if (len(employee_constraints) > 1 and
                any(isinstance(constraint, SequenceFixed) for constraint in employee_constraints)):
                raise ValueError(f"Employee {employee.name} carries a SequenceFixed constraint "
                                 f"together with another constraint")
        for operator in self._operators:
            for entity in operator.scope:
                if (isinstance(entity, Employee) and
                    any(isinstance(constraint, SequenceFixed)
                        for constraint in constraints_by_employee.get(entity, []))):
                    raise ValueError(f"Employee {entity.name} is targeted by an operator "
                                     f"but also carries a SequenceFixed constraint")

    @property
    def solution(self):
        """The solution this neighborhood is defined relative to."""
        return self._solution

    @property
    def scope(self):
        """The employees and tasks in scope for this neighborhood, deduced from its operators and constraints."""
        return frozenset().union(*[primitive.scope for primitive in self._operators + self._constraints])

    @property
    def employees(self):
        """The employees in scope for this neighborhood, as a frozenset."""
        return frozenset(entity for entity in self.scope if isinstance(entity, Employee))

    @property
    def operators(self):
        """The elementary operators that may transform the in-scope sequences."""
        return self._operators

    @property
    def constraints(self):
        """The elementary constraints that restrict how the in-scope sequences may be transformed."""
        return self._constraints

    @property
    def target_tasks(self):
        """The tasks targeted by this neighborhood's operators."""
        return frozenset().union(*[operator.target_tasks for operator in self._operators])
