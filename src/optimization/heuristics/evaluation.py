# Standard library
from typing import Optional, cast

# Local libraries
from src.modeling.activity import Activity
from src.modeling.employee import Employee
from src.modeling.task import Task


##############
# Evaluation #
##############

class Evaluation:
    """
    Base evaluation of a hypothetical sequence transformation's feasibility and cost,
    used to rank candidate transformations against each other.
    """

    def __init__(self):
        self._is_feasible: Optional[bool] = None
        self._is_skill_feasible: Optional[bool] = None
        self._is_time_feasible: Optional[bool] = None
        self._is_upstream_feasible: Optional[bool] = None
        self._is_downstream_feasible: Optional[bool] = None
        self._start_time: Optional[int] = None
        self._earliest_start_time_for_upstream: Optional[int] = None
        self._latest_start_time_for_downstream: Optional[int] = None
        self._travel_time_increase: Optional[int] = None
        self._late: Optional[int] = None
        self._task: Optional[Task] = None
        self._employee: Optional[Employee] = None

    @property
    def is_feasible(self):
        """Whether the evaluated transformation is feasible (time- and skill-wise)."""
        return self._is_feasible

    @is_feasible.setter
    def is_feasible(self, is_feasible: bool):
        self._is_feasible = is_feasible

    @property
    def is_skill_feasible(self):
        """Whether the employee has the skills required to perform the transformation."""
        return self._is_skill_feasible

    @is_skill_feasible.setter
    def is_skill_feasible(self, is_skill_feasible: bool):
        self._is_skill_feasible = is_skill_feasible

    @property
    def is_time_feasible(self):
        """Whether the transformation's times are feasible."""
        return self._is_time_feasible

    @is_time_feasible.setter
    def is_time_feasible(self, is_time_feasible: bool):
        self._is_time_feasible = is_time_feasible

    @property
    def is_upstream_feasible(self):
        """Whether the times of the sequence portion before the transformation stay consistent."""
        return self._is_upstream_feasible

    @is_upstream_feasible.setter
    def is_upstream_feasible(self, is_upstream_feasible: bool):
        self._is_upstream_feasible = is_upstream_feasible

    @property
    def is_downstream_feasible(self):
        """Whether the times of the sequence portion after the transformation stay consistent."""
        return self._is_downstream_feasible

    @is_downstream_feasible.setter
    def is_downstream_feasible(self, is_downstream_feasible: bool):
        self._is_downstream_feasible = is_downstream_feasible

    @property
    def start_time(self):
        """The start time (minutes since midnight) that would be applied to the transformed task."""
        return self._start_time

    @start_time.setter
    def start_time(self, start_time: int):
        self._start_time = start_time

    @property
    def earliest_start_time_for_upstream(self):
        """The artificial start time keeping the upstream portion consistent, or None if feasible."""
        return self._earliest_start_time_for_upstream

    @earliest_start_time_for_upstream.setter
    def earliest_start_time_for_upstream(self, earliest_start_time_for_upstream: Optional[int]):
        self._earliest_start_time_for_upstream = earliest_start_time_for_upstream

    @property
    def latest_start_time_for_downstream(self):
        """The artificial start time keeping the downstream portion consistent, or None if feasible."""
        return self._latest_start_time_for_downstream

    @latest_start_time_for_downstream.setter
    def latest_start_time_for_downstream(self, latest_start_time_for_downstream: Optional[int]):
        self._latest_start_time_for_downstream = latest_start_time_for_downstream

    @property
    def travel_time_increase(self):
        """The additional traveling duration (minutes) the transformation would add to the sequence."""
        return self._travel_time_increase

    @travel_time_increase.setter
    def travel_time_increase(self, travel_time_increase: int):
        self._travel_time_increase = travel_time_increase

    @property
    def late(self):
        """By how much (minutes) the earliest and latest feasible start times fail to overlap; 0 if feasible."""
        return self._late

    @late.setter
    def late(self, late: int):
        self._late = late

    @property
    def task(self):
        """The task involved in the transformation."""
        return self._task

    @task.setter
    def task(self, task: Task):
        self._task = task

    @property
    def employee(self):
        """The employee who would perform the transformation."""
        return self._employee

    @employee.setter
    def employee(self, employee: Employee):
        self._employee = employee

    def _skill_gap(self):
        """
        By how many skill levels the employee falls short of the task's requirement;
        used to rank evaluations that are equally infeasible skill-wise (smaller gap is better).

        Raises:
            ValueError: If this evaluation has no task or no employee set yet.
        """
        if self.task is None:
            raise ValueError(f"This evaluation {self} has no task to compute a skill gap for")
        elif self.employee is None:
            raise ValueError(f"This evaluation {self} has no employee to compute a skill gap for")
        else:
            return self.task.skill_level - self.employee.skill_level

    def is_better_than(self, other):
        """
        Whether this evaluation ranks better than other, when both are evaluations of the same task
        at different positions/orderings (see InsertionEvaluation.is_better_insertion_than for a version
        that also accounts for the task's own duration, for comparisons across different candidate tasks).

        Priority order: feasibility, then (while infeasible) skill feasibility and skill gap, then
        (once skill-wise tied) how far from feasible it is (late), then the additional traveling duration.

        Raises:
            TypeError: If other is not an Evaluation.
        """
        if not isinstance(other, Evaluation):
            raise TypeError(f"Cannot compare Evaluation with {type(other)}")
        if self.is_feasible:
            if not other.is_feasible:
                return True
            elif self.travel_time_increase < other.travel_time_increase:
                return True
            else:
                return False
        elif other.is_feasible:
            return False
        elif not self.is_skill_feasible and other.is_skill_feasible:
            return False
        elif self.is_skill_feasible and not other.is_skill_feasible:
            return True
        elif not self.is_skill_feasible and not other.is_skill_feasible:
            if self._skill_gap() < other._skill_gap():
                return True
            if self._skill_gap() > other._skill_gap():
                return False
        if self.late < other.late:
            return True
        elif self.late > other.late:
            return False
        else:
            return self.travel_time_increase < other.travel_time_increase

    def _string_about_evaluation_type(self):
        return "Evaluation"

    def _string_related_to_time_feasibility(self):
        return f"Time-feasible: {self.is_time_feasible} | " \
               f"Upstream-feasible: {self.is_upstream_feasible} | " \
               f"Downstream-feasible: {self.is_downstream_feasible} | " \
               f"Start time: {self.start_time} | " \
               f"Earliest start time for upstream: {self.earliest_start_time_for_upstream} | " \
               f"Latest start time for downstream: {self.latest_start_time_for_downstream}"

    def _string_related_to_transformation(self):
        return f"Employee name: {self.employee.name if self.employee is not None else 'None'} | " \
               f"Task name: {self.task.name if self.task is not None else 'None'}"

    def __str__(self):
        return f"{self._string_about_evaluation_type()}: " \
               f"{self._string_related_to_transformation()} | " \
               f"Feasible: {self.is_feasible} | " \
               f"Skill-feasible: {self.is_skill_feasible} | " \
               f"{self._string_related_to_time_feasibility()} | " \
               f"Travel time increase: {self.travel_time_increase} | " \
               f"Late: {self.late}"

    def __eq__(self, other):
        if not isinstance(other, Evaluation):
            return False
        if self.employee != other.employee:
            return False
        if self.is_feasible != other.is_feasible:
            return False
        if self.is_skill_feasible != other.is_skill_feasible:
            return False
        if self.is_time_feasible != other.is_time_feasible:
            return False
        if self.is_upstream_feasible != other.is_upstream_feasible:
            return False
        if self.is_downstream_feasible != other.is_downstream_feasible:
            return False
        if self.start_time != other.start_time:
            return False
        if self.earliest_start_time_for_upstream != other.earliest_start_time_for_upstream:
            return False
        if self.latest_start_time_for_downstream != other.latest_start_time_for_downstream:
            return False
        if self.travel_time_increase != other.travel_time_increase:
            return False
        # NB: late can be None before it is ever set; treat that the same as 0 (feasible/no lateness)
        # rather than making two not-yet-fully-evaluated instances compare unequal solely because of it.
        late = self.late if self.late is not None else 0
        other_late = other.late if other.late is not None else 0
        if late != other_late:
            return False
        return True


