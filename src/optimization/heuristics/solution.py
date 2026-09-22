# Standard libraries
from contextlib import nullcontext
from typing import Optional, cast

# Local libraries
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.lunchbreakperformance import LunchBreakPerformance
from src.modeling.solution import Solution
from src.modeling.task import Task
from src.modeling.taskperformance import TaskPerformance
from src.optimization.heuristics.sequence import SequenceForHeuristics
from src.optimization.heuristics.slacks import SlackTimeComputer
from src.optimization.milp.subproblems.sequenceinsertingmodel import SequenceInsertingModel
from src.optimization.milp.subproblems.sequenceprescribingmodel import SequencePrescribingModel
from src.optimization.milp.subproblems.sequencereorderingmodel import SequenceReorderingModel
from src.optimization.solution import SolutionOpti


# Global variables
HEURISTIC_ID = "heuristic"


#########################
# SolutionForHeuristics #
#########################

class SolutionForHeuristics(SolutionOpti):
    """
    A Solution extended with per-employee SequenceForHeuristics (state and mutation operations for the heuristics)
    and the local-change operations (insertion, removal, replacement, reassignment, reorder)
    the heuristics build their moves from.
    """

    def __init__(
            self, instance: Instance, name: Optional[str] = None,
            sequences: Optional[dict[str, SequenceForHeuristics]] = None,
            tasks_realizations: Optional[dict[str, TaskPerformance]] = None,
            lunch_breaks_realizations: Optional[dict[str, LunchBreakPerformance]] = None,
            heuristic_id: Optional[str] = None
    ):
        """
        Args:
            instance: The instance this solution belongs to.
            name: The name of this solution. If None, a default name is used.
            sequences: The per-employee sequences making up this solution.
              If None, an empty SequenceForHeuristics is created for each of the instance's employees.
            tasks_realizations: The realization (assignee, start time) of each performed task, by task name.
            lunch_breaks_realizations: The realization of each employee's lunch break, by employee name, if any.
            heuristic_id: The identifier of the heuristic that produced this solution.
              If None, HEURISTIC_ID is used.
        """
        heuristic_id = HEURISTIC_ID if heuristic_id is None else heuristic_id
        super().__init__(instance, name, None, tasks_realizations, lunch_breaks_realizations, heuristic_id)
        if sequences is None:
            sequences = dict()
            for employee in self._instance.employees:
                sequences[employee.name] = SequenceForHeuristics(instance, employee)
        self._sequences = sequences
        self.compute_kpis()

    @classmethod
    def from_solution_opti(cls, solution: SolutionOpti, heuristic_id: Optional[str] = None):
        sequences = dict([(employee_name, SequenceForHeuristics.from_sequence(sequence))
                          for (employee_name, sequence) in solution._sequences.items()])
        name = solution.name if heuristic_id is None else None
        return cls(solution.instance, name, sequences,
                   solution._copy_tasks_realizations(), solution._copy_lunch_breaks_realizations(), heuristic_id)

    @classmethod
    def from_solution(cls, solution: Solution, heuristic_id: Optional[str] = None):
        sequences = dict([(employee_name, SequenceForHeuristics.from_sequence(sequence))
                          for (employee_name, sequence) in solution._sequences.items()])
        name = solution.name if heuristic_id is None else None
        return cls(solution.instance, name, sequences,
                   solution._copy_tasks_realizations(), solution._copy_lunch_breaks_realizations(), heuristic_id)

    @property
    def _nb_performed_tasks(self) -> int:
        """Number of tasks performed in this solution."""
        return self._kpis.nb_performed_tasks

    @_nb_performed_tasks.setter
    def _nb_performed_tasks(self, nb_performed_tasks: int):
        self._kpis.nb_performed_tasks = nb_performed_tasks

    @property
    def _total_traveling_duration(self) -> int:
        """Total time, in minutes, spent traveling between steps across this solution's sequences."""
        return self._kpis.total_traveling_duration

    @_total_traveling_duration.setter
    def _total_traveling_duration(self, total_traveling_duration: int):
        self._kpis.total_traveling_duration = total_traveling_duration

    @property
    def _total_working_duration(self) -> int:
        """Total time, in minutes, spent performing tasks across this solution's sequences."""
        return self._kpis.total_working_duration

    @_total_working_duration.setter
    def _total_working_duration(self, total_working_duration: int):
        self._kpis.total_working_duration = total_working_duration

    @property
    def _total_traveling_distance(self) -> float:
        """Total distance, in km, traveled across this solution's sequences."""
        return self._kpis.total_traveling_distance

    @_total_traveling_distance.setter
    def _total_traveling_distance(self, total_traveling_distance: float):
        self._kpis.total_traveling_distance = total_traveling_distance

    @property
    def _total_idle_time(self) -> int:
        """Total idle time, in minutes, spent waiting between steps across this solution's sequences."""
        return self._kpis.total_idle_time

    @_total_idle_time.setter
    def _total_idle_time(self, total_idle_time: int):
        self._kpis.total_idle_time = total_idle_time

    ############
    # Sequence #
    ############

    @property
    def _sequences_for_heuristics(self) -> dict[str, SequenceForHeuristics]:
        """self._sequences, narrowed to the SequenceForHeuristics values this subclass always stores."""
        return cast(dict[str, SequenceForHeuristics], self._sequences)

    def get_sequence(self, employee: Employee) -> SequenceForHeuristics:
        return self._sequences_for_heuristics[employee.name]

    def compute_sequences_based_on_tasks_performances(self):
        """
        Rebuild every employee's sequence from the current tasks performances.

        Overridden so that this solution keeps holding SequenceForHeuristics.
        """
        super().compute_sequences_based_on_tasks_performances()
        self._sequences = {
            employee_name: SequenceForHeuristics.from_sequence(sequence)
            for employee_name, sequence in self._sequences.items()
        }
        self.compute_kpis()

    ########
    # Copy #
    ########

    def _copy_sequences(self) -> dict[str, SequenceForHeuristics]:
        return cast(dict[str, SequenceForHeuristics], super()._copy_sequences())

    def copy(self, name: Optional[str] = None):
        name = self._name + "_copy" if name is None else name
        solution = SolutionForHeuristics(
            self._instance, name, self._copy_sequences(),
            self._copy_tasks_realizations(), self._copy_lunch_breaks_realizations()
        )
        solution.name = name
        solution._kpis = self._copy_kpis()
        return solution

    ###############
    # Time Slacks #
    ###############

    def tighten_times(self, update_kpis: bool = True):
        """
        Shift the steps of every employee's sequence as close together as their time slacks allow,
        to minimize idle time.

        Args:
            update_kpis: Whether to keep this solution's idle-time KPI up to date after the change.
        """
        for sequence in self._sequences_for_heuristics.values():
            if update_kpis:
                former_sequence_idle_time = sequence.total_idle_time
                SlackTimeComputer.tighten_times(sequence, update_kpis)
                self._total_idle_time += sequence.total_idle_time - former_sequence_idle_time
            else:
                SlackTimeComputer.tighten_times(sequence, update_kpis)

    def update_time_slacks(self):
        """Recompute the BTS and FTS slacks of every step of every employee's sequence, from scratch."""
        for sequence in self._sequences_for_heuristics.values():
            SlackTimeComputer.update_time_slacks(sequence)

    ###############################
    # Mutations - Private helpers #
    ###############################

    def _set_task_performance_to_non_performed(self, task: Task):
        task_performance = self._tasks_performances[task.name]
        task_performance.performed = False
        task_performance.assignee_name = None
        task_performance.start_time = None

    def _set_task_performance_to_performed(self, task: Task, employee: Employee, start_time: int):
        task_performance = self._tasks_performances[task.name]
        task_performance.performed = True
        task_performance.assignee_name = employee.name
        task_performance.start_time = start_time

    def _update_tasks_realizations_based_on_sequences(
            self, employee: Employee, start_step_index: int, end_step_index: int
    ):
        """
        Update the start times of the tasks which are performed by the given employee
        and which indices is between the given start and end indices (included).

        Args:
            employee: The given employee.
            start_step_index: The index (included) from which the update starts.
            end_step_index: The index (included) to which the update ends.
        """
        sequence = self.__getitem__(employee.name)
        for step in sequence.get_steps(index_start=start_step_index, index_end=end_step_index + 1):
            if isinstance(step.activity, Task):
                self.set_task_start_time(step.activity, step.start_time)

    def _replace_sequence_by_another(
            self, employee: Employee, new_sequence: SequenceForHeuristics, update_kpis: bool = True
    ):
        """
        Replace the given employee's sequence by the given new sequence,
        updating tasks performances and this solution's KPIs accordingly.

        Args:
            employee: The employee whose sequence is replaced.
            new_sequence: The sequence to replace the employee's current one with.
            update_kpis: Whether to keep this solution's KPIs up to date after the change.
        """
        former_sequence = self.get_sequence(employee)
        former_sequence_kpis = former_sequence.kpis
        for task in former_sequence.get_contained_tasks():
            self._set_task_performance_to_non_performed(task)
        self._sequences[employee.name] = new_sequence
        for step in new_sequence.get_steps(1, -1):
            if isinstance(step.activity, Task):
                self._set_task_performance_to_performed(step.activity, employee, step.start_time)
        if update_kpis:
            self._kpis = self._kpis + (new_sequence.kpis - former_sequence_kpis)

    #############
    # Mutations #
    #############

    def remove_task(self, task: Task, tighten_times: bool = True, update_kpis: bool = True):
        """
        Remove the given task from the sequence of the employee who performs it.
        This local change is always feasible.

        The given task must be performed by an employee, otherwise a ValueError is raised.

        Args:
            task: The task to remove from the sequence of the employee who performs it.
            tighten_times: If True, tightens the times of the sequence of the employee who performs the
              given task after it has been removed, in order to minimize idle time.
            update_kpis: Whether to keep the KPIs up to date after the change.

        Returns:
            Whether the obtained solution is feasible.

        Raises:
            ValueError: If the given task is not performed in this solution.
        """

        # Check that the given task is performed
        if not self.get_task_performance_status(task):
            raise ValueError(f"The given task {task.name} is not performed in this solution")

        # Get the sequence and the step index of the given task
        sequence = self.get_sequence(self.get_task_assignee(task))
        sequence_former_kpis = sequence.kpis
        step_index = sequence.get_step_index_of(task)

        # Remove the task from its assigned employee's sequence (and update tasks realizations)
        removed_task = sequence.get_step(step_index).activity
        with SlackTimeComputer.suspend_tightening(sequence) if not tighten_times else nullcontext():
            sequence.remove_step(step_index)
        self._set_task_performance_to_non_performed(removed_task)

        # Update KPIs if needed
        if update_kpis:
            self._kpis = self._kpis + (sequence.kpis - sequence_former_kpis)

        # Return a boolean True as the change is feasible
        return True

    def insert_task_after_activity(
            self, task: Task, activity: Activity, start_time: Optional[int] = None,
            start_time_for_backward: Optional[int] = None, start_time_for_forward: Optional[int] = None,
            tighten_times: bool = True, update_kpis: bool = True, ignore_skill_constraint: bool = False
    ):
        """
        Insert the given task after the given activity in the sequence of the employee who performs the former:

        - if the change is known to be feasible, a start time for the task to insert shall be provided;

        - if the change is known to be infeasible, a start time for the task to insert,
          as well as two artificial start times for backward and forward computation, shall be provided;

        - if the feasibility of the change is not known, start times inputs shall remain vacant.

        The given activity must not be an employee's comeback, otherwise a ValueError is raised.
        The given activity must be realized by an employee, otherwise a ValueError is raised.
        This employee must be capable of performing the given task to insert, otherwise a ValueError is also raised.

        Args:
            task: The task to insert in the sequence of the employee who performs the given activity.
            activity: The activity after which the given task is inserted.
            start_time: The start time of the task to insert.
            start_time_for_backward: The artificial start time of the task to insert used for the
              computation of the times of the steps before it; to be used if the change is known to be infeasible.
            start_time_for_forward: The artificial start time of the task to insert used for the
              computation of the times of the steps after it; to be used if the change is known to be infeasible.
            tighten_times: If True, tightens the times of the sequence of the employee who performs the
              given task after it has been inserted, in order to minimize idle time.
            update_kpis: Whether to keep the KPIs up to date after the change.
            ignore_skill_constraint: If True, the insertion is performed even if the employee who performs
              the given activity is not capable of performing the given task, rather than raising a ValueError.

        Returns:
            Whether the obtained solution is feasible.

        Raises:
            ValueError: If the given activity is the employee's comeback, is not realized in this solution,
              or if the employee who performs it is not capable of performing the given task and
              ignore_skill_constraint is False.
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
                             f"is not capable of performing the given task to insert {task.name}")

        # If the task to insert is performed, remove it from its assigned employee's sequence
        if self.get_task_performance_status(task):
            self.remove_task(task, tighten_times, update_kpis)

        # Get the sequence and the step index of the given activity
        sequence = self.get_sequence(employee)
        sequence_former_kpis = sequence.kpis
        step_index = self.get_sequence(employee).get_step_index_of(activity)

        # Insert the given task in the sequence (and update tasks realizations)
        with SlackTimeComputer.suspend_tightening(sequence) if not tighten_times else nullcontext():
            is_feasible, (first_step_with_time_change_index, last_step_with_time_change_index) = \
                sequence.insert_task_at(
                    task, step_index + 1,
                    start_time, start_time_for_backward, start_time_for_forward
                )
        is_feasible &= insertion_is_skill_feasible
        self._set_task_performance_to_performed(task, employee, start_time)
        self._update_tasks_realizations_based_on_sequences(
            employee, max(first_step_with_time_change_index, 1),
            min(last_step_with_time_change_index, len(sequence) - 2)
        )

        # Update the solution's KPIs if needed
        if update_kpis:
            self._kpis = self._kpis + (sequence.kpis - sequence_former_kpis)

        # Return whether the insertion has given a feasible solution
        return is_feasible

    def insert_task_by_reordering_sequence(
            self, employee: Employee, task: Task, tighten_times: bool = True, update_kpis: bool = True
    ):
        """
        Insert the given task in the given employee's sequence at all costs, using a MILP-based sequence-
        prescribing model that forces the task to be performed, replacing the employee's sequence with
        the one obtained.

        Args:
            employee: The employee whose sequence the task is inserted in.
            task: The task to insert.
            tighten_times: If True, tightens the times of the new sequence after the insertion,
              in order to minimize idle time.
            update_kpis: Whether to keep the KPIs up to date after the change.

        Returns:
            True, since the insertion is enforced by the underlying MILP model.

        Raises:
            ValueError: If the underlying MILP model has no solution, meaning the insertion is infeasible
              given the employee's other prescribed tasks.
        """

        # If the task to insert is performed by an employee,
        # then remove it from his/her sequence
        if self.get_task_performance_status(task):
            self.remove_task(task, False, update_kpis)

        # Create and run the IP model for sequence optimization with assigned tasks
        candidate_tasks = self.get_sequence(employee).get_contained_tasks() + [task]
        prescribed_tasks = [task]
        model = SequencePrescribingModel(self._instance, employee, candidate_tasks, prescribed_tasks)
        model.solve(mute=True)

        # Save the sequence obtained by solving the IP model
        if not model.has_solution_sequence:
            raise ValueError(f"Inserting the task(s) {[task.name for task in prescribed_tasks]} "
                             f"in {employee}'s sequence is infeasible")
        new_sequence = SequenceForHeuristics.from_sequence(model.solution_sequence)
        if update_kpis:
            new_sequence.compute_kpis()
        if tighten_times:
            SlackTimeComputer.tighten_times(new_sequence, update_kpis)

        # Replace sequence
        self._replace_sequence_by_another(employee, new_sequence, update_kpis)

        # Return whether the insertion has given a feasible solution
        return True

    def replace_task_by_another(
            self, leaving_task: Task, replacing_task: Task, start_time: Optional[int] = None,
            start_time_for_backward: Optional[int] = None, start_time_for_forward: Optional[int] = None,
            tighten_times: bool = True, update_kpis: bool = True, ignore_skill_constraint: bool = False
    ):
        """
        Change the given leaving task by the replacing task in the sequence of the employee who performs the former:

        - if the change is known to be feasible, a start time for the replacing task shall be provided;

        - if the change is known to be infeasible, a start time for the replacing task,
          as well as two artificial start times for backward and forward computation, shall be provided;

        - if the feasibility of the change is not known, start times inputs shall remain vacant.

        The given leaving task must be performed by an employee, otherwise a ValueError is raised.
        This employee must be capable of performing the given replacing task, otherwise a ValueError is also raised.

        Args:
            leaving_task: The leaving task to remove from the sequence of the employee who performs it.
            replacing_task: The replacing task to insert in the sequence in place of the leaving task.
            start_time: The start time of the replacing task.
            start_time_for_backward: The artificial start time of the replacing task used for the
              computation of the times of the steps before it; to be used if the change is known to be infeasible.
            start_time_for_forward: The artificial start time of the replacing task used for the
              computation of the times of the steps after it; to be used if the change is known to be infeasible.
            tighten_times: If True, tightens the times of the sequence of the employee who performs the
              given task after the replacement, in order to minimize idle time.
            update_kpis: Whether to keep the KPIs up to date after the change.
            ignore_skill_constraint: If True, the replacement is performed even if the employee who
              performs the leaving task is not capable of performing the replacing task, rather than
              raising a ValueError.

        Returns:
            Whether the obtained solution is feasible.

        Raises:
            ValueError: If the given leaving task is not performed in this solution, if the employee who
              performs it is not capable of performing the given replacing task and ignore_skill_constraint
              is False, or if start_time_for_backward/start_time_for_forward are given without start_time.
        """

        # Check that the given leaving task is performed
        if not self.get_task_performance_status(leaving_task):
            raise ValueError(f"The given leaving task {leaving_task.name} is not performed in this solution")

        # Check that the employee assigned to the leaving task is capable of performing the replacing task
        employee = self.get_task_assignee(leaving_task)
        replacement_is_skill_feasible = employee.is_capable_of_performing(replacing_task)
        if not ignore_skill_constraint and not replacement_is_skill_feasible:
            raise ValueError(f"The employee {employee.name} who performs the given leaving task {leaving_task.name} "
                             f"is not capable of performing the given replacing task {replacing_task.name}")

        # Check that the start times inputs are consistent
        if (start_time is None) and ((start_time_for_backward is not None) or (start_time_for_forward is not None)):
            raise ValueError("The start times for backward and forward can be given as inputs "
                             "only if a start time is also given")

        # If the replacing task is performed, remove it from its assigned employee's sequence
        if self.get_task_performance_status(replacing_task):
            self.remove_task(replacing_task, tighten_times, update_kpis)

        # Get the sequence and the step index of the given leaving task
        sequence = self.get_sequence(employee)
        sequence_former_kpis = sequence.kpis
        step_index = self.get_sequence(employee).get_step_index_of(leaving_task)

        # Replace the given leaving task by the replacing task in the sequence (and update tasks realizations)
        with SlackTimeComputer.suspend_tightening(sequence) if not tighten_times else nullcontext():
            is_feasible, (first_step_with_time_change_index, last_step_with_time_change_index) = \
                sequence.replace_task_by_another_at(
                    replacing_task, step_index,
                    start_time, start_time_for_backward, start_time_for_forward
                )
        is_feasible &= replacement_is_skill_feasible
        self._set_task_performance_to_non_performed(leaving_task)
        self._set_task_performance_to_performed(replacing_task, employee, start_time)
        self._update_tasks_realizations_based_on_sequences(
            employee, max(first_step_with_time_change_index, 1),
            min(last_step_with_time_change_index, len(sequence) - 2)
        )

        # Update the solution's KPIs if needed
        if update_kpis:
            self._kpis = self._kpis + (sequence.kpis - sequence_former_kpis)

        # Return whether the insertion has given a feasible solution
        return is_feasible

    def reassign_task_after_activity(
            self, task: Task, activity: Activity, start_time: Optional[int] = None,
            start_time_for_backward: Optional[int] = None, start_time_for_forward: Optional[int] = None,
            tighten_times: bool = True, update_kpis: bool = True, ignore_skill_constraint: bool = False):
        """
        Reassign the given task to the employee who performs the given activity, inserting it after that
        activity: a thin wrapper around insert_task_after_activity(), removing the given task from its
        current assignee first if needed (handled by insert_task_after_activity() itself).

        Args:
            task: The task to reassign.
            activity: The activity after which the given task is inserted, in its performer's sequence.
            start_time: The start time of the task to insert.
            start_time_for_backward: The artificial start time of the task to insert used for the
              computation of the times of the steps before it; to be used if the change is known to be infeasible.
            start_time_for_forward: The artificial start time of the task to insert used for the
              computation of the times of the steps after it; to be used if the change is known to be infeasible.
            tighten_times: If True, tightens the times of the sequence of the employee who performs the
              given task after the reassignment, in order to minimize idle time.
            update_kpis: Whether to keep the KPIs up to date after the change.
            ignore_skill_constraint: If True, the reassignment is performed even if the employee who
              performs the given activity is not capable of performing the given task, rather than
              raising a ValueError.

        Returns:
            Whether the obtained solution is feasible.
        """
        return self.insert_task_after_activity(task, activity, start_time, start_time_for_backward,
                                               start_time_for_forward, tighten_times, update_kpis,
                                               ignore_skill_constraint)

    def reposition_task_in_sequence_after_activity(
            self, task: Task, activity: Activity, start_time: Optional[int] = None,
            start_time_for_backward: Optional[int] = None, start_time_for_forward: Optional[int] = None,
            tighten_times: bool = True, update_kpis: bool = True
    ):
        """
        Move a given task after a given activity in the sequence of the employee who performs these task and activity:

        - if the move is known to be feasible, a start time for the moving task shall be provided;

        - if the move is known to be infeasible, a start time for the moving task,
          as well as two artificial start times for backward and forward computation, shall be provided;

        - if the feasibility of the move is not known, start times inputs shall remain vacant.

        The given moving task must be performed by an employee, otherwise a ValueError is raised.
        The given activity must be performed by the same employee, otherwise a ValueError is raised.
        The given activity must not be the last activity of the sequence, otherwise a ValueError is raised.

        Args:
            task: The task to move in the sequence of the employee who performs it.
            activity: The activity after which the moving task shall be inserted.
            start_time: The start time of the moving task.
            start_time_for_backward: The artificial start time of the moving task used for computing the
              times of the steps before it once reinserted; to be used if the move is known to be infeasible.
            start_time_for_forward: The artificial start time of the moving task used for computing the
              times of the steps after it; to be used if the move is known to be infeasible.
            tighten_times: If True, tightens the times of the sequence of the employee who performs the
              given task and activity after the transformation, in order to minimize idle time.
            update_kpis: Whether to keep the KPIs up to date after the shift.

        Returns:
            Whether the obtained solution is feasible.

        Raises:
            ValueError: If the given moving task is not performed in this solution, if the given activity
              is a task that is not performed in this solution, if the given activity is not performed by
              the same employee as the moving task, if the given activity is the last activity of the
              sequence, or if start_time_for_backward/start_time_for_forward are given without start_time.
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
        self.remove_task(task, tighten_times, update_kpis)
        is_feasible = self.insert_task_after_activity(
            task, activity, start_time, start_time_for_backward, start_time_for_forward,
            tighten_times, update_kpis
        )
        return is_feasible

    def reposition_task_in_sequence_before_activity(
            self, task: Task, activity: Activity, start_time: Optional[int] = None,
            start_time_for_backward: Optional[int] = None, start_time_for_forward: Optional[int] = None,
            tighten_times: bool = True, update_kpis: bool = True
    ):
        """
        Move a given task before a given activity in the sequence of the employee who performs these task and activity:

        - if the move is known to be feasible, a start time for the moving task shall be provided;

        - if the move is known to be infeasible, a start time for the moving task,
          as well as two artificial start times for backward and forward computation, shall be provided;

        - if the feasibility of the move is not known, start times inputs shall remain vacant.

        The given moving task must be performed by an employee, otherwise a ValueError is raised.
        The given activity must be performed by the same employee, otherwise a ValueError is raised.
        The given activity must not be the first activity of the sequence, otherwise a ValueError is raised.

        Args:
            task: The task to move in the sequence of the employee who performs it.
            activity: The activity before which the moving task shall be inserted.
            start_time: The start time of the moving task.
            start_time_for_backward: The artificial start time of the moving task used for computing the
              times of the steps before it once reinserted; to be used if the move is known to be infeasible.
            start_time_for_forward: The artificial start time of the moving task used for computing the
              times of the steps after it; to be used if the move is known to be infeasible.
            tighten_times: If True, tightens the times of the sequence of the employee who performs the
              given task and activity after the transformation, in order to minimize idle time.
            update_kpis: Whether to keep the KPIs up to date after the shift.

        Returns:
            Whether the obtained solution is feasible.

        Raises:
            ValueError: If the given moving task is not performed in this solution, if the given activity
              is a task that is not performed in this solution, if the given activity is not performed by
              the same employee as the moving task, if the given activity is the first activity of the
              sequence, or if start_time_for_backward/start_time_for_forward are given without start_time.
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
        if isinstance(activity, Departure):
            raise ValueError(f"The given activity {activity.name} is the first activity of the sequence")
        # - Check that the start times inputs are consistent
        if (start_time is None) and ((start_time_for_backward is not None) or (start_time_for_forward is not None)):
            raise ValueError("The start times for backward and forward can be given as inputs "
                             "only if a start time is also given")

        # Shift the task in the sequence using the method for shifting after an activity
        sequence = self.get_sequence(employee)
        step_index_of_activity_before = sequence.get_step_index_of(activity) - 1
        activity_before = sequence.get_step(step_index_of_activity_before).activity
        return self.reposition_task_in_sequence_after_activity(
            task, activity_before, start_time, start_time_for_backward, start_time_for_forward,
            tighten_times, update_kpis
        )

    def reorder(self, employee: Employee, tighten_times: bool = True, update_kpis: bool = True):
        """
        Reorder the tasks in the given employee's sequence using a MILP-based sequence-reordering model,
        replacing the employee's sequence with the one obtained.

        Args:
            employee: The employee whose sequence is reordered.
            tighten_times: If True, tightens the times of the new sequence after reordering,
              in order to minimize idle time.
            update_kpis: Whether to keep the KPIs up to date after the change.

        Returns:
            True, since a feasible reordering is always found when one exists.

        Raises:
            ValueError: If the underlying MILP model has no solution, meaning no feasible reordering exists.
        """

        # Create and run the IP model for sequence reordering optimization
        model = SequenceReorderingModel(self.get_sequence(employee))
        model.solve(mute=True)

        # Save the sequence obtained by solving the IP model
        if not model.has_solution_sequence:
            raise ValueError(f"Reordering the tasks in {employee}'s sequence is infeasible")
        new_sequence = SequenceForHeuristics.from_sequence(model.solution_sequence)
        if update_kpis:
            new_sequence.compute_kpis()
        if tighten_times:
            SlackTimeComputer.tighten_times(new_sequence, update_kpis)

        # Replace sequence
        self._replace_sequence_by_another(employee, new_sequence, update_kpis)

        # Return whether the insertion has given a feasible solution
        return True
