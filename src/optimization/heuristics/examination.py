# Local libraries
from src.modeling.activity import Activity
from src.modeling.employee import Employee
from src.modeling.task import Task


#####################
# Class Examination #
#####################

class Examination:

    def __init__(self):
        self._is_feasible = None
        self._is_skill_feasible = None
        self._is_time_feasible = None
        self._is_upstream_feasible = None
        self._is_downstream_feasible = None
        self._start_time = None
        self._earliest_start_time_for_upstream = None
        self._latest_start_time_for_downstream = None
        self._travel_time_increase = None
        self._late = None
        self._task = None
        self._employee = None

    @property
    def is_feasible(self):
        return self._is_feasible

    @is_feasible.setter
    def is_feasible(self, is_feasible: bool):
        self._is_feasible = is_feasible

    @property
    def is_skill_feasible(self):
        return self._is_skill_feasible

    @is_skill_feasible.setter
    def is_skill_feasible(self, is_skill_feasible: bool):
        self._is_skill_feasible = is_skill_feasible

    @property
    def is_time_feasible(self):
        return self._is_time_feasible

    @is_time_feasible.setter
    def is_time_feasible(self, is_time_feasible: bool):
        self._is_time_feasible = is_time_feasible

    @property
    def is_upstream_feasible(self):
        return self._is_upstream_feasible

    @is_upstream_feasible.setter
    def is_upstream_feasible(self, is_upstream_feasible: bool):
        self._is_upstream_feasible = is_upstream_feasible

    @property
    def is_downstream_feasible(self):
        return self._is_downstream_feasible

    @is_downstream_feasible.setter
    def is_downstream_feasible(self, is_downstream_feasible: bool):
        self._is_downstream_feasible = is_downstream_feasible

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, start_time: int):
        self._start_time = start_time

    @property
    def earliest_start_time_for_upstream(self):
        return self._earliest_start_time_for_upstream

    @earliest_start_time_for_upstream.setter
    def earliest_start_time_for_upstream(self, earliest_start_time_for_upstream: int):
        self._earliest_start_time_for_upstream = earliest_start_time_for_upstream

    @property
    def latest_start_time_for_downstream(self):
        return self._latest_start_time_for_downstream

    @latest_start_time_for_downstream.setter
    def latest_start_time_for_downstream(self, latest_start_time_for_downstream: int):
        self._latest_start_time_for_downstream = latest_start_time_for_downstream

    @property
    def travel_time_increase(self):
        return self._travel_time_increase

    @travel_time_increase.setter
    def travel_time_increase(self, travel_time_increase: int):
        self._travel_time_increase = travel_time_increase

    @property
    def late(self):
        return self._late

    @late.setter
    def late(self, late: int):
        self._late = late

    @property
    def task(self):
        return self._task

    @task.setter
    def task(self, task: Task):
        self._task = task

    @property
    def employee(self):
        return self._employee

    @employee.setter
    def employee(self, employee: Employee):
        self._employee = employee

    def _skill_gap(self):
        return self.task.skill_level - self.employee.skill_level

    def is_better_than(self, other):
        if not isinstance(other, Examination):
            raise TypeError(f"Cannot compare Examination with {type(other)}")
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
        if self.is_upstream_feasible:
            if not other.is_upstream_feasible:
                return True
            elif self.late < other.late:
                return True
            elif self.late > other.late:
                return False
            else:
                return self.travel_time_increase < other.travel_time_increase
        elif other.is_upstream_feasible:
            return False
        else:
            if self.late < other.late:
                return True
            elif self.late > other.late:
                return False
            else:
                return self.travel_time_increase < other.travel_time_increase

    def _string_about_examination_type(self):
        return "Examination"

    def _string_related_to_time_feasibility(self):
        return f"Time-feasible: {self.is_time_feasible} | " \
               f"Upstream-feasible: {self.is_upstream_feasible} | " \
               f"Downstream-feasible: {self.is_downstream_feasible} | " \
               f"Start time: {self.start_time} | " \
               f"Earliest start time for upstream: {self.earliest_start_time_for_upstream} | " \
               f"Latest start time for downstream: {self.latest_start_time_for_downstream}"

    def _string_related_to_transformation(self):
        return f"Employee name: {self.employee.name if self.employee is not None else None} | " \
               f"Task name: {self.task.name if self.task is not None else None}"

    def __str__(self):
        return f"{self._string_about_examination_type()}: " \
               f"{self._string_related_to_transformation()} | " \
               f"Feasible: {self.is_feasible} | " \
               f"Skill-feasible: {self.is_skill_feasible} | " \
               f"{self._string_related_to_time_feasibility()} | " \
               f"Travel time increase: {self.travel_time_increase} | " \
               f"Late: {self.late}"

    def __eq__(self, other):
        if not isinstance(other, Examination):
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
        late = self.late if self.late is not None else 0
        other_late = other.late if other.late is not None else 0
        if late != other_late:
            return False
        return True


