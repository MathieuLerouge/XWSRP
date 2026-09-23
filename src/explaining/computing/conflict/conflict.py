# Local libraries
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.task import Task

# Global variables
CONFLICT_TYPE_KEY = 'type'
CONFLICTING_EMPLOYEE_NAME_KEY = 'employee'
CONFLICTING_TASK_NAME_KEY = 'task'
IS_UPSTREAM_FEASIBLE_KEY = 'upstream feasible'
IS_DOWNSTREAM_FEASIBLE_KEY = 'downstream feasible'
EARLIEST_UPSTREAM_FEASIBLE_START_TIME_OF_CONFLICTING_TASK_KEY = 'early start time'
LATEST_DOWNSTREAM_FEASIBLE_START_TIME_OF_CONFLICTING_TASK_KEY = 'late start time'
# Spelled 'critical' rather than 'binding' on purpose: these are the keys of already-saved explanation
# JSON files (see data/*/explanations/), which renaming the concept must not invalidate.
UPSTREAM_BINDING_STEP_INDEX_KEY = 'upstream critical index'
DOWNSTREAM_BINDING_STEP_INDEX_KEY = 'downstream critical index'
SKILL_CONFLICT_TYPE = 'skill'
TIME_CONFLICT_TYPE = 'time'


############
# Conflict #
############

class Conflict:
    """
    Why a requested transformation of a solution cannot be carried out, as an (employee, task) pair that clashes,
    ready for the answering layer to phrase an explanation from.
    It is local to the one hypothetical arrangement a question asked about.
    """

    def __init__(self, conflicting_employee: Employee, conflicting_task: Task):
        """
        Args:
            conflicting_employee: The employee the requested transformation cannot be carried out for.
            conflicting_task: The task they cannot be given.
        """
        self._conflicting_employee = conflicting_employee
        self._conflicting_task = conflicting_task

    @property
    def conflicting_employee(self) -> Employee:
        """The employee the requested transformation cannot be carried out for."""
        return self._conflicting_employee

    @property
    def conflicting_task(self) -> Task:
        """The task they cannot be given."""
        return self._conflicting_task

    def __repr__(self):
        return f"Conflict between {self._conflicting_employee.name} and {self._conflicting_task.name}"

    def to_dict(self) -> dict:
        """Return this conflict as a dictionary, as read back by from_dict."""
        return {CONFLICTING_EMPLOYEE_NAME_KEY: self.conflicting_employee.name,
                CONFLICTING_TASK_NAME_KEY: self.conflicting_task.name}

    @classmethod
    def from_dict(cls, dictionary: dict, instance: Instance):
        """
        Rebuild the SkillConflict or TimeConflict the given dictionary describes.

        Args:
            dictionary: The dictionary to read, as produced by to_dict.
            instance: The instance whose employees and tasks the dictionary's names refer to.

        Returns:
            The rebuilt conflict.

        Raises:
            ValueError: if the dictionary's type is neither SKILL_CONFLICT_TYPE nor TIME_CONFLICT_TYPE.
        """
        if dictionary[CONFLICT_TYPE_KEY] == SKILL_CONFLICT_TYPE:
            return SkillConflict.from_dict(dictionary, instance)
        elif dictionary[CONFLICT_TYPE_KEY] == TIME_CONFLICT_TYPE:
            return TimeConflict.from_dict(dictionary, instance)
        else:
            raise ValueError("The conflict should be regarding skill or time")


#################
# SkillConflict #
#################

class SkillConflict(Conflict):
    """
    A Conflict whose cause is the employee not being skilled enough to perform the task at all.
    It carries no further detail: unlike a TimeConflict, there is no quantity to report
    - the employee's skill level either reaches what the task requires or it does not.
    """

    def to_dict(self) -> dict:
        """Return this conflict as a dictionary, as read back by from_dict."""
        dictionary = super().to_dict()
        dictionary[CONFLICT_TYPE_KEY] = SKILL_CONFLICT_TYPE
        return dictionary

    @classmethod
    def from_dict(cls, dictionary: dict, instance: Instance):
        """
        Rebuild the skill conflict the given dictionary describes.

        Args:
            dictionary: The dictionary to read, as produced by to_dict.
            instance: The instance whose employees and tasks the dictionary's names refer to.

        Returns:
            The rebuilt skill conflict.
        """
        return cls(instance.get_employee_by_name(dictionary[CONFLICTING_EMPLOYEE_NAME_KEY]),
                   instance.get_task_by_name(dictionary[CONFLICTING_TASK_NAME_KEY]))


################
# TimeConflict #
################

