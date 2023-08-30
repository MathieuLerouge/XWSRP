# Local libraries modules
from src.modeling.comeback import ComeBack
from src.modeling.constants import NB_PERFORMED_TASKS_KEY, TOTAL_TRAVELING_DURATION_KEY, TOTAL_WORKING_DURATION_KEY, \
    TOTAL_TRAVELING_DISTANCE_KEY, TOTAL_IDLE_TIME_KEY
from src.modeling.departure import Departure
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.sequence import Sequence
from src.modeling.task import Task
from src.optimization.heuristics.examination import InsertionExamination, ReplacementExamination, ReorderExamination
from src.optimization.heuristics.step import StepForHeuristics


###############################
# Class SequenceForHeuristics #
###############################

class SequenceForHeuristics(Sequence):

    def __init__(self, instance: Instance, employee: Employee, steps: list[StepForHeuristics] = None):
        super().__init__(instance, employee, None)
        if steps is None:
            steps = \
                [StepForHeuristics(Departure(employee), employee.start_time_LB,
                                   employee.start_time_LB, employee.start_time_LB),
                 StepForHeuristics(ComeBack(employee), employee.start_time_LB,
                                   employee.start_time_LB, employee.start_time_LB)]
        self._steps = steps
        self.update_time_slacks()

    @classmethod
    def from_Sequence(cls, sequence: Sequence):
        steps = [StepForHeuristics.from_Step(step) for step in sequence]
        return SequenceForHeuristics(sequence.instance, sequence.employee, steps)

    def __getitem__(self, index: int) -> StepForHeuristics:
        return self._steps[index]

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
    def _total_traveling_distance(self) -> int:
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

    @property
    def KPIs(self):
        return self._copy_KPIs()

    ########
    # Copy #
    ########

    def copy(self):
        sequence = SequenceForHeuristics(self._instance, self._employee, self._copy_steps())
        sequence._KPIs = self._copy_KPIs()
        return sequence

    ########
    # Step #
    ########

    def get_step(self, index: int) -> StepForHeuristics:
        return self._steps[index]

    #########
    # Times #
    #########

    # TODO adapt to lunch breaks
    def shift_steps_times_backward_from(self, step_index: int, start_time: int):
        """
        Assumption: instance without lunch breaks.

        :param step_index: index (int) of the step whose start time is changed
        and from which times of previous steps are changed in consequence
        :param start_time: start time of the step (int)
        :return: index (int) of the first step which start time is changed
        """
        time_variation = self[step_index].start_time - start_time
        while time_variation > 0 and step_index >= 0:
            step = self[step_index]
            step.start_time -= time_variation
            step.end_time -= time_variation
            step.BTS -= time_variation
            step.FTS += time_variation
            time_variation = max(step.arrival_time - step.start_time, 0)
            step.arrival_time -= time_variation
            step_index -= 1
        return step_index + 1

    # TODO adapt to lunch breaks
    def shift_steps_times_forward_from(self, step_index, start_time):
        """
        Assumption: instance without lunch breaks.

        :param step_index: index (int) of the step which start time is changed
        and from which times of next steps are changed in consequence
        :param start_time: start time of the step (int)
        :return: index (int) of the last step which start time is changed
        """
        time_variation = start_time - self[step_index].start_time
        if step_index == 0 and time_variation > 0:
            self[0].arrival_time = start_time
        while time_variation > 0 and step_index <= self.nb_steps - 2:
            step = self[step_index]
            next_step = self[step_index + 1]
            step.start_time += time_variation
            step.end_time += time_variation
            step.BTS += time_variation
            step.FTS -= time_variation
            next_step.arrival_time += time_variation
            time_variation = max(next_step.arrival_time - next_step.start_time, 0)
            step_index += 1
        if step_index == self.nb_steps - 1:
            step = self[step_index]
            step.start_time = step.arrival_time
            step.end_time = step.arrival_time
            step.BTS += time_variation
            step.FTS -= time_variation
        return step_index

    def tighten_times(self, update_KPIs: bool = True):
        assert (self.is_time_consistent, "The times are not consistent")
        idle_time_loss = 0
        time_variation_forward = self[0].FTS
        if time_variation_forward > 0:
            former_comeback_time = self[-1].start_time
            self.shift_steps_times_forward_from(0, self[0].start_time + time_variation_forward)
            idle_time_loss += time_variation_forward - (self[-1].start_time - former_comeback_time)
        time_variation_backward = self[-1].BTS
        if time_variation_backward > 0:
            former_departure_time = self[0].start_time
            self.shift_steps_times_backward_from(self.nb_steps - 1,
                                                 self[-1].start_time - time_variation_backward)
            idle_time_loss += time_variation_backward - (former_departure_time - self[0].start_time)
        if update_KPIs:
            self._total_idle_time -= idle_time_loss

    ###############
    # Time slacks #
    ###############

    # TODO adapt to tasks unavailabilities and lunch breaks
    def update_BTS_forward_from(self, step_index: int):
        """
        Assumption: there are no tasks unavailabilities and no lunch breaks
        Assumption: when step_index > 0, it is assumed that BTS[step_index-1] is computed and valid

        :param step_index: (int)
        """
        if step_index == 0:
            self[0].BTS = self[0].start_time - self.employee.start_time_LB
            step_index += 1
        for previous_step_index in range(step_index - 1, self.nb_steps - 1):
            step = self[previous_step_index + 1]
            previous_step = self[previous_step_index]
            step.BTS = min(
                step.start_time - step.activity.start_time_LB,
                step.start_time - (previous_step.start_time - previous_step.BTS + previous_step.activity.duration +
                                   self.instance.compute_traveling_duration(previous_step.activity, step.activity))
            )

    # TODO adapt to tasks unavailabilities and lunch breaks
    def update_FTS_backward_from(self, step_index: int):
        """
        Assumption: there are no tasks unavailabilities and no lunch breaks
        Assumption: when step_index < nb_steps - 1, it is assumed that FTS[step_index+1] is computed and valid

        :param step_index: (int)
        """
        if step_index == self.nb_steps - 1:
            self[-1].FTS = self.employee.end_time_UB - self[-1].start_time
            step_index -= 1
        for next_step_index in range(step_index + 1, 0, -1):
            step = self[next_step_index - 1]
            next_step = self[next_step_index]
            step.FTS = min(
                step.activity.end_time_UB - (step.start_time + step.activity.duration),
                next_step.start_time + next_step.FTS -
                (step.start_time + step.activity.duration +
                 self.instance.compute_traveling_duration(step.activity, next_step.activity))
            )

    def update_time_slacks(self):
        self.update_BTS_forward_from(0)
        self.update_FTS_backward_from(self.nb_steps - 1)

    ###############################################
    # Examining - Insertion - Best transformation #
    ###############################################

    # TODO to remove if not necessary
    # def examine_placing_between(self, entering_task: Task,
    #                             step_before_placement_index: int, step_after_placement_index: int):
    #     """
    #     Examine the feasibility of placing the given entering task between
    #     the step at the given index before the placement and the step at given index after the placement;
    #     provide a dictionary, describing this examination, with keys:
    #     'is_feasible', 'is_upstream_feasible', 'is_downstream_feasible'
    #     'start_time', 'earliest_start_time_for_upstream', 'latest_start_time_for_downstream' and
    #     'traveling_duration_detour'.
    #
    #     - If the placement is feasible, the value associated to the key 'start_time' is the start time (int)
    #       that could be applied to the entering task, when following the earliest policy,
    #       whereas the values associated to 'earliest_start_time_for_upstream' and
    #       'latest_start_time_for_downstream' are both None;
    #     - If the placement is infeasible, the values associated to the keys 'earliest_start_time_for_upstream' and
    #       'latest_start_time_for_downstream' are the start times that could be applied to the entering task so that
    #       the time consistency of respectively the upstream and the downstream portions of the sequence,
    #       while the value associated to the keys 'start_time' is an average of these artificial values.
    #
    #     Assumptions (only checked in debug):
    #
    #     - 1. the given entering task can be realized by the employee of this sequence;
    #     - 2. the given entering task must not be already in this sequence;
    #     - 3. the given index of the step before placement must both be
    #     between 0 (included) and the number of steps - 2 (included);
    #     - 4. the given index of the step before placement must both be
    #     between 1 (included) and the number of steps - 1 (included);
    #     - 5. the index of the step before the placement is smaller or equal to
    #     the one of the step after the placement;
    #     - 6. the times of this sequence are consistent.
    #
    #     :param entering_task: the task (Task) that is figured to be inserted
    #     :param step_before_placement_index: the index of the step (int) before the position
    #       where the given task would be placed
    #     :param step_after_placement_index: the index of the step (int) after the position
    #       where the given task would be placed
    #     :return: the dictionary with keys 'is_feasible', 'is_upstream_feasible', 'is_downstream_feasible',
    #       'start_time', 'earliest_start_time_for_upstream', 'latest_start_time_for_downstream' and
    #       'traveling_duration_detour'
    #     """
    #
    #     # Check the assumptions
    #     assert (self.employee.is_capable_of_performing(entering_task),
    #             f"The employee {self.employee.name} is not capable of realizing the given task {entering_task.name}")
    #     assert (not (entering_task in self.get_contained_tasks()),
    #             f"The given entering task {entering_task.name} is already in this sequence")
    #     assert (0 <= step_before_placement_index < self.__len__() - 1,
    #             f"The given step index {step_before_placement_index} is not between "
    #             f"1 and {self.__len__() - 1} included")
    #     assert (0 < step_after_placement_index < self.__len__(),
    #             f"The given step index {step_after_placement_index} is not between "
    #             f"1 and {self.__len__() - 1} included")
    #     assert (step_before_placement_index <= step_after_placement_index,
    #             f"The given step before the placement index {step_before_placement_index} is larger than"
    #             f"the given step after the placement index {step_after_placement_index}")
    #     assert self.is_time_consistent, "The times are not consistent"
    #
    #     # Get the step before and after the hypothetical placement
    #     step_before = self[step_before_placement_index]
    #     step_after = self[step_after_placement_index]
    #
    #     # Compute the earliest time at which the employee can start realizing the entering task,
    #     # so that the times of the upstream portion of his/her sequence before the placement are consistent,
    #     # and the latest time at which he/she can start realizing the entering task,
    #     # so that the times of the downstream portion of his/her sequence after the placement are consistent
    #     traveling_duration_from_step_before_placement_to_entering_task = \
    #         self.instance.compute_traveling_duration(step_before.activity, entering_task)
    #     earliest_start_time_of_entering_task = max(
    #         entering_task.start_time_LB,
    #         step_before.start_time - step_before.BTS + step_before.activity.duration +
    #         traveling_duration_from_step_before_placement_to_entering_task
    #     )
    #     traveling_duration_from_entering_task_to_step_after_placement = \
    #         self.instance.compute_traveling_duration(entering_task, step_after.activity)
    #     latest_start_time_of_entering_task = min(
    #         entering_task.end_time_UB,
    #         step_after.start_time + step_after.FTS -
    #         traveling_duration_from_entering_task_to_step_after_placement
    #     ) - entering_task.duration
    #     traveling_duration_detour = (
    #             traveling_duration_from_step_before_placement_to_entering_task +
    #             traveling_duration_from_entering_task_to_step_after_placement -
    #             np.sum([
    #                 self.instance.compute_traveling_duration(self[step_index].activity, self[step_index + 1].activity)
    #                 for step_index in range(step_before_placement_index, step_after_placement_index)
    #             ])
    #     )
    #
    #     # Compute two booleans indicating whether the entering task can be placed while guaranteeing
    #     # the consistency of the times of respectively the upstream and the downstream portions of the sequence
    #     upstream_portion_is_feasible = (earliest_start_time_of_entering_task + entering_task.duration <=
    #                                     entering_task.end_time_UB)
    #     downstream_portion_is_feasible = (latest_start_time_of_entering_task >= entering_task.start_time_LB)
    #     is_feasible = (
    #             upstream_portion_is_feasible and downstream_portion_is_feasible and
    #             earliest_start_time_of_entering_task < latest_start_time_of_entering_task
    #     )
    #
    #     # Initialize the artificial start times
    #     start_time_for_upstream = None
    #     start_time_for_downstream = None
    #
    #     # If the consistency of both upstream and downstream portions can be guaranteed,
    #     # then set start time according to the earliest policy
    #     if is_feasible:
    #         start_time = earliest_start_time_of_entering_task
    #
    #     # If the consistency of one the upstream or downstream portions can not be guaranteed,
    #     # then set artificial start times for backward and forward to earliest and latest start times
    #     # and the start time itself as the average of these artificial start times
    #     else:
    #         start_time_for_upstream = earliest_start_time_of_entering_task
    #         start_time = (earliest_start_time_of_entering_task + latest_start_time_of_entering_task) // 2
    #         start_time_for_downstream = latest_start_time_of_entering_task
    #
    #     return {'is_feasible': is_feasible,
    #             'is_upstream_feasible': upstream_portion_is_feasible,
    #             'is_downstream_feasible': downstream_portion_is_feasible,
    #             'start_time': start_time,
    #             'earliest_start_time_for_upstream': start_time_for_upstream,
    #             'latest_start_time_for_downstream': start_time_for_downstream,
    #             'traveling_duration_detour': traveling_duration_detour}

    # def examine_insertion_at(self, entering_task: Task, step_index: int):
    #     return self.examine_placing_between(entering_task, step_index - 1, step_index)

    def examine_insertion_at(self, task: Task, insertion_step_index: int,
                             compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Examine the feasibility of the insertion of the given task at the given insertion step index

        Assumptions (only checked in debug):

        - 1. the given task must not be already in this sequence;
        - 2. the given insertion step index must be between 1 (included) and the number of steps - 1 (included);
        - 3. the times of this sequence are consistent.

        :param task: the task (Task) that would be inserted
        :param insertion_step_index: the index of the step (int) where the given task would be inserted
        :param compute_times_only_if_skill_constraints_satisfied: a boolean (bool) for telling whether
          if the skill constraints are not satisfied start times should still be computed
        :return: the insertion examination (InsertionExamination)
        """

        # Check the assumptions
        assert (not (task in self.get_contained_tasks()),
                f"The given entering task {task.name} is already in this sequence")
        assert (0 < insertion_step_index < self.__len__(),
                f"The given step index {insertion_step_index} is not between 1 and {self.__len__() - 1} included")
        assert self.is_time_consistent, "The times are not consistent"

        # Examine skill-wise feasibility
        is_skill_feasible = self.employee.is_capable_of_performing(task)
        if compute_times_only_if_skill_constraints_satisfied and not is_skill_feasible:
            examination = InsertionExamination()
            examination.is_feasible = False
            examination.is_skill_feasible = False
            examination.inserted_task = task
            examination.employee = self.employee
            return examination

        # Get the step before and after the hypothetical insertion
        step_before = self[insertion_step_index - 1]
        step_after = self[insertion_step_index]

        # Compute the earliest time at which the employee can start realizing the entering task,
        # so that the times of the upstream portion of his/her sequence before the insertion are consistent,
        # and the latest time at which he/she can start realizing the entering task,
        # so that the times of the downstream portion of his/her sequence after the insertion are consistent
        traveling_duration_from_step_before_insertion_to_entering_task = \
            self.instance.compute_traveling_duration(step_before.activity, task)
        earliest_start_time_of_entering_task = max(
            task.start_time_LB,
            step_before.start_time - step_before.BTS + step_before.activity.duration +
            traveling_duration_from_step_before_insertion_to_entering_task
        )
        traveling_duration_from_entering_task_to_step_after_insertion = \
            self.instance.compute_traveling_duration(task, step_after.activity)
        latest_start_time_of_entering_task = min(
            task.end_time_UB,
            step_after.start_time + step_after.FTS -
            traveling_duration_from_entering_task_to_step_after_insertion
        ) - task.duration
        traveling_duration_detour = (
                traveling_duration_from_step_before_insertion_to_entering_task +
                traveling_duration_from_entering_task_to_step_after_insertion -
                self.instance.compute_traveling_duration(step_before.activity, step_after.activity)
        )

        # Compute two booleans indicating whether the entering task can be inserted while guaranteeing
        # the consistency of the times of respectively the upstream and the downstream portions of the sequence
        upstream_portion_is_feasible = (earliest_start_time_of_entering_task + task.duration <=
                                        task.end_time_UB)
        downstream_portion_is_feasible = (latest_start_time_of_entering_task >= task.start_time_LB)
        if upstream_portion_is_feasible:
            late = max(earliest_start_time_of_entering_task - latest_start_time_of_entering_task, 0)
        else:
            late = earliest_start_time_of_entering_task + task.duration - task.end_time_UB
        is_time_feasible = upstream_portion_is_feasible and downstream_portion_is_feasible and late == 0

        # Initialize the artificial start times
        start_time_for_upstream = None
        start_time_for_downstream = None

        # If the consistency of both upstream and downstream portions can be guaranteed,
        # then set start time according to the earliest policy
        if is_time_feasible:
            start_time = earliest_start_time_of_entering_task

        # If the consistency of one the upstream or downstream portions can not be guaranteed,
        # then set artificial start times for backward and forward to earliest and latest start times
        # and the start time itself as the average of these artificial start times
        else:
            start_time_for_upstream = earliest_start_time_of_entering_task
            start_time_for_downstream = latest_start_time_of_entering_task
            start_time = (earliest_start_time_of_entering_task + latest_start_time_of_entering_task) // 2
            if downstream_portion_is_feasible:
                start_time = start_time_for_downstream
            if upstream_portion_is_feasible:
                start_time = start_time_for_upstream

        # Return examination
        examination = InsertionExamination()
        examination.is_feasible = is_time_feasible and is_skill_feasible
        examination.is_skill_feasible = is_skill_feasible
        examination.is_time_feasible = is_time_feasible
        examination.is_upstream_feasible = upstream_portion_is_feasible
        examination.is_downstream_feasible = downstream_portion_is_feasible
        examination.start_time = start_time
        examination.earliest_start_time_for_upstream = start_time_for_upstream
        examination.latest_start_time_for_downstream = start_time_for_downstream
        examination.travel_time_increase = traveling_duration_detour
        examination.late = late
        examination.inserted_task = task
        examination.insertion_step_index = insertion_step_index
        examination.activity_before_insertion = step_before.activity
        examination.employee = self.employee
        return examination

    # TODO: Remove these lines
    # def find_best_insertion_between_consecutive_activities_bis(
    #         self, task: Task, tabu_indices: list[int] = None,
    #         compute_times_only_if_skill_constraints_satisfied: bool = True):
    #     """
    #     Find the best insertion of the given task in this sequence, that is to say:
    #
    #     - if there is any feasible insertion,
    #       the best insertion is the feasible one that engenders the smallest additional traveling duration;
    #     - if there are no feasible insertions,
    #       the best insertion is the infeasible one that is the closest to be feasible duration-wise.
    #
    #     Assumptions (only checked in debug):
    #     The times of this sequence are consistent.
    #
    #     :param task: the task (Task) that would be inserted
    #     :param tabu_indices: steps indices (list[int]) where the task must not be inserted
    #     :param compute_times_only_if_skill_constraints_satisfied: a boolean (bool) for telling whether
    #       if the skill constraints are not satisfied start times should still be computed
    #     :return: the insertion examination (InsertionExamination)
    #     """
    #
    #     # Examine skill-wise feasibility
    #     insertion_is_skill_feasible = self.employee.is_capable_of_performing(task)
    #     if compute_times_only_if_skill_constraints_satisfied and not insertion_is_skill_feasible:
    #         examination = InsertionExamination()
    #         examination.is_feasible = False
    #         examination.is_skill_feasible = False
    #         examination.inserted_task = task
    #         examination.employee = self.employee
    #         return examination
    #
    #     # The assumptions are checked when calling examine_insertion_at
    #
    #     # Set tabu indices as empty list if None
    #     if tabu_indices is None:
    #         tabu_indices = []
    #
    #     # Initialize variables
    #     best_insertion_is_time_feasible = False
    #     best_insertion_is_upstream_feasible = False
    #     best_insertion_is_downstream_feasible = False
    #     best_insertion_step_index = None
    #     best_start_time_of_entering_task = None
    #     best_start_time_of_entering_task_for_upstream = None
    #     best_start_time_of_entering_task_for_downstream = None
    #     best_traveling_duration_detour = None
    #     best_late = None
    #
    #     # Examine all step index for insertion starting from index 1
    #     examined_step_index = 1
    #     while examined_step_index <= self.nb_steps - 1:
    #         # If the examined step is tabu, then go to next step
    #         if examined_step_index in tabu_indices:
    #             examined_step_index += 1
    #         # If the examined step is not tabu, then examine it
    #         else:
    #             examination = self.examine_insertion_at(task, examined_step_index, False)
    #
    #             # If the insertion is time-wise feasible, ...
    #             if examination.is_time_feasible:
    #
    #                 # If time-wise feasibility has not yet been noticed,
    #                 if not best_insertion_is_time_feasible:
    #
    #                     # Signal that the insertion is feasible (and a fortiori upstream-feasible)
    #                     best_insertion_is_time_feasible = True
    #                     best_insertion_is_upstream_feasible = True
    #                     best_insertion_is_downstream_feasible = True
    #                     best_start_time_of_entering_task_for_upstream = None
    #                     best_start_time_of_entering_task_for_downstream = None
    #                     best_late = None
    #
    #                     # Save this insertion as the best one
    #                     best_insertion_step_index = examined_step_index
    #                     best_start_time_of_entering_task = examination.start_time
    #                     best_traveling_duration_detour = examination.travel_time_increase
    #
    #                 # If time-wise feasibility has already been noticed,
    #                 else:
    #
    #                     # If it is the best feasible insertion traveling-duration-wise,
    #                     # then save it
    #                     if examination.travel_time_increase < best_traveling_duration_detour:
    #                         best_insertion_step_index = examined_step_index
    #                         best_start_time_of_entering_task = examination.start_time
    #                         best_traveling_duration_detour = examination.travel_time_increase
    #
    #                 # Go to the next step
    #                 examined_step_index += 1
    #
    #             # If the insertion is upstream-feasible, ...
    #             elif examination.is_upstream_feasible:
    #
    #                 # If no feasible insertions are yet known, ...
    #                 if not best_insertion_is_time_feasible:
    #                     late_due_to_upstream_at_step_after_insertion = (
    #                         examination.earliest_start_time_for_upstream - examination.latest_start_time_for_downstream
    #                     )
    #
    #                     # If upstream-feasibility has not yet been noticed,
    #                     if not best_insertion_is_upstream_feasible:
    #
    #                         # Signal that the insertion is upstream-feasible
    #                         best_insertion_is_upstream_feasible = True
    #
    #                         # Save this insertion as the best one
    #                         best_insertion_is_downstream_feasible = examination.is_downstream_feasible
    #                         best_insertion_step_index = examined_step_index
    #                         best_start_time_of_entering_task = examination.start_time
    #                         best_start_time_of_entering_task_for_upstream = \
    #                             examination.earliest_start_time_for_upstream
    #                         best_start_time_of_entering_task_for_downstream = \
    #                             examination.latest_start_time_for_downstream
    #                         best_late = late_due_to_upstream_at_step_after_insertion
    #                         best_traveling_duration_detour = examination.travel_time_increase
    #
    #                     # If upstream-feasibility has already been noticed,
    #                     else:
    #
    #                         # If it is the best insertion late-wise,
    #                         # then save it
    #                         if late_due_to_upstream_at_step_after_insertion < best_late:
    #                             best_insertion_is_downstream_feasible = examination.is_downstream_feasible
    #                             best_insertion_step_index = examined_step_index
    #                             best_start_time_of_entering_task = examination.start_time
    #                             best_start_time_of_entering_task_for_upstream = \
    #                                 examination.earliest_start_time_for_upstream
    #                             best_start_time_of_entering_task_for_downstream = \
    #                                 examination.latest_start_time_for_downstream
    #                             best_late = late_due_to_upstream_at_step_after_insertion
    #                             best_traveling_duration_detour = examination.travel_time_increase
    #
    #                 # Go to the next step
    #                 examined_step_index += 1
    #
    #             # If the insertion is not upstream-feasible, ...
    #             else:
    #
    #                 # If no upstream-feasible insertions are yet known,
    #                 # then save it
    #                 if not best_insertion_is_upstream_feasible:
    #                     best_insertion_is_downstream_feasible = examination.is_downstream_feasible
    #                     late_due_to_upstream_at_insertion = \
    #                         examination.earliest_start_time_for_upstream + task.duration - task.end_time_UB
    #                     best_insertion_step_index = examined_step_index
    #                     best_start_time_of_entering_task = examination.start_time
    #                     best_start_time_of_entering_task_for_upstream = \
    #                         examination.earliest_start_time_for_upstream
    #                     best_start_time_of_entering_task_for_downstream = \
    #                         examination.latest_start_time_for_downstream
    #                     best_late = late_due_to_upstream_at_insertion
    #                     best_traveling_duration_detour = examination.travel_time_increase
    #
    #                 # Stop the examinations
    #                 examined_step_index = self.nb_steps
    #
    #     # Return examination
    #     examination = InsertionExamination()
    #     examination.is_feasible = insertion_is_skill_feasible and best_insertion_is_time_feasible
    #     examination.is_skill_feasible = insertion_is_skill_feasible
    #     examination.is_time_feasible = best_insertion_is_time_feasible
    #     examination.is_upstream_feasible = best_insertion_is_upstream_feasible
    #     examination.is_downstream_feasible = best_insertion_is_downstream_feasible
    #     examination.start_time = best_start_time_of_entering_task
    #     examination.earliest_start_time_for_upstream = best_start_time_of_entering_task_for_upstream
    #     examination.latest_start_time_for_downstream = best_start_time_of_entering_task_for_downstream
    #     examination.travel_time_increase = best_traveling_duration_detour
    #     examination.late = best_late
    #     examination.inserted_task = task
    #     examination.insertion_step_index = best_insertion_step_index
    #     examination.activity_before_insertion = self.get_step(best_insertion_step_index - 1).activity
    #     examination.employee = self.employee
    #     return examination

    def find_best_insertion_between_consecutive_activities(
            self, task: Task, tabu_indices: list[int] = None,
            compute_times_only_if_skill_constraints_satisfied: bool = True):
        # Examine skill-wise feasibility
        insertion_is_skill_feasible = self.employee.is_capable_of_performing(task)
        if compute_times_only_if_skill_constraints_satisfied and not insertion_is_skill_feasible:
            examination = InsertionExamination()
            examination.is_feasible = False
            examination.is_skill_feasible = False
            examination.inserted_task = task
            examination.employee = self.employee
            return examination
        # Examine all step index for insertion starting from index 1
        if tabu_indices is None:
            tabu_indices = []
        examined_step_index = 1
        best_examination = None
        while examined_step_index <= self.nb_steps - 1:
            # If the examined step is tabu, then go to next step
            if examined_step_index in tabu_indices:
                examined_step_index += 1
            # If the examined step is not tabu, then examine it
            else:
                examination = self.examine_insertion_at(task, examined_step_index, False)
                if best_examination is None or examination.is_better_than(best_examination):
                    best_examination = examination
                if best_examination.is_upstream_feasible and not examination.is_upstream_feasible:
                    examined_step_index = self.nb_steps
                else:
                    examined_step_index += 1
        # TODO: Remove these lines
        # best_examination_bis = self.find_best_insertion_between_consecutive_activities_bis(
        #     task, tabu_indices, compute_times_only_if_skill_constraints_satisfied
        # )
        # if best_examination != best_examination_bis:
        #     print(best_examination)
        #     print(best_examination_bis)
        #     raise Exception("ERROR")
        return best_examination

    def find_best_insertion_between_consecutive_activities_among_tasks_set(
            self, tasks: list[Task], compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Among all tasks of given set, find the best insertion of a task in this sequence, that is to say:

        - if there is any feasible insertion,
          the best insertion is the feasible one that engenders the smallest additional traveling duration;
        - if there are no feasible insertions,
          the best insertion is the infeasible one that is the closest to be feasible duration-wise.

        Assumptions (only checked in debug):
        The times of this sequence are consistent.

        :param tasks: the list of candidate tasks (Task) that would be inserted
        :param compute_times_only_if_skill_constraints_satisfied: a boolean (bool) for telling whether
          if the skill constraints are not satisfied start times should still be computed
        :return: the examination of the best insertion (InsertionExamination)
        """

        # The assumptions are checked when calling find_best_insertion_between_consecutive_activities

        best_insertion_examination = self.find_best_insertion_between_consecutive_activities(
            tasks[0], None, compute_times_only_if_skill_constraints_satisfied
        )
        best_task = tasks[0]
        for task in tasks[1:]:
            examination = self.find_best_insertion_between_consecutive_activities(
                task, None, compute_times_only_if_skill_constraints_satisfied
            )
            # Case where the current insertion is feasible
            if examination.is_feasible:
                if not best_insertion_examination.is_feasible or \
                    (examination.travel_time_increase <
                     best_insertion_examination.travel_time_increase):
                    best_insertion_examination = examination
                    # TODO remove if not necessary
                    # best_task = task
            # Case where both the current insertion and the best currently known one are infeasible
            elif not best_insertion_examination.is_feasible:
                # Case where the current insertion is infeasible skill-wise
                if not examination.is_skill_feasible:
                    if not best_insertion_examination.is_skill_feasible and \
                            task.skill_level < best_task.skill_level:
                        best_insertion_examination = examination
                        # best_task = task
                # Case where the current insertion is feasible skill-wise
                else:
                    if not best_insertion_examination.is_skill_feasible:
                        best_insertion_examination = examination
                        # best_task = task
                    # Case where both the current insertion and the best currently known one are feasible skill-wise
                    else:
                        # Case where the current insertion is infeasible upstream-wise
                        if not examination.is_upstream_feasible:
                            if not best_insertion_examination.is_upstream_feasible and \
                                    examination.late < best_insertion_examination.late:
                                best_insertion_examination = examination
                                # best_task = task
                        # Case where the current insertion is feasible upstream-wise
                        else:
                            if not best_insertion_examination.is_upstream_feasible:
                                best_insertion_examination = examination
                                # best_task = task
                            # Case where both the current insertion and the best currently known one
                            # are feasible upstream-wise
                            elif examination.late < best_insertion_examination.late:
                                best_insertion_examination = examination
                                # best_task = task
        # best_insertion_examination.inserted_task = best_task
        return best_insertion_examination

    ####################################################
    # Examining - Insertion - Feasible transformations #
    ####################################################

    def find_feasible_insertions_between_consecutive_activities(self, task: Task):
        """
        Find all feasible insertions of a task in this sequence.

        Assumptions (only checked in debug):
        The times of this sequence are consistent.

        :param task: the candidate task (Task) that would be inserted
        :return: the list of all feasible insertions (list[InsertionExamination])
        """
        examinations = []
        one_insertion_is_upstream_feasible = False
        if self.employee.is_capable_of_performing(task):
            insertion_step_index = 1
            while insertion_step_index <= self.nb_steps - 1:
                examination = self.examine_insertion_at(task, insertion_step_index, True)
                if examination.is_feasible:
                    one_insertion_is_upstream_feasible = True
                    examinations.append(examination)
                elif examination.is_upstream_feasible:
                    one_insertion_is_upstream_feasible = True
                else:
                    if one_insertion_is_upstream_feasible:
                        insertion_step_index = self.nb_steps
                insertion_step_index += 1
        return examinations

    ###########################
    # Examining - Replacement #
    ###########################

    def examine_replacing_task_with_another(self, replaced_task: Task, replacing_task: Task,
                                            compute_times_only_if_skill_constraints_satisfied: bool = True):
        # Check the assumptions
        assert (not (replaced_task in self.get_contained_tasks()),
                f"The given replaced_task task {replaced_task.name} is not in this sequence")
        assert (not (replacing_task in self.get_contained_tasks()),
                f"The given replacing_task task {replacing_task.name} is already in this sequence")
        assert self.is_time_consistent, "The times are not consistent"
        # Examine skill-wise feasibility
        is_skill_feasible = self.employee.is_capable_of_performing(replacing_task)
        if compute_times_only_if_skill_constraints_satisfied and not is_skill_feasible:
            examination = ReplacementExamination()
            examination.is_feasible = False
            examination.is_skill_feasible = False
            examination.employee = self.employee
            examination.replaced_task = replaced_task
            examination.replacing_task = replacing_task
            return examination
        # Examine time-wise
        sequence_copy = self.copy()
        task_index = sequence_copy.get_step_index_of(replaced_task)
        sequence_travel_time_before_removing = sequence_copy.total_traveling_duration
        sequence_copy.remove_step(task_index, False, True)
        sequence_travel_time_after_removing = sequence_copy.total_traveling_duration
        sequence_travel_time_decrease_due_to_removal = \
            sequence_travel_time_before_removing - sequence_travel_time_after_removing
        insertion_examination = \
            sequence_copy.examine_insertion_at(replacing_task, task_index,
                                               compute_times_only_if_skill_constraints_satisfied)
        examination = ReplacementExamination.from_examination(insertion_examination)
        examination.replaced_task = replaced_task
        examination.replacing_task = replacing_task
        examination.travel_time_increase -= sequence_travel_time_decrease_due_to_removal
        return examination

    # # TODO function could be simplified by introducing sooner the Examination object
    # def find_best_task_to_be_replaced_with_given_task_bis(
    #         self, task: Task, compute_times_only_if_skill_constraints_satisfied: bool = True):
    #
    #     # Examine skill-wise feasibility
    #     swap_is_skill_feasible = self.employee.is_capable_of_performing(task)
    #     if compute_times_only_if_skill_constraints_satisfied and not swap_is_skill_feasible:
    #         examination = ReplacementExamination()
    #         examination.is_feasible = False
    #         examination.is_skill_feasible = False
    #         examination.employee = self.employee
    #         examination.replacing_task = task
    #         return examination
    #
    #     # The assumptions are checked when calling examine_replacing_task_with_another
    #
    #     # Initialize variables
    #     best_swap_is_time_feasible = False
    #     best_swap_is_upstream_feasible = False
    #     best_swap_is_downstream_feasible = False
    #     best_swap_step_index = None
    #     best_start_time_of_entering_task = None
    #     best_start_time_of_entering_task_for_upstream = None
    #     best_start_time_of_entering_task_for_downstream = None
    #     best_traveling_duration_detour = None
    #     best_late = None
    #
    #     # Examine all step index for swap starting from index 1
    #     examined_step_index = 1
    #     while examined_step_index <= self.nb_steps - 2:
    #         replaced_task = self.get_step(examined_step_index).activity
    #         examination = self.examine_replacing_task_with_another(replaced_task, task, False)
    #
    #         # If the insertion is time-wise feasible, ...
    #         if examination.is_time_feasible:
    #
    #             # If time-wise feasibility has not yet been noticed,
    #             if not best_swap_is_time_feasible:
    #
    #                 # Signal that the insertion is feasible (and a fortiori upstream-feasible)
    #                 best_swap_is_time_feasible = True
    #                 best_swap_is_upstream_feasible = True
    #                 best_swap_is_downstream_feasible = True
    #                 best_start_time_of_entering_task_for_upstream = None
    #                 best_start_time_of_entering_task_for_downstream = None
    #                 best_late = None
    #
    #                 # Save this insertion as the best one
    #                 best_swap_step_index = examined_step_index
    #                 best_start_time_of_entering_task = examination.start_time
    #                 best_traveling_duration_detour = examination.travel_time_increase
    #
    #             # If time-wise feasibility has already been noticed,
    #             else:
    #
    #                 # If it is the best feasible insertion traveling-duration-wise,
    #                 # then save it
    #                 if examination.travel_time_increase < best_traveling_duration_detour:
    #                     best_swap_step_index = examined_step_index
    #                     best_start_time_of_entering_task = examination.start_time
    #                     best_traveling_duration_detour = examination.travel_time_increase
    #
    #             # Go to the next step
    #             examined_step_index += 1
    #
    #         # If the insertion is upstream-feasible, ...
    #         elif examination.is_upstream_feasible:
    #
    #             # If no feasible insertions are yet known, ...
    #             if not best_swap_is_time_feasible:
    #                 late_due_to_upstream_at_step_after_insertion = (
    #                         examination.earliest_start_time_for_upstream -
    #                         examination.latest_start_time_for_downstream
    #                 )
    #
    #                 # If upstream-feasibility has not yet been noticed,
    #                 if not best_swap_is_upstream_feasible:
    #
    #                     # Signal that the insertion is upstream-feasible
    #                     best_swap_is_upstream_feasible = True
    #
    #                     # Save this insertion as the best one
    #                     best_swap_is_downstream_feasible = examination.is_downstream_feasible
    #                     best_swap_step_index = examined_step_index
    #                     best_start_time_of_entering_task = examination.start_time
    #                     best_start_time_of_entering_task_for_upstream = \
    #                         examination.earliest_start_time_for_upstream
    #                     best_start_time_of_entering_task_for_downstream = \
    #                         examination.latest_start_time_for_downstream
    #                     best_late = late_due_to_upstream_at_step_after_insertion
    #                     best_traveling_duration_detour = examination.travel_time_increase
    #
    #                 # If upstream-feasibility has already been noticed,
    #                 else:
    #
    #                     # If it is the best insertion late-wise,
    #                     # then save it
    #                     if late_due_to_upstream_at_step_after_insertion < best_late:
    #                         best_swap_is_downstream_feasible = examination.is_downstream_feasible
    #                         best_swap_step_index = examined_step_index
    #                         best_start_time_of_entering_task = examination.start_time
    #                         best_start_time_of_entering_task_for_upstream = \
    #                             examination.earliest_start_time_for_upstream
    #                         best_start_time_of_entering_task_for_downstream = \
    #                             examination.latest_start_time_for_downstream
    #                         best_late = late_due_to_upstream_at_step_after_insertion
    #                         best_traveling_duration_detour = examination.travel_time_increase
    #
    #             # Go to the next step
    #             examined_step_index += 1
    #
    #         # If the insertion is not upstream-feasible, ...
    #         else:
    #
    #             # If no upstream-feasible insertions are yet known,
    #             # then save it
    #             if not best_swap_is_upstream_feasible:
    #                 best_swap_is_downstream_feasible = examination.is_downstream_feasible
    #                 late_due_to_upstream_at_insertion = \
    #                     examination.earliest_start_time_for_upstream + task.duration - task.end_time_UB
    #                 best_swap_step_index = examined_step_index
    #                 best_start_time_of_entering_task = examination.start_time
    #                 best_start_time_of_entering_task_for_upstream = \
    #                     examination.earliest_start_time_for_upstream
    #                 best_start_time_of_entering_task_for_downstream = \
    #                     examination.latest_start_time_for_downstream
    #                 best_late = late_due_to_upstream_at_insertion
    #                 best_traveling_duration_detour = examination.travel_time_increase
    #
    #             # Stop the examinations
    #             examined_step_index = self.nb_steps
    #
    #     examination = ReplacementExamination()
    #     examination.is_feasible = swap_is_skill_feasible and best_swap_is_time_feasible
    #     examination.is_skill_feasible = swap_is_skill_feasible
    #     examination.is_time_feasible = best_swap_is_time_feasible
    #     examination.is_upstream_feasible = best_swap_is_upstream_feasible
    #     examination.is_downstream_feasible = best_swap_is_downstream_feasible
    #     examination.start_time = best_start_time_of_entering_task
    #     examination.earliest_start_time_for_upstream = best_start_time_of_entering_task_for_upstream
    #     examination.latest_start_time_for_downstream = best_start_time_of_entering_task_for_downstream
    #     examination.travel_time_increase = best_traveling_duration_detour
    #     examination.late = best_late
    #     examination.employee = self.employee
    #     examination.replacement_step_index = best_swap_step_index
    #     examination.replaced_task = self.get_step(best_swap_step_index).activity
    #     examination.replacing_task = task
    #     return examination

    def find_best_task_to_be_replaced_with_given_task(self, task: Task,
                                                      compute_times_only_if_skill_constraints_satisfied: bool = True):
        # Examine skill-wise feasibility
        swap_is_skill_feasible = self.employee.is_capable_of_performing(task)
        if compute_times_only_if_skill_constraints_satisfied and not swap_is_skill_feasible:
            examination = ReplacementExamination()
            examination.is_feasible = False
            examination.is_skill_feasible = False
            examination.employee = self.employee
            examination.replacing_task = task
            return examination
        # Examine all step index for swap starting from index 1
        examined_step_index = 1
        best_examination = None
        while examined_step_index <= self.nb_steps - 2:
            replaced_task = self.get_step(examined_step_index).activity
            examination = self.examine_replacing_task_with_another(replaced_task, task, False)
            if best_examination is None or examination.is_better_than(best_examination):
                best_examination = examination
            if best_examination.is_upstream_feasible and not examination.is_upstream_feasible:
                examined_step_index = self.nb_steps
            else:
                examined_step_index += 1
        # TODO: Remove these lines
        # best_examination_bis = self.find_best_task_to_be_replaced_with_given_task_bis(
        #     task, compute_times_only_if_skill_constraints_satisfied
        # )
        # if best_examination != best_examination_bis:
        #     print(best_examination)
        #     print(best_examination_bis)
        #     raise Exception("ERROR")
        return best_examination

    def find_best_replacement_among_various_replacing_tasks(
            self, tasks: list[Task], compute_times_only_if_skill_constraints_satisfied: bool = True):
        best_examination = self.find_best_task_to_be_replaced_with_given_task(
            tasks[0], compute_times_only_if_skill_constraints_satisfied
        )
        for task in tasks[1:]:
            examination = self.find_best_task_to_be_replaced_with_given_task(
                task, compute_times_only_if_skill_constraints_satisfied
            )
            # Case where the current transformation is feasible
            if examination.is_feasible:
                if not best_examination.is_feasible or \
                        (examination.travel_time_increase <
                         best_examination.travel_time_increase):
                    best_examination = examination
            # Case where both the current transformation and the best currently known one are infeasible
            elif not best_examination.is_feasible:
                # Case where the current transformation is infeasible skill-wise
                if not examination.is_skill_feasible:
                    if not best_examination.is_skill_feasible and \
                            task.skill_level < best_examination.replacing_task.skill_level:
                        best_examination = examination
                # Case where the current transformation is feasible skill-wise
                else:
                    if not best_examination.is_skill_feasible:
                        best_examination = examination
                    # Case where both the current transformation and
                    # the best currently known one are feasible skill-wise
                    else:
                        # Case where the current transformation is infeasible upstream-wise
                        if not examination.is_upstream_feasible:
                            if not best_examination.is_upstream_feasible and examination.late < best_examination.late:
                                best_examination = examination
                        # Case where the current transformation is feasible upstream-wise
                        else:
                            if not best_examination.is_upstream_feasible:
                                best_examination = examination
                            # Case where both the current transformation and the best currently known one
                            # are feasible upstream-wise
                            elif examination.late < best_examination.late:
                                best_examination = examination
        return best_examination

    #############################################
    # Examining - Reorder - Best transformation #
    #############################################

    def examine_moving_after_a_task(self, moving_task: Task, fixed_task: Task):
        """
        Examine the feasibility of moving the given moving task after the fixed task in this sequence

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given employee's sequence;
        - 2. the given fixed task must be in the given employee's sequence;
        - 3. the given moving task must be before the given fixed task in the given employee's sequence;
        - 4. the times of the given employee's sequence are consistent.

        :param moving_task: the task which would move (Task)
        :param fixed_task: the task after which the moving task would be moved
        :return: the reordering examination (ReorderExamination)
        """
        # Check the assumptions
        assert (moving_task in self.get_contained_tasks(),
                f"The given moving task {moving_task.name} is not in this sequence")
        assert (fixed_task in self.get_contained_tasks(),
                f"The given leaving task {fixed_task.name} is not in this sequence")
        assert (self.get_step_index_of(moving_task) < self.get_step_index_of(fixed_task),
                f"The given moving task {moving_task.name} is not before the given fixed task {fixed_task.name} ")
        assert self.is_time_consistent, "The times are not consistent"
        # Examine
        sequence_copy = self.copy()
        moving_task_index = sequence_copy.get_step_index_of(moving_task)
        sequence_travel_time_before_removing = sequence_copy.total_traveling_duration
        sequence_copy.remove_step(moving_task_index, False, True)
        sequence_travel_time_after_removing = sequence_copy.total_traveling_duration
        sequence_travel_time_decrease_due_to_removal = \
            sequence_travel_time_before_removing - sequence_travel_time_after_removing
        fixed_task_index = sequence_copy.get_step_index_of(fixed_task)
        insertion_examination = sequence_copy.examine_insertion_at(moving_task, fixed_task_index + 1)
        examination = ReorderExamination.from_examination(insertion_examination)
        examination.moving_task = moving_task
        examination.activity_before = fixed_task
        examination.activity_after = sequence_copy.get_step(fixed_task_index + 1).activity
        examination.travel_time_increase -= sequence_travel_time_decrease_due_to_removal
        return examination

    def examine_moving_before_a_task(self, moving_task: Task, fixed_task: Task):
        """
        Examine the feasibility of moving the given moving task before the fixed task in this sequence

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given employee's sequence;
        - 2. the given fixed task must be in the given employee's sequence;
        - 3. the given moving task must be before the given fixed task in the given employee's sequence;
        - 4. the times of the given employee's sequence are consistent.

        :param moving_task: the task which would move (Task)
        :param fixed_task: the task before which the moving task would be moved (Task)
        :return: the reordering examination (ReorderExamination)
        """
        # Check the assumptions
        assert (moving_task in self.get_contained_tasks(),
                f"The given moving task {moving_task.name} is not in this sequence")
        assert (fixed_task in self.get_contained_tasks(),
                f"The given leaving task {fixed_task.name} is not in this sequence")
        assert (self.get_step_index_of(moving_task) > self.get_step_index_of(fixed_task),
                f"The given moving task {moving_task.name} is not after the given fixed task {fixed_task.name} ")
        assert self.is_time_consistent, "The times are not consistent"
        # Examine
        sequence_copy = self.copy()
        moving_task_index = sequence_copy.get_step_index_of(moving_task)
        sequence_travel_time_before_removing = sequence_copy.total_traveling_duration
        sequence_copy.remove_step(moving_task_index, False, True)
        sequence_travel_time_after_removing = sequence_copy.total_traveling_duration
        sequence_travel_time_decrease_due_to_removal = \
            sequence_travel_time_before_removing - sequence_travel_time_after_removing
        fixed_task_index = sequence_copy.get_step_index_of(fixed_task)
        insertion_examination = sequence_copy.examine_insertion_at(moving_task, fixed_task_index)
        examination = ReorderExamination.from_examination(insertion_examination)
        examination.moving_task = moving_task
        examination.activity_before = sequence_copy.get_step(fixed_task_index - 1).activity
        examination.activity_after = fixed_task
        examination.travel_time_increase -= sequence_travel_time_decrease_due_to_removal
        return examination

    def find_best_reorder_to_perform_task_later(self, moving_task: Task):
        """
        Find the best reorder such that the given task is performed at a later step

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given employee's sequence;
        - 2. the given moving task must not be the last task in the given employee's sequence;
        - 3. the times of the given employee's sequence are consistent.

        :param moving_task: the task which would move (Task)
        :return: the reordering examination (ReorderExamination)
        """
        step_index = self.get_step_index_of(moving_task)
        last_task_step_index = self.get_last_task_step_index()
        # Check the assumptions
        assert (step_index < last_task_step_index,
                f"The given moving task {moving_task.name} is the last task in this sequence")
        # Find the best shift to later
        best_examination = None
        for step in self.get_steps(step_index + 1, last_task_step_index + 1):
            task = step.activity
            examination = self.examine_moving_after_a_task(moving_task, task)
            if not best_examination or examination.is_better_than(best_examination):
                best_examination = examination
        return best_examination

    def find_best_reorder_to_perform_task_earlier(self, moving_task: Task):
        """
        Find the best reorder such that the given task is performed at an earlier step

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given employee's sequence;
        - 2. the given moving task must not be the first task in the given employee's sequence;
        - 3. the times of the given employee's sequence are consistent.

        :param moving_task: the task which would move (Task)
        :return: the reordering examination (ReorderExamination)
        """
        step_index = self.get_step_index_of(moving_task)
        first_task_step_index = self.get_first_task_step_index()
        # Check the assumptions
        assert (step_index > first_task_step_index,
                f"The given moving task {moving_task.name} is the first task in this sequence")
        # Find the best shift to earlier
        best_examination = None
        for step in self.get_steps(first_task_step_index, step_index):
            task = step.activity
            examination = self.examine_moving_before_a_task(moving_task, task)
            if not best_examination or examination.is_better_than(best_examination):
                best_examination = examination
        return best_examination

    def find_best_task_reorder(self, moving_task: Task):
        """
        Find the best reorder such that the given task is performed at a later or earlier step

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given employee's sequence;
        - 2. the given moving task must not be the first or last task in the given employee's sequence;
        - 3. the times of the given employee's sequence are consistent.

        :param moving_task: the task which would move (Task)
        :return: the reordering examination (ReorderExamination)
        """
        if self.get_step_index_of(moving_task) == self.get_first_task_step_index():
            return self.find_best_reorder_to_perform_task_later(moving_task)
        elif self.get_step_index_of(moving_task) == self.get_last_task_step_index():
            return self.find_best_reorder_to_perform_task_earlier(moving_task)
        else:
            examination_later = self.find_best_reorder_to_perform_task_later(moving_task)
            examination_earlier = self.find_best_reorder_to_perform_task_earlier(moving_task)
            if examination_later.is_better_than(examination_earlier):
                return examination_later
            else:
                return examination_earlier

    ##################################################
    # Examining - Reorder - Feasible transformations #
    ##################################################

    def find_feasible_reorders_to_perform_task_later(self, moving_task: Task):
        """
        Find the feasible reorders such that the given task is performed at a later step

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given employee's sequence;
        - 2. the times of the given employee's sequence are consistent.

        :param moving_task: the task which would move (Task)
        :return: the reordering examinations (list of ReorderExamination)
        """
        step_index = self.get_step_index_of(moving_task)
        last_task_step_index = self.get_last_task_step_index()
        examinations = []
        for step in self.get_steps(step_index + 1, last_task_step_index + 1):
            task = step.activity
            examination = self.examine_moving_after_a_task(moving_task, task)
            if examination.is_feasible:
                examinations.append(examination)
        return examinations

    def find_feasible_reorders_to_perform_task_earlier(self, moving_task: Task):
        """
        Find the feasible reorders such that the given task is performed at an earlier step

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given employee's sequence;
        - 2. the times of the given employee's sequence are consistent.

        :param moving_task: the task which would move (Task)
        :return: the reordering examinations (list of ReorderExamination)
        """
        step_index = self.get_step_index_of(moving_task)
        first_task_step_index = self.get_first_task_step_index()
        examinations = []
        for step in self.get_steps(first_task_step_index, step_index):
            task = step.activity
            examination = self.examine_moving_before_a_task(moving_task, task)
            if examination.is_feasible:
                examinations.append(examination)
        return examinations

    def find_task_feasible_reorders(self, moving_task: Task):
        """
        Find the feasible reorders such that the given task is performed at a later or earlier step

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given employee's sequence;
        - 2. the given moving task must not be the first or last task in the given employee's sequence;
        - 3. the times of the given employee's sequence are consistent.

        :param moving_task: the task which would move (Task)
        :return: the reordering examinations (list of ReorderExamination)
        """
        examinations_later = self.find_feasible_reorders_to_perform_task_later(moving_task)
        examinations_earlier = self.find_feasible_reorders_to_perform_task_earlier(moving_task)
        return examinations_later + examinations_earlier

    ##################
    # Critical steps #
    ##################

    def find_first_critical_step_index_backward_from(self, step_index: int):
        """
        Find the index of the first backward critical step that can be found,
        starting from the given step index and going backward.

        Remark: A backward critical step is a step which BTS is limited by its start time lower bound,
        not by the times of steps before it.

        :param step_index: (int)
        :return: the index of the first critical step found
        """
        step = self[step_index]
        while step.BTS < step.start_time - step.activity.start_time_LB:
            step_index -= 1
            step = self[step_index]
        return step_index

    def find_first_critical_step_index_forward_from(self, step_index: int):
        """
        Find the index of the first forward critical step that can be found,
        starting from the given step index and going forward.

        Remark: A forward critical step is a step which FTS is limited by its end time upper bound,
        not by the times of the steps after it.

        :param step_index: (int)
        :return: the index of the first critical step found
        """
        step = self[step_index]
        while step.FTS < step.activity.end_time_UB - (step.start_time + step.activity.duration):
            step_index += 1
            step = self[step_index]
        return step_index

    #####################################
    # Local change - Private - Feasible #
    #####################################

    def _feasibly_remove_step(self, step_index: int, tighten_times: bool = True, update_KPIs: bool = True):
        """
        Remove the step from this sequence at the given index.

        Assumptions (only checked in debug):

        - 1. the given step index is between 1 (included) and len(sequence) - 1 (included);
        - 2. the activity at the given step index is a Task;
        - 3. the times of the sequence are consistent.

        :param step_index: the index (int) of the step that is removed from this sequence
        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence
          after the step has been removed in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the change
        """

        # Check assumptions
        assert (0 < step_index < self.__len__(),
                f"The given step index {step_index} is not between 1 and {self.__len__() - 1} included")
        assert (isinstance(self.get_step(step_index).activity, Task),
                f"It is not possible to removed step {step_index} as its corresponding activity "
                f"{self.get_step(step_index).activity.name} is not a task")
        assert self.is_time_consistent, "The times are not consistent"

        # Remove the step
        removed_step = self._steps.pop(step_index)
        # Remark: now that the step has been popped out, step_index corresponds to the step after the removal

        # Get steps around the removed step
        step_before_removal = self[step_index - 1]
        step_before_removal_former_end_time = step_before_removal.end_time
        step_after_removal = self[step_index]
        step_after_removal_former_start_time = step_after_removal.start_time
        step_after_removal_former_arrival_time = step_after_removal.arrival_time

        # Compute traveling duration
        traveling_duration_before_after = \
            self.instance.compute_traveling_duration(step_before_removal.activity, step_after_removal.activity)

        # If the step before removal is a departure, then update it
        if step_index == 1:
            step_after_removal.arrival_time = step_after_removal.start_time
            step_before_removal.end_time = step_after_removal.arrival_time - traveling_duration_before_after
            step_before_removal.start_time = step_before_removal.end_time
            step_before_removal.arrival_time = step_before_removal.start_time
            step_before_removal.BTS += step_before_removal.start_time - step_before_removal_former_end_time
            assert step_before_removal.start_time >= step_before_removal_former_end_time, \
                "After removal, departure time is found to be earlier than before"

        # Else, update arrival time of step after removal
        else:
            step_after_removal.arrival_time = step_before_removal.end_time + traveling_duration_before_after
            assert step_after_removal.arrival_time <= step_after_removal_former_arrival_time, \
                "After removal, arrival time of step-after-removal is found to be later than before"

            # If the step after removal is a comeback, then update return times to be all equal
            if step_index == self.nb_steps - 1:
                step_after_removal.FTS += step_after_removal.start_time - step_after_removal.arrival_time
                step_after_removal.start_time = step_after_removal.arrival_time
                step_after_removal.end_time = step_after_removal.start_time
                assert step_after_removal.arrival_time <= step_after_removal_former_arrival_time, \
                    "After removal, return time is found to be later than before"

        # Update KPIs if needed
        if update_KPIs:
            # Update tasks realization
            self._nb_realized_tasks -= 1
            self._total_working_duration -= removed_step.activity.duration

            # Update traveling duration
            # Remark: rather than computing the traveling durations between the step before / after the removal and
            # the removed step, these durations can be computed thanks to former times values of steps,
            # however it supposes that arrival, start and end times of these steps are valid
            traveling_duration_variation = (
                    traveling_duration_before_after -
                    (removed_step.arrival_time - step_before_removal_former_end_time) -
                    (step_after_removal_former_arrival_time - removed_step.end_time)
            )
            assert (removed_step.arrival_time - step_before_removal_former_end_time ==
                    self.instance.compute_traveling_duration(step_before_removal.activity, removed_step.activity),
                    "Times before removal were incorrect, traveling duration was not respected")
            assert (step_after_removal_former_arrival_time - removed_step.end_time ==
                    self.instance.compute_traveling_duration(removed_step.activity, step_after_removal.activity),
                    "Times after removal were incorrect, traveling duration was not respected")
            assert (traveling_duration_variation <= 0,
                    "After removal, variation of traveling duration is found to be positive")
            self._total_traveling_duration += traveling_duration_variation

            # Update idle time
            idle_time_variation = (
                    (step_after_removal.start_time - step_after_removal.arrival_time) -
                    (step_after_removal_former_start_time - step_after_removal_former_arrival_time) -
                    (removed_step.start_time - removed_step.arrival_time)
            )
            self._total_idle_time += idle_time_variation

            # Update traveling distance
            self._total_traveling_distance += (
                    step_before_removal.activity.distance_to(step_after_removal.activity) -
                    (step_before_removal.activity.distance_to(removed_step.activity) +
                     removed_step.activity.distance_to(step_after_removal.activity))
            )

        # Update times slacks
        # BTS of steps from steps[0] (included) to steps[step_index - 1] (included) are correct
        # BTS of steps following steps[step_index] (included) must be updated
        self.update_BTS_forward_from(step_index)
        # FTS of steps from steps[-1] (included) to steps[step_index] (included) are correct
        # FTS of steps preceding steps[step_index - 1] (included) must be updated
        self.update_FTS_backward_from(step_index - 1)

        # Tighten times if needed
        if tighten_times:
            self.tighten_times(update_KPIs)

        # Clear removed step
        removed_step.clear()

    def _feasibly_remove_all_tasks(self, tighten_times: bool = True, update_KPIs: bool = True):
        """
        Remove all the steps which correspond to tasks from this sequence.

        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence
          after the step has been removed in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the change
        """
        step_indices = self.get_step_indices_of_contained_tasks()
        for step_index in reversed(step_indices):
            self._feasibly_remove_step(step_index, False, False)
        if update_KPIs:
            self.compute_KPIs()
        if tighten_times:
            self.tighten_times(update_KPIs)

    def _feasibly_insert_task_at(self, task: Task, step_index: int, start_time: int,
                                 tighten_times: bool = True, update_KPIs: bool = True):
        """
        Insert the given task at the given step index with the given start time;
        this method shall only be used when the insertion is known to be feasible.

        Assumptions (only checked in debug):
        
        - 1. the given task is not in this sequence;
        - 2. the given step index is between 1 (included) and len(sequence) - 1 (included);
        - 3. the times of the sequence are consistent.

        :param task: the task (Task) to insert
        :param step_index: the index (int) of the step where the given task is inserted
        :param start_time: the start time (int) at which the task is realized
        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence
          after the step has been inserted in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the change
        :return: a pair of indices of the first and last step which start time has been changed
        """

        # Check assumptions
        assert (not (task in self.get_contained_tasks()),
                f"The given task {task.name} is already in this sequence")
        assert (0 < step_index < self.__len__(),
                f"The given step index {step_index} is not between 1 and {self.__len__() - 1} included")
        assert self.is_time_consistent, "The times are not consistent"

        # Initialize indices of the range of steps which start_time has been changed
        first_step_with_time_change_index = step_index
        last_step_with_time_change_index = step_index

        # Insert step
        inserted_step = StepForHeuristics(task, start_time, start_time, start_time + task.duration)
        self._steps.insert(step_index, inserted_step)
        # Remark: currently the sequence of times around the inserted step is not valid,
        # the current arrival time of the inserted step is likely to be different from the arrival time obtained by
        # considering that the employee leaves the step before the insertion at its current end time, and
        # the current arrival time of the step after the insertion is likely to be different from the arrival time
        # obtained by considering that the employee leaves the inserted step at its current end time

        # Get steps around the insertion
        step_before_insertion = self[step_index - 1]
        step_after_insertion = self[step_index + 1]

        # Compute traveling durations
        traveling_duration_before_after = step_after_insertion.arrival_time - step_before_insertion.end_time
        assert (traveling_duration_before_after ==
                self.instance.compute_traveling_duration(step_before_insertion.activity, step_after_insertion.activity),
                "Times before and after insertion were incorrect, traveling duration was not respected")
        traveling_duration_before = self.instance.compute_traveling_duration(step_before_insertion.activity, task)
        traveling_duration_after = self.instance.compute_traveling_duration(task, step_after_insertion.activity)

        # Update times before insertion
        arrival_times_difference_at_inserted_step = (
                inserted_step.arrival_time - (step_before_insertion.end_time + traveling_duration_before)
        )
        idle_time_variation_strictly_up_to_insertion = 0
        idle_time_at_inserted_step = 0
        # If the current arrival time of the inserted step is earlier than the arrival time obtained by considering
        # that the employee leaves the step before the insertion at its current end time,
        # then times before insertion must be shifted backward, this time shift quantity may be partially absorbed,
        # by the idle time contained in the portion of the sequence before the insertion,
        # which can be detected by the time shift of the departure time
        if arrival_times_difference_at_inserted_step < 0:
            backward_time_shift = -arrival_times_difference_at_inserted_step
            departure_former_time = self[0].start_time
            first_step_with_time_change_index = self.shift_steps_times_backward_from(
                step_index - 1, step_before_insertion.start_time - backward_time_shift
            )
            departure_backward_time_shift = departure_former_time - self[0].start_time
            idle_time_variation_strictly_up_to_insertion = departure_backward_time_shift - backward_time_shift
        # Otherwise
        else:
            idle_time_at_inserted_step = arrival_times_difference_at_inserted_step
            inserted_step.arrival_time = step_before_insertion.end_time + traveling_duration_before

        # Update times after insertion
        former_idle_time_at_step_after = step_after_insertion.start_time - step_after_insertion.arrival_time
        step_after_insertion.arrival_time = inserted_step.end_time + traveling_duration_after
        difference_start_and_arrival_times_after = step_after_insertion.start_time - step_after_insertion.arrival_time
        if difference_start_and_arrival_times_after < 0:
            forward_time_shift = -difference_start_and_arrival_times_after
            comeback_former_time = self[-1].start_time
            last_step_with_time_change_index = self.shift_steps_times_forward_from(
                step_index + 1, step_after_insertion.arrival_time
            )
            comeback_forward_time_shift = self[-1].start_time - comeback_former_time
            idle_time_variation_strictly_down_from_insertion = \
                -former_idle_time_at_step_after + (comeback_forward_time_shift - forward_time_shift)
        else:
            idle_time_variation_strictly_down_from_insertion = \
                difference_start_and_arrival_times_after - former_idle_time_at_step_after

        # Update KPIs if needed
        if update_KPIs:

            # Update tasks realization
            self._nb_realized_tasks += 1
            self._total_working_duration += inserted_step.activity.duration

            # Update traveling duration
            traveling_duration_variation = (
                    traveling_duration_before + traveling_duration_after - traveling_duration_before_after
            )
            self._total_traveling_duration += traveling_duration_variation
            assert (traveling_duration_variation >= 0,
                    "After insertion, variation of traveling duration is found to be negative")

            # Update idle time
            idle_time_variation = (
                    idle_time_variation_strictly_up_to_insertion + idle_time_at_inserted_step +
                    idle_time_variation_strictly_down_from_insertion
            )
            self._total_idle_time += idle_time_variation

            # Update traveling distance
            self._total_traveling_distance += (
                    step_before_insertion.activity.distance_to(task) + step_after_insertion.activity.distance_to(task) -
                    step_before_insertion.activity.distance_to(step_after_insertion.activity)
            )

        # Update times slacks
        # BTS of steps from steps[0] (included) to steps[step_index - 1] (included) are correct
        # BTS of steps following steps[step_index] (included) must be updated
        self.update_BTS_forward_from(step_index)
        # FTS of steps from steps[-1] (included) to steps[step_index + 1] (included) are correct
        # FTS of steps preceding steps[step_index] (included) must be updated
        self.update_FTS_backward_from(step_index)

        # Tighten times
        if tighten_times:
            self.tighten_times(update_KPIs)

        # Return indices of the range of steps which start times has been changed
        return first_step_with_time_change_index, last_step_with_time_change_index

    #######################################
    # Local change - Private - Infeasible #
    #######################################

    def _infeasibly_insert_task_at(self, task: Task, step_index: int, start_time: int,
                                   start_time_for_backward: int, start_time_for_forward: int):
        """
        Insert the given task at the given step index with the given start time;
        two artificial start times are provided for the computation of the times of the steps and after the insertion;
        this method shall only be used when the insertion is known to be infeasible.

        Assumptions (only checked in debug):

        - 1. the given task is not in this sequence;
        - 2. the given step index is between 1 (included) and the number of steps - 1 (included);
        - 3. the times of the sequence are consistent.

        :param task: the task (Task) to insert
        :param step_index: the index (int) of the step where the given task is inserted
        :param start_time: the start time (int) of the task to insert
        :param start_time_for_backward: the artificial start time (int) of the task to insert used for
          the computation of the times of the steps before the task to insert
        :param start_time_for_forward: the artificial start time (int) of the task to insert used for
          the computation of the times of the steps after the task to insert
        :return: a pair of indices of the first and last step which start time has been changed
        """

        # Initialize indices of the range of steps which start_time has been changed
        first_step_with_time_change_index = step_index
        last_step_with_time_change_index = step_index

        # Insert step
        inserted_step = StepForHeuristics(task, start_time, start_time, start_time + task.duration)
        self._steps.insert(step_index, inserted_step)

        # Update times before insertion
        step_before_insertion = self[step_index - 1]
        traveling_duration_before = self.instance.compute_traveling_duration(step_before_insertion.activity, task)
        step_before_insertion_start_time = \
            start_time_for_backward - (traveling_duration_before + step_before_insertion.activity.duration)
        if step_before_insertion_start_time < step_before_insertion.start_time:
            first_step_with_time_change_index = \
                self.shift_steps_times_backward_from(step_index - 1, step_before_insertion_start_time)
            inserted_step.arrival_time = start_time_for_backward
        else:
            inserted_step.arrival_time = step_before_insertion.end_time + traveling_duration_before

        # Update times after insertion
        step_after_insertion = self[step_index + 1]
        traveling_duration_after = self.instance.compute_traveling_duration(task, step_after_insertion.activity)
        step_after_insertion_arrival_time = start_time_for_forward + task.duration + traveling_duration_after
        step_after_insertion.arrival_time = step_after_insertion_arrival_time
        if step_after_insertion.start_time < step_after_insertion_arrival_time:
            last_step_with_time_change_index = \
                self.shift_steps_times_forward_from(step_index + 1, step_after_insertion_arrival_time)

        # Return indices of the range of steps which start time has been changed
        return first_step_with_time_change_index, last_step_with_time_change_index

    #########################
    # Local change - Public #
    #########################

    def remove_step(self, step_index: int, tighten_times: bool = True, update_KPIs: bool = True):
        """
        Remove the step from this sequence at the given index

        Assumptions (only checked in debug):
        - 1. the given step index is between 1 (included) and the number of steps - 1 (included)
        - 2. the activity at the given step index is a Task
        - 3. the times of the sequence are consistent

        :param step_index: the index (int) of the step that is removed from this sequence
        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence
          after the step has been removed in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the change
        :return: a boolean (bool) which indicates whether the change is feasible
        """
        # Remark: the assumptions are checked in _feasibly_remove_step
        assert self.is_time_consistent, "The times of the sequence are not consistent before removing."
        self._feasibly_remove_step(step_index, tighten_times, update_KPIs)
        assert self.is_time_consistent, "The times of the sequence are not consistent after removing."
        return True

    def remove_task(self, task: Task, tighten_times: bool = True, update_KPIs: bool = True):
        """
        Remove the task from this sequence

        Assumptions (only checked in debug):
        - 1. the task is in the sequence
        - 2. the times of the sequence are consistent

        :param task: the task (Task) to remove from this sequence
        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence
          after the task has been removed in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the change
        :return: a boolean (bool) which indicates whether the change is feasible
        """
        assert self.contains(task), f"Task {task} is not in the sequence"
        return self.remove_step(self.get_step_index_of(task), tighten_times, update_KPIs)

    def remove_all_tasks(self, tighten_times: bool = True, update_KPIs: bool = True):
        """
        Remove all the steps which correspond to tasks from this sequence.

        :param tighten_times: a boolean (bool) which, if set to True, tightens the times of the sequence
          after the step has been removed in order to minimize idle time
        :param update_KPIs: a boolean (bool) which maintains the KPIs up to date after the change
        :return: a boolean (bool) which indicates whether the change is feasible
        """
        # Remark: the assumptions are checked in _feasibly_remove_step
        assert self.is_time_consistent, "The times of the sequence are not consistent before removing."
        self._feasibly_remove_all_tasks(tighten_times, update_KPIs)
        assert self.is_time_consistent, "The times of the sequence are not consistent after removing."
        return True

    def insert_task_at(self, entering_task: Task, step_index: int, start_time: int = None,
                       start_time_for_backward: int = None, start_time_for_forward: int = None,
                       tighten_times: bool = True, update_KPIs: bool = True):
        """
        TODO

        :param entering_task:
        :param step_index:
        :param start_time:
        :param start_time_for_backward:
        :param start_time_for_forward:
        :param tighten_times:
        :param update_KPIs:
        :return: a boolean (bool) which indicates whether the change is feasible and
          a pair of indices of the first and last step which start time has been changed
        """

        # If the start time of the task to insert is not provided,
        # then compute it
        if start_time is None:
            examination = self.examine_insertion_at(entering_task, step_index)
            start_time = examination.start_time
            start_time_for_backward = examination.earliest_start_time_for_upstream
            start_time_for_forward = examination.latest_start_time_for_downstream
        insertion_is_feasible = start_time_for_backward is None

        # If the insertion is feasible (that is to say there are no start time for backward and forward),
        # then do the change and return a boolean True as it is feasible
        if insertion_is_feasible:
            assert self.is_time_consistent, "The times of the sequence are not consistent before inserting"
            first_step_with_time_change_index, last_step_with_time_change_index = \
                self._feasibly_insert_task_at(entering_task, step_index, start_time, tighten_times, update_KPIs)
            assert self.is_time_consistent, "The times of the sequence are not consistent after inserting"
            return True, (first_step_with_time_change_index, last_step_with_time_change_index)

        # If the insertion is not feasible,
        # then do the change and return a boolean False as it is not feasible
        else:
            first_step_with_time_change_index, last_step_with_time_change_index = \
                self._infeasibly_insert_task_at(entering_task, step_index, start_time,
                                                start_time_for_backward, start_time_for_forward)
            return False, (first_step_with_time_change_index, last_step_with_time_change_index)

    # Remark: entering task must not be already in this sequence
    def replace_task_by_another_at(self, entering_task: Task, step_index: int, start_time: int = None,
                                   start_time_for_backward: int = None, start_time_for_forward: int = None,
                                   tighten_times: bool = True, update_KPIs: bool = True):
        """
        TODO

        Assumptions (only checked in debug):

        - 1. the entering task is not already in the sequence;
        - 2. the given step index is between 1 (included) and the number of steps - 1 (included);
        - 3. the activity at the given step index is a Task;
        - 4. the times of the sequence are consistent.

        :param entering_task:
        :param step_index:
        :param start_time:
        :param start_time_for_backward:
        :param start_time_for_forward:
        :param tighten_times:
        :param update_KPIs:
        :return: a boolean (bool) which indicates whether the change is feasible
          and a pair of indices of the first and last step which start time has been changed
        """

        # Check assumptions
        # Remark: the assumptions are already checked in remove_step and insert_task_at

        # Remove the given step from this sequence
        self.remove_step(step_index, False, update_KPIs)

        # Insert the task in this sequence at the given step index
        return self.insert_task_at(entering_task, step_index,
                                   start_time, start_time_for_backward, start_time_for_forward,
                                   tighten_times, update_KPIs)