#######################
# InsertionEvaluation #
#######################

class InsertionEvaluation(Evaluation):
    """
    Evaluation of a hypothetical task insertion between two consecutive activities.

    - If the insertion is feasible, the value associated to the field 'start_time' is the start time (int)
      that could be applied to the entering task, when following the earliest policy,
      whereas the values associated to 'earliest_start_time_for_upstream' and
      'latest_start_time_for_downstream' are both None;
    - If the insertion is infeasible, the values associated to the fields 'earliest_start_time_for_upstream' and
      'latest_start_time_for_downstream' are the start times that could be applied to the entering task so that
      the time consistency of respectively the upstream and the downstream portions of the sequence,
      while the value associated to the fields 'start_time' is an average of these artificial values.
    """

    def __init__(self):
        super().__init__()
        self._inserted_task: Optional[Task] = None
        self._insertion_step_index: Optional[int] = None
        self._activity_before_insertion: Optional[Activity] = None

    @classmethod
    def from_evaluation(cls, evaluation: Evaluation):
        insertion_evaluation = InsertionEvaluation()
        insertion_evaluation.is_feasible = evaluation.is_feasible
        insertion_evaluation.is_skill_feasible = evaluation.is_skill_feasible
        insertion_evaluation.is_time_feasible = evaluation.is_time_feasible
        insertion_evaluation.is_upstream_feasible = evaluation.is_upstream_feasible
        insertion_evaluation.is_downstream_feasible = evaluation.is_downstream_feasible
        insertion_evaluation.start_time = evaluation.start_time
        insertion_evaluation.earliest_start_time_for_upstream = evaluation.earliest_start_time_for_upstream
        insertion_evaluation.latest_start_time_for_downstream = evaluation.latest_start_time_for_downstream
        insertion_evaluation.travel_time_increase = evaluation.travel_time_increase
        insertion_evaluation.late = evaluation.late
        insertion_evaluation.task = evaluation.task
        insertion_evaluation.employee = evaluation.employee
        return insertion_evaluation

    @property
    def inserted_task(self):
        """The task that would be inserted."""
        return self._inserted_task

    @inserted_task.setter
    def inserted_task(self, inserted_task: Task):
        self._inserted_task = inserted_task

    @property
    def insertion_step_index(self):
        """The index of the step at which the task would be inserted."""
        return self._insertion_step_index

    @insertion_step_index.setter
    def insertion_step_index(self, insertion_step_index: int):
        self._insertion_step_index = insertion_step_index

    @property
    def activity_before_insertion(self):
        """The activity immediately before the hypothetical insertion point."""
        return self._activity_before_insertion

    @activity_before_insertion.setter
    def activity_before_insertion(self, activity_before_insertion: Activity):
        self._activity_before_insertion = activity_before_insertion

    def _skill_gap(self):
        return cast(Task, self.inserted_task).skill_level - cast(Employee, self.employee).skill_level

    def is_better_insertion_than(self, other):
        """
        Whether this evaluation is a better insertion than other,
        when the two may be insertions of different candidate tasks
        (unlike Evaluation.is_better_than, which only compares different positions/orderings of the same task,
        and so has no notion of the inserted task's own duration).

        Priority order, mirroring the (target feasibility gap, working duration, traveling duration)
        order used elsewhere: feasibility, then (while infeasible) skill feasibility and skill gap,
        then (once skill-wise tied) how far from feasible it is (late), then the inserted task's own duration,
        then the additional traveling duration.

        Raises:
            TypeError: if other is not an InsertionEvaluation.
        """
        if not isinstance(other, InsertionEvaluation):
            raise TypeError(f"Cannot compare InsertionEvaluation with {type(other)}")
        if self.is_feasible:
            if not other.is_feasible:
                return True
            return self._is_better_insertion_among_equally_feasible(other)
        elif other.is_feasible:
            return False
        elif not self.is_skill_feasible and other.is_skill_feasible:
            return False
        elif self.is_skill_feasible and not other.is_skill_feasible:
            return True
        elif not self.is_skill_feasible and not other.is_skill_feasible:
            if self._skill_gap() < other._skill_gap():
                return True
            if self._skill_gap() > other._skill_gap():
                return False
        if self.late < other.late:
            return True
        elif self.late > other.late:
            return False
        else:
            return self._is_better_insertion_among_equally_feasible(other)

    def _is_better_insertion_among_equally_feasible(self, other):
        """
        Whether this evaluation is a better insertion than other, among two evaluations already known
        to be tied on feasibility (both fully feasible, or both infeasible by the same late amount):
        prefer the smaller inserted task's own duration, then the smaller additional traveling duration.
        """
        if self.inserted_task.duration != other.inserted_task.duration:
            return self.inserted_task.duration < other.inserted_task.duration
        return self.travel_time_increase < other.travel_time_increase

    def __str__(self):
        return f"Insertion evaluation: " \
               f"Employee name: {self.employee.name if self.employee is not None else 'None'} | " \
               f"Inserted task name: {self.inserted_task.name if self.inserted_task is not None else 'None'} | " \
               f"Activity before: " \
               f"{self.activity_before_insertion.name if self.activity_before_insertion is not None else 'None'} | " \
               f"Step index: {self.insertion_step_index} | " \
               f"Feasible: {self.is_feasible} | " \
               f"Skill-feasible: {self.is_skill_feasible} | " \
               f"Time-feasible: {self.is_time_feasible} | " \
               f"Upstream-feasible: {self.is_upstream_feasible} | " \
               f"Downstream-feasible: {self.is_downstream_feasible} | " \
               f"Start time: {self.start_time} | " \
               f"Earliest start time for upstream: {self.earliest_start_time_for_upstream} | " \
               f"Latest start time for downstream: {self.latest_start_time_for_downstream} | " \
               f"Travel time increase: {self.travel_time_increase} | " \
               f"Late: {self.late}"

    def __eq__(self, other):
        if not isinstance(other, InsertionEvaluation):
            return False
        if not super().__eq__(other):
            return False
        if self.inserted_task != other.inserted_task:
            return False
        if self.activity_before_insertion != other.activity_before_insertion:
            return False
        return True


