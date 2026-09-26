# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.conflict import Conflict
from src.explaining.modeling.instance_changes import InstanceChanges
from src.modeling.solution import Solution


########################
# TransformationResult #
########################

class TransformationResult:
    """
    Everything the transformation induced by a question produces, for an explanation to be built from.
    """

    def __init__(self, support_solution: Solution, conflict: Optional[Conflict], descriptions: dict[str, str],
                 instance_alterations: Optional[InstanceChanges] = None):
        """
        Return the result of a transformation applied to a solution.

        Args:
            support_solution: The solution the transformation produced.
            conflict: The conflict making the transformation infeasible, or None when it is feasible.
            descriptions: The text describing the applied transformation, keyed by language.
            instance_alterations: The instance parameter changes the transformation needed to become feasible.
                Only counterfactual transformations alter the instance; the other kinds leave this None.
        """
        self._support_solution = support_solution
        self._conflict = conflict
        self._descriptions: dict[str, str] = descriptions
        self._instance_alterations = instance_alterations

    @property
    def support_solution(self) -> Solution:
        """The solution the transformation produced."""
        return self._support_solution

    @property
    def conflict(self) -> Optional[Conflict]:
        """The conflict making the transformation infeasible, or None when it is feasible."""
        return self._conflict

    @property
    def descriptions(self) -> dict[str, str]:
        """The text describing the applied transformation, keyed by language."""
        return self._descriptions

    @property
    def instance_alterations(self) -> Optional[InstanceChanges]:
        """The instance parameter changes the transformation needed, or None when it needed none."""
        return self._instance_alterations
