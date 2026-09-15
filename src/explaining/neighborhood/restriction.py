# Local libraries
from src.explaining.neighborhood.primitive import Primitive
from src.modeling.activity import Activity
from src.modeling.employee import Employee
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


##############
# Precedence #
##############

class Precedence(Restriction):
    """
    A Restriction requiring that successor starts no earlier than predecessor finishes,
    without requiring immediate adjacency (see ImmediatePrecedence for that stronger requirement).
    """

    def __init__(self, predecessor: Task, successor: Task):
        """
        Args:
            predecessor: The task that must finish no later than successor starts.
            successor: The task that must start no earlier than predecessor finishes.

        Raises:
            ValueError: If predecessor and successor are the same task.
        """
        if predecessor is successor:
            raise ValueError("predecessor and successor must not be the same task")
        self._predecessor = predecessor
        self._successor = successor

    @property
    def predecessor(self):
        """The task that must finish no later than successor starts."""
        return self._predecessor

    @property
    def successor(self):
        """The task that must start no earlier than predecessor finishes."""
        return self._successor


###################
# PrecedenceChain #
###################

class PrecedenceChain(Restriction):
    """
    A Restriction requiring that the relative order of a given, explicit, ordered list of tasks stays
    unchanged: a chain of Precedence relations, one between each consecutive pair.
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


#####################
# ForbiddenSequence #
#####################

class ForbiddenSequence(Restriction):
    """
    A Restriction forbidding a specific employee's sequence from containing a given,
    explicit, ordered chain of activities as a contiguous run.
    """

    def __init__(self, employee: Employee, activities: list[Activity]):
        """
        Args:
            employee: The employee whose sequence must not contain the forbidden chain.
            activities: The forbidden chain of activities, in the order they must not appear contiguously in.

        Raises:
            ValueError: If activities has fewer than 2 elements (there would be no arc left to forbid).
        """
        if len(activities) < 2:
            raise ValueError("activities must contain at least 2 elements")
        self._employee = employee
        self._activities = activities

    @property
    def employee(self):
        """The employee whose sequence must not contain the forbidden chain."""
        return self._employee

    @property
    def activities(self):
        """The forbidden chain of activities, in the order they must not appear contiguously in."""
        return self._activities


################################
# ForbiddenBackwardSubsequence #
################################

class ForbiddenBackwardSubsequence(Restriction):
    """
    A Restriction requiring that a specific employee's route never travels directly or indirectly from a
    later task to an earlier one within a given, explicit, ordered list of tasks - i.e. whichever of them
    remain performed keep their original relative order, though any of them may become unperformed.
    """

    def __init__(self, employee: Employee, tasks: list[Task]):
        """
        Args:
            employee: The employee whose route must not travel backward within tasks.
            tasks: The tasks, in the relative order that whichever of them remain performed must keep.
        """
        self._employee = employee
        self._tasks = tasks

    @property
    def employee(self):
        """The employee whose route must not travel backward within tasks."""
        return self._employee

    @property
    def tasks(self):
        """The tasks, in the relative order that whichever of them remain performed must keep."""
        return self._tasks
