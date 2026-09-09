# Local library
from src.optimization.milp.solver.outcome import Outcome


##################
# SolveException #
##################

class SolveException(Exception):
    """Base class for exceptions describing a MILP solve that didn't produce a usable result."""
    pass


############################
# InfeasibleModelException #
############################

class InfeasibleModelException(SolveException):
    """Raised when the solver proves a model infeasible."""
    pass


###########################
# UnboundedModelException #
###########################

class UnboundedModelException(SolveException):
    """Raised when the solver proves a model unbounded."""
    pass


#########################################
# TimeLimitReachedWithSolutionException #
#########################################

class TimeLimitReachedWithSolutionException(SolveException):
    """Raised when the solving time limit is reached with a feasible solution found."""

    def __init__(self, outcome: Outcome, message="Time limit was reached but a feasible solution was found"):
        """
        Args:
            outcome: the Outcome describing the time-limited solve, including its solution.
            message: the exception's message.
        """
        self.outcome = outcome
        self.message = message
        super().__init__(message)


############################################
# TimeLimitReachedWithoutSolutionException #
############################################

class TimeLimitReachedWithoutSolutionException(SolveException):
    """Raised when the solving time limit is reached with no feasible solution found."""

    def __init__(self, message="No solution was found before time limit was reached"):
        """
        Args:
            message: the exception's message.
        """
        super().__init__(message)