#########################
# ReplacementEvaluation #
#########################

class ReplacementEvaluation(Evaluation):
    """Evaluation of a hypothetical task-for-task replacement at a given step of a sequence."""

    def __init__(self):
        super().__init__()
        self._replacement_step_index: Optional[int] = None
        self._replaced_task: Optional[Task] = None
        self._replacing_task: Optional[Task] = None

    @classmethod
    def from_evaluation(cls, evaluation: Evaluation):
        replacement_evaluation = ReplacementEvaluation()
        replacement_evaluation.is_feasible = evaluation.is_feasible
        replacement_evaluation.is_skill_feasible = evaluation.is_skill_feasible
        replacement_evaluation.is_time_feasible = evaluation.is_time_feasible
        replacement_evaluation.is_upstream_feasible = evaluation.is_upstream_feasible
        replacement_evaluation.is_downstream_feasible = evaluation.is_downstream_feasible
        replacement_evaluation.start_time = evaluation.start_time
        replacement_evaluation.earliest_start_time_for_upstream = evaluation.earliest_start_time_for_upstream
        replacement_evaluation.latest_start_time_for_downstream = evaluation.latest_start_time_for_downstream
        replacement_evaluation.travel_time_increase = evaluation.travel_time_increase
        replacement_evaluation.late = evaluation.late
        replacement_evaluation.task = evaluation.task
        replacement_evaluation.employee = evaluation.employee
        return replacement_evaluation

    @property
    def replacement_step_index(self):
        """The index of the step that would be replaced."""
        return self._replacement_step_index

    @replacement_step_index.setter
    def replacement_step_index(self, replacement_step_index: int):
        self._replacement_step_index = replacement_step_index

    @property
    def replaced_task(self):
        """The task that would be removed."""
        return self._replaced_task

    @replaced_task.setter
    def replaced_task(self, replaced_task: Task):
        self._replaced_task = replaced_task

    @property
    def replacing_task(self):
        """The task that would take its place."""
        return self._replacing_task

    @replacing_task.setter
    def replacing_task(self, replacing_task: Task):
        self._replacing_task = replacing_task

    def _skill_gap(self):
        return cast(Task, self.replacing_task).skill_level - cast(Employee, self.employee).skill_level

    def is_better_replacement_than(self, other):
        """
        Whether this evaluation is a better replacement than other, when the two may be replacements by
        different candidate replacing tasks, in the same or a different employee's sequence.

        Priority order: feasibility, then (while infeasible) skill feasibility and skill gap, then (once
        skill-wise tied) upstream feasibility, then how far from feasible it is (late), then the
        additional traveling duration.

        Raises:
            TypeError: If other is not a ReplacementEvaluation.
        """
        if not isinstance(other, ReplacementEvaluation):
            raise TypeError(f"Cannot compare ReplacementEvaluation with {type(other)}")
        if self.is_feasible:
            return not other.is_feasible or self.travel_time_increase < other.travel_time_increase
        elif other.is_feasible:
            return False
        elif not self.is_skill_feasible:
            return not other.is_skill_feasible and self._skill_gap() < other._skill_gap()
        elif not other.is_skill_feasible:
            return True
        elif not self.is_upstream_feasible:
            return not other.is_upstream_feasible and self.late < other.late
        elif not other.is_upstream_feasible:
            return True
        else:
            return self.late < other.late

    def __eq__(self, other):
        if not isinstance(other, ReplacementEvaluation):
            return False
        if not super().__eq__(other):
            return False
        if self.replaced_task != other.replaced_task:
            return False
        if self.replacing_task != other.replacing_task:
            return False
        return True

    def _string_about_evaluation_type(self):
        return "ReplacementEvaluation"

    def _string_related_to_transformation(self):
        return f"Employee name: {self.employee.name if self.employee is not None else 'None'} | " \
               f"Replaced task name: {self.replaced_task.name if self.replaced_task is not None else 'None'} | " \
               f"Replacing task name: {self.replacing_task.name if self.replacing_task is not None else 'None'}"


