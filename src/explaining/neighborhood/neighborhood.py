# Standard library
from typing import Optional

# Local libraries
from src.explaining.neighborhood.operator import Operator
from src.explaining.neighborhood.restriction import Restriction
from src.modeling.employee import Employee
from src.modeling.solution import Solution


################
# Neighborhood #
################

class Neighborhood:
    """
    A search space around a solution, defined by:
    - the elementary operators that may transform its scope's employees' sequences;
    - and the elementary scope restrictions that narrow how they may be transformed.

    The neighborhood's scope is deduced from its operators' own scope alone.
    Restrictions narrow freedom already granted elsewhere, they never contribute to scope themselves.
    An employee in scope has their sequence eligible to be modified by the model obtained from this Neighborhood;
    a task in scope is individually free to be added/removed/relocated,
    even if its current employee (if any) is not itself in scope.

    How much an in-scope employee's sequence can vary is governed by their own operators and restrictions:
    • With no restriction (e.g. an employee solely targeted by a TaskInsertion/TaskDeletion/TaskRelocation operator),
      the sequence is fully free to be reordered;
    • Under PrecedenceChain, the sequence is order-preserving but open to the operators' insertions,
      deletions and relocations.

    An employee or task not in scope is fixed:
    • for an employee, their entire sequence, which tasks they perform, in what order, and at what times,
    is reproduced unchanged rather than searched at all;
    • for a task belonging to an out-of-scope employee, it stays exactly where and when it currently is.
    """

    def __init__(self, solution: Solution, operators: list[Operator],
                 restrictions: Optional[list[Restriction]] = None):
        """
        Args:
            solution: The solution this neighborhood is defined relative to.
            operators: The elementary operators that may transform the in-scope sequences.
            restrictions: The elementary scope restrictions that narrow how the in-scope sequences may be
                transformed.

        Raises:
            ValueError: If operators and restrictions are both empty (there would be nothing to search).
        """
        if restrictions is None:
            restrictions = []
        if len(operators) == 0 and len(restrictions) == 0:
            raise ValueError("operators and restrictions must not both be empty")
        self._solution = solution
        self._operators: list[Operator] = operators
        self._restrictions: list[Restriction] = restrictions

    @property
    def solution(self):
        """The solution this neighborhood is defined relative to."""
        return self._solution

    @property
    def scope(self):
        """The employees and tasks in scope for this neighborhood, deduced from its operators' own scope."""
        return frozenset().union(*[operator.scope for operator in self._operators])

    @property
    def employees(self):
        """The employees in scope for this neighborhood, as a frozenset."""
        return frozenset(entity for entity in self.scope if isinstance(entity, Employee))

    @property
    def operators(self):
        """The elementary operators that may transform the in-scope sequences."""
        return self._operators

    @property
    def restrictions(self):
        """The elementary scope restrictions that narrow how the in-scope sequences may be transformed."""
        return self._restrictions

    @property
    def target_tasks(self):
        """The tasks targeted by this neighborhood's operators."""
        return frozenset().union(*[operator.target_tasks for operator in self._operators])
