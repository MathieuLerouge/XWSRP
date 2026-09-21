# Standard library
from typing import TYPE_CHECKING, Optional, cast

# Local libraries
from src.modeling.activity import Activity
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.optimization.heuristics.evaluation import (
    InsertionEvaluation, ReassigningEvaluation, ReplacementEvaluation, ReorderEvaluation
)

if TYPE_CHECKING:
    from src.optimization.heuristics.sequence import SequenceForHeuristics
    from src.optimization.heuristics.solution import SolutionForHeuristics


#############
# Evaluator #
#############

class Evaluator:
    """
    Stateless collection of static methods evaluating hypothetical task insertions, replacements, reassignments,
    and reorderings, either in a single SequenceForHeuristics or across the sequences of a SolutionForHeuristics,
    without mutating the given sequence(s).
    """

    ########################
    # Sequence - Insertion #
    ########################

    @staticmethod
    def evaluate_insertion_at(
            sequence: "SequenceForHeuristics", task: Task, insertion_step_index: int,
            compute_times_only_if_skill_constraints_satisfied: bool = True
    ):
        """
        Evaluate the feasibility of the insertion of the given task at the given insertion step index.

        Assumptions (only checked in debug):

        - 1. the given task must not be already in the given sequence;
        - 2. the given insertion step index must be between 1 (included) and the number of steps - 1 (included);
        - 3. the times of the given sequence are consistent.

        Args:
            sequence: The sequence the task would be inserted in.
            task: The task that would be inserted.
            insertion_step_index: The index of the step where the given task would be inserted.
            compute_times_only_if_skill_constraints_satisfied: Whether start times should still be computed
              if the skill constraints are not satisfied.

        Returns:
            The insertion evaluation.
        """

        # Check the assumptions
        assert task not in sequence.get_contained_tasks(), \
            f"The given entering task {task.name} is already in this sequence"
        assert 0 < insertion_step_index < sequence.__len__(), \
            f"The given step index {insertion_step_index} is not between 1 and {sequence.__len__() - 1} included"
        assert sequence.is_time_consistent, "The times are not consistent"

        # Evaluate skill-wise feasibility
        is_skill_feasible = sequence.employee.is_capable_of_performing(task)
        if compute_times_only_if_skill_constraints_satisfied and not is_skill_feasible:
            evaluation = InsertionEvaluation()
            evaluation.is_feasible = False
            evaluation.is_skill_feasible = False
            evaluation.inserted_task = task
            evaluation.employee = sequence.employee
            return evaluation

        # Get the step before and after the hypothetical insertion
        step_before = sequence[insertion_step_index - 1]
        step_after = sequence[insertion_step_index]

        # Compute the earliest time at which the employee can start performing the entering task,
        # so that the times of the upstream portion of his/her sequence before the insertion are consistent,
        # and the latest time at which he/she can start performing the entering task,
        # so that the times of the downstream portion of his/her sequence after the insertion are consistent
        traveling_duration_from_step_before_insertion_to_entering_task = \
            sequence.instance.compute_traveling_duration(step_before.activity, task)
        earliest_start_time_of_entering_task = cast(int, max(
            task.start_time_lb,
            step_before.start_time - step_before.bts + step_before.activity.duration +
            traveling_duration_from_step_before_insertion_to_entering_task
        ))
        traveling_duration_from_entering_task_to_step_after_insertion = \
            sequence.instance.compute_traveling_duration(task, step_after.activity)
        latest_start_time_of_entering_task = cast(int, min(
            task.end_time_ub,
            step_after.start_time + step_after.fts -
            traveling_duration_from_entering_task_to_step_after_insertion
        )) - task.duration
        traveling_duration_detour = (
                traveling_duration_from_step_before_insertion_to_entering_task +
                traveling_duration_from_entering_task_to_step_after_insertion -
                sequence.instance.compute_traveling_duration(step_before.activity, step_after.activity)
        )

        # Compute two booleans indicating whether the entering task can be inserted while guaranteeing
        # the consistency of the times of respectively the upstream and the downstream portions of the sequence
        upstream_portion_is_feasible = (earliest_start_time_of_entering_task + task.duration <=
                                        task.end_time_ub)
        downstream_portion_is_feasible = (latest_start_time_of_entering_task >= task.start_time_lb)
        late = max(earliest_start_time_of_entering_task - latest_start_time_of_entering_task, 0)
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

        # Return evaluation
        evaluation = InsertionEvaluation()
        evaluation.is_feasible = is_time_feasible and is_skill_feasible
        evaluation.is_skill_feasible = is_skill_feasible
        evaluation.is_time_feasible = is_time_feasible
        evaluation.is_upstream_feasible = upstream_portion_is_feasible
        evaluation.is_downstream_feasible = downstream_portion_is_feasible
        evaluation.start_time = start_time
        evaluation.earliest_start_time_for_upstream = start_time_for_upstream
        evaluation.latest_start_time_for_downstream = start_time_for_downstream
        evaluation.travel_time_increase = traveling_duration_detour
        evaluation.late = late
        evaluation.inserted_task = task
        evaluation.insertion_step_index = insertion_step_index
        evaluation.activity_before_insertion = step_before.activity
        evaluation.employee = sequence.employee
        return evaluation

    @staticmethod
    def evaluate_insertion_after(sequence: "SequenceForHeuristics", task: Task, activity: Activity,
                                compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Evaluate the feasibility of inserting the given task after the given activity in the given sequence.

        Assumptions (only checked in debug):

        - 1. the given task must not be already in the given sequence;
        - 2. the given activity must be in the given sequence;
        - 3. the times of the given sequence are consistent.

        Args:
            sequence: The sequence the task would be inserted in.
            task: The task that would be inserted.
            activity: The activity after which the given task would be inserted.
            compute_times_only_if_skill_constraints_satisfied: Whether start times should still be computed
              if the skill constraints are not satisfied.

        Returns:
            The insertion evaluation.
        """
        step_index = sequence.get_step_index_of(activity) + 1
        return Evaluator.evaluate_insertion_at(sequence, task, step_index,
                                              compute_times_only_if_skill_constraints_satisfied)

    @staticmethod
    def find_best_insertion_between_consecutive_activities(
            sequence: "SequenceForHeuristics", task: Task, tabu_indices: Optional[list[int]] = None,
            compute_times_only_if_skill_constraints_satisfied: bool = True
    ):
        """
        Find the best insertion of the given task between two consecutive activities of the given sequence,
        skipping the given tabu step indices: see InsertionEvaluation.is_better_than for the exact ranking
        criteria used to decide which candidate insertion is kept.

        Args:
            sequence: The sequence the task would be inserted in.
            task: The task that would be inserted.
            tabu_indices: Step indices that must not be evaluated as insertion points, if any.
            compute_times_only_if_skill_constraints_satisfied: Whether start times should still be computed
              if the skill constraints are not satisfied.

        Returns:
            The evaluation of the best insertion found.
        """
        # Evaluate skill-wise feasibility
        insertion_is_skill_feasible = sequence.employee.is_capable_of_performing(task)
        if compute_times_only_if_skill_constraints_satisfied and not insertion_is_skill_feasible:
            evaluation = InsertionEvaluation()
            evaluation.is_feasible = False
            evaluation.is_skill_feasible = False
            evaluation.inserted_task = task
            evaluation.employee = sequence.employee
            return evaluation
        # Evaluate all step index for insertion starting from index 1
        if tabu_indices is None:
            tabu_indices = []
        evaluated_step_index = 1
        best_evaluation = None
        while evaluated_step_index <= sequence.nb_steps - 1:
            # If the evaluated step is tabu, then go to next step
            if evaluated_step_index in tabu_indices:
                evaluated_step_index += 1
            # If the evaluated step is not tabu, then evaluate it
            else:
                evaluation = Evaluator.evaluate_insertion_at(sequence, task, evaluated_step_index, False)
                if best_evaluation is None or evaluation.is_better_than(best_evaluation):
                    best_evaluation = evaluation
                if best_evaluation.is_upstream_feasible and not evaluation.is_upstream_feasible:
                    evaluated_step_index = sequence.nb_steps
                else:
                    evaluated_step_index += 1
        return best_evaluation

    @staticmethod
    def find_best_insertion_between_consecutive_activities_among_tasks_set(
            sequence: "SequenceForHeuristics", tasks: list[Task],
            compute_times_only_if_skill_constraints_satisfied: bool = True
    ):
        """
        Among all tasks of given set, find the best insertion of a task in the given sequence: see
        InsertionEvaluation.is_better_insertion_than for the exact ranking criteria.

        Assumptions (only checked in debug):
        The times of the given sequence are consistent.

        Args:
            sequence: The sequence a task would be inserted in.
            tasks: The candidate tasks that would be inserted.
            compute_times_only_if_skill_constraints_satisfied: Whether start times should still be computed
              if the skill constraints are not satisfied.

        Returns:
            The evaluation of the best insertion found.
        """

        # The assumptions are checked when calling find_best_insertion_between_consecutive_activities

        best_insertion_evaluation = Evaluator.find_best_insertion_between_consecutive_activities(
            sequence, tasks[0], None, compute_times_only_if_skill_constraints_satisfied
        )
        for task in tasks[1:]:
            evaluation = cast(
                InsertionEvaluation,
                Evaluator.find_best_insertion_between_consecutive_activities(
                    sequence, task, None, compute_times_only_if_skill_constraints_satisfied
                )
            )
            if evaluation.is_better_insertion_than(best_insertion_evaluation):
                best_insertion_evaluation = evaluation
        return best_insertion_evaluation

    @staticmethod
    def find_feasible_insertions_between_consecutive_activities(
            sequence: "SequenceForHeuristics", task: Task) -> list[InsertionEvaluation]:
        """
        Find all feasible insertions of a task in the given sequence.

        Assumptions (only checked in debug):
        The times of the given sequence are consistent.

        Args:
            sequence: The sequence a task would be inserted in.
            task: The candidate task that would be inserted.

        Returns:
            The list of all feasible insertions found.
        """
        evaluations = []
        one_insertion_is_upstream_feasible = False
        if sequence.employee.is_capable_of_performing(task):
            insertion_step_index = 1
            while insertion_step_index <= sequence.nb_steps - 1:
                evaluation = Evaluator.evaluate_insertion_at(sequence, task, insertion_step_index, True)
                if evaluation.is_feasible:
                    one_insertion_is_upstream_feasible = True
                    evaluations.append(evaluation)
                elif evaluation.is_upstream_feasible:
                    one_insertion_is_upstream_feasible = True
                else:
                    if one_insertion_is_upstream_feasible:
                        insertion_step_index = sequence.nb_steps
                insertion_step_index += 1
        return evaluations

    @staticmethod
    def find_best_feasible_insertion_between_consecutive_activities_for_each_task(
            sequence: "SequenceForHeuristics", tasks: list[Task]) -> list[InsertionEvaluation]:
        """
        Find, for each of the given tasks, the best feasible insertion (if any) of this task between two
        consecutive activities of the given sequence.

        Args:
            sequence: The sequence a task would be inserted in.
            tasks: The candidate tasks that would be inserted.

        Returns:
            A list of the feasible best-insertion evaluations found, one per feasible task.
        """
        evaluations = []
        for task in tasks:
            evaluation = Evaluator.find_best_insertion_between_consecutive_activities(sequence, task)
            if evaluation.is_feasible:
                evaluations.append(evaluation)
        return evaluations

    ##########################
    # Sequence - Replacement #
    ##########################

    @staticmethod
    def evaluate_replacing_task_with_another(
            sequence: "SequenceForHeuristics", replaced_task: Task, replacing_task: Task,
            compute_times_only_if_skill_constraints_satisfied: bool = True
    ):
        """
        Evaluate the feasibility of replacing the given replaced task by the given replacing task, in the
        given sequence.

        Assumptions (only checked in debug):

        - 1. the given replaced task must be in the given sequence;
        - 2. the given replacing task must not be already in the given sequence;
        - 3. the times of the given sequence are consistent.

        Args:
            sequence: The sequence in which the replaced task would be replaced.
            replaced_task: The task that would be replaced.
            replacing_task: The task that would replace the replaced task.
            compute_times_only_if_skill_constraints_satisfied: Whether start times should still be computed
              if the skill constraints are not satisfied.

        Returns:
            The replacement evaluation.
        """
        # Check the assumptions
        assert replaced_task in sequence.get_contained_tasks(), \
            f"The given replaced_task task {replaced_task.name} is not in this sequence"
        assert replacing_task not in sequence.get_contained_tasks(), \
            f"The given replacing_task task {replacing_task.name} is already in this sequence"
        assert sequence.is_time_consistent, "The times are not consistent"

        # Evaluate skill-wise feasibility
        is_skill_feasible = sequence.employee.is_capable_of_performing(replacing_task)
        if compute_times_only_if_skill_constraints_satisfied and not is_skill_feasible:
            evaluation = ReplacementEvaluation()
            evaluation.is_feasible = False
            evaluation.is_skill_feasible = False
            evaluation.employee = sequence.employee
            evaluation.replaced_task = replaced_task
            evaluation.replacing_task = replacing_task
            return evaluation

        # Evaluate time-wise

        # Get the step before and after the hypothetical insertion
        replacement_step_index = sequence.get_step_index_of(replaced_task)
        step_before = sequence[replacement_step_index - 1]
        step_after = sequence[replacement_step_index + 1]

        # Compute the earliest time at which the employee can start performing the entering task,
        # so that the times of the upstream portion of his/her sequence before the insertion are consistent,
        # and the latest time at which he/she can start performing the entering task,
        # so that the times of the downstream portion of his/her sequence after the insertion are consistent
        traveling_duration_from_step_before_insertion_to_entering_task = \
            sequence.instance.compute_traveling_duration(step_before.activity, replacing_task)
        earliest_start_time_of_entering_task = cast(int, max(
            replacing_task.start_time_lb,
            step_before.start_time - step_before.bts + step_before.activity.duration +
            traveling_duration_from_step_before_insertion_to_entering_task
        ))
        traveling_duration_from_entering_task_to_step_after_insertion = \
            sequence.instance.compute_traveling_duration(replacing_task, step_after.activity)
        latest_start_time_of_entering_task = cast(int, min(
            replacing_task.end_time_ub,
            step_after.start_time + step_after.fts -
            traveling_duration_from_entering_task_to_step_after_insertion
        )) - replacing_task.duration
        traveling_duration_detour = (
                traveling_duration_from_step_before_insertion_to_entering_task +
                traveling_duration_from_entering_task_to_step_after_insertion -
                sequence.instance.compute_traveling_duration(step_before.activity, replaced_task) -
                sequence.instance.compute_traveling_duration(replaced_task, step_after.activity)
        )

        # Compute two booleans indicating whether the entering task can be inserted while guaranteeing
        # the consistency of the times of respectively the upstream and the downstream portions of the sequence
        upstream_portion_is_feasible = (earliest_start_time_of_entering_task + replacing_task.duration <=
                                        replacing_task.end_time_ub)
        downstream_portion_is_feasible = (latest_start_time_of_entering_task >= replacing_task.start_time_lb)
        late = max(earliest_start_time_of_entering_task - latest_start_time_of_entering_task, 0)
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
        evaluation = ReplacementEvaluation()
        evaluation.is_feasible = is_time_feasible and is_skill_feasible
        evaluation.is_skill_feasible = is_skill_feasible
        evaluation.is_time_feasible = is_time_feasible
        evaluation.is_upstream_feasible = upstream_portion_is_feasible
        evaluation.is_downstream_feasible = downstream_portion_is_feasible
        evaluation.start_time = start_time
        evaluation.earliest_start_time_for_upstream = start_time_for_upstream
        evaluation.latest_start_time_for_downstream = start_time_for_downstream
        evaluation.travel_time_increase = traveling_duration_detour
        evaluation.late = late
        evaluation.replacement_step_index = replacement_step_index
        evaluation.replaced_task = replaced_task
        evaluation.replacing_task = replacing_task
        evaluation.employee = sequence.employee
        return evaluation

    @staticmethod
    def find_best_task_to_be_replaced_with_given_task(
            sequence: "SequenceForHeuristics", task: Task,
            compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Find the best task of the given sequence to be replaced by the given replacing task: see
        ReplacementEvaluation.is_better_than for the exact ranking criteria used to decide which
        candidate replacement is kept.

        Args:
            sequence: The sequence in which a task would be replaced.
            task: The task that would replace a task already in the sequence.
            compute_times_only_if_skill_constraints_satisfied: Whether start times should still be computed
              if the skill constraints are not satisfied.

        Returns:
            The evaluation of the best replacement found.
        """
        # Evaluate skill-wise feasibility
        swap_is_skill_feasible = sequence.employee.is_capable_of_performing(task)
        if compute_times_only_if_skill_constraints_satisfied and not swap_is_skill_feasible:
            evaluation = ReplacementEvaluation()
            evaluation.is_feasible = False
            evaluation.is_skill_feasible = False
            evaluation.employee = sequence.employee
            evaluation.replacing_task = task
            return evaluation
        # Evaluate all step index for swap starting from index 1
        evaluated_step_index = 1
        best_evaluation = None
        while evaluated_step_index <= sequence.nb_steps - 2:
            replaced_task = sequence.get_step(evaluated_step_index).activity
            evaluation = Evaluator.evaluate_replacing_task_with_another(sequence, replaced_task, task, False)
            if best_evaluation is None or evaluation.is_better_than(best_evaluation):
                best_evaluation = evaluation
            if best_evaluation.is_upstream_feasible and not evaluation.is_upstream_feasible:
                evaluated_step_index = sequence.nb_steps
            else:
                evaluated_step_index += 1
        return best_evaluation

    @staticmethod
    def find_best_replacement_among_various_replacing_tasks(
            sequence: "SequenceForHeuristics", tasks: list[Task],
            compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Among the given replacing tasks, find the best replacement of a task already in the given sequence.

        Args:
            sequence: The sequence in which a task would be replaced.
            tasks: The candidate tasks that would replace a task already in the sequence.
            compute_times_only_if_skill_constraints_satisfied: Whether start times should still be computed
              if the skill constraints are not satisfied.

        Returns:
            The evaluation of the best replacement found.
        """
        best_evaluation = cast(
            ReplacementEvaluation,
            Evaluator.find_best_task_to_be_replaced_with_given_task(
                sequence, tasks[0], compute_times_only_if_skill_constraints_satisfied
            )
        )
        for task in tasks[1:]:
            evaluation = cast(
                ReplacementEvaluation,
                Evaluator.find_best_task_to_be_replaced_with_given_task(
                    sequence, task, compute_times_only_if_skill_constraints_satisfied
                )
            )
            if evaluation.is_better_replacement_than(best_evaluation):
                best_evaluation = evaluation
        return best_evaluation

    @staticmethod
    def find_feasible_replacements_of_task_given_various_replacing_tasks(
            sequence: "SequenceForHeuristics", replaced_task: Task,
            replacing_tasks: list[Task]) -> list[ReplacementEvaluation]:
        """
        Find all feasible replacements of the given replaced task by one of the given replacing tasks,
        in the given sequence.

        Args:
            sequence: The sequence in which the replaced task would be replaced.
            replaced_task: The task that would be replaced.
            replacing_tasks: The candidate tasks that would replace the replaced task.

        Returns:
            A list of the feasible replacement evaluations found, one per feasible replacing task.
        """
        evaluations = []
        for replacing_task in replacing_tasks:
            evaluation = Evaluator.evaluate_replacing_task_with_another(sequence, replaced_task, replacing_task)
            if evaluation.is_feasible:
                evaluations.append(evaluation)
        return evaluations

    @staticmethod
    def find_best_feasible_replacement_for_each_replacing_task(
            sequence: "SequenceForHeuristics", replacing_tasks: list[Task]) -> list[ReplacementEvaluation]:
        """
        Find, for each of the given replacing tasks, the best feasible replacement (if any) of any task
        already in the given sequence by this replacing task.

        Args:
            sequence: The sequence in which a task would be replaced.
            replacing_tasks: The candidate tasks that would replace a task already in the sequence.

        Returns:
            A list of the feasible best-replacement evaluations found, one per feasible replacing task.
        """
        evaluations = []
        for replacing_task in replacing_tasks:
            evaluation = Evaluator.find_best_task_to_be_replaced_with_given_task(sequence, replacing_task)
            if evaluation.is_feasible:
                evaluations.append(evaluation)
        return evaluations

    ######################
    # Sequence - Reorder #
    ######################

    @staticmethod
    def evaluate_moving_after_a_task(sequence: "SequenceForHeuristics", moving_task: Task, fixed_task: Task):
        """
        Evaluate the feasibility of moving the given moving task after the fixed task in the given sequence.

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given sequence;
        - 2. the given fixed task must be in the given sequence;
        - 3. the given moving task must be before the given fixed task in the given sequence;
        - 4. the times of the given sequence are consistent.

        Args:
            sequence: The sequence the moving task would be moved in.
            moving_task: The task which would move.
            fixed_task: The task after which the moving task would be moved.

        Returns:
            The reordering evaluation.
        """
        # Check the assumptions
        assert moving_task in sequence.get_contained_tasks(), \
            f"The given moving task {moving_task.name} is not in this sequence"
        assert fixed_task in sequence.get_contained_tasks(), \
            f"The given leaving task {fixed_task.name} is not in this sequence"
        assert sequence.get_step_index_of(moving_task) < sequence.get_step_index_of(fixed_task), \
            f"The given moving task {moving_task.name} is not before the given fixed task {fixed_task.name} "
        assert sequence.is_time_consistent, "The times are not consistent"
        # Evaluate
        sequence_copy = sequence.copy()
        moving_task_index = sequence_copy.get_step_index_of(moving_task)
        sequence_travel_time_before_removing = sequence_copy.total_traveling_duration
        sequence_copy.remove_step(moving_task_index)
        sequence_travel_time_after_removing = sequence_copy.total_traveling_duration
        sequence_travel_time_decrease_due_to_removal = \
            sequence_travel_time_before_removing - sequence_travel_time_after_removing
        fixed_task_index = sequence_copy.get_step_index_of(fixed_task)
        insertion_evaluation = Evaluator.evaluate_insertion_at(sequence_copy, moving_task, fixed_task_index + 1)
        evaluation = ReorderEvaluation.from_evaluation(insertion_evaluation)
        evaluation.moving_task = moving_task
        evaluation.activity_before = fixed_task
        evaluation.activity_after = sequence_copy.get_step(fixed_task_index + 1).activity
        evaluation.travel_time_increase -= sequence_travel_time_decrease_due_to_removal
        return evaluation

    @staticmethod
    def evaluate_moving_before_a_task(sequence: "SequenceForHeuristics", moving_task: Task, fixed_task: Task):
        """
        Evaluate the feasibility of moving the given moving task before the fixed task in the given sequence.

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given sequence;
        - 2. the given fixed task must be in the given sequence;
        - 3. the given moving task must be before the given fixed task in the given sequence;
        - 4. the times of the given sequence are consistent.

        Args:
            sequence: The sequence the moving task would be moved in.
            moving_task: The task which would move.
            fixed_task: The task before which the moving task would be moved.

        Returns:
            The reordering evaluation.
        """
        # Check the assumptions
        assert moving_task in sequence.get_contained_tasks(), \
            f"The given moving task {moving_task.name} is not in this sequence"
        assert fixed_task in sequence.get_contained_tasks(), \
            f"The given leaving task {fixed_task.name} is not in this sequence"
        assert sequence.get_step_index_of(moving_task) > sequence.get_step_index_of(fixed_task), \
            f"The given moving task {moving_task.name} is not after the given fixed task {fixed_task.name} "
        assert sequence.is_time_consistent, "The times are not consistent"
        # Evaluate
        sequence_copy = sequence.copy()
        moving_task_index = sequence_copy.get_step_index_of(moving_task)
        sequence_travel_time_before_removing = sequence_copy.total_traveling_duration
        sequence_copy.remove_step(moving_task_index)
        sequence_travel_time_after_removing = sequence_copy.total_traveling_duration
        sequence_travel_time_decrease_due_to_removal = \
            sequence_travel_time_before_removing - sequence_travel_time_after_removing
        fixed_task_index = sequence_copy.get_step_index_of(fixed_task)
        insertion_evaluation = Evaluator.evaluate_insertion_at(sequence_copy, moving_task, fixed_task_index)
        evaluation = ReorderEvaluation.from_evaluation(insertion_evaluation)
        evaluation.moving_task = moving_task
        evaluation.activity_before = sequence_copy.get_step(fixed_task_index - 1).activity
        evaluation.activity_after = fixed_task
        evaluation.travel_time_increase -= sequence_travel_time_decrease_due_to_removal
        return evaluation

    @staticmethod
    def find_best_reorder_to_perform_task_later(sequence: "SequenceForHeuristics", moving_task: Task):
        """
        Find the best reorder such that the given task is performed at a later step.

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given sequence;
        - 2. the given moving task must not be the last task in the given sequence;
        - 3. the times of the given sequence are consistent.

        Args:
            sequence: The sequence the moving task would be moved in.
            moving_task: The task which would move.

        Returns:
            The reordering evaluation.
        """
        step_index = sequence.get_step_index_of(moving_task)
        last_task_step_index = cast(int, sequence.get_last_task_step_index())
        # Check the assumptions
        assert step_index < last_task_step_index, \
            f"The given moving task {moving_task.name} is the last task in this sequence"
        # Find the best shift to later
        best_evaluation = None
        for step in sequence.get_steps(step_index + 1, last_task_step_index + 1):
            task = step.activity
            evaluation = Evaluator.evaluate_moving_after_a_task(sequence, moving_task, task)
            if not best_evaluation or evaluation.is_better_than(best_evaluation):
                best_evaluation = evaluation
        return best_evaluation

    @staticmethod
    def find_best_reorder_to_perform_task_earlier(sequence: "SequenceForHeuristics", moving_task: Task):
        """
        Find the best reorder such that the given task is performed at an earlier step.

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given sequence;
        - 2. the given moving task must not be the first task in the given sequence;
        - 3. the times of the given sequence are consistent.

        Args:
            sequence: The sequence the moving task would be moved in.
            moving_task: The task which would move.

        Returns:
            The reordering evaluation.
        """
        step_index = sequence.get_step_index_of(moving_task)
        first_task_step_index = cast(int, sequence.get_first_task_step_index())
        # Check the assumptions
        assert step_index > first_task_step_index, \
            f"The given moving task {moving_task.name} is the first task in this sequence"
        # Find the best shift to earlier
        best_evaluation = None
        for step in sequence.get_steps(first_task_step_index, step_index):
            task = step.activity
            evaluation = Evaluator.evaluate_moving_before_a_task(sequence, moving_task, task)
            if not best_evaluation or evaluation.is_better_than(best_evaluation):
                best_evaluation = evaluation
        return best_evaluation

    @staticmethod
    def find_best_task_reorder(sequence: "SequenceForHeuristics", moving_task: Task):
        """
        Find the best reorder such that the given task is performed at a later or earlier step.

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given sequence;
        - 2. the given moving task must not be the first or last task in the given sequence;
        - 3. the times of the given sequence are consistent.

        Args:
            sequence: The sequence the moving task would be moved in.
            moving_task: The task which would move.

        Returns:
            The reordering evaluation.
        """
        if sequence.get_step_index_of(moving_task) == sequence.get_first_task_step_index():
            return Evaluator.find_best_reorder_to_perform_task_later(sequence, moving_task)
        elif sequence.get_step_index_of(moving_task) == sequence.get_last_task_step_index():
            return Evaluator.find_best_reorder_to_perform_task_earlier(sequence, moving_task)
        else:
            evaluation_later = cast(
                ReorderEvaluation,
                Evaluator.find_best_reorder_to_perform_task_later(sequence, moving_task)
            )
            evaluation_earlier = cast(
                ReorderEvaluation,
                Evaluator.find_best_reorder_to_perform_task_earlier(sequence, moving_task)
            )
            if evaluation_later.is_better_than(evaluation_earlier):
                return evaluation_later
            else:
                return evaluation_earlier

    @staticmethod
    def find_feasible_reorders_to_perform_task_later(
            sequence: "SequenceForHeuristics", moving_task: Task) -> list[ReorderEvaluation]:
        """
        Find the feasible reorders such that the given task is performed at a later step.

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given sequence;
        - 2. the times of the given sequence are consistent.

        Args:
            sequence: The sequence the moving task would be moved in.
            moving_task: The task which would move.

        Returns:
            The reordering evaluations found.
        """
        step_index = sequence.get_step_index_of(moving_task)
        last_task_step_index = cast(int, sequence.get_last_task_step_index())
        evaluations = []
        for step in sequence.get_steps(step_index + 1, last_task_step_index + 1):
            task = step.activity
            evaluation = Evaluator.evaluate_moving_after_a_task(sequence, moving_task, task)
            if evaluation.is_feasible:
                evaluations.append(evaluation)
        return evaluations

    @staticmethod
    def find_feasible_reorders_to_perform_task_earlier(
            sequence: "SequenceForHeuristics", moving_task: Task) -> list[ReorderEvaluation]:
        """
        Find the feasible reorders such that the given task is performed at an earlier step.

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given sequence;
        - 2. the times of the given sequence are consistent.

        Args:
            sequence: The sequence the moving task would be moved in.
            moving_task: The task which would move.

        Returns:
            The reordering evaluations found.
        """
        step_index = sequence.get_step_index_of(moving_task)
        first_task_step_index = cast(int, sequence.get_first_task_step_index())
        evaluations = []
        for step in sequence.get_steps(first_task_step_index, step_index):
            task = step.activity
            evaluation = Evaluator.evaluate_moving_before_a_task(sequence, moving_task, task)
            if evaluation.is_feasible:
                evaluations.append(evaluation)
        return evaluations

    @staticmethod
    def find_task_feasible_reorders(
            sequence: "SequenceForHeuristics", moving_task: Task) -> list[ReorderEvaluation]:
        """
        Find the feasible reorders such that the given task is performed at a later or earlier step.

        Assumptions (only checked in debug):

        - 1. the given moving task must be in the given sequence;
        - 2. the given moving task must not be the first or last task in the given sequence;
        - 3. the times of the given sequence are consistent.

        Args:
            sequence: The sequence the moving task would be moved in.
            moving_task: The task which would move.

        Returns:
            The reordering evaluations found.
        """
        evaluations_later = Evaluator.find_feasible_reorders_to_perform_task_later(sequence, moving_task)
        evaluations_earlier = Evaluator.find_feasible_reorders_to_perform_task_earlier(sequence, moving_task)
        return evaluations_later + evaluations_earlier

    ########################
    # Solution - Insertion #
    ########################

    @staticmethod
    def find_best_insertion_between_consecutive_activities_among_sets(
            solution: "SolutionForHeuristics", tasks: list[Task], employees: list[Employee],
            compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Among all given employees and all given tasks, find the best insertion of a task in an employee's
        sequence, that is to say:

        - if there is any feasible insertion,
          the best insertion is the feasible one that engenders the smallest additional traveling duration;
        - if there are no feasible insertions,
          the best insertion is the infeasible one that is the closest to be feasible duration-wise.

        Assumptions (only checked in debug):
        The times of each candidate employee's sequence are consistent.

        Args:
            solution: The solution whose employees' sequences are searched.
            tasks: The candidate tasks that would be inserted.
            employees: The candidate employees whose sequence would be changed.
            compute_times_only_if_skill_constraints_satisfied: Whether start times should still be computed
              if the skill constraints are not satisfied.

        Returns:
            The evaluation of the best insertion found.
        """
        sequence = solution.get_sequence(employees[0])
        best_insertion_evaluation = Evaluator.find_best_insertion_between_consecutive_activities_among_tasks_set(
            sequence, tasks, compute_times_only_if_skill_constraints_satisfied
        )
        for employee in employees[1:]:
            sequence = solution.get_sequence(employee)
            evaluation = Evaluator.find_best_insertion_between_consecutive_activities_among_tasks_set(
                sequence, tasks, compute_times_only_if_skill_constraints_satisfied
            )
            if evaluation.is_better_insertion_than(best_insertion_evaluation):
                best_insertion_evaluation = evaluation
        return best_insertion_evaluation

    @staticmethod
    def find_best_feasible_insertion_between_consecutive_activities_for_each_employee(
            solution: "SolutionForHeuristics", task: Task, employees: list[Employee]
    ) -> list[InsertionEvaluation]:
        """
        Find, for each of the given employees, the best feasible insertion (if any) of the given task
        between two consecutive activities performed by this employee.

        Args:
            solution: The solution whose employees' sequences are searched.
            task: The task that would be inserted.
            employees: The candidate employees whose sequence would be changed.

        Returns:
            A list of the feasible best-insertion evaluations found, one per feasible employee.
        """
        evaluations = []
        for employee in employees:
            evaluation = Evaluator.find_best_insertion_between_consecutive_activities(
                solution.get_sequence(employee), task)
            if evaluation.is_feasible:
                evaluations.append(evaluation)
        return evaluations

    ##########################
    # Solution - Replacement #
    ##########################

    # TODO could be factorized with insertion among sets
    @staticmethod
    def find_best_replacement_among_sets(
            solution: "SolutionForHeuristics", employees: list[Employee], tasks: list[Task],
            compute_times_only_if_skill_constraints_satisfied: bool = True):
        """
        Among all given employees, find the best replacement of one of their currently performed tasks by
        one of the given tasks.

        Args:
            solution: The solution whose employees' sequences are searched.
            employees: The candidate employees whose sequence would be changed.
            tasks: The candidate tasks that would replace a task already performed by one of the employees.
            compute_times_only_if_skill_constraints_satisfied: Whether start times should still be computed
              if the skill constraints are not satisfied.

        Returns:
            The evaluation of the best replacement found.
        """
        sequence = solution.get_sequence(employees[0])
        best_swap_evaluation = Evaluator.find_best_replacement_among_various_replacing_tasks(
            sequence, tasks, compute_times_only_if_skill_constraints_satisfied
        )
        for employee in employees[1:]:
            sequence = solution.get_sequence(employee)
            evaluation = Evaluator.find_best_replacement_among_various_replacing_tasks(
                sequence, tasks, compute_times_only_if_skill_constraints_satisfied
            )
            if evaluation.is_better_replacement_than(best_swap_evaluation):
                best_swap_evaluation = evaluation
        return best_swap_evaluation

    #######################
    # Solution - Reassign #
    #######################

    @staticmethod
    def evaluate_reassigning_task_after_activity(solution: "SolutionForHeuristics", stolen_employee: Employee,
                                                moving_task: Task, stealing_employee: Employee, activity: Activity):
        """
        Evaluate the feasibility of moving the given moving task from the given stolen employee's sequence
        to the given stealing employee's sequence, after the given activity.

        Args:
            solution: The solution whose employees' sequences are involved in the reassignment.
            stolen_employee: The employee who currently performs the moving task.
            moving_task: The task that would be moved.
            stealing_employee: The employee who would perform the moving task instead.
            activity: The activity, in the stealing employee's sequence, after which the moving task
              would be inserted.

        Returns:
            The reassigning evaluation.
        """
        # Compute the travel time decrease due to removing the moving task from the stolen employee
        stolen_sequence_copy = solution.get_sequence(stolen_employee).copy()
        sequence_travel_time_before_removing = stolen_sequence_copy.total_traveling_duration
        moving_task_index = stolen_sequence_copy.get_step_index_of(moving_task)
        stolen_sequence_copy.remove_step(moving_task_index)
        sequence_travel_time_after_removing = stolen_sequence_copy.total_traveling_duration
        sequence_travel_time_decrease_due_to_removal = \
            sequence_travel_time_before_removing - sequence_travel_time_after_removing
        # Evaluate inserting the moving task after the given activity in the stealing employee sequence
        stealing_sequence = solution.get_sequence(stealing_employee)
        insertion_step_index = stealing_sequence.get_step_index_of(activity) + 1
        insertion_evaluation = Evaluator.evaluate_insertion_at(stealing_sequence, moving_task, insertion_step_index)
        evaluation = ReassigningEvaluation.from_evaluation(insertion_evaluation)
        evaluation.moving_task = moving_task
        evaluation.stolen_employee = stolen_employee
        evaluation.stealing_employee = stealing_employee
        evaluation.activity_before_reassignment = activity
        evaluation.travel_time_increase -= sequence_travel_time_decrease_due_to_removal
        return evaluation

    @staticmethod
    def find_best_reassigning_in_employee_sequence(solution: "SolutionForHeuristics", stolen_employee: Employee,
                                                   moving_task: Task, stealing_employee: Employee):
        """
        Find the best reassigning transformation moving the given moving task from the given stolen
        employee's sequence to the given stealing employee's sequence.

        Args:
            solution: The solution whose employees' sequences are involved in the reassignment.
            stolen_employee: The employee who currently performs the moving task.
            moving_task: The task that would be moved.
            stealing_employee: The employee who would perform the moving task instead.

        Raises:
            NotImplementedError: Always; this transformation is not implemented yet.
        """
        # TODO to implement
        raise NotImplementedError

    @staticmethod
    def find_feasible_reassignments(
            solution: "SolutionForHeuristics", stolen_employee: Employee, moving_task: Task,
            stealing_employee: Employee) -> list[ReassigningEvaluation]:
        """
        Find all feasible reassigning transformations moving the given moving task from the given stolen
        employee's sequence to the given stealing employee's sequence.

        Args:
            solution: The solution whose employees' sequences are involved in the reassignment.
            stolen_employee: The employee who currently performs the moving task.
            moving_task: The task that would be moved.
            stealing_employee: The employee who would perform the moving task instead.

        Returns:
            A list of the feasible reassigning evaluations found, one per activity of the stealing
            employee's sequence after which the reassignment is feasible.
        """
        sequence = solution.get_sequence(stealing_employee)
        evaluations = []
        for step in sequence.get_steps(0, len(sequence) - 1):
            activity = step.activity
            evaluation = Evaluator.evaluate_reassigning_task_after_activity(
                solution, stolen_employee, moving_task, stealing_employee, activity)
            if evaluation.is_feasible:
                evaluations.append(evaluation)
        return evaluations
