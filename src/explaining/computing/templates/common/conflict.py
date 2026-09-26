# Standard library
from typing import Optional, cast

# Local libraries
from src.explaining.computing.conflict import Conflict, SkillConflict, TimeConflict
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.optimization.heuristics.evaluation import Evaluation
from src.optimization.heuristics.sequence import SequenceForHeuristics
from src.optimization.heuristics.slacks import SlackTimeComputer


###########################
# TailoredConflictBuilder #
###########################

class TailoredConflictBuilder:
    """
    Assembles the Conflict a tailored per-template transformation ran into, out of values it already holds.

    This only puts a Conflict together: what makes the transformation infeasible, and by how much,
    has been worked out by the evaluation or the MILP model the caller ran, and is handed over as arguments.
    """

    @staticmethod
    def build(employee: Employee, task: Task, sequence: SequenceForHeuristics, step_index: int,
              is_skill_feasible: Optional[bool], is_upstream_feasible: Optional[bool],
              is_downstream_feasible: Optional[bool], earliest_start_time_for_upstream: Optional[int],
              latest_start_time_for_downstream: Optional[int]) -> Conflict:
        """
        Return the conflict standing in the way of the transformation.

        Args:
            employee: The employee whose sequence the transformation changed.
            task: The task the transformation could not fit in.
            sequence: The support sequence, holding the task at step_index.
            step_index: The index the task sits at in the support sequence.
            is_skill_feasible: Whether the employee is skilled enough for the task. None counts as not being
                skilled enough, an evaluation leaving it unset having never got as far as the time checks.
            is_upstream_feasible: Whether the sequence upstream of the task can be made time-consistent.
            is_downstream_feasible: Whether the sequence downstream of the task can be made time-consistent.
            earliest_start_time_for_upstream: The earliest the task can start for the upstream part to hold.
            latest_start_time_for_downstream: The latest the task can start for the downstream part to hold.

        Returns:
            A SkillConflict when the employee is not skilled enough for the task, a TimeConflict otherwise.
        """
        if not is_skill_feasible:
            return SkillConflict(employee, task)
        upstream_binding_step_index = SlackTimeComputer.find_bts_binding_step_index_from(sequence, step_index - 1)
        downstream_binding_step_index = SlackTimeComputer.find_fts_binding_step_index_from(sequence, step_index + 1)
        return TimeConflict(
            employee, task, cast(bool, is_upstream_feasible), cast(bool, is_downstream_feasible),
            cast(int, earliest_start_time_for_upstream), cast(int, latest_start_time_for_downstream),
            upstream_binding_step_index, downstream_binding_step_index
        )

    @staticmethod
    def build_from_evaluation(employee: Employee, task: Task, sequence: SequenceForHeuristics, step_index: int,
                              evaluation: Evaluation) -> Conflict:
        """
        Return the conflict standing in the way of the transformation the given evaluation evaluated.

        Args:
            employee: The employee whose sequence the transformation changed.
            task: The task the transformation could not fit in.
            sequence: The support sequence, holding the task at step_index.
            step_index: The index the task sits at in the support sequence.
            evaluation: The evaluation of the transformation, which the feasibility flags and the
                artificial start times are read off.

        Returns:
            A SkillConflict when the employee is not skilled enough for the task, a TimeConflict otherwise.
        """
        return TailoredConflictBuilder.build(
            employee, task, sequence, step_index, evaluation.is_skill_feasible,
            evaluation.is_upstream_feasible, evaluation.is_downstream_feasible,
            evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream
        )

    @staticmethod
    def build_from_start_times(employee: Employee, task: Task, sequence: SequenceForHeuristics, step_index: int,
                               is_skill_feasible: bool, earliest_start_time_for_upstream: Optional[int],
                               latest_start_time_for_downstream: Optional[int]) -> Conflict:
        """
        Return the conflict standing in the way of the transformation, given only the artificial start times.

        Unlike an evaluation, a MILP model reports the start times without saying which side they break, so
        both feasibility flags are worked out here by comparing them against the task's own time window.

        Args:
            employee: The employee whose sequence the transformation changed.
            task: The task the transformation could not fit in.
            sequence: The support sequence, holding the task at step_index.
            step_index: The index the task sits at in the support sequence.
            is_skill_feasible: Whether the employee is skilled enough for the task. When they are not, the
                start times are not read, so a caller may pass None for them.
            earliest_start_time_for_upstream: The earliest the task can start for the upstream part to hold.
            latest_start_time_for_downstream: The latest the task can start for the downstream part to hold.

        Returns:
            A SkillConflict when the employee is not skilled enough for the task, a TimeConflict otherwise.
        """
        if not is_skill_feasible:
            return SkillConflict(employee, task)
        earliest_start_time = cast(int, earliest_start_time_for_upstream)
        latest_start_time = cast(int, latest_start_time_for_downstream)
        return TailoredConflictBuilder.build(
            employee, task, sequence, step_index, True,
            earliest_start_time + task.duration <= task.end_time_ub,
            latest_start_time >= task.start_time_lb,
            earliest_start_time, latest_start_time
        )
