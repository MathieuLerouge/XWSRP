# Local libraries
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack
from src.modeling.constants import NB_PERFORMED_TASKS_KEY, TOTAL_TRAVELING_DURATION_KEY, TOTAL_WORKING_DURATION_KEY, \
    TOTAL_TRAVELING_DISTANCE_KEY, TOTAL_IDLE_TIME_KEY
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.solution import Solution, TASK_PERFORMANCE_STATUS_KEY, TASK_ASSIGNEE_KEY, TASK_START_TIME_KEY
from src.modeling.task import Task
from src.optimization.IP.sequence.insertingmodel import IPModelForSequenceInserting
from src.optimization.IP.sequence.prescribingmodel import IPModelForSequencePrescribing
from src.optimization.IP.sequence.reorderingmodel import IPModelForSequenceReordering
from src.optimization.localsearch.sequence import SequenceLS
from src.optimization.solution import SolutionOpti


# Global variables
LS_ID = "LS"


# Class SolutionLS
class SolutionLS(SolutionOpti):

    def __init__(self, instance: Instance, name: str = None, sequences: dict[str, SequenceLS] = None,
                 tasks_realizations: dict = None, lunch_breaks_realizations: dict = None):
        super().__init__(LS_ID, instance, name, None, tasks_realizations, lunch_breaks_realizations)
        self._sequences = sequences

    @classmethod
    def from_SolutionOpti(cls, solution: SolutionOpti):
        sequences = dict([(employee_name, SequenceLS.from_Sequence(sequence))
                          for (employee_name, sequence) in solution._sequences.items()])
        return cls(solution.instance, solution.name, sequences,
                   solution._copy_tasks_realizations(), solution._copy_lunch_breaks_realizations())

    @classmethod
    def from_Solution(cls, solution: Solution):
        sequences = dict([(employee_name, SequenceLS.from_Sequence(sequence))
                          for (employee_name, sequence) in solution._sequences.items()])
        return cls(solution.instance, solution.name, sequences,
                   solution._copy_tasks_realizations(), solution._copy_lunch_breaks_realizations())

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
        solution = SolutionLS(self._instance, name, self._copy_sequences(),
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

    #########################
    # Examining - Insertion #
    #########################

    def examine_insertion_at(self, entering_task: Task, employee: Employee, step_index: int,
                             compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Examine the feasibility of the insertion of the given entering task at the given step index;
        provide a dictionary, describing this examination, with keys:
        'is_feasible', 'is_skill_feasible', 'is_time_feasible', 'is_upstream_feasible', 'is_downstream_feasible',
        'start_time', 'earliest_start_time_for_upstream', 'latest_start_time_for_downstream' and
        'traveling_duration_detour'.

        - If the insertion is feasible, the value associated to the key 'start_time' is the start time (int)
          that could be applied to the entering task, when following the earliest policy,
          whereas the values associated to 'earliest_start_time_for_upstream' and
          'latest_start_time_for_downstream' are both None;
        - If the insertion is infeasible, the values associated to the keys 'earliest_start_time_for_upstream' and
          'latest_start_time_for_downstream' are the start times that could be applied to the entering task so that
          the time consistency of respectively the upstream and the downstream portions of the sequence,
          while the value associated to the keys 'start_time' is an average of these artificial values.

        Assumptions (only checked in debug):

        - 1. the given entering task must not be already in this sequence;
        - 2. the given step index must be between 1 (included) and the number of steps - 1 (included);
        - 3. the times of this sequence are consistent.

        :param entering_task: the task (Task) that is figured to be inserted
        :param employee: the employee (Employee) who would perform the entering task
        :param step_index: the index of the step (int) where the given task would be inserted
        :param compute_times_only_if_skill_constraints_satisfied: a boolean (bool) for telling whether or not
          if the skill constraints are not satisfied start times should still be computed
        :return: the examination dictionary
        """
        return self.get_sequence(employee).examine_insertion_at(entering_task, step_index,
                                                                compute_times_only_if_skill_constraints_satisfied)

    def examine_insertion_after(self, entering_task: Task, employee: Employee, activity: Activity,
                                compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Examine the feasibility of the insertion of the given entering task after the given activity
        in the employee's sequence; provide a dictionary, describing this examination, with keys:
        'is_feasible', 'is_upstream_feasible', 'is_downstream_feasible',
        'start_time', 'earliest_start_time_for_upstream', 'latest_start_time_for_downstream' and
        'traveling_duration_detour'.

        - If the insertion is feasible, the value associated to the key 'start_time' is the start time (int)
          that could be applied to the entering task, when following the earliest policy,
          whereas the values associated to 'earliest_start_time_for_upstream' and
          'latest_start_time_for_downstream' are both None;
        - If the insertion is infeasible, the values associated to the keys 'earliest_start_time_for_upstream' and
          'latest_start_time_for_downstream' are the start times that could be applied to the entering task so that
          the time consistency of respectively the upstream and the downstream portions of the sequence,
          while the value associated to the keys 'start_time' is an average of these artificial values.

        Assumptions (only checked in debug):

        - 1. the given entering task must not be already in this sequence;
        - 2. the given activity must be in the given employee's sequence;
        - 3. the times of this sequence are consistent.

        :param entering_task: the task (Task) that is figured to be inserted
        :param employee: the employee (Employee) who would perform the entering task
        :param activity: the activity (Activity) after which the given task would be inserted
        :param compute_times_only_if_skill_constraints_satisfied: a boolean (bool) for telling whether or not
          if the skill constraints are not satisfied start times should still be computed
        :return: the examination dictionary
        """
        step_index = self.get_sequence(employee).get_step_index_of(activity) + 1
        return self.examine_insertion_at(entering_task, employee, step_index,
                                         compute_times_only_if_skill_constraints_satisfied)

    def examine_best_insertion_between_consecutive_activities(
            self, task: Task, employee: Employee, compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Examine the best insertion of the given task between two consecutive activities of the given employee's
        sequence, that is to say:

        - if there is any feasible insertion,
          the best insertion is the feasible one that engenders the smallest additional traveling duration;
        - if there are no feasible insertions,
          the best insertion is the infeasible one that is the closest to be feasible duration-wise.

        Provide a dictionary describing this examination with keys:
        'is_feasible', 'is_skill_feasible', 'is_time_feasible', 'is_upstream_feasible', 'step_index_for_insertion',
        'start_time', 'earliest_start_time_for_upstream', 'latest_start_time_for_downstream',
        'traveling_duration_detour' and 'late'.

        Assumptions (only checked in debug):
        The times of this sequence are consistent.

        :param task: the task (Task) that would be inserted
        :param employee: the employee (Employee) whose planning would be changed
        :param compute_times_only_if_skill_constraints_satisfied: a boolean (bool) for telling whether or not
          if the skill constraints are not satisfied start times should still be computed
        :return: the examination dictionary
        """
        return self.get_sequence(employee).examine_best_insertion_between_consecutive_activities(
            task, compute_times_only_if_skill_constraints_satisfied=compute_times_only_if_skill_constraints_satisfied)

    def examine_best_insertion_between_consecutive_activities_among_sets(
            self, tasks: list[Task], employees: list[Employee],
            compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Among all employees and all tasks of given sets, examine the best insertion of a task in an employee's sequence,
        that is to say:

        - if there is any feasible insertion,
          the best insertion is the feasible one that engenders the smallest additional traveling duration;
        - if there are no feasible insertions,
          the best insertion is the infeasible one that is the closest to be feasible duration-wise.

        Provide a dictionary describing this examination with keys:
        'is_feasible', 'is_skill_feasible', 'is_time_feasible', 'is_upstream_feasible', 'step_index_for_insertion',
        'start_time', 'earliest_start_time_for_upstream', 'latest_start_time_for_downstream',
        'traveling_duration_detour', 'late', 'task_name' and 'employee_name'.

        Assumptions (only checked in debug):
        The times of this sequence are consistent.

        :param tasks: the list of candidate tasks (Task) that may be inserted
        :param employees:
        :param compute_times_only_if_skill_constraints_satisfied: a boolean (bool) for telling whether or not
          if the skill constraints are not satisfied start times should still be computed
        :return: the examination dictionary
        """
        best_employee = employees[0]
        sequence = self.get_sequence(best_employee)
        best_insertion_examination = sequence.examine_best_insertion_between_consecutive_activities_among_tasks_set(
            tasks, compute_times_only_if_skill_constraints_satisfied
        )
        for employee in employees[1:]:
            sequence = self.get_sequence(employee)
            examination = sequence.examine_best_insertion_between_consecutive_activities_among_tasks_set(
                tasks, compute_times_only_if_skill_constraints_satisfied
            )
            # Case where the current insertion is feasible
            if examination['is_feasible']:
                if not best_insertion_examination['is_feasible'] or \
                        (examination['traveling_duration_detour'] <
                         best_insertion_examination['traveling_duration_detour']):
                    best_insertion_examination = examination
                    best_employee = employee
            # Case where both the current insertion and the best currently known one are infeasible
            elif not best_insertion_examination['is_feasible']:
                # Case where the current insertion is infeasible skill-wise
                if not examination['is_skill_feasible']:
                    task = self.instance.get_task_by_name(examination['task_name'])
                    best_task = self.instance.get_task_by_name(best_insertion_examination['task_name'])
                    if not best_insertion_examination['is_skill_feasible'] and \
                            (task.skill_level - employee.skill_level <
                             best_task.skill_level - best_employee.skill_level):
                        best_insertion_examination = examination
                        best_employee = employee
                # Case where the current insertion is feasible skill-wise
                else:
                    if not best_insertion_examination['is_skill_feasible']:
                        best_insertion_examination = examination
                        best_employee = employee
                    # Case where both the current insertion and the best currently known one are feasible skill-wise
                    else:
                        # Case where the current insertion is infeasible upstream-wise
                        if not examination['is_upstream_feasible']:
                            if not best_insertion_examination['is_upstream_feasible'] and \
                                    examination['late'] < best_insertion_examination['late']:
                                best_insertion_examination = examination
                                best_employee = employee
                        # Case where the current insertion is feasible upstream-wise
                        else:
                            if not best_insertion_examination['is_upstream_feasible']:
                                best_insertion_examination = examination
                                best_employee = employee
                            # Case where both the current insertion and the best currently known one
                            # are feasible upstream-wise
                            elif examination['late'] < best_insertion_examination['late']:
                                best_insertion_examination = examination
                                best_employee = employee
        best_insertion_examination['employee_name'] = best_employee.name
        return best_insertion_examination

    # TODO deprecated, remove
    def examine_best_insertion_deprecated(self, task: Task, employee: Employee = None, tabu_indices: list[int] = None):
        if employee is None:
            insertion_is_feasible = False
            insertion_is_upstream_feasible = False
            best_examination = {'employee': None}
            for employee in self._instance.employees:
                if employee.is_capable_of_performing(task):
                    examination = self.get_sequence(employee).examine_best_insertion_between_consecutive_activities(task)
                    if examination['is_feasible']:
                        if not insertion_is_feasible:
                            insertion_is_feasible = True
                            insertion_is_upstream_feasible = True
                            best_examination = examination
                            best_examination['employee'] = employee
                        elif examination['traveling_duration_detour'] < best_examination['traveling_duration_detour']:
                            best_examination = examination
                            best_examination['employee'] = employee
                    elif examination['is_upstream_feasible']:
                        if not insertion_is_feasible:
                            if not insertion_is_upstream_feasible:
                                insertion_is_upstream_feasible = True
                                best_examination = examination
                                best_examination['employee'] = employee
                            elif examination['late'] < best_examination['late']:
                                best_examination = examination
                                best_examination['employee'] = employee
                    else:
                        if not insertion_is_upstream_feasible:
                            if best_examination['employee'] is None:
                                best_examination = examination
                                best_examination['employee'] = employee
                            elif examination['late'] < best_examination['late']:
                                best_examination = examination
                                best_examination['employee'] = employee
            return best_examination
        else:
            return self.get_sequence(employee).examine_best_insertion_between_consecutive_activities(task, tabu_indices)

    ####################
    # Examining - Swap #
    ####################

    def examine_swap_with_a_task(self, employee: Employee, entering_task: Task, leaving_task: Task,
                                 compute_times_only_if_skill_constraints_satisfied: bool = True):
        return self.get_sequence(employee).examine_swap_with_a_task(entering_task, leaving_task,
                                                                    compute_times_only_if_skill_constraints_satisfied)

    def examine_swap_with_any_task(self, employee: Employee, task: Task,
                                   compute_times_only_if_skill_constraints_satisfied: bool = True):
        return self.get_sequence(employee).examine_swap_with_any_task(task,
                                                                      compute_times_only_if_skill_constraints_satisfied)

    # TODO could be factorized with insertion among sets
    def examine_swap_tasks_among_sets(self, employees: list[Employee], tasks: list[Task],
                                      compute_times_only_if_skill_constraints_satisfied: bool = True):
        best_employee = employees[0]
        sequence = self.get_sequence(best_employee)
        best_swap_examination = sequence.examine_best_swap_tasks_among_tasks_set(
            tasks, compute_times_only_if_skill_constraints_satisfied
        )
        for employee in employees[1:]:
            sequence = self.get_sequence(employee)
            examination = sequence.examine_best_swap_tasks_among_tasks_set(
                tasks, compute_times_only_if_skill_constraints_satisfied
            )
            # Case where the current swap is feasible
            if examination['is_feasible']:
                if not best_swap_examination['is_feasible'] or \
                        (examination['traveling_duration_detour'] <
                         best_swap_examination['traveling_duration_detour']):
                    best_swap_examination = examination
                    best_employee = employee
            # Case where both the current swap and the best currently known one are infeasible
            elif not best_swap_examination['is_feasible']:
                # Case where the current swap is infeasible skill-wise
                if not examination['is_skill_feasible']:
                    task = self.instance.get_task_by_name(examination['task_name'])
                    best_task = self.instance.get_task_by_name(best_swap_examination['task_name'])
                    if not best_swap_examination['is_skill_feasible'] and \
                            (task.skill_level - employee.skill_level <
                             best_task.skill_level - best_employee.skill_level):
                        best_swap_examination = examination
                        best_employee = employee
                # Case where the current swap is feasible skill-wise
                else:
                    if not best_swap_examination['is_skill_feasible']:
                        best_swap_examination = examination
                        best_employee = employee
                    # Case where both the current swap and the best currently known one are feasible skill-wise
                    else:
                        # Case where the current swap is infeasible upstream-wise
                        if not examination['is_upstream_feasible']:
                            if not best_swap_examination['is_upstream_feasible'] and \
                                    examination['late'] < best_swap_examination['late']:
                                best_swap_examination = examination
                                best_employee = employee
                        # Case where the current swap is feasible upstream-wise
                        else:
                            if not best_swap_examination['is_upstream_feasible']:
                                best_swap_examination = examination
                                best_employee = employee
                            # Case where both the current insertion and the best currently known one
                            # are feasible upstream-wise
                            elif examination['late'] < best_swap_examination['late']:
                                best_swap_examination = examination
                                best_employee = employee
        best_swap_examination['employee_name'] = best_employee.name
        return best_swap_examination

    ####################################
    # Local change - Private - General #
    ####################################

    def _set_task_performance_to_non_performed(self, task: Task):
        task_performance = self._tasks_realizations[task.name]
        task_performance[TASK_PERFORMANCE_STATUS_KEY] = False
        del task_performance[TASK_ASSIGNEE_KEY]
        del task_performance[TASK_START_TIME_KEY]

    def _set_task_performance_to_performed(self, task: Task, employee: Employee, startTime: int):
        task_performance = self._tasks_realizations[task.name]
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

    def _replace_sequence_by_another(self, employee: Employee, new_sequence: SequenceLS,
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
        Remove the given task from the sequence of the employee who realizes it.
        This local change is always feasible.

        The given task must be realized by an employee, otherwise a ValueError is raised.

        :param task: the task (Task) to remove from the sequence of the employee who realizes it
        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence of the employee
          who realizes the given task after it has been removed in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the change
        :return: a boolean (bool) to indicate whether or not the obtained solution is feasible
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
        Insert the given task after the given activity in the sequence of the employee who realizes the former:

        - if the change is known to be feasible, a start time for the task to insert shall be provided;

        - if the change is known to be infeasible, a start time for the task to insert,
          as well as two artificial start times for backward and forward computation, shall be provided;

        - if the feasibility of the change is not known, start times inputs shall remain vacant.

        The given activity must not be an employee's comeback, otherwise a ValueError is raised.
        The given activity must be realized by an employee, otherwise a ValueError is raised.
        This employee must be capable of realizing the given task to insert, otherwise a ValueError is also raised.

        :param task: the task (Task) to insert in the sequence of the employee who realizes the given activity
        :param activity: the activity (Activity) after which the given task is inserted
        :param start_time: the start time of the task to insert
        :param start_time_for_backward: the artificial start time of the task to insert used for the computation of
          the times of the steps before the task to insert; to be used if the change is known to be infeasible
        :param start_time_for_forward: the artificial start time of the task to insert used for the computation of
          the times of the steps after the task to insert; to be used if the change is known to be infeasible
        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence of the employee
          who realizes the given task after it has been removed in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the change
        :param ignore_skill_constraint:
        :return: a boolean (bool) to indicate whether or not the obtained solution is feasible
        """

        # Check that the given activity is not an employee's comeback
        if isinstance(activity, ComeBack):
            raise ValueError(f"The given task {task.name} cannot be inserted "
                             f"after the employee {activity.employee}'s comeback {activity.name}")

        # Check that the given activity is performed by an employee
        if not self.get_activity_realization(activity):
            raise ValueError(f"The given activity {activity.name} is not performed in this solution")

        # Check that the employee assigned to the activity is capable of performing the entering task
        employee = self.get_activity_assignee(activity)
        insertion_is_skill_feasible = employee.is_capable_of_performing(task)
        if not ignore_skill_constraint and not insertion_is_skill_feasible:
            raise ValueError(f"The employee {employee.name} who realizes the given activity {activity.name} "
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

        # Return whether or not the insertion has given a feasible solution
        return is_feasible

    def replace_task_by_another(self, leaving_task: Task, replacing_task: Task, start_time: int = None,
                                start_time_for_backward: int = None, start_time_for_forward: int = None,
                                tighten_times: bool = True, update_KPIs: bool = True,
                                ignore_skill_constraint: bool = False):
        """
        Change the given leaving task by the replacing task in the sequence of the employee who realizes the former:

        - if the change is known to be feasible, a start time for the replacing task shall be provided;

        - if the change is known to be infeasible, a start time for the replacing task,
          as well as two artificial start times for backward and forward computation, shall be provided;

        - if the feasibility of the change is not known, start times inputs shall remain vacant.

        The given leaving task must be realized by an employee, otherwise a ValueError is raised.
        This employee must be capable of realizing the given replacing task, otherwise a ValueError is also raised.

        :param leaving_task: the leaving task (Task) to remove from the sequence of the employee who realizes it
        :param replacing_task: the replacing task (Task) to insert in the sequence to replace the leaving task
        :param start_time: the start time of the replacing task
        :param start_time_for_backward: the artificial start time of the replacing task used for the computation of
          the times of the steps before the replacing task; to be used if the change is known to be infeasible
        :param start_time_for_forward: the artificial start time of the replacing task used for the computation of
          the times of the steps after the replacing task; to be used if the change is known to be infeasible
        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence of the employee
          who realizes the given task after it has been removed in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the change
        :param ignore_skill_constraint:
        :return: a boolean (bool) to indicate whether or not the obtained solution is feasible
        """

        # Check that the given leaving task is realized
        if not self.get_task_performance_status(leaving_task):
            raise ValueError(f"The given leaving task {leaving_task.name} is not realized in this solution")

        # Check that the employee assigned to the leaving task is capable of realizing the replacing task
        employee = self.get_task_assignee(leaving_task)
        if not ignore_skill_constraint and not employee.is_capable_of_performing(replacing_task):
            raise ValueError(f"The employee {employee.name} who realizes the given leaving task {leaving_task.name} "
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

        # Return whether or not the insertion has given a feasible solution
        return is_feasible

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
        new_sequence = SequenceLS.from_Sequence(model.solution_sequence)

        # If the task has been inserted,
        if task in new_sequence.get_contained_tasks():

            # Replace sequence
            if update_KPIs:
                new_sequence.compute_KPIs()
            if tighten_times:
                new_sequence.tighten_times(update_KPIs)
            self._replace_sequence_by_another(employee, new_sequence, update_KPIs)

            # Return whether or not the insertion has given a feasible solution
            return True

        # If the task has not been inserted,
        else:
            return False

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
        new_sequence = SequenceLS.from_Sequence(model.solution_sequence)
        if update_KPIs:
            new_sequence.compute_KPIs()
        if tighten_times:
            new_sequence.tighten_times(update_KPIs)

        # Replace sequence
        self._replace_sequence_by_another(employee, new_sequence, update_KPIs)

        # Return whether or not the insertion has given a feasible solution
        return True

    def reorder(self, employee: Employee, tighten_times: bool = True, update_KPIs: bool = True):

        # Create and run the IP model for sequence reordering optimization
        model = IPModelForSequenceReordering(self.get_sequence(employee))
        model.optimize(mute=True)

        # Save the sequence obtained by solving the IP model
        if not model.has_solution_sequence:
            raise Exception(f"Reordering the tasks in {employee}'s sequence is infeasible")
        new_sequence = SequenceLS.from_Sequence(model.solution_sequence)
        if update_KPIs:
            new_sequence.compute_KPIs()
        if tighten_times:
            new_sequence.tighten_times(update_KPIs)

        # Replace sequence
        self._replace_sequence_by_another(employee, new_sequence, update_KPIs)

        # Return whether or not the insertion has given a feasible solution
        return True