#########################
# ReassigningEvaluation #
#########################

class ReassigningEvaluation(Evaluation):
    """Evaluation of a hypothetical reassignment of a task from one employee to another."""

    def __init__(self):
        super().__init__()
        self._moving_task: Optional[Task] = None
        self._stolen_employee: Optional[Employee] = None
        self._stealing_employee: Optional[Employee] = None
        self._activity_before_reassignment: Optional[Activity] = None

    @classmethod
    def from_evaluation(cls, evaluation: Evaluation):
        reassigning_evaluation = ReassigningEvaluation()
        reassigning_evaluation.is_feasible = evaluation.is_feasible
        reassigning_evaluation.is_skill_feasible = evaluation.is_skill_feasible
        reassigning_evaluation.is_time_feasible = evaluation.is_time_feasible
        reassigning_evaluation.is_upstream_feasible = evaluation.is_upstream_feasible
        reassigning_evaluation.is_downstream_feasible = evaluation.is_downstream_feasible
        reassigning_evaluation.start_time = evaluation.start_time
        reassigning_evaluation.earliest_start_time_for_upstream = evaluation.earliest_start_time_for_upstream
        reassigning_evaluation.latest_start_time_for_downstream = evaluation.latest_start_time_for_downstream
        reassigning_evaluation.travel_time_increase = evaluation.travel_time_increase
        reassigning_evaluation.late = evaluation.late
        reassigning_evaluation.task = evaluation.task
        reassigning_evaluation.employee = evaluation.employee
        return reassigning_evaluation

    @property
    def moving_task(self):
        """The task that would be reassigned."""
        return self._moving_task

    @moving_task.setter
    def moving_task(self, moving_task: Task):
        self._moving_task = moving_task

    @property
    def stolen_employee(self):
        """The employee the task would be taken from."""
        return self._stolen_employee

    @stolen_employee.setter
    def stolen_employee(self, stolen_employee: Employee):
        self._stolen_employee = stolen_employee

    @property
    def stealing_employee(self):
        """The employee the task would be given to."""
        return self._stealing_employee

    @stealing_employee.setter
    def stealing_employee(self, stealing_employee: Employee):
        self._stealing_employee = stealing_employee

    @property
    def activity_before_reassignment(self):
        """The activity after which the task would be reassigned, in the stealing employee's sequence."""
        return self._activity_before_reassignment

    @activity_before_reassignment.setter
    def activity_before_reassignment(self, activity_before_reassignment: Activity):
        self._activity_before_reassignment = activity_before_reassignment

    def _skill_gap(self):
        return cast(Task, self.moving_task).skill_level - cast(Employee, self.stealing_employee).skill_level

    def _string_related_to_transformation(self):
        return f"Employee name: {self.employee.name if self.employee is not None else 'None'} | " \
               f"Moving task name: {self.moving_task.name if self.moving_task is not None else 'None'}"


