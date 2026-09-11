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
    - the employees whose sequences are in scope;
    - the elementary operators that may transform those sequences;
    - and the elementary constraints that restrict how they may be transformed.

    An employee is in scope exactly when they appear in employees:
    their sequence is eligible to be examined and modified by the solvable model obtained from this Neighborhood.
    How much of it can vary is then governed by their own operators and constraint:
    • When neither is present (e.g. the neighborhood related to "why not perform this route in another order"
    has one employee in scope but no operator or constraint) the sequence is fully free to be reordered;
    • Under SequenceOrderFixed, the sequence is order-preserving but open to the operators' insertions/deletions/relocations;
    • under SequenceFixed, it is entirely pinned despite being in scope.

    An employee not listed in employees is out of scope:
    their entire sequence, which tasks they perform, in what order, and at what times, is treated as fixed,
    and is reproduced unchanged rather than searched at all.
    An employee should simply be left out of employees whenever there is no need to reason about them at all.

    Two operators within the same Neighborhood that must resolve a shared candidate dimension to the same value
    (e.g. an insertion and a deletion that must act on the same, otherwise-unspecified employee)
    are expected to be given the identical frozenset object for that dimension, not merely an equal one:
    the MILP builder that later turns this Neighborhood into a solvable model relies on that object identity to
    detect the link.
    """

    def __init__(self, solution: Solution, employees: list[Employee], operators: list[NeighborhoodOperator],
                 constraints: Optional[list[NeighborhoodConstraint]] = None):
        """
        Args:
            solution: The solution this neighborhood is defined relative to.
            employees: The employees whose sequences are in scope for this neighborhood.
            operators: The elementary operators that may transform the in-scope sequences.
            constraints: The elementary constraints that restrict how the in-scope sequences may be
                transformed.

        Raises:
            ValueError: If employees is empty,
                if an operator or a constraint concerns an employee not listed in employees,
                if an employee targeted by an operator also carries a SequenceFixed constraint,
                or if an employee carrying a SequenceFixed constraint also carries another constraint.
        """
        if len(employees) == 0:
            raise ValueError("employees must not be empty")
        if constraints is None:
            constraints = []
        self._solution = solution
        self._employees: frozenset[Employee] = frozenset(employees)
        self._operators: list[NeighborhoodOperator] = operators
        self._constraints: list[NeighborhoodConstraint] = constraints
        self._check_consistency()

    def _check_consistency(self):
        """
        Check that:
        - every operator and constraint concerns an employee listed in this neighborhood's employees;
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
            if constraint.employee not in self._employees:
                raise ValueError(f"Constraint on employee {constraint.employee.name} "
                                 f"who is not listed in this neighborhood's employees")
            constraints_by_employee.setdefault(constraint.employee, []).append(constraint)
        for employee, employee_constraints in constraints_by_employee.items():
            if len(employee_constraints) > 1 and any(
                    isinstance(constraint, SequenceFixed) for constraint in employee_constraints):
                raise ValueError(f"Employee {employee.name} carries a SequenceFixed constraint "
                                 f"together with another constraint")
        for operator in self._operators:
            for employee in operator.employees:
                if employee not in self._employees:
                    raise ValueError(f"Operator on employee {employee.name} "
                                     f"who is not listed in this neighborhood's employees")
                if any(isinstance(constraint, SequenceFixed)
                       for constraint in constraints_by_employee.get(employee, [])):
                    raise ValueError(f"Employee {employee.name} is targeted by an operator "
                                     f"but also carries a SequenceFixed constraint")

    @property
    def solution(self):
        """The solution this neighborhood is defined relative to."""
        return self._solution

    @property
    def employees(self):
        """The employees whose sequences are in scope for this neighborhood."""
        return self._employees

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
