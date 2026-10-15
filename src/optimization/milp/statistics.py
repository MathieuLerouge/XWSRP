# Standard libraries
from collections import Counter
from typing import Optional

# Third-party library
import pyomo.environ as pyo

# Local library
from src.optimization.milp.solver.outcome import Outcome


##################
# MilpStatistics #
##################

class MilpStatistics:
    """
    Size snapshot of a built MILP model, along with how long it took to build and to solve.
    """

    def __init__(self, nb_binary_variables: int, nb_integer_variables: int, nb_continuous_variables: int,
                 nb_fixed_variables: int, nb_constraints_by_family: dict[str, int], nb_objectives: int,
                 build_time: float, solver_name: Optional[str] = None, solve_time: Optional[float] = None,
                 lexicographic_outcomes: Optional[list[tuple[str, Outcome]]] = None):
        """
        Args:
            nb_binary_variables: The number of binary variables.
            nb_integer_variables: The number of non-binary integer variables.
            nb_continuous_variables: The number of continuous variables.
            nb_fixed_variables: The number of variables fixed to a value, whatever their domain.
            nb_constraints_by_family: The number of constraints of each family,
                a family being a constraint's name without its bracketed indices (e.g. "FlowConstraint").
            nb_objectives: The number of objectives, counting each level of a lexicographic objective.
            build_time: The time taken to build the model, in seconds.
            solver_name: The name of the MILP backend the model was solved with (e.g. SOLVER_HIGHS),
                or None if it hasn't been solved yet.
            solve_time: The time taken to solve the model, in seconds, or None if it hasn't been solved yet.
            lexicographic_outcomes: The objective name and outcome of each level of a lexicographic solve,
                highest priority first, or None (no level) if the model hasn't been solved lexicographically yet.
        """
        self._nb_binary_variables = nb_binary_variables
        self._nb_integer_variables = nb_integer_variables
        self._nb_continuous_variables = nb_continuous_variables
        self._nb_fixed_variables = nb_fixed_variables
        self._nb_constraints_by_family: dict[str, int] = nb_constraints_by_family
        self._nb_objectives = nb_objectives
        self._build_time = build_time
        self._solver_name = solver_name
        self._solve_time = solve_time
        self._lexicographic_outcomes: list[tuple[str, Outcome]] = (
            lexicographic_outcomes if lexicographic_outcomes is not None else []
        )

    @staticmethod
    def from_pyomo_model(model: pyo.ConcreteModel, nb_objectives: int, build_time: float) -> 'MilpStatistics':
        """
        Take the size snapshot of a Pyomo model.

        NB: To be taken before solving it, since a lexicographic solve adds freezing constraints to the model.

        Args:
            model: The Pyomo model, fully built.
            nb_objectives: The number of objectives, which the caller passes since a lexicographic objective
                is only declared on the Pyomo model while being solved.
            build_time: The time taken to build the model, in seconds.

        Returns:
            The statistics describing the model, with no solve time yet.
        """
        # NB: Counted directly rather than with pyomo.util.model_size.build_model_size_report,
        # which walks every constraint's expression and costs about a third of the model's build time.
        nb_binary_variables, nb_integer_variables, nb_continuous_variables, nb_fixed_variables = 0, 0, 0, 0
        for variable in model.component_data_objects(pyo.Var):
            if variable.is_binary():
                nb_binary_variables += 1
            elif variable.is_integer():
                nb_integer_variables += 1
            else:
                nb_continuous_variables += 1
            if variable.fixed:
                nb_fixed_variables += 1
        # NB: local_name, unlike name, is not quoted when it holds brackets (e.g. 'Flow[1,2]', not "'Flow[1,2]'").
        nb_constraints_by_family = Counter(
            constraint.local_name.split('[')[0]
            for constraint in model.component_data_objects(pyo.Constraint, active=True)
        )
        return MilpStatistics(
            nb_binary_variables, nb_integer_variables, nb_continuous_variables, nb_fixed_variables,
            dict(nb_constraints_by_family), nb_objectives, build_time
        )

    #############
    # Variables #
    #############

    @property
    def nb_variables(self) -> int:
        """The number of variables, whatever their domain."""
        return self._nb_binary_variables + self._nb_integer_variables + self._nb_continuous_variables

    @property
    def nb_binary_variables(self) -> int:
        """The number of binary variables."""
        return self._nb_binary_variables

    @property
    def nb_integer_variables(self) -> int:
        """The number of non-binary integer variables."""
        return self._nb_integer_variables

    @property
    def nb_continuous_variables(self) -> int:
        """The number of continuous variables."""
        return self._nb_continuous_variables

    @property
    def nb_fixed_variables(self) -> int:
        """The number of variables fixed to a value, whatever their domain."""
        return self._nb_fixed_variables

    ###############
    # Constraints #
    ###############

    @property
    def nb_constraints(self) -> int:
        """The number of constraints."""
        return sum(self._nb_constraints_by_family.values())

    @property
    def nb_constraints_by_family(self) -> dict[str, int]:
        """The number of constraints of each family."""
        return self._nb_constraints_by_family

    def count_constraints_in_families_starting_with(self, prefix: str) -> int:
        """
        Count the constraints whose family starts with the given prefix.

        Args:
            prefix: The prefix of the families to count the constraints of (e.g. "Neighborhood").

        Returns:
            The number of such constraints.
        """
        return sum(
            nb_constraints for family, nb_constraints in self._nb_constraints_by_family.items()
            if family.startswith(prefix)
        )

    ##############
    # Objectives #
    ##############

    @property
    def nb_objectives(self) -> int:
        """The number of objectives, counting each level of a lexicographic objective."""
        return self._nb_objectives

    ##########
    # Solver #
    ##########

    @property
    def solver_name(self) -> Optional[str]:
        """The name of the MILP backend the model was solved with, or None if it hasn't been solved yet."""
        return self._solver_name

    @solver_name.setter
    def solver_name(self, solver_name: str):
        self._solver_name = solver_name

    #########
    # Times #
    #########

    @property
    def build_time(self) -> float:
        """The time taken to build the model, in seconds."""
        return self._build_time

    @property
    def solve_time(self) -> Optional[float]:
        """The time taken to solve the model, in seconds, or None if it hasn't been solved yet."""
        return self._solve_time

    @solve_time.setter
    def solve_time(self, solve_time: float):
        self._solve_time = solve_time

    #######################
    # Lexicographic solve #
    #######################

    @property
    def lexicographic_outcomes(self) -> list[tuple[str, Outcome]]:
        """
        The objective name and outcome of each level of a lexicographic solve, highest priority first.

        Only the levels actually solved are listed:
        the solve stops at a level finding no incumbent or using up the time limit,
        so there can be fewer than nb_objectives of them.
        Empty if the model hasn't been solved lexicographically.
        """
        return self._lexicographic_outcomes

    @lexicographic_outcomes.setter
    def lexicographic_outcomes(self, lexicographic_outcomes: list[tuple[str, Outcome]]):
        self._lexicographic_outcomes = lexicographic_outcomes
