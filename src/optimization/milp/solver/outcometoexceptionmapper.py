# Local libraries
from src.optimization.milp.solver.exceptions import InfeasibleModelException, UnboundedModelException
from src.optimization.milp.solver.outcome import Outcome


############################
# OutcomeToExceptionMapper #
############################

class OutcomeToExceptionMapper:
    """
    Maps an Outcome that describes a plain failure (infeasible or unbounded) to the exception it
    warrants, leaving it up to the caller of solve() to decide whether to actually raise it.
    """

    @staticmethod
    def map(outcome: Outcome):
        """
        Return the exception the given outcome warrants, if any.

        Args:
            outcome: the outcome to interpret.

        Returns:
            an InfeasibleModelException or UnboundedModelException instance, or None if the outcome
            doesn't describe a plain failure (e.g. it succeeded, or it's a time-limit outcome, which
            solve() raises directly rather than routing through this mapper).
        """
        if outcome.is_infeasible:
            return InfeasibleModelException("The model is infeasible.")
        elif outcome.is_unbounded:
            return UnboundedModelException("The model is unbounded.")
        else:
            return None
