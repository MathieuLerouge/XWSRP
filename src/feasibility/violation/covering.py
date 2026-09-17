# Local libraries
from src.feasibility.violation.violation import Violation
from src.modeling.task import Task


#####################
# CoveringViolation #
#####################

class CoveringViolation(Violation):
    """
    A task that is not performed, while all tasks must be performed.
    """

    def __init__(self, task: Task):
        """
        Args:
            task: Task that is not performed.
        """
        self._task = task

    @property
    def task(self):
        """Task that is not performed."""
        return self._task

    @property
    def text(self):
        """Human-readable description of this violation."""
        return f"Task {self._task.name} is not performed while all tasks must be performed."
