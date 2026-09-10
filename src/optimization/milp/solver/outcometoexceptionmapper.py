# Local libraries
from src.optimization.milp.solver.exceptions import InfeasibleModelException, UnboundedModelException, \
    TimeLimitReachedWithSolutionException, TimeLimitReachedWithoutSolutionException
from src.optimization.milp.solver.outcome import Outcome


############################
# OutcomeToExceptionMapper #
############################

class OutcomeToExceptionMapper:
    """
    Maps an Outcome that describes a failure (infeasible, unbounded, or a time limit) to the
    exception it warrants, leaving it up to the caller of solve() to decide whether to actually
    raise it.
    """

    @staticmethod
    def map(outcome: Outcome):
        """
        Return the exception the given outcome warrants, if any.

        Args:
            outcome: the outcome to interpret.

        Returns:
            an InfeasibleModelException, UnboundedModelException, TimeLimitReachedWithSolutionException
            or TimeLimitReachedWithoutSolutionException instance, or None if the outcome describes a
            plain success.
        """
        if outcome.is_infeasible:
            return InfeasibleModelException("The model is infeasible.")
        elif outcome.is_unbounded:
            return UnboundedModelException("The model is unbounded.")
        elif outcome.is_time_limit:
            if outcome.has_incumbent:
                return TimeLimitReachedWithSolutionException(outcome)
            else:
                return TimeLimitReachedWithoutSolutionException()
        else:
            return None
