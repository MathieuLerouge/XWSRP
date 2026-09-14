# Standard library
from abc import abstractmethod
from typing import Union

# Local libraries
from src.explaining.neighborhood.primitive import Primitive
from src.modeling.employee import Employee
from src.modeling.task import Task


############
# Operator #
############

class Operator(Primitive):
    """
    An elementary transformation (inserting, deleting, relocating or repositioning a task,
    or reordering an employee's whole sequence) applied to a solution to compose a Neighborhood.
    """

    @property
    @abstractmethod
    def target_tasks(self):
        """The tasks this operator may act on."""
        pass

    @property
    @abstractmethod
    def scope(self) -> frozenset[Union[Employee, Task]]:
        """The employees' sequences and tasks this operator frees from being fixed to their current state."""
        pass


#################
# TaskInsertion #
#################

class TaskInsertion(Operator):
    """
    An Operator that inserts a target task into an employee's sequence.
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
        """The employees among which the one to perform the inserted task is chosen."""
        return self._candidate_employees

    @property
    def candidate_tasks(self):
        """The tasks among which the one to insert is chosen."""
        return self._candidate_tasks

    @property
    def target_tasks(self):
        """The tasks among which the one to insert is chosen."""
        return self.candidate_tasks

    @property
    def scope(self):
        """The candidate employees and candidate tasks."""
        return self._candidate_employees | self._candidate_tasks


################
# TaskDeletion #
################

class TaskDeletion(Operator):
    """
    An Operator that removes a target task from an employee's sequence.
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
        """The employees among which the one currently performing the removed task is chosen."""
        return self._candidate_employees

    @property
    def candidate_tasks(self):
        """The tasks among which the one to remove is chosen."""
        return self._candidate_tasks

    @property
    def target_tasks(self):
        """The tasks among which the one to remove is chosen."""
        return self.candidate_tasks

    @property
    def scope(self):
        """The candidate employees and candidate tasks."""
        return self._candidate_employees | self._candidate_tasks


##################
# TaskRelocation #
##################

class TaskRelocation(Operator):
    """
    An Operator that moves a target task from an origin employee's sequence to a destination employee's
    sequence. See TaskRepositioning for the more specific, same-employee, within-sequence special case.
    """

    def __init__(self, origin_employee: Employee, destination_employee: Employee, target_task: Task):
        """
        Args:
            origin_employee: The employee whose sequence loses the target task.
            destination_employee: The employee whose sequence gains the target task.
            target_task: The task to relocate.
        """
        self._origin_employee = origin_employee
        self._destination_employee = destination_employee
        self._target_task = target_task

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
    def target_tasks(self):
        """The relocated task, as a single-element frozenset."""
        return frozenset({self._target_task})

    @property
    def scope(self):
        """The origin and destination employees and the relocated task."""
        return frozenset({self._origin_employee, self._destination_employee}) | self.target_tasks


#####################
# TaskRepositioning #
#####################

class TaskRepositioning(Operator):
    """
    An Operator that moves a target task to a different position within its own employee's sequence.
    The special case of TaskRelocation where the origin and destination employee are the same.
    """

    def __init__(self, employee: Employee, target_task: Task):
        """
        Args:
            employee: The employee whose sequence the target task is repositioned within.
            target_task: The task to reposition.
        """
        self._employee = employee
        self._target_task = target_task

    @property
    def employee(self):
        """The employee whose sequence the target task is repositioned within."""
        return self._employee

    @property
    def target_task(self):
        """The task to reposition."""
        return self._target_task

    @property
    def target_tasks(self):
        """The repositioned task, as a single-element frozenset."""
        return frozenset({self._target_task})

    @property
    def scope(self):
        """The employee and the repositioned task."""
        return frozenset({self._employee}) | self.target_tasks


######################
# SequenceReordering #
######################

class SequenceReordering(Operator):
    """
    An Operator that frees an employee's entire sequence to be reordered,
    without adding, removing or reassigning any of their tasks.
    """

    def __init__(self, employee: Employee):
        """
        Args:
            employee: The employee whose sequence is freed to be reordered.
        """
        self._employee = employee

    @property
    def employee(self):
        """The employee whose sequence is freed to be reordered."""
        return self._employee

    @property
    def target_tasks(self):
        """No specific task is targeted: the whole sequence is, as a single unit."""
        return frozenset()

    @property
    def scope(self):
        """The employee, as a single-element frozenset."""
        return frozenset({self._employee})
