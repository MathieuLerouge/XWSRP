# Local libraries
from src.explaining.neighborhood.primitive import Primitive
from src.modeling.activity import Activity
from src.modeling.task import Task


###############
# Restriction #
###############

class Restriction(Primitive):
    """
    An elementary scope restriction.
    It narrows the freedom an already in-scope task or employee have by default, within a Neighborhood.
    It never frees anything itself.
    """


#######################
# ImmediatePrecedence #
#######################

class ImmediatePrecedence(Restriction):
    """
    A Restriction requiring that successor occurs immediately after predecessor,
    regardless of which employee ends up performing them.
    """

    def __init__(self, predecessor: Activity, successor: Activity):
        """
        Args:
            predecessor: The activity that successor must immediately follow.
            successor: The activity that must immediately follow predecessor.

        Raises:
            ValueError: If predecessor and successor are the same activity.
        """
        if predecessor is successor:
            raise ValueError("predecessor and successor must not be the same activity")
        self._predecessor = predecessor
        self._successor = successor

    @property
    def predecessor(self):
        """The activity that successor must immediately follow."""
        return self._predecessor

    @property
    def successor(self):
        """The activity that must immediately follow predecessor."""
        return self._successor


######################
# SequenceOrderFixed #
######################

class SequenceOrderFixed(Restriction):
    """
    A Restriction requiring that the relative order of a given, explicit, ordered list of tasks stays unchanged.
    """

    def __init__(self, tasks: list[Task]):
        """
        Args:
            tasks: The tasks, in the relative order they must keep.
        """
        self._tasks = tasks

    @property
    def tasks(self):
        """The tasks, in the relative order they must keep."""
        return self._tasks
