# Local libraries
from src.explaining.neighborhood.primitive import NeighborhoodPrimitive
from src.modeling.employee import Employee


##########################
# NeighborhoodConstraint #
##########################

class NeighborhoodConstraint(NeighborhoodPrimitive):
    """
    An elementary constraints on how a single employee's sequence must be transformed within a Neighborhood.
    """

    def __init__(self, employee: Employee):
        """
        Args:
            employee: The employee whose sequence this constraint restricts.
        """
        self._employee = employee

    @property
    def employee(self):
        """The employee whose sequence this constraint restricts."""
        return self._employee

    @property
    def employees(self):
        """The employee this constraint restricts, as a single-element set."""
        return frozenset({self._employee})


######################
# SequenceOrderFixed #
######################

class SequenceOrderFixed(NeighborhoodConstraint):
    """
    A NeighborhoodConstraint requiring that the order of the employee's already-performed tasks stays unchanged.
    Only the tasks targeted by an operator may be added, removed, or repositioned;
    without this constraint, an employee in scope has their sequence's order fully free by default.
    """


#################
# SequenceFixed #
#################

class SequenceFixed(NeighborhoodConstraint):
    """
    A NeighborhoodConstraint requiring that the employee's sequence is left entirely unchanged.
    An employee carrying this constraint cannot also be targeted by an operator.
    """
