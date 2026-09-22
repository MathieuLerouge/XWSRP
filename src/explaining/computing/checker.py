# Standard library
from typing import Optional

# Local libraries
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import (
    Operator, SequenceReordering, TaskDeletion, TaskInsertion, TaskRepositioning
)
from src.explaining.neighborhood.restriction import ImmediatePrecedence


#############################
# ModelCompatibilityChecker #
#############################

class ModelCompatibilityChecker:
    """
    Stateless collection of static methods telling whether a Neighborhood is compatible with NeighborhoodModel,
    i.e. one that NeighborhoodModel can be built for, and saying why when it is not.

    WIP: As NeighborhoodModel grows, neighborhoods that were previously incompatible could become compatible.
    """

    @staticmethod
    def unsupported_reason(neighborhood: Neighborhood) -> Optional[str]:
        """
        Return why NeighborhoodModel cannot be built for the given neighborhood, or None if it can.

        Args:
            neighborhood: The neighborhood to check.

        Returns:
            A user-facing explanation of the first limit the neighborhood runs into, or None if it runs into
            none of them.
        """
        instance = neighborhood.solution.instance
        if instance.has_lunch_break:
            return "NeighborhoodModel does not support instances with a lunch break"
        if instance.must_cover_all_tasks:
            return "NeighborhoodModel does not support instances whose tasks must all be covered"
        if len(neighborhood.operators) not in (1, 2):
            return "NeighborhoodModel currently only supports a neighborhood with one or two operators"
        feasibility_shortfall_operator = None
        deletion_operator = None
        for candidate_operator in neighborhood.operators:
            if isinstance(candidate_operator, TaskDeletion):
                if deletion_operator is not None:
                    return "NeighborhoodModel does not support more than one TaskDeletion operator"
                deletion_operator = candidate_operator
            elif isinstance(candidate_operator, (TaskInsertion, TaskRepositioning, SequenceReordering)):
                if feasibility_shortfall_operator is not None:
                    return ("NeighborhoodModel does not support more than one TaskInsertion, "
                            "TaskRepositioning or SequenceReordering operator")
                feasibility_shortfall_operator = candidate_operator
            else:
                return ("NeighborhoodModel currently only supports TaskInsertion, TaskDeletion, "
                        "TaskRepositioning or SequenceReordering operators")
        if feasibility_shortfall_operator is None:
            return ("NeighborhoodModel requires a TaskInsertion, TaskRepositioning or "
                    "SequenceReordering operator alongside TaskDeletion")
        has_immediate_precedence = any(
            isinstance(restriction, ImmediatePrecedence) for restriction in neighborhood.restrictions
        )
        if has_immediate_precedence and _has_several_candidates(feasibility_shortfall_operator):
            return ("NeighborhoodModel does not support an ImmediatePrecedence restriction together "
                    "with more than one candidate employee or candidate task")
        return None

    @staticmethod
    def is_compatible(neighborhood: Neighborhood) -> bool:
        """
        Return whether NeighborhoodModel can be built for the given neighborhood.

        Args:
            neighborhood: The neighborhood to check.

        Returns:
            Whether it runs into none of NeighborhoodModel's limits.
        """
        return ModelCompatibilityChecker.unsupported_reason(neighborhood) is None


###########
# Helpers #
###########

def _has_several_candidates(feasibility_shortfall_operator: Operator) -> bool:
    """
    Return whether the given feasibility-shortfall operator offers more than one candidate employees
    or more than one candidate task.

    Args:
        feasibility_shortfall_operator: The operator the feasibility shortfall would be attached to.

    Returns:
        Whether it leaves either side of the pairing open.
    """
    if not isinstance(feasibility_shortfall_operator, TaskInsertion):
        return False
    return (len(feasibility_shortfall_operator.candidate_employees) > 1
            or len(feasibility_shortfall_operator.candidate_tasks) > 1)