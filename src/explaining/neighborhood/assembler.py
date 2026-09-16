# Local libraries
from src.explaining.computing.model import NeighborhoodModel
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
    deferring to NeighborhoodModel to check whether it's actually one NeighborhoodModel can solve
    - the single source of truth for "not supported yet", so this step never re-derives its own capability list..
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
                Whoever actually solves the neighborhood afterward will build a NeighborhoodModel again
                - a known deliberate inefficiency (model construction is cheap relative to solving),
                rather than threading the already-built model back out through this method's return type.

        Raises:
            NeighborhoodError: If operators and restrictions are both empty,
                or NeighborhoodModel doesn't support the resulting Neighborhood yet.
        """
        try:
            neighborhood = Neighborhood(solution, operators, restrictions)
        except ValueError as error:
            raise NeighborhoodError() from error
        try:
            NeighborhoodModel(neighborhood)
        except NotImplementedError as error:
            raise NeighborhoodError() from error
        return neighborhood
