# Local libraries
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack
from src.modeling.constants import NB_PERFORMED_TASKS_KEY, TOTAL_TRAVELING_DURATION_KEY, TOTAL_WORKING_DURATION_KEY, \
    TOTAL_TRAVELING_DISTANCE_KEY, TOTAL_IDLE_TIME_KEY
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.solution import Solution, TASK_PERFORMANCE_STATUS_KEY, TASK_ASSIGNEE_KEY, TASK_START_TIME_KEY
from src.modeling.task import Task
from src.optimization.heuristics.examination import ReassigningExamination
from src.optimization.heuristics.sequence import SequenceForHeuristics
from src.optimization.solution import SolutionOpti

# Local libraries under conditions
from main_configuration import GUROBI_IS_ENABLED
if GUROBI_IS_ENABLED:
    from src.optimization.IP.sequence.insertingmodel import IPModelForSequenceInserting
    from src.optimization.IP.sequence.prescribingmodel import IPModelForSequencePrescribing
    from src.optimization.IP.sequence.reorderingmodel import IPModelForSequenceReordering


# Global variables
HEURISTIC_ID = "heuristic"


###############################
# Class SolutionForHeuristics #
###############################

class SolutionForHeuristics(SolutionOpti):

    def __init__(self, instance: Instance, name: str = None, sequences: dict[str, SequenceForHeuristics] = None,
                 tasks_realizations: dict = None, lunch_breaks_realizations: dict = None, heuristic_ID: str = None):
        heuristic_ID = HEURISTIC_ID if heuristic_ID is None else heuristic_ID
        super().__init__(instance, name, None, tasks_realizations, lunch_breaks_realizations, heuristic_ID)
        if sequences is None:
            sequences = dict()
            for employee in self._instance.employees:
                sequences[employee.name] = SequenceForHeuristics(instance, employee)
        self._sequences = sequences
        self.compute_KPIs()

    @classmethod
    def from_SolutionOpti(cls, solution: SolutionOpti, heuristic_ID: str = None):
        sequences = dict([(employee_name, SequenceForHeuristics.from_Sequence(sequence))
                          for (employee_name, sequence) in solution._sequences.items()])
        name = solution.name if heuristic_ID is None else None
        return cls(solution.instance, name, sequences,
                   solution._copy_tasks_realizations(), solution._copy_lunch_breaks_realizations(), heuristic_ID)

    @classmethod
    def from_Solution(cls, solution: Solution, heuristic_ID: str = None):
        sequences = dict([(employee_name, SequenceForHeuristics.from_Sequence(sequence))
                          for (employee_name, sequence) in solution._sequences.items()])
        name = solution.name if heuristic_ID is None else None
        return cls(solution.instance, name, sequences,
                   solution._copy_tasks_realizations(), solution._copy_lunch_breaks_realizations(), heuristic_ID)

    @property
    def _nb_realized_tasks(self) -> int:
        return self._KPIs[NB_PERFORMED_TASKS_KEY]

    @_nb_realized_tasks.setter
    def _nb_realized_tasks(self, nb_realized_tasks: int):
        self._KPIs[NB_PERFORMED_TASKS_KEY] = nb_realized_tasks

    @property
    def _total_traveling_duration(self) -> int:
        return self._KPIs[TOTAL_TRAVELING_DURATION_KEY]

    @_total_traveling_duration.setter
    def _total_traveling_duration(self, total_traveling_duration: int):
        self._KPIs[TOTAL_TRAVELING_DURATION_KEY] = total_traveling_duration

    @property
    def _total_working_duration(self) -> int:
        return self._KPIs[TOTAL_WORKING_DURATION_KEY]

    @_total_working_duration.setter
    def _total_working_duration(self, total_working_duration: int):
        self._KPIs[TOTAL_WORKING_DURATION_KEY] = total_working_duration

    @property
    def _total_traveling_distance(self) -> float:
        return self._KPIs[TOTAL_TRAVELING_DISTANCE_KEY]

    @_total_traveling_distance.setter
    def _total_traveling_distance(self, total_traveling_distance: int):
        self._KPIs[TOTAL_TRAVELING_DISTANCE_KEY] = total_traveling_distance

    @property
    def _total_idle_time(self) -> int:
        return self._KPIs[TOTAL_IDLE_TIME_KEY]

    @_total_idle_time.setter
    def _total_idle_time(self, total_idle_time: int):
        self._KPIs[TOTAL_IDLE_TIME_KEY] = total_idle_time

    ########
    # Copy #
    ########

    def copy(self, name: str = None):
        name = self._name + "_copy" if name is None else name
        solution = SolutionForHeuristics(self._instance, name, self._copy_sequences(),
                                         self._copy_tasks_realizations(), self._copy_lunch_breaks_realizations())
        solution.name = name
        solution._KPIs = self._copy_KPIs()
        return solution

    ############
    # Sequence #
    ############

    def get_sequence(self, employee: Employee):
        return self._sequences[employee.name]

    #########
    # Times #
    #########

    def tighten_times(self, update_KPIs: bool = True):
        for sequence in self._sequences.values():
            if update_KPIs:
                former_sequence_idle_time = sequence.total_idle_time
                sequence.tighten_times(update_KPIs)
                self._total_idle_time += sequence.total_idle_time - former_sequence_idle_time
            else:
                sequence.tighten_times(update_KPIs)

    ###############
    # Time Slacks #
    ###############

    def update_time_slacks(self):
        for sequence in self._sequences.values():
            sequence.update_time_slacks()

    ###############################################
    # Examining - Insertion - Best transformation #
    ###############################################

    def examine_insertion_at(self, entering_task: Task, employee: Employee, step_index: int,
                             compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Examine the feasibility of the insertion of the given entering task at the given step index;

        Assumptions (only checked in debug):

        - 1. the given entering task must not be already in this sequence;
        - 2. the given step index must be between 1 (included) and the number of steps - 1 (included);
        - 3. the times of this sequence are consistent.

        :param entering_task: the task (Task) that would be inserted
        :param employee: the employee (Employee) who would perform the entering task
        :param step_index: the index of the step (int) where the given task would be inserted
        :param compute_times_only_if_skill_constraints_satisfied: a boolean (bool) for telling whether
          if the skill constraints are not satisfied start times should still be computed
        :return: the insertion examination (InsertionExamination)
        """
        return self.get_sequence(employee).examine_insertion_at(entering_task, step_index,
                                                                compute_times_only_if_skill_constraints_satisfied)

    def examine_insertion_after(self, employee: Employee, task: Task, activity: Activity,
                                compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Examine the feasibility of inserting the given task after the given activity
        in the sequence of the given employee

        Assumptions (only checked in debug):

        - 1. the given entering task must not be already in this sequence;
        - 2. the given activity must be in the given employee's sequence;
        - 3. the times of this sequence are consistent.

        :param employee: the employee (Employee) who would perform the entering task
        :param task: the task (Task) that is figured to be inserted
        :param activity: the activity (Activity) after which the given task would be inserted
        :param compute_times_only_if_skill_constraints_satisfied: a boolean (bool) for telling whether
          if the skill constraints are not satisfied start times should still be computed
        :return: the insertion examination (InsertionExamination)
        """
        step_index = self.get_sequence(employee).get_step_index_of(activity) + 1
        return self.examine_insertion_at(task, employee, step_index, compute_times_only_if_skill_constraints_satisfied)

    def find_best_insertion_between_consecutive_activities(
            self, employee: Employee, task: Task, compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Find the best insertion of the given task between two consecutive activities of the given employee's
        sequence, that is to say:

        - if there is any feasible insertion,
          the best insertion is the feasible one that engenders the smallest additional traveling duration;
        - if there are no feasible insertions,
          the best insertion is the infeasible one that is the closest to be feasible duration-wise.

        Assumptions (only checked in debug):
        The times of this sequence are consistent.

        :param task: the task (Task) that would be inserted
        :param employee: the employee (Employee) whose planning would be changed
        :param compute_times_only_if_skill_constraints_satisfied: a boolean (bool) for telling whether
          if the skill constraints are not satisfied start times should still be computed
        :return: the examination of the best insertion (InsertionExamination)
        """
        return self.get_sequence(employee).find_best_insertion_between_consecutive_activities(
            task, compute_times_only_if_skill_constraints_satisfied=compute_times_only_if_skill_constraints_satisfied)

    def find_best_insertion_between_consecutive_activities_among_sets(
            self, tasks: list[Task], employees: list[Employee],
            compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Among all given employees and all given tasks, find the best insertion of a task in an employee's sequence,
        that is to say:

        - if there is any feasible insertion,
          the best insertion is the feasible one that engenders the smallest additional traveling duration;
        - if there are no feasible insertions,
          the best insertion is the infeasible one that is the closest to be feasible duration-wise.

        Assumptions (only checked in debug):
        The times of this sequence are consistent.

        :param tasks: the list of candidate tasks (Task) which would be inserted
        :param employees: the list of candidate employees (Employee) whose planning would be changed
        :param compute_times_only_if_skill_constraints_satisfied: a boolean (bool) for telling whether,
          if the skill constraints are not satisfied, start times should still be computed
        :return: the examination of the best insertion (InsertionExamination)
        """
        sequence = self.get_sequence(employees[0])
        best_insertion_examination = sequence.find_best_insertion_between_consecutive_activities_among_tasks_set(
            tasks, compute_times_only_if_skill_constraints_satisfied
        )
        for employee in employees[1:]:
            sequence = self.get_sequence(employee)
            examination = sequence.find_best_insertion_between_consecutive_activities_among_tasks_set(
                tasks, compute_times_only_if_skill_constraints_satisfied
            )
            # Case where the current insertion is feasible
            if examination.is_feasible:
                if not best_insertion_examination.is_feasible or \
                        (examination.travel_time_increase < best_insertion_examination.travel_time_increase):
                    best_insertion_examination = examination
            # Case where both the current insertion and the best currently known one are infeasible
            elif not best_insertion_examination.is_feasible:
                # Case where the current insertion is infeasible skill-wise
                if not examination.is_skill_feasible:
                    # task = self.instance.get_task_by_name(examination['task_name'])
                    # best_task = self.instance.get_task_by_name(best_insertion_examination['task_name'])
                    best_task = best_insertion_examination.inserted_task
                    best_employee = best_insertion_examination.employee
                    if not best_insertion_examination.is_skill_feasible and \
                            (examination.inserted_task.skill_level - employee.skill_level <
                             best_task.skill_level - best_employee.skill_level):
                        best_insertion_examination = examination
                # Case where the current insertion is feasible skill-wise
                else:
                    if not best_insertion_examination.is_skill_feasible:
                        best_insertion_examination = examination
                    # Case where both the current insertion and the best currently known one are feasible skill-wise
                    else:
                        # Case where the current insertion is infeasible upstream-wise
                        if not examination.is_upstream_feasible:
                            if not best_insertion_examination.is_upstream_feasible and \
                                    examination.late < best_insertion_examination.late:
                                best_insertion_examination = examination
                        # Case where the current insertion is feasible upstream-wise
                        else:
                            if not best_insertion_examination.is_upstream_feasible:
                                best_insertion_examination = examination
                            # Case where both the current insertion and the best currently known one
                            # are feasible upstream-wise
                            elif examination.late < best_insertion_examination.late:
                                best_insertion_examination = examination
        return best_insertion_examination

    ####################################################
    # Examining - Insertion - Feasible transformations #
    ####################################################

    def find_feasible_insertions_between_consecutive_activities(self, employee: Employee, task: Task):
        """
        Find all feasible insertions of the given task between two consecutive activities of the given employee's
        sequence.

        Assumptions (only checked in debug):
        The times of this sequence are consistent.

        :param task: the task (Task) that would be inserted
        :param employee: the employee (Employee) whose planning would be changed
        :return: the list of feasible insertions (list[InsertionExamination])
        """
        return self.get_sequence(employee).find_feasible_insertions_between_consecutive_activities(task)

    # TODO make it a SequenceForHeuristics method
    def find_best_feasible_insertion_between_consecutive_activities_for_each_task(self, tasks: list[Task],
                                                                                  employee: Employee):
        """
        Find, for each of the given tasks, the best feasible insertion (if any) of this task
        between two consecutive activities performed by the given employee

        :param tasks: the list of candidate tasks (list[Task]) that would be inserted
        :param employee: the employee (Employee) whose planning would be changed
        :return: a list of examinations (list[InsertionExamination])
        """
        examinations = []
        for task in tasks:
            examination = self.find_best_insertion_between_consecutive_activities(employee, task)
            if examination.is_feasible:
                examinations.append(examination)
        return examinations

    def find_best_feasible_insertion_between_consecutive_activities_for_each_employee(self, task: Task,
                                                                                      employees: list[Employee]):
        """
        Find, for each of the given employee, the best feasible insertion (if any) of the given task
        between two consecutive activities performed by the given employee

        :param task: the tasks (Task) that would be inserted
        :param employees: the list of candidate employees (list[Employee]) whose planning would be changed
        :return: a list of insertion examinations (list[InsertionExamination])
        """
        examinations = []
        for employee in employees:
            examination = self.find_best_insertion_between_consecutive_activities(employee, task)
            if examination.is_feasible:
                examinations.append(examination)
        return examinations

    #################################################
    # Examining - Replacement - Best transformation #
    #################################################

    def examine_replacing_task_with_another(self, employee: Employee, replaced_task: Task, replacing_task: Task,
                                            compute_times_only_if_skill_constraints_satisfied: bool = True):
        return self.get_sequence(employee).examine_replacing_task_with_another(
            replaced_task, replacing_task, compute_times_only_if_skill_constraints_satisfied
        )

    def examine_replacing_any_task_with_given_task(self, employee: Employee, replacing_task: Task,
                                                   compute_times_only_if_skill_constraints_satisfied: bool = True):
        return self.get_sequence(employee).find_best_task_to_be_replaced_with_given_task(
            replacing_task, compute_times_only_if_skill_constraints_satisfied
        )

    # TODO could be factorized with insertion among sets
    def find_best_replacement_among_sets(self, employees: list[Employee], tasks: list[Task],
                                         compute_times_only_if_skill_constraints_satisfied: bool = True):
        sequence = self.get_sequence(employees[0])
        best_swap_examination = sequence.find_best_replacement_among_various_replacing_tasks(
            tasks, compute_times_only_if_skill_constraints_satisfied
        )
        for employee in employees[1:]:
            sequence = self.get_sequence(employee)
            examination = sequence.find_best_replacement_among_various_replacing_tasks(
                tasks, compute_times_only_if_skill_constraints_satisfied
            )
            # Case where the current swap is feasible
            if examination.is_feasible:
                if not best_swap_examination.is_feasible or \
                        (examination.travel_time_increase <
                         best_swap_examination.travel_time_increase):
                    best_swap_examination = examination
            # Case where both the current swap and the best currently known one are infeasible
            elif not best_swap_examination.is_feasible:
                # Case where the current swap is infeasible skill-wise
                if not examination.is_skill_feasible:
                    # task = self.instance.get_task_by_name(examination['task_name'])
                    # best_task = self.instance.get_task_by_name(best_swap_examination['task_name'])
                    best_task = best_swap_examination.replacing_task
                    best_employee = best_swap_examination.employee
                    if not best_swap_examination.is_skill_feasible and \
                            (examination.replacing_task.skill_level - employee.skill_level <
                             best_task.skill_level - best_employee.skill_level):
                        best_swap_examination = examination
                # Case where the current swap is feasible skill-wise
                else:
                    if not best_swap_examination.is_skill_feasible:
                        best_swap_examination = examination
                    # Case where both the current swap and the best currently known one are feasible skill-wise
                    else:
                        # Case where the current swap is infeasible upstream-wise
                        if not examination.is_upstream_feasible:
                            if not best_swap_examination.is_upstream_feasible and \
                                    examination.late < best_swap_examination.late:
                                best_swap_examination = examination
                        # Case where the current swap is feasible upstream-wise
                        else:
                            if not best_swap_examination.is_upstream_feasible:
                                best_swap_examination = examination
                            # Case where both the current insertion and the best currently known one
                            # are feasible upstream-wise
                            elif examination.late < best_swap_examination.late:
                                best_swap_examination = examination
        return best_swap_examination

    ######################################################
    # Examining - Replacement - Feasible transformations #
    ######################################################

    # TODO make it a SequenceForHeuristics method
    def find_feasible_replacements_of_task_given_various_replacing_tasks(self, employee: Employee, replaced_task: Task,
                                                                         replacing_tasks: list[Task]):
        examinations = []
        for replacing_task in replacing_tasks:
            examination = self.examine_replacing_task_with_another(employee, replaced_task, replacing_task)
            if examination.is_feasible:
                examinations.append(examination)
        return examinations

    # TODO make it a SequenceForHeuristics method
    def find_best_feasible_replacement_for_each_replacing_task(self, employee: Employee, replacing_tasks: list[Task]):
        examinations = []
        for replacing_task in replacing_tasks:
            examination = self.examine_replacing_any_task_with_given_task(employee, replacing_task)
            if examination.is_feasible:
                examinations.append(examination)
        return examinations

    ##############################################
    # Examining - Reassign - Best transformation #
    ##############################################

    def examine_reassigning_task_after_activity(self, stolen_employee: Employee, moving_task: Task,
                                                stealing_employee: Employee, activity: Activity):
        """
        Examine the feasibility of moving the given moving task from the given stolen employee
        to the given stealing employee after the given activity

        :param stolen_employee:
        :param moving_task:
        :param stealing_employee:
        :param activity:
        :return:
        """
        # Compute the travel time decrease due to removing the moving task from the stolen employee
        stolen_sequence_copy = self.get_sequence(stolen_employee).copy()
        sequence_travel_time_before_removing = stolen_sequence_copy.total_traveling_duration
        moving_task_index = stolen_sequence_copy.get_step_index_of(moving_task)
        stolen_sequence_copy.remove_step(moving_task_index, False, True)
        sequence_travel_time_after_removing = stolen_sequence_copy.total_traveling_duration
        sequence_travel_time_decrease_due_to_removal = \
            sequence_travel_time_before_removing - sequence_travel_time_after_removing
        # Examine inserting the moving task after the given activity in the stealing employee sequence
        stealing_sequence = self.get_sequence(stealing_employee)
        insertion_step_index = stealing_sequence.get_step_index_of(activity) + 1
        insertion_examination = stealing_sequence.examine_insertion_at(moving_task, insertion_step_index)
        examination = ReassigningExamination.from_examination(insertion_examination)
        examination.moving_task = moving_task
        examination.stolen_employee = stolen_employee
        examination.stealing_employee = stealing_employee
        examination.activity_before_reassignment = activity
        examination.travel_time_increase -= sequence_travel_time_decrease_due_to_removal
        return examination

    def find_best_reassigning_in_employee_sequence(self, stolen_employee: Employee, moving_task: Task,
                                                   stealing_employee: Employee):
        """
        Find the best reassigning transformation in the given employee sequence

        :param stolen_employee:
        :param moving_task:
        :param stealing_employee:
        :return:
        """
        # TODO to implement
        raise NotImplementedError

    ############################################################
    # Examining - Reassign - Multiple feasible transformations #
    ############################################################

    def find_feasible_reassignments(self, stolen_employee: Employee, moving_task: Task, stealing_employee: Employee):
        """
        Find all feasible reassigning transformations in the given employee sequence

        :param stolen_employee:
        :param moving_task:
        :param stealing_employee:
        :return:
        """
        sequence = self.get_sequence(stealing_employee)
        examinations = []
        for step in sequence.get_steps(0, len(sequence) - 1):
            activity = step.activity
            examination = self.examine_reassigning_task_after_activity(stolen_employee, moving_task,
                                                                       stealing_employee, activity)
            if examination.is_feasible:
                examinations.append(examination)
        return examinations

    #############################################
    # Examining - Reorder - Best transformation #
    #############################################

    def examine_moving_after_a_task(self, employee: Employee, moving_task: Task, fixed_task: Task):
        """
        Examine the feasibility of moving the given task after the fixed task in the employee's sequence.

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given employee's sequence;
        - 2. the given fixed task must be in the given employee's sequence;
        - 3. the given moving task must be before the given fixed task in the given employee's sequence;
        - 4. the times of the given employee's sequence are consistent.

        :param employee: the employee whose sequence transformation is to be examined
        :param moving_task: the task to be moved
        :param fixed_task: the task after which the moving task is to be moved
        :return: a reordering examination (ReorderingExamination)
        """
        sequence = self.get_sequence(employee)
        return sequence.examine_moving_after_a_task(moving_task, fixed_task)

    def examine_moving_before_a_task(self, employee: Employee, moving_task: Task, fixed_task: Task):
        """
        Examine the feasibility of moving the given task before the fixed task in the employee's sequence.

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given employee's sequence;
        - 2. the given fixed task must be in the given employee's sequence;
        - 3. the given moving task must be before the given fixed task in the given employee's sequence;
        - 4. the times of the given employee's sequence are consistent.

        :param employee: the employee whose sequence transformation is to be examined
        :param moving_task: the task to be moved (Task)
        :param fixed_task: the task before which the moving task is to be moved (Task)
        :return: a reordering examination (ReorderingExamination)
        """
        sequence = self.get_sequence(employee)
        return sequence.examine_moving_before_a_task(moving_task, fixed_task)

    def find_best_reordering_later_in_employee_sequence(self, employee: Employee, moving_task: Task):
        """
        Find the best reordering transformation in the given employee sequence

        :param employee: the employee whose sequence transformation is to be examined (Employee)
        :param moving_task: the task to be moved (Task)
        :return: a reordering examination (ReorderingExamination)
        """
        sequence = self.get_sequence(employee)
        return sequence.find_best_reorder_to_perform_task_later(moving_task)

    def find_best_reordering_earlier_in_employee_sequence(self, employee: Employee, moving_task: Task):
        """
        Find the best reordering transformation in the given employee sequence

        :param moving_task: the task to be moved (Task)
        :param employee: the employee whose sequence transformation is to be examined (Employee)
        :return: a reordering examination (ReorderingExamination)
        """
        sequence = self.get_sequence(employee)
        return sequence.find_best_reorder_to_perform_task_earlier(moving_task)

    def find_best_reordering_in_employee_sequence(self, employee: Employee, moving_task: Task):
        """
        Find the best reordering transformation in the given employee sequence

        :param moving_task: the task to be moved (Task)
        :param employee: the employee whose sequence transformation is to be examined (Employee)
        :return: a reordering examination (ReorderingExamination)
        """
        sequence = self.get_sequence(employee)
        return sequence.find_best_task_reorder(moving_task)

    ###########################################################
    # Examining - Reorder - Multiple feasible transformations #
    ###########################################################

    def find_task_feasible_reorders(self, employee: Employee, task: Task):
        """
        Find all the feasible reorders of the given task in the given employee's sequence.

        Assumptions (only checked in debug):

        - 1. the given task must be in the given employee's sequence;
        - 2. the times of the given employee's sequence are consistent.

        :param employee: the employee whose sequence transformation is to be examined (Employee)
        :param task: the task to be reordered (Task)
        :return: a list of reorders examinations (list[ReorderExamination])
        """
        sequence = self.get_sequence(employee)
        return sequence.find_task_feasible_reorders(task)

    ####################################
    # Local change - Private - General #
    ####################################

    def _set_task_performance_to_non_performed(self, task: Task):
        task_performance = self._tasks_performances[task.name]
        task_performance[TASK_PERFORMANCE_STATUS_KEY] = False
        del task_performance[TASK_ASSIGNEE_KEY]
        del task_performance[TASK_START_TIME_KEY]

    def _set_task_performance_to_performed(self, task: Task, employee: Employee, startTime: int):
        task_performance = self._tasks_performances[task.name]
        task_performance[TASK_PERFORMANCE_STATUS_KEY] = True
        task_performance[TASK_ASSIGNEE_KEY] = employee.name
        task_performance[TASK_START_TIME_KEY] = startTime

    def _update_tasks_realizations_based_on_sequences(self, employee: Employee,
                                                      start_step_index: int, end_step_index: int):
        """
        Update the start times of the tasks which are realized by the given employee
        and which indices is between the given start and end indices (included)

        :param employee: the given employee (Employee)
        :param start_step_index: the index (included) from which the update starts (int)
        :param end_step_index: the index (included) to which the update ends (int)
        """
        sequence = self.__getitem__(employee.name)
        for step in sequence.get_steps(index_start=start_step_index, index_end=end_step_index + 1):
            if isinstance(step.activity, Task):
                self.set_task_start_time(step.activity, step.start_time)

    #####################################
    # Local change - Private - Feasible #
    #####################################

    def _replace_sequence_by_another(self, employee: Employee, new_sequence: SequenceForHeuristics,
                                     update_KPIs: bool = True):
        former_sequence = self.get_sequence(employee)
        former_sequence_KPIs = former_sequence.KPIs
        for task in former_sequence.get_contained_tasks():
            self._set_task_performance_to_non_performed(task)
        self._sequences[employee.name] = new_sequence
        for step in new_sequence.get_steps(1, -1):
            if isinstance(step.activity, Task):
                self._set_task_performance_to_performed(step.activity, employee, step.start_time)
        if update_KPIs:
            for key, value in former_sequence_KPIs.items():
                self._KPIs[key] += new_sequence.get_KPI(key) - value

    #############################
    # Local change - Infeasible #
    #############################

    #########################
    # Local change - Public #
    #########################

    def remove_task(self, task: Task, tighten_times: bool = True, update_KPIs: bool = True):
        """
        Remove the given task from the sequence of the employee who performs it.
        This local change is always feasible.

        The given task must be realized by an employee, otherwise a ValueError is raised.

        :param task: the task (Task) to remove from the sequence of the employee who performs it
        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence of the employee
          who performs the given task after it has been removed in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the change
        :return: a boolean (bool) to indicate whether the obtained solution is feasible
        """

        # Check that the given task is realized
        if not self.get_task_performance_status(task):
            raise ValueError(f"The given task {task.name} is not realized in this solution")

        # Get the sequence and the step index of the given task
        sequence = self.get_sequence(self.get_task_assignee(task))
        sequence_former_KPIs = sequence.KPIs
        step_index = sequence.get_step_index_of(task)

        # Remove the task from its assigned employee's sequence (and update tasks realizations)
        removed_task = sequence.get_step(step_index).activity
        sequence.remove_step(step_index, tighten_times, update_KPIs)
        self._set_task_performance_to_non_performed(removed_task)

        # Update KPIs if needed
        if update_KPIs:
            for key, former_value in sequence_former_KPIs.items():
                self._KPIs[key] += sequence.get_KPI(key) - former_value

        # Return a boolean True as the change is feasible
        return True

    def insert_task_after_activity(self, task: Task, activity: Activity, start_time: int = None,
                                   start_time_for_backward: int = None, start_time_for_forward: int = None,
                                   tighten_times: bool = True, update_KPIs: bool = True,
                                   ignore_skill_constraint: bool = False):
        """
        Insert the given task after the given activity in the sequence of the employee who performs the former:

        - if the change is known to be feasible, a start time for the task to insert shall be provided;

        - if the change is known to be infeasible, a start time for the task to insert,
          as well as two artificial start times for backward and forward computation, shall be provided;

        - if the feasibility of the change is not known, start times inputs shall remain vacant.

        The given activity must not be an employee's comeback, otherwise a ValueError is raised.
        The given activity must be realized by an employee, otherwise a ValueError is raised.
        This employee must be capable of realizing the given task to insert, otherwise a ValueError is also raised.

        :param task: the task (Task) to insert in the sequence of the employee who performs the given activity
        :param activity: the activity (Activity) after which the given task is inserted
        :param start_time: the start time of the task to insert
        :param start_time_for_backward: the artificial start time of the task to insert used for the computation of
          the times of the steps before the task to insert; to be used if the change is known to be infeasible
        :param start_time_for_forward: the artificial start time of the task to insert used for the computation of
          the times of the steps after the task to insert; to be used if the change is known to be infeasible
        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence of the employee
          who performs the given task after it has been removed in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the change
        :param ignore_skill_constraint:
        :return: a boolean (bool) to indicate whether the obtained solution is feasible
        """

        # Check that the given activity is not an employee's comeback
        if isinstance(activity, ComeBack):
            raise ValueError(f"The given task {task.name} cannot be inserted "
                             f"after the employee {activity.employee.name}'s comeback {activity.name}")

        # Check that the given activity is performed by an employee
        if not self.get_activity_realization(activity):
            raise ValueError(f"The given activity {activity.name} is not performed in this solution")

        # Check that the employee assigned to the activity is capable of performing the entering task
        employee = self.get_activity_assignee(activity)
        insertion_is_skill_feasible = employee.is_capable_of_performing(task)
        if not ignore_skill_constraint and not insertion_is_skill_feasible:
            raise ValueError(f"The employee {employee.name} who performs the given activity {activity.name} "
                             f"is not capable of realizing the given task to insert {task.name}")

        # If the task to insert is realized, remove it from its assigned employee's sequence
        if self.get_task_performance_status(task):
            self.remove_task(task, tighten_times, update_KPIs)

        # Get the sequence and the step index of the given activity
        sequence = self.get_sequence(employee)
        sequence_former_KPIs = sequence.KPIs
        step_index = self.get_sequence(employee).get_step_index_of(activity)

        # Insert the given task in the sequence (and update tasks realizations)
        is_feasible, (first_step_with_time_change_index, last_step_with_time_change_index) = \
            sequence.insert_task_at(
                task, step_index + 1,
                start_time, start_time_for_backward, start_time_for_forward,
                tighten_times, update_KPIs
            )
        is_feasible &= insertion_is_skill_feasible
        self._set_task_performance_to_performed(task, employee, start_time)
        self._update_tasks_realizations_based_on_sequences(
            employee, max(first_step_with_time_change_index, 1),
            min(last_step_with_time_change_index, len(sequence) - 2)
        )

        # Update the solution's KPIs if needed
        if update_KPIs:
            for key, value in sequence_former_KPIs.items():
                self._KPIs[key] += sequence.get_KPI(key) - value

        # Return whether the insertion has given a feasible solution
        return is_feasible

    def replace_task_by_another(self, leaving_task: Task, replacing_task: Task, start_time: int = None,
                                start_time_for_backward: int = None, start_time_for_forward: int = None,
                                tighten_times: bool = True, update_KPIs: bool = True,
                                ignore_skill_constraint: bool = False):
        """
        Change the given leaving task by the replacing task in the sequence of the employee who performs the former:

        - if the change is known to be feasible, a start time for the replacing task shall be provided;

        - if the change is known to be infeasible, a start time for the replacing task,
          as well as two artificial start times for backward and forward computation, shall be provided;

        - if the feasibility of the change is not known, start times inputs shall remain vacant.

        The given leaving task must be realized by an employee, otherwise a ValueError is raised.
        This employee must be capable of realizing the given replacing task, otherwise a ValueError is also raised.

        :param leaving_task: the leaving task (Task) to remove from the sequence of the employee who performs it
        :param replacing_task: the replacing task (Task) to insert in the sequence to replace the leaving task
        :param start_time: the start time of the replacing task
        :param start_time_for_backward: the artificial start time of the replacing task used for the computation of
          the times of the steps before the replacing task; to be used if the change is known to be infeasible
        :param start_time_for_forward: the artificial start time of the replacing task used for the computation of
          the times of the steps after the replacing task; to be used if the change is known to be infeasible
        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence of the employee
          who performs the given task after it has been removed in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the change
        :param ignore_skill_constraint:
        :return: a boolean (bool) to indicate whether the obtained solution is feasible
        """

        # Check that the given leaving task is realized
        if not self.get_task_performance_status(leaving_task):
            raise ValueError(f"The given leaving task {leaving_task.name} is not realized in this solution")

        # Check that the employee assigned to the leaving task is capable of realizing the replacing task
        employee = self.get_task_assignee(leaving_task)
        if not ignore_skill_constraint and not employee.is_capable_of_performing(replacing_task):
            raise ValueError(f"The employee {employee.name} who performs the given leaving task {leaving_task.name} "
                             f"is not capable of realizing the given replacing task {replacing_task.name}")

        # Check that the start times inputs are consistent
        if (start_time is None) and ((start_time_for_backward is not None) or (start_time_for_forward is not None)):
            raise ValueError("The start times for backward and forward can be given as inputs "
                             "only if a start time is also given")

        # If the replacing task is realized, remove it from its assigned employee's sequence
        if self.get_task_performance_status(replacing_task):
            self.remove_task(replacing_task, tighten_times, update_KPIs)

        # Get the sequence and the step index of the given leaving task
        sequence = self.get_sequence(employee)
        sequence_former_KPIs = sequence.KPIs
        step_index = self.get_sequence(employee).get_step_index_of(leaving_task)

        # Replace the given leaving task by the replacing task in the sequence (and update tasks realizations)
        is_feasible, (first_step_with_time_change_index, last_step_with_time_change_index) = \
            sequence.replace_task_by_another_at(
                replacing_task, step_index,
                start_time, start_time_for_backward, start_time_for_forward,
                tighten_times, update_KPIs
            )
        self._set_task_performance_to_non_performed(leaving_task)
        self._set_task_performance_to_performed(replacing_task, employee, start_time)
        self._update_tasks_realizations_based_on_sequences(
            employee, max(first_step_with_time_change_index, 1),
            min(last_step_with_time_change_index, len(sequence) - 2)
        )

        # Update the solution's KPIs if needed
        if update_KPIs:
            for key, value in sequence_former_KPIs.items():
                self._KPIs[key] += sequence.get_KPI(key) - value

        # Return whether the insertion has given a feasible solution
        return is_feasible

    def reassign_task_after_activity(self, task: Task, activity: Activity, start_time: int = None,
                                     start_time_for_backward: int = None, start_time_for_forward: int = None,
                                     tighten_times: bool = True, update_KPIs: bool = True,
                                     ignore_skill_constraint: bool = False):
        """
        Reassign the given task to the employee who performs the given activity:

        :param task:
        :param activity:
        :param start_time:
        :param start_time_for_backward:
        :param start_time_for_forward:
        :param tighten_times:
        :param update_KPIs:
        :param ignore_skill_constraint:
        :return:
        """
        return self.insert_task_after_activity(task, activity, start_time, start_time_for_backward,
                                               start_time_for_forward, tighten_times, update_KPIs,
                                               ignore_skill_constraint)

    def shift_task_in_sequence_after_activity(self, task: Task, activity: Activity, start_time: int = None,
                                              start_time_for_backward: int = None, start_time_for_forward: int = None,
                                              tighten_times: bool = True, update_KPIs: bool = True):
        """
        Move a given task after a given activity in the sequence of the employee who performs these task and activity:

        - if the move is known to be feasible, a start time for the moving task shall be provided;

        - if the move is known to be infeasible, a start time for the moving task,
          as well as two artificial start times for backward and forward computation, shall be provided;

        - if the feasibility of the move is not known, start times inputs shall remain vacant.

        The given moving task must be performed by an employee, otherwise a ValueError is raised.
        The given activity must be performed by the same employee, otherwise a ValueError is raised.
        The given activity must not be the last activity of the sequence, otherwise a ValueError is raised.

        :param task: the task (Task) to move in the sequence of the employee who performs it
        :param activity: the activity (Activity) after which the moving task shall be inserted
        :param start_time: the start time (int) of the moving task
        :param start_time_for_backward: the artificial start time (int) of the moving task used for computing the times
          of the steps before the moving task once reinserted; to be used if the move is known to be infeasible
        :param start_time_for_forward: the artificial start time (int) of the moving task used for computing the times
          of the steps after the moving task; to be used if the move is known to be infeasible
        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence of the employee
          who performs the given task and activity after transformation in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the shift
        :return: a boolean (bool) to indicate whether the obtained solution is feasible
        """

        # Check that the task is performed and that the activity is performed
        if not self.get_task_performance_status(task):
            raise ValueError(f"The given moving task {task.name} is not performed in this solution")
        if isinstance(activity, Task) and not self.get_task_performance_status(activity):
            raise ValueError(f"The given activity {activity.name} is not performed in this solution")

        # Check that the employee assigned to the moving task is also assigned to the given activity
        employee = self.get_task_assignee(task)
        if self.get_activity_assignee(activity) != employee:
            raise ValueError(f"The employee {employee.name} who performs the given moving task {task.name} "
                             f"is not assigned to the given activity {activity.name}")

        # Check that the activity is not the last activity of the sequence
        if isinstance(activity, ComeBack):
            raise ValueError(f"The given activity {activity.name} is the last activity of the sequence")

        # Check that the start times inputs are consistent
        if (start_time is None) and ((start_time_for_backward is not None) or (start_time_for_forward is not None)):
            raise ValueError("The start times for backward and forward can be given as inputs "
                             "only if a start time is also given")

        # Get the sequence and the step index of the given moving task
        # sequence = self.get_sequence(employee)
        # sequence_former_KPIs = sequence.KPIs
        # step_index = self.get_sequence(employee).get_step_index_of(task)

        # Remove the given moving task from its assigned employee's sequence
        self.remove_task(task, tighten_times, update_KPIs)
        is_feasible = self.insert_task_after_activity(task, activity, start_time,
                                                      start_time_for_backward, start_time_for_forward,
                                                      tighten_times, update_KPIs)
        return is_feasible

    def shift_task_in_sequence_before_activity(self, task: Task, activity: Activity, start_time: int = None,
                                               start_time_for_backward: int = None, start_time_for_forward: int = None,
                                               tighten_times: bool = True, update_KPIs: bool = True):
        """
        Move a given task before a given activity in the sequence of the employee who performs these task and activity:

        - if the move is known to be feasible, a start time for the moving task shall be provided;

        - if the move is known to be infeasible, a start time for the moving task,
          as well as two artificial start times for backward and forward computation, shall be provided;

        - if the feasibility of the move is not known, start times inputs shall remain vacant.

        The given moving task must be performed by an employee, otherwise a ValueError is raised.
        The given activity must be performed by the same employee, otherwise a ValueError is raised.
        The given activity must not be the first activity of the sequence, otherwise a ValueError is raised.

        :param task: the task (Task) to move in the sequence of the employee who performs it
        :param activity: the activity (Activity) before which the moving task shall be inserted
        :param start_time: the start time (int) of the moving task
        :param start_time_for_backward: the artificial start time (int) of the moving task used for computing the times
          of the steps before the moving task once reinserted; to be used if the move is known to be infeasible
        :param start_time_for_forward: the artificial start time (int) of the moving task used for computing the times
          of the steps after the moving task; to be used if the move is known to be infeasible
        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence of the employee
          who performs the given task and activity after transformation in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the shift
        :return: a boolean (bool) to indicate whether the obtained solution is feasible
        """

        # Check assumptions
        # - Check that the task is performed and that the activity is performed
        if not self.get_task_performance_status(task):
            raise ValueError(f"The given moving task {task.name} is not performed in this solution")
        if isinstance(activity, Task) and not self.get_task_performance_status(activity):
            raise ValueError(f"The given activity {activity.name} is not performed in this solution")
        # - Check that the employee assigned to the moving task is also assigned to the given activity
        employee = self.get_task_assignee(task)
        if self.get_activity_assignee(activity) != employee:
            raise ValueError(f"The employee {employee.name} who performs the given moving task {task.name} "
                             f"is not assigned to the given activity {activity.name}")
        # - Check that the activity is not the first activity of the sequence
        if isinstance(activity, ComeBack):
            raise ValueError(f"The given activity {activity.name} is the last activity of the sequence")
        # - Check that the start times inputs are consistent
        if (start_time is None) and ((start_time_for_backward is not None) or (start_time_for_forward is not None)):
            raise ValueError("The start times for backward and forward can be given as inputs "
                             "only if a start time is also given")

        # Shift the task in the sequence using the method for shifting after an activity
        sequence = self.get_sequence(employee)
        step_index_of_activity_before = sequence.get_step_index_of(activity) - 1
        activity_before = sequence.get_step(step_index_of_activity_before).activity
        return self.shift_task_in_sequence_after_activity(task, activity_before, start_time,
                                                          start_time_for_backward, start_time_for_forward,
                                                          tighten_times, update_KPIs)

    #################
    # Miscellaneous #
    #################

    # TODO to remove
    def try_inserting(self, employee: Employee, task: Task,
                      tighten_times: bool = True, update_KPIs: bool = True):

        # If the task to insert is realized by an employee,
        # then remove it from his/her sequence
        if self.get_task_performance_status(task):
            self.remove_task(task, False, update_KPIs)

        # Create and run the IP model for sequence optimization with attempt to insert new task
        model = IPModelForSequenceInserting(self.get_sequence(employee), task)
        model.optimize(mute=True)

        # Get the sequence obtained by solving the IP model
        new_sequence = SequenceForHeuristics.from_Sequence(model.solution_sequence)

        # If the task has been inserted,
        if task in new_sequence.get_contained_tasks():

            # Replace sequence
            if update_KPIs:
                new_sequence.compute_KPIs()
            if tighten_times:
                new_sequence.tighten_times(update_KPIs)
            self._replace_sequence_by_another(employee, new_sequence, update_KPIs)

            # Return whether the insertion has given a feasible solution
            return True

    def insert_task_at_all_costs(self, employee: Employee, task: Task,
                                 tighten_times: bool = True, update_KPIs: bool = True):
        """
        TODO

        :param employee:
        :param task:
        :param tighten_times:
        :param update_KPIs:
        :return:
        """

        # If the task to insert is realized by an employee,
        # then remove it from his/her sequence
        if self.get_task_performance_status(task):
            self.remove_task(task, False, update_KPIs)

        # Create and run the IP model for sequence optimization with assigned tasks
        candidate_tasks = self.get_sequence(employee).get_contained_tasks() + [task]
        prescribed_tasks = [task]
        model = IPModelForSequencePrescribing(self._instance, employee, candidate_tasks, prescribed_tasks)
        model.optimize(mute=True)

        # Save the sequence obtained by solving the IP model
        if not model.has_solution_sequence:
            raise Exception(f"Inserting the task(s) {[task.name for task in prescribed_tasks]} "
                            f"in {employee}'s sequence is infeasible")
        new_sequence = SequenceForHeuristics.from_Sequence(model.solution_sequence)
        if update_KPIs:
            new_sequence.compute_KPIs()
        if tighten_times:
            new_sequence.tighten_times(update_KPIs)

        # Replace sequence
        self._replace_sequence_by_another(employee, new_sequence, update_KPIs)

        # Return whether the insertion has given a feasible solution
        return True

    def reorder(self, employee: Employee, tighten_times: bool = True, update_KPIs: bool = True):

        # Create and run the IP model for sequence reordering optimization
        model = IPModelForSequenceReordering(self.get_sequence(employee))
        model.optimize(mute=True)

        # Save the sequence obtained by solving the IP model
        if not model.has_solution_sequence:
            raise Exception(f"Reordering the tasks in {employee}'s sequence is infeasible")
        new_sequence = SequenceForHeuristics.from_Sequence(model.solution_sequence)
        if update_KPIs:
            new_sequence.compute_KPIs()
        if tighten_times:
            new_sequence.tighten_times(update_KPIs)

        # Replace sequence
        self._replace_sequence_by_another(employee, new_sequence, update_KPIs)

        # Return whether the insertion has given a feasible solution
        return True
