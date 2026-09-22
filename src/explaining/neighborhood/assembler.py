# Local libraries
from src.explaining.computing.checker import ModelCompatibilityChecker
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import Operator
from src.explaining.neighborhood.restriction import Restriction
from src.modeling.solution import Solution


#############
# Assembler #
#############

class Assembler:
    """
    Assembles operators/restrictions into a Neighborhood,
    deferring to ModelCompatibilityChecker to check whether it's actually one NeighborhoodModel can solve
    - the single source of truth for "not supported yet", so this step never re-derives its own capability list.
    """

    @staticmethod
    def assemble(operators: list[Operator], restrictions: list[Restriction], solution: Solution) -> Neighborhood:
        """
        Args:
            operators: The operators to assemble into a Neighborhood.
            restrictions: The restrictions to assemble into a Neighborhood.
            solution: The solution the neighborhood is defined relative to.

        Returns:
            Neighborhood: The assembled neighborhood.

        Raises:
            NeighborhoodError: If operators and restrictions are both empty,
                or NeighborhoodModel doesn't support the resulting Neighborhood yet.

        NB: only the capability limits ModelCompatibilityChecker knows about are caught here.
        """
        try:
            neighborhood = Neighborhood(solution, operators, restrictions)
        except ValueError as error:
            raise NeighborhoodError() from error
        unsupported_reason = ModelCompatibilityChecker.unsupported_reason(neighborhood)
        if unsupported_reason is not None:
            raise NeighborhoodError(unsupported_reason)
        return neighborhood
