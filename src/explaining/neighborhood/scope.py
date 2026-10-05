# Standard library
from typing import Union, FrozenSet

# Local libraries
from src.modeling.employee import Employee
from src.modeling.task import Task


#########
# Scope #
#########

class Scope:
    """
    Represents the scope of a neighborhood, containing the employees and tasks
    that are eligible for modification.
    """

    def __init__(self, items: FrozenSet[Union[Employee, Task]]):
        """
        Args:
            items: A frozenset containing Employee and Task objects.
        """
        self._items = items
        self._employees = frozenset(item for item in items if isinstance(item, Employee))
        self._tasks = frozenset(item for item in items if isinstance(item, Task))

    @property
    def employees(self) -> FrozenSet[Employee]:
        """The employees in this scope."""
        return self._employees

    @property
    def tasks(self) -> FrozenSet[Task]:
        """The tasks in this scope."""
        return self._tasks

    @property
    def items(self) -> FrozenSet[Union[Employee, Task]]:
        """All items (employees and tasks) in this scope."""
        return self._items

    def __repr__(self):
        """Return a human-readable representation of the scope."""
        employees = sorted(emp.name for emp in self._employees)
        if len(employees) > 1:
            employee_str = "[" + "'s, ".join(employees) + "'s sequences]"
        elif len(employees) == 1:
            employee_str = f"{employees[0]}'s sequence"
        else:
            employee_str = ""
        tasks = sorted(task.name for task in self._tasks)
        if len(tasks) > 1:
            task_str = "[" + ", ".join(tasks) + "]"
        elif len(tasks) == 1:
            task_str = tasks[0]
        else:
            task_str = ""
        if len(employees) > 0 and len(tasks) > 0:
            return f"{employee_str} and {task_str}"
        else:
            return f"{employee_str}{task_str}"

    def __eq__(self, other):
        """Check equality with another Scope object or frozenset."""
        if isinstance(other, Scope):
            return self._items == other._items
        elif isinstance(other, frozenset):
            return self._items == other
        return False

    def __hash__(self):
        """Make Scope hashable for use in sets/dicts."""
        return hash(self._items)

    def __iter__(self):
        """Make Scope iterable for use in loops and comprehensions."""
        return iter(self._items)

    def __contains__(self, item):
        """Support the 'in' operator to check if an item is in scope."""
        return item in self._items

    def __len__(self):
        """Return the number of items in scope."""
        return len(self._items)