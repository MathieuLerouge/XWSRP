# Standard library
from abc import abstractmethod
from typing import Optional

# Local libraries
from src.explaining.neighborhood.primitive import NeighborhoodPrimitive
from src.modeling.activity import Activity
from src.modeling.employee import Employee
from src.modeling.task import Task

# Global variables
POSITION_SIDE_AFTER = "after"
POSITION_SIDE_BEFORE = "before"
POSITION_SIDES = [POSITION_SIDE_AFTER, POSITION_SIDE_BEFORE]


########################
# NeighborhoodOperator #
########################

class NeighborhoodOperator(NeighborhoodPrimitive):
    """
    An elementary transformation (inserting, deleting or relocating a task) applied to a solution to
    compose a Neighborhood.
    """

    @property
    @abstractmethod
    def target_tasks(self):
        """The tasks this operator may act on, as a frozenset."""
        pass


#################
# TaskInsertion #
#################

class TaskInsertion(NeighborhoodOperator):
    """
    A NeighborhoodOperator that inserts a target task into an employee's sequence.
    """

    def __init__(self, candidate_employees: frozenset[Employee], candidate_tasks: frozenset[Task]):
        """
        Args:
            candidate_employees: The employees among which the one to perform the inserted task is chosen.
            candidate_tasks: The tasks among which the one to insert is chosen.

        Raises:
            ValueError: If candidate_employees or candidate_tasks is empty.
        """
        if len(candidate_employees) == 0:
            raise ValueError("candidate_employees must not be empty")
        if len(candidate_tasks) == 0:
            raise ValueError("candidate_tasks must not be empty")
        self._candidate_employees = candidate_employees
        self._candidate_tasks = candidate_tasks

    @property
    def candidate_employees(self):
        """The employees among which the one to perform the inserted task is chosen, as a frozenset."""
        return self._candidate_employees

    @property
    def candidate_tasks(self):
        """The tasks among which the one to insert is chosen, as a frozenset."""
        return self._candidate_tasks

    @property
    def employees(self):
        """The employees among which the one to perform the inserted task is chosen, as a frozenset."""
        return self.candidate_employees

    @property
    def target_tasks(self):
        """The tasks among which the one to insert is chosen, as a frozenset."""
        return self.candidate_tasks


################
# TaskDeletion #
################

class TaskDeletion(NeighborhoodOperator):
    """
    A NeighborhoodOperator that removes a target task from an employee's sequence.
    """

    def __init__(self, candidate_employees: frozenset[Employee], candidate_tasks: frozenset[Task]):
        """
        Args:
            candidate_employees: The employees among which the one currently performing the removed task
                is chosen.
            candidate_tasks: The tasks among which the one to remove is chosen.

        Raises:
            ValueError: If candidate_employees or candidate_tasks is empty.
        """
        if len(candidate_employees) == 0:
            raise ValueError("candidate_employees must not be empty")
        if len(candidate_tasks) == 0:
            raise ValueError("candidate_tasks must not be empty")
        self._candidate_employees = candidate_employees
        self._candidate_tasks = candidate_tasks

    @property
    def candidate_employees(self):
        """The employees among which the one currently performing the removed task is chosen, as a frozenset."""
        return self._candidate_employees

    @property
    def candidate_tasks(self):
        """The tasks among which the one to remove is chosen, as a frozenset."""
        return self._candidate_tasks

    @property
    def employees(self):
        """The employees among which the one currently performing the removed task is chosen, as a frozenset."""
        return self.candidate_employees

    @property
    def target_tasks(self):
        """The tasks among which the one to remove is chosen, as a frozenset."""
        return self.candidate_tasks


##################
# TaskRelocation #
##################

class TaskRelocation(NeighborhoodOperator):
    """
    A NeighborhoodOperator that moves a target task from an origin employee's sequence to a destination
    employee's sequence: the same employee for a within-sequence reorder, or a different one for a
    cross-employee move.
    """

    def __init__(self, origin_employee: Employee, destination_employee: Employee, target_task: Task,
                 anchor_activity: Optional[Activity] = None, anchor_side: Optional[str] = None):
        """
        Args:
            origin_employee: The employee whose sequence loses the target task.
            destination_employee: The employee whose sequence gains the target task.
            target_task: The task to relocate.
            anchor_activity: The activity the relocated task must be positioned immediately next to, if the
                position is pinned rather than searched for freely.
            anchor_side: If anchor_activity is set, the side of anchor_activity (POSITION_SIDE_AFTER or
                POSITION_SIDE_BEFORE) the relocated task is positioned at. If anchor_activity is None, the
                direction (POSITION_SIDE_AFTER or POSITION_SIDE_BEFORE) relative to the task's current
                position its new position must be searched in, or None to search freely in both directions.

        Raises:
            ValueError: If anchor_activity is set without anchor_side, or if anchor_side is set to something
                other than POSITION_SIDE_AFTER or POSITION_SIDE_BEFORE.
        """
        if anchor_activity is not None and anchor_side is None:
            raise ValueError("anchor_side must be set when anchor_activity is set")
        if anchor_side is not None and anchor_side not in POSITION_SIDES:
            raise ValueError(f"anchor_side must be one of {POSITION_SIDES}, got {anchor_side}")
        self._origin_employee = origin_employee
        self._destination_employee = destination_employee
        self._target_task = target_task
        self._anchor_activity = anchor_activity
        self._anchor_side = anchor_side

    @property
    def origin_employee(self):
        """The employee whose sequence loses the target task."""
        return self._origin_employee

    @property
    def destination_employee(self):
        """The employee whose sequence gains the target task."""
        return self._destination_employee

    @property
    def target_task(self):
        """The task to relocate."""
        return self._target_task

    @property
    def anchor_activity(self):
        """The activity the relocated task must be positioned immediately next to, if any."""
        return self._anchor_activity

    @property
    def anchor_side(self):
        """The side of, or direction from (if anchor_activity is unset), the relocated task's new position."""
        return self._anchor_side

    @property
    def employees(self):
        """The origin and destination employees, as a frozenset."""
        return frozenset({self._origin_employee, self._destination_employee})

    @property
    def target_tasks(self):
        """The relocated task, as a single-element frozenset."""
        return frozenset({self._target_task})