##############################
# Class InsertionExamination #
##############################

class InsertionExamination(Examination):
    """
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
        self._inserted_task = None
        self._insertion_step_index = None
        self._activity_before_insertion = None

    @classmethod
    def from_examination(cls, examination: Examination):
        insertion_examination = InsertionExamination()
        insertion_examination.is_feasible = examination.is_feasible
        insertion_examination.is_skill_feasible = examination.is_skill_feasible
        insertion_examination.is_time_feasible = examination.is_time_feasible
        insertion_examination.is_upstream_feasible = examination.is_upstream_feasible
        insertion_examination.is_downstream_feasible = examination.is_downstream_feasible
        insertion_examination.start_time = examination.start_time
        insertion_examination.earliest_start_time_for_upstream = examination.earliest_start_time_for_upstream
        insertion_examination.latest_start_time_for_downstream = examination.latest_start_time_for_downstream
        insertion_examination.travel_time_increase = examination.travel_time_increase
        insertion_examination.late = examination.late
        insertion_examination.task = examination.task
        insertion_examination.employee = examination.employee
        return insertion_examination

    @property
    def inserted_task(self):
        return self._inserted_task

    @inserted_task.setter
    def inserted_task(self, inserted_task: Task):
        self._inserted_task = inserted_task

    @property
    def insertion_step_index(self):
        return self._insertion_step_index

    @insertion_step_index.setter
    def insertion_step_index(self, insertion_step_index: int):
        self._insertion_step_index = insertion_step_index

    @property
    def activity_before_insertion(self):
        return self._activity_before_insertion

    @activity_before_insertion.setter
    def activity_before_insertion(self, activity_before_insertion: Activity):
        self._activity_before_insertion = activity_before_insertion

    def _skill_gap(self):
        return self.inserted_task.skill_level - self.employee.skill_level

    def __str__(self):
        return f"Insertion examination: " \
               f"Employee name: {self.employee.name if self.employee is not None else None} | " \
               f"Inserted task name: {self.inserted_task.name if self.inserted_task is not None else None} | " \
               f"Activity before: " \
               f"{self.activity_before_insertion.name if self.activity_before_insertion is not None else None} | " \
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
        if not isinstance(other, InsertionExamination):
            return False
        if not super().__eq__(other):
            return False
        if self.inserted_task != other.inserted_task:
            return False
        if self.activity_before_insertion != other.activity_before_insertion:
            return False
        return True


################################
# Class ReplacementExamination #
################################

class ReplacementExamination(Examination):

    def __init__(self):
        super().__init__()
        self._replacement_step_index = None
        self._replaced_task = None
        self._replacing_task = None

    @classmethod
    def from_examination(cls, examination: Examination):
        replacement_examination = ReplacementExamination()
        replacement_examination.is_feasible = examination.is_feasible
        replacement_examination.is_skill_feasible = examination.is_skill_feasible
        replacement_examination.is_time_feasible = examination.is_time_feasible
        replacement_examination.is_upstream_feasible = examination.is_upstream_feasible
        replacement_examination.is_downstream_feasible = examination.is_downstream_feasible
        replacement_examination.start_time = examination.start_time
        replacement_examination.earliest_start_time_for_upstream = examination.earliest_start_time_for_upstream
        replacement_examination.latest_start_time_for_downstream = examination.latest_start_time_for_downstream
        replacement_examination.travel_time_increase = examination.travel_time_increase
        replacement_examination.late = examination.late
        replacement_examination.task = examination.task
        replacement_examination.employee = examination.employee
        return replacement_examination

    @property
    def replacement_step_index(self):
        return self._replacement_step_index

    @replacement_step_index.setter
    def replacement_step_index(self, replacement_step_index: int):
        self._replacement_step_index = replacement_step_index

    @property
    def replaced_task(self):
        return self._replaced_task

    @replaced_task.setter
    def replaced_task(self, replaced_task: Task):
        self._replaced_task = replaced_task

    @property
    def replacing_task(self):
        return self._replacing_task

    @replacing_task.setter
    def replacing_task(self, replacing_task: Task):
        self._replacing_task = replacing_task

    def _skill_gap(self):
        return self.replacing_task.skill_level - self.employee.skill_level

    def __eq__(self, other):
        if not isinstance(other, ReplacementExamination):
            return False
        if not super().__eq__(other):
            return False
        if self.replaced_task != other.replaced_task:
            return False
        if self.replacing_task != other.replacing_task:
            return False
        return True

    def _string_about_examination_type(self):
        return "ReplacementExamination"

    def _string_related_to_transformation(self):
        return f"Employee name: {self.employee.name if self.employee is not None else None} | " \
               f"Replaced task name: {self.replaced_task.name if self.replaced_task is not None else None} | " \
               f"Replacing task name: {self.replacing_task.name if self.replacing_task is not None else None}"


################################
# Class ReassigningExamination #
################################

class ReassigningExamination(Examination):

    def __init__(self):
        super().__init__()
        self._moving_task = None
        self._stolen_employee = None
        self._stealing_employee = None
        self._activity_before_reassignment = None

    @classmethod
    def from_examination(cls, examination: Examination):
        reassigning_examination = ReassigningExamination()
        reassigning_examination.is_feasible = examination.is_feasible
        reassigning_examination.is_skill_feasible = examination.is_skill_feasible
        reassigning_examination.is_time_feasible = examination.is_time_feasible
        reassigning_examination.is_upstream_feasible = examination.is_upstream_feasible
        reassigning_examination.is_downstream_feasible = examination.is_downstream_feasible
        reassigning_examination.start_time = examination.start_time
        reassigning_examination.earliest_start_time_for_upstream = examination.earliest_start_time_for_upstream
        reassigning_examination.latest_start_time_for_downstream = examination.latest_start_time_for_downstream
        reassigning_examination.travel_time_increase = examination.travel_time_increase
        reassigning_examination.late = examination.late
        reassigning_examination.task = examination.task
        reassigning_examination.employee = examination.employee
        return reassigning_examination

    @property
    def moving_task(self):
        return self._moving_task

    @moving_task.setter
    def moving_task(self, moving_task: Task):
        self._moving_task = moving_task

    @property
    def stolen_employee(self):
        return self._stolen_employee

    @stolen_employee.setter
    def stolen_employee(self, stolen_employee: Employee):
        self._stolen_employee = stolen_employee

    @property
    def stealing_employee(self):
        return self._stealing_employee

    @stealing_employee.setter
    def stealing_employee(self, stealing_employee: Employee):
        self._stealing_employee = stealing_employee

    @property
    def activity_before_reassignment(self):
        return self._activity_before_reassignment

    @activity_before_reassignment.setter
    def activity_before_reassignment(self, activity_before_reassignment: Activity):
        self._activity_before_reassignment = activity_before_reassignment

    def _skill_gap(self):
        return self.moving_task.skill_level - self.stealing_employee.skill_level


############################
# Class ReorderExamination #
############################

class ReorderExamination(Examination):
    """
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
        self._moving_task = None
        self._activity_before = None
        self._activity_after = None

    @classmethod
    def from_examination(cls, examination: Examination):
        reorder_examination = ReorderExamination()
        reorder_examination.is_feasible = examination.is_feasible
        reorder_examination.is_skill_feasible = examination.is_skill_feasible
        reorder_examination.is_time_feasible = examination.is_time_feasible
        reorder_examination.is_upstream_feasible = examination.is_upstream_feasible
        reorder_examination.is_downstream_feasible = examination.is_downstream_feasible
        reorder_examination.start_time = examination.start_time
        reorder_examination.earliest_start_time_for_upstream = examination.earliest_start_time_for_upstream
        reorder_examination.latest_start_time_for_downstream = examination.latest_start_time_for_downstream
        reorder_examination.travel_time_increase = examination.travel_time_increase
        reorder_examination.late = examination.late
        reorder_examination.task = examination.task
        reorder_examination.employee = examination.employee
        return reorder_examination

    @property
    def moving_task(self):
        return self._moving_task

    @moving_task.setter
    def moving_task(self, moving_task: Task):
        self._moving_task = moving_task
        
    @property
    def activity_before(self):
        return self._activity_before
    
    @activity_before.setter
    def activity_before(self, activity_before: Activity):
        self._activity_before = activity_before
    
    @property
    def activity_after(self):
        return self._activity_after
    
    @activity_after.setter
    def activity_after(self, activity_after: Activity):
        self._activity_after = activity_after

    def _skill_gap(self):
        return self.moving_task.skill_level - self.employee.skill_level
