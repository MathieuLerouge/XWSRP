# Local libraries
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.feasibility.violation.violation import Violation


##################
# SkillViolation #
##################

class SkillViolation(Violation):
    """
    A task performed by an employee whose skill level is below the task's required skill level.
    """

    def __init__(self, task: Task, employee: Employee):
        """
        Args:
            task: Task performed by an under-qualified employee.
            employee: Employee assigned to the task, whose skill level is below the task's required skill level.
        """
        self._task = task
        self._employee = employee

    @property
    def task(self):
        """Task performed by an under-qualified employee."""
        return self._task

    @property
    def employee(self):
        """Employee assigned to the task, whose skill level is below the task's required skill level."""
        return self._employee

    @property
    def text(self):
        """Human-readable description of this violation."""
        return (f"{self._employee.name} is supposed to perform task "
                f"{self._task.name}, which has a skill level equal to {self._task.skill_level}, "
                f"while he/she has a skill level which is equal to {self._employee.skill_level}.")
