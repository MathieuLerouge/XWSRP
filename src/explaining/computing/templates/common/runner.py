# Local libraries
from src.optimization.milp.solver.outcometoexceptionmapper import OutcomeToExceptionMapper
from src.optimization.milp.subproblems.sequencemodel import SequenceModel


############################
# MILPTransformationRunner #
############################

class MILPTransformationRunner:
    """
    Runs the MILP models computing transformations, turning a solve outcome holding no usable solution into a raise.
    """

    @staticmethod
    def solve_or_raise(model: SequenceModel):
        """
        Solve the given model, and raise whichever exception its outcome warrants.

        Args:
            model: The MILP model computing the transformation.

        Raises:
            InfeasibleModelException: if the model has no feasible solution.
            UnboundedModelException: if the model is unbounded.
            TimeLimitReachedWithSolutionException: if the solving time limit was reached, with an incumbent found.
            TimeLimitReachedWithoutSolutionException: if the solving time limit was reached with no incumbent.
        """
        solve_outcome = model.solve(mute=True)
        exception = OutcomeToExceptionMapper.map(solve_outcome)
        if exception is not None:
            raise exception