class TimeConflict(Conflict):
    """
    A Conflict whose cause is the conflicting task not fitting, in time, where it would have to go.
    The task's start time is squeezed from both sides:
    the route upstream of it cannot get the employee there before earliest_upstream_feasible_start_time_of_conflicting_task,
    while the route downstream of it has to be left by latest_downstream_feasible_start_time_of_conflicting_task.
    The conflict is what separates the two, and each binding step index points at the step, on its own side,
    that is actually binding rather than merely passing the pressure along.
    """

    def __init__(self, conflicting_employee: Employee, conflicting_task: Task,
                 is_upstream_feasible: bool, is_downstream_feasible: bool,
                 earliest_upstream_feasible_start_time_of_conflicting_task: int,
                 latest_downstream_feasible_start_time_of_conflicting_task: int,
                 upstream_binding_step_index: int, downstream_binding_step_index: int):
        """
        Args:
            conflicting_employee: The employee the requested transformation cannot be carried out for.
            conflicting_task: The task they cannot be given.
            is_upstream_feasible: Whether the portion of the route before the conflicting task can
                accommodate it on its own, ignoring everything after it.
            is_downstream_feasible: Whether the portion of the route after the conflicting task can
                accommodate it on its own, ignoring everything before it.
            earliest_upstream_feasible_start_time_of_conflicting_task: Earliest time, in minutes since
                midnight, the conflicting task could start given the route before it.
            latest_downstream_feasible_start_time_of_conflicting_task: Latest time, in minutes since
                midnight, the conflicting task could start given the route after it.
            upstream_binding_step_index: Index of the first step, searching backward from the conflicting
                task, whose own start-time lower bound is what holds the route back.
            downstream_binding_step_index: Index of the first step, searching forward from the conflicting
                task, whose own end-time upper bound is what holds the route back.
        """
        super().__init__(conflicting_employee, conflicting_task)
        self._is_upstream_feasible = is_upstream_feasible
        self._is_downstream_feasible = is_downstream_feasible
        self._earliest_start_time = earliest_upstream_feasible_start_time_of_conflicting_task
        self._latest_start_time = latest_downstream_feasible_start_time_of_conflicting_task
        self._upstream_binding_step_index = upstream_binding_step_index
        self._downstream_binding_step_index = downstream_binding_step_index

    @property
    def is_upstream_feasible(self) -> bool:
        """Whether the route before the conflicting task can accommodate it on its own."""
        return self._is_upstream_feasible

    @property
    def is_downstream_feasible(self) -> bool:
        """Whether the route after the conflicting task can accommodate it on its own."""
        return self._is_downstream_feasible

    @property
    def earliest_upstream_feasible_start_time_of_conflicting_task(self) -> int:
        """Earliest start time, in minutes since midnight, the route before the conflicting task allows."""
        return self._earliest_start_time

    @property
    def latest_downstream_feasible_start_time_of_conflicting_task(self) -> int:
        """Latest start time, in minutes since midnight, the route after the conflicting task allows."""
        return self._latest_start_time

    @property
    def upstream_binding_step_index(self) -> int:
        """Index of the first step backward from the conflicting task whose own lower bound is binding."""
        return self._upstream_binding_step_index

    @property
    def downstream_binding_step_index(self) -> int:
        """Index of the first step forward from the conflicting task whose own upper bound is binding."""
        return self._downstream_binding_step_index

    def to_dict(self) -> dict:
        """Return this conflict as a dictionary, as read back by from_dict."""
        dictionary = super().to_dict()
        dictionary[CONFLICT_TYPE_KEY] = TIME_CONFLICT_TYPE
        dictionary[IS_UPSTREAM_FEASIBLE_KEY] = int(self.is_upstream_feasible)
        dictionary[IS_DOWNSTREAM_FEASIBLE_KEY] = int(self.is_downstream_feasible)
        dictionary[EARLIEST_UPSTREAM_FEASIBLE_START_TIME_OF_CONFLICTING_TASK_KEY] = \
            self.earliest_upstream_feasible_start_time_of_conflicting_task
        dictionary[LATEST_DOWNSTREAM_FEASIBLE_START_TIME_OF_CONFLICTING_TASK_KEY] = \
            self.latest_downstream_feasible_start_time_of_conflicting_task
        dictionary[UPSTREAM_BINDING_STEP_INDEX_KEY] = self.upstream_binding_step_index
        dictionary[DOWNSTREAM_BINDING_STEP_INDEX_KEY] = self.downstream_binding_step_index
        return dictionary

    @classmethod
    def from_dict(cls, dictionary: dict, instance: Instance):
        """
        Rebuild the time conflict the given dictionary describes.

        Args:
            dictionary: The dictionary to read, as produced by to_dict.
            instance: The instance whose employees and tasks the dictionary's names refer to.

        Returns:
            The rebuilt time conflict.
        """
        return cls(instance.get_employee_by_name(dictionary[CONFLICTING_EMPLOYEE_NAME_KEY]),
                   instance.get_task_by_name(dictionary[CONFLICTING_TASK_NAME_KEY]),
                   bool(dictionary[IS_UPSTREAM_FEASIBLE_KEY]),
                   bool(dictionary[IS_DOWNSTREAM_FEASIBLE_KEY]),
                   int(dictionary[EARLIEST_UPSTREAM_FEASIBLE_START_TIME_OF_CONFLICTING_TASK_KEY]),
                   int(dictionary[LATEST_DOWNSTREAM_FEASIBLE_START_TIME_OF_CONFLICTING_TASK_KEY]),
                   int(dictionary[UPSTREAM_BINDING_STEP_INDEX_KEY]),
                   int(dictionary[DOWNSTREAM_BINDING_STEP_INDEX_KEY]))
