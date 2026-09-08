# Standard library
from typing import Optional


# Global variables
TASK_PERFORMANCE_STATUS_KEY = 'performed'
TASK_ASSIGNEE_KEY = 'employee name'
TASK_START_TIME_KEY = 'start time'


###################
# TaskPerformance #
###################

class TaskPerformance:
    """
    How a task is performed in a solution: whether it is performed, and if so, by whom and when.
    """

    def __init__(self, performed: bool = False, assignee_name: Optional[str] = None,
                 start_time: Optional[int] = None):
        """
        Args:
            performed: Whether the task is performed.
            assignee_name: Name of the employee assigned to the task, if performed.
            start_time: Start time of the task, in minutes since midnight, if performed.
        """
        self._performed = performed
        self._assignee_name = assignee_name
        self._start_time = start_time

    @property
    def performed(self) -> bool:
        """Whether the task is performed."""
        return self._performed

    @performed.setter
    def performed(self, performed: bool):
        self._performed = performed

    @property
    def assignee_name(self) -> Optional[str]:
        """Name of the employee assigned to the task, or None if the task is not performed."""
        return self._assignee_name

    @assignee_name.setter
    def assignee_name(self, assignee_name: Optional[str]):
        self._assignee_name = assignee_name

    @property
    def start_time(self) -> Optional[int]:
        """Start time of the task, in minutes since midnight, or None if the task is not performed."""
        return self._start_time

    @start_time.setter
    def start_time(self, start_time: Optional[int]):
        self._start_time = start_time

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of this task performance.

        Returns:
            A dict with TASK_PERFORMANCE_STATUS_KEY always set, and, only when performed,
            TASK_ASSIGNEE_KEY and TASK_START_TIME_KEY.
        """
        if self._performed:
            return {
                TASK_PERFORMANCE_STATUS_KEY: 1,
                TASK_ASSIGNEE_KEY: self._assignee_name,
                TASK_START_TIME_KEY: self._start_time,
            }
        else:
            return {TASK_PERFORMANCE_STATUS_KEY: 0}

    @classmethod
    def from_dict(cls, dictionary: dict) -> "TaskPerformance":
        """
        Args:
            dictionary: Dictionary describing the task performance, as produced by to_dict.

        Returns:
            The corresponding TaskPerformance.
        """
        performed = bool(dictionary[TASK_PERFORMANCE_STATUS_KEY])
        if not performed:
            return cls()
        return cls(performed, dictionary[TASK_ASSIGNEE_KEY], int(dictionary[TASK_START_TIME_KEY]))