#####################
# ReorderEvaluation #
#####################

class ReorderEvaluation(Evaluation):
    """
    Evaluation of a hypothetical reordering of a task within the same employee's sequence.

    - If moving is feasible, the value associated to the field 'start_time' is the start time (int)
      that could be applied to the moving task, when following the earliest policy,
      whereas the values associated to 'earliest_start_time_for_upstream' and
      'latest_start_time_for_downstream' are both None;
    - If moving is infeasible, the values associated to the fields 'earliest_start_time_for_upstream' and
      'latest_start_time_for_downstream' are the start times that could be applied to the moving task so that
      the time consistency of respectively the upstream and the downstream portions of the sequence,
      while the value associated to the fields 'start_time' is an average of these artificial values.
    """

    def __init__(self):
        super().__init__()
        self._moving_task: Optional[Task] = None
        self._activity_before: Optional[Activity] = None
        self._activity_after: Optional[Activity] = None

    @classmethod
    def from_evaluation(cls, evaluation: Evaluation):
        reorder_evaluation = ReorderEvaluation()
        reorder_evaluation.is_feasible = evaluation.is_feasible
        reorder_evaluation.is_skill_feasible = evaluation.is_skill_feasible
        reorder_evaluation.is_time_feasible = evaluation.is_time_feasible
        reorder_evaluation.is_upstream_feasible = evaluation.is_upstream_feasible
        reorder_evaluation.is_downstream_feasible = evaluation.is_downstream_feasible
        reorder_evaluation.start_time = evaluation.start_time
        reorder_evaluation.earliest_start_time_for_upstream = evaluation.earliest_start_time_for_upstream
        reorder_evaluation.latest_start_time_for_downstream = evaluation.latest_start_time_for_downstream
        reorder_evaluation.travel_time_increase = evaluation.travel_time_increase
        reorder_evaluation.late = evaluation.late
        reorder_evaluation.task = evaluation.task
        reorder_evaluation.employee = evaluation.employee
        return reorder_evaluation

    @property
    def moving_task(self):
        """The task that would move."""
        return self._moving_task

    @moving_task.setter
    def moving_task(self, moving_task: Task):
        self._moving_task = moving_task

    @property
    def activity_before(self):
        """The activity that would immediately precede the moved task."""
        return self._activity_before

    @activity_before.setter
    def activity_before(self, activity_before: Activity):
        self._activity_before = activity_before

    @property
    def activity_after(self):
        """The activity that would immediately follow the moved task."""
        return self._activity_after

    @activity_after.setter
    def activity_after(self, activity_after: Activity):
        self._activity_after = activity_after

    def _skill_gap(self):
        return cast(Task, self.moving_task).skill_level - cast(Employee, self.employee).skill_level

    def _string_related_to_transformation(self):
        return f"Employee name: {self.employee.name if self.employee is not None else 'None'} | " \
               f"Moving task name: {self.moving_task.name if self.moving_task is not None else 'None'}"
