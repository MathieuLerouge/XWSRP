# Local libraries
from model.activity import Activity
from model.comeback import ComeBack
from model.employee import Employee
from model.instance import Instance
from model.solution import Solution
from model.task import Task
from model.constants import *
from optimization.IP.SequenceModel import IPModelForSequence
from optimization.localsearch.sequence import SequenceLS
from optimization.solution import SolutionOpti


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
        return self._KPIs[NB_REALIZED_TASKS_KEY]

    @_nb_realized_tasks.setter
    def _nb_realized_tasks(self, nb_realized_tasks: int):
        self._KPIs[NB_REALIZED_TASKS_KEY] = nb_realized_tasks

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

    def copy(self, copy_name=False):
        name = self._name if copy_name else self._name + "_Copy"
        solution = SolutionLS(self._instance, None, self._copy_sequences(),
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
            former_sequence_idle_time = sequence.total_idle_time
            sequence.tighten_times(update_KPIs)
            if update_KPIs:
                self._total_idle_time += sequence.total_idle_time - former_sequence_idle_time

    ###############
    # Time Slacks #
    ###############

    def update_time_slacks(self):
        for sequence in self._sequences.values():
            sequence.update_time_slacks()

    ##############
    # Looking up #
    ##############

    def examine_insertion_at(self, entering_task: Task, employee: Employee, step_index: int):
        return self.get_sequence(employee).examine_insertion_at(entering_task, step_index)

    def examine_best_insertion_when_alone(self, employee: Employee, task: Task):
        sequence = self.get_sequence(employee).copy()
        sequence.remove_all_tasks(False, False)
        examination = sequence.examine_best_insertion(task)
        sequence.insert_task_at(
            task, examination['step_index_for_insertion'], examination['start_time'],
            examination['earliest_start_time_for_upstream'], examination['latest_start_time_for_downstream'],
            False, False
        )
        solution = self.copy(True)
        solution._replace_sequence_by_another(employee, sequence)
        examination['solution'] = solution
        return examination

    def examine_best_insertion(self, task: Task, employee: Employee = None, tabu_indices: list[int] = None):
        if employee is None:
            insertion_is_feasible = False
            insertion_is_upstream_feasible = False
            best_examination = {'employee': None}
            for employee in self._instance.employees:
                if employee.is_capable_of_realizing(task):
                    examination = self.get_sequence(employee).examine_best_insertion(task)
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
                                print(best_examination)
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
            return self.get_sequence(employee).examine_best_insertion(task, tabu_indices)

    def findBestInsertion(self, task: Task):
        insertionResult = dict()
        insertionResult['feasible'] = False
        insertionResult['employee'] = None
        insertionResult['step_index'] = None
        insertionResult['start_time'] = None
        insertionResult['travelingDurationVariation'] = None
        insertionResult['late'] = None
        insertionResult['taskSkillLevelTooHigh'] = True
        insertionResult['taskTooFar'] = True
        for employee in self._instance.employees:
            employeeInsertionResult = self.get_sequence(employee).examine_best_insertion(task)
            if employeeInsertionResult['feasible']:
                insertionResult['feasible'] = True
                insertionResult['taskSkillLevelTooHigh'] = False
                if insertionResult['taskTooFar']:
                    insertionResult['taskTooFar'] = False
                    insertionResult['late'] = None
                if insertionResult['travelingDurationVariation'] == None or \
                        employeeInsertionResult['travelingDurationVariation'] < insertionResult[
                    'travelingDurationVariation']:
                    insertionResult['employee'] = employee
                    insertionResult['step_index'] = employeeInsertionResult['step_index']
                    insertionResult['start_time'] = employeeInsertionResult['start_time']
                    insertionResult['travelingDurationVariation'] = employeeInsertionResult[
                        'travelingDurationVariation']
            else:
                if not (employeeInsertionResult['taskSkillLevelTooHigh']):
                    insertionResult['taskSkillLevelTooHigh'] = False
                    if employeeInsertionResult['taskTooFar']:
                        if insertionResult['taskTooFar']:
                            if insertionResult['late'] == None or employeeInsertionResult['late'] < insertionResult[
                                'late']:
                                insertionResult['employee'] = employee
                                insertionResult['step_index'] = employeeInsertionResult['step_index']
                                insertionResult['start_time'] = employeeInsertionResult['start_time']
                                insertionResult['travelingDurationVariation'] = employeeInsertionResult[
                                    'travelingDurationVariation']
                                insertionResult['late'] = employeeInsertionResult['late']
                    else:
                        if insertionResult['taskTooFar']:
                            insertionResult['taskTooFar'] = False
                            insertionResult['late'] = None
                        if insertionResult['late'] == None or employeeInsertionResult['late'] < insertionResult[
                            'late']:
                            insertionResult['employee'] = employee
                            insertionResult['step_index'] = employeeInsertionResult['step_index']
                            insertionResult['start_time'] = employeeInsertionResult['start_time']
                            insertionResult['travelingDurationVariation'] = employeeInsertionResult[
                                'travelingDurationVariation']
                            insertionResult['late'] = employeeInsertionResult['late']

        return insertionResult

    ####################################
    # Local change - Private - General #
    ####################################

    def _set_task_realization_to_unrealized(self, task: Task):
        task_realization = self._tasks_realizations[task.name]
        task_realization['realized'] = False
        del task_realization['employee_name']
        del task_realization['start_time']

    def _set_task_realization_to_realized(self, task: Task, employee: Employee, startTime: int):
        task_realization = self._tasks_realizations[task.name]
        task_realization['realized'] = True
        task_realization['employee_name'] = employee.name
        task_realization['start_time'] = startTime

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
            self._set_task_realization_to_unrealized(task)
        self._sequences[employee.name] = new_sequence
        for step in new_sequence.get_steps(1, -1):
            if isinstance(step.activity, Task):
                self._set_task_realization_to_realized(step.activity, employee, step.start_time)
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
        if not self.get_task_realization(task):
            raise ValueError(f"The given task {task.name} is not realized in this solution")

        # Get the sequence and the step index of the given task
        sequence = self.get_sequence(self.get_task_assignee(task))
        sequence_former_KPIs = sequence.KPIs
        step_index = sequence.get_step_index_of(task)

        # Remove the task from its assigned employee's sequence (and update tasks realizations)
        removed_task = sequence.get_step(step_index).activity
        sequence.remove_step(step_index, tighten_times, update_KPIs)
        self._set_task_realization_to_unrealized(removed_task)

        # Update KPIs if needed
        if update_KPIs:
            for key, former_value in sequence_former_KPIs.items():
                self._KPIs[key] += sequence.get_KPI(key) - former_value

        # Return a boolean True as the change is feasible
        return True

    def insert_task_after_activity(self, task: Task, activity: Activity, start_time: int = None,
                                   start_time_for_backward: int = None, start_time_for_forward: int = None,
                                   tighten_times: bool = True, update_KPIs: bool = True):
        """
        Insert the given task after the given activity in the sequence of the employee who realizes the former:

        - if the change is known to be feasible, a start time for the task to insert shall be provided;

        - if the change is known to be infeasible, a start time for the task task to insert,
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
        :return: a boolean (bool) to indicate whether or not the obtained solution is feasible
        """

        # Check that the given activity is not the employee's comeback
        if isinstance(activity, ComeBack):
            raise ValueError(f"The given task {task.name} cannot be inserted "
                             f"after the employee {activity.employee}'s comeback {activity.name}")

        # Check that the given activity is realized by an employee
        if not self.get_activity_realization(activity):
            raise ValueError(f"The given activity {activity.name} is not realized in this solution")

        # Check that the employee assigned to the leaving task is capable of realizing the entering task
        employee = self.get_activity_assignee(activity)
        if not employee.is_capable_of_realizing(task):
            raise ValueError(f"The employee {employee.name} who realizes the given activity {activity.name} "
                             f"is not capable of realizing the given task to insert {task.name}")

        # If the task to insert is realized, remove it from its assigned employee's sequence
        if self.get_task_realization(task):
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
        self._set_task_realization_to_realized(task, employee, start_time)
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
                                tighten_times: bool = True, update_KPIs: bool = True):
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
        :return: a boolean (bool) to indicate whether or not the obtained solution is feasible
        """

        # Check that the given leaving task is realized
        if not self.get_task_realization(leaving_task):
            raise ValueError(f"The given leaving task {leaving_task.name} is not realized in this solution")

        # Check that the employee assigned to the leaving task is capable of realizing the replacing task
        employee = self.get_task_assignee(leaving_task)
        if not employee.is_capable_of_realizing(replacing_task):
            raise ValueError(f"The employee {employee.name} who realizes the given leaving task {leaving_task.name} "
                             f"is not capable of realizing the given replacing task {replacing_task.name}")

        # Check that the start times inputs are consistent
        if (start_time is None) and ((start_time_for_backward is not None) or (start_time_for_forward is not None)):
            raise ValueError("The start times for backward and forward can be given as inputs "
                             "only if a start time is also given")

        # If the replacing task is realized, remove it from its assigned employee's sequence
        if self.get_task_realization(replacing_task):
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
        self._set_task_realization_to_realized(replacing_task, employee, start_time)
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
        if self.get_task_realization(task):
            self.remove_task(task, False, update_KPIs)

        # Create and run the IP model for sequence optimization
        former_sequence_tasks = self.get_sequence(employee).get_contained_tasks()
        candidate_tasks = former_sequence_tasks + [task]
        prescribed_tasks = [task]
        model = IPModelForSequence(self._instance, employee, candidate_tasks, prescribed_tasks)
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
        removed_tasks = set(former_sequence_tasks).difference(new_sequence.get_contained_tasks())
        self._replace_sequence_by_another(employee, new_sequence, update_KPIs)

        # Return whether or not the insertion has given a feasible solution
        # as well as removed tasks
        return True, removed_tasks
