# Standard library
from typing import cast, Optional

# Local libraries
from src.explaining.computing.conflict.conflict import TimeConflict
from src.explaining.computing.exceptions import UnattributableFeasibilityShortfallException
from src.explaining.computing.model import NeighborhoodModel
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.optimization.heuristics.evaluator import Evaluator
from src.optimization.heuristics.sequence import SequenceForHeuristics
from src.optimization.heuristics.slacks import SlackTimeComputer


#####################
# ConflictExtractor #
#####################

class ConflictExtractor:
    """
    Stateless collection of static methods turning a solved NeighborhoodModel's feasibility shortfall
    into the Conflict the answering layer phrases explanations from, without mutating the given model.

    NB: This is the neighborhood computation pipeline's counterpart to what the tailored per-template pipeline
    does at the end of each of its transformations.

    WIP: Only time conflicts are in scope. NeighborhoodModel never relaxes a skill constraint,
    so a pairing that is skill-infeasible has no incumbent at all rather than a shortfall to explain.
    """

    @staticmethod
    def _build_route_without_conflicting_task(
            model: NeighborhoodModel, conflicting_employee: Employee, conflicting_task: Task
    ) -> tuple[SequenceForHeuristics, int]:
        """
        Return the conflicting employee's solved route minus the conflicting task, as a time-consistent sequence,
        together with the step index the conflicting task would go back at.

        NB: Rebuilt activity by activity rather than copied from the model's solved sequence and trimmed.

        Args:
            model: The solved model whose route is rebuilt.
            conflicting_employee: The employee whose solved route is rebuilt.
            conflicting_task: The task to leave out of the rebuilt route.

        Returns:
            A pair made of the rebuilt route, with its time slacks up to date,
            and the step index the conflicting task occupied in the solved route.

        Raises:
            NotImplementedError: if the solved route holds anything but tasks between leaving home and coming back home
                (an employee unavailability, a lunch break), which neither this rebuild
                nor the slack machinery it feeds supports.
            UnattributableFeasibilityShortfallException: if the solved route does not pass
                through the conflicting task at all (see that exception).
        """
        route = SequenceForHeuristics(model.solution.instance, conflicting_employee)
        route.compute_kpis()
        conflicting_task_step_index = None
        with SlackTimeComputer.deferred_tightening(route):
            for activity in model.get_solved_route(conflicting_employee):
                if not isinstance(activity, Task):
                    raise NotImplementedError(
                        f"ConflictExtractor cannot rebuild {conflicting_employee.name}'s route around {activity.name}, "
                        f"which is not a task"
                    )
                elif activity == conflicting_task:
                    conflicting_task_step_index = len(route) - 1
                else:
                    route.insert_task_at(cast(Task, activity), len(route) - 1)
        if conflicting_task_step_index is None:
            raise UnattributableFeasibilityShortfallException(
                f"{conflicting_employee.name}'s solved route leaves home and comes back without passing "
                f"through {conflicting_task.name}, which is performed on a disconnected cycle of its own"
            )
        SlackTimeComputer.update_time_slacks(route)
        return route, conflicting_task_step_index

    @staticmethod
    def extract(model: NeighborhoodModel) -> Optional[TimeConflict]:
        """
        Return the TimeConflict the given solved model's feasibility shortfall stands for,
        or None when the solution it found is feasible (zero shortfall) and so needs no explaining.

        NB: The conflicting task is examined at the position the solver settled on, not the one the given solution had
        - including when a paired TaskDeletion changed who is adjacent to whom.

        Args:
            model: The solved NeighborhoodModel to explain the feasibility shortfall of.

        Returns:
            The TimeConflict describing the shortfall, or None if there is no shortfall.

        Raises:
            AttributeError: if the given model hasn't been solved yet, or found no feasible solution.
            NotImplementedError: if the conflicting employee's solved route holds anything but tasks.
            UnattributableFeasibilityShortfallException:
                if the solved arrangement is not one a single position accounts for,
                or examining it at the position solved for does not reproduce the shortfall.
        """
        feasibility_shortfall = model.feasibility_shortfall
        if feasibility_shortfall == 0:
            return None
        conflicting_employee, conflicting_task = model.conflicting_employee_and_task
        route, step_index = ConflictExtractor._build_route_without_conflicting_task(
            model, conflicting_employee, conflicting_task
        )
        evaluation = Evaluator.evaluate_insertion_at(
            route, conflicting_task, step_index, compute_times_only_if_skill_constraints_satisfied=False
        )
        if evaluation.late != feasibility_shortfall:
            raise UnattributableFeasibilityShortfallException(
                f"Examining {conflicting_task.name} at the position solved for in {conflicting_employee.name}'s "
                f"route puts it short by {evaluation.late}, not by the solved feasibility shortfall "
                f"{feasibility_shortfall}: the shortfall is paying for something other than that position"
            )
        # Both indices are reported in the tailored pipeline's numbering, that of the route *with* the
        # conflicting task back at step_index: indices below it are the same in both numberings, indices at
        # or above it are one higher there than in the route the search actually runs on.
        upstream_critical_step_index = SlackTimeComputer.find_first_critical_step_index_backward_from(
            route, step_index - 1
        )
        downstream_critical_step_index = SlackTimeComputer.find_first_critical_step_index_forward_from(
            route, step_index
        ) + 1
        return TimeConflict(
            conflicting_employee, conflicting_task,
            evaluation.is_upstream_feasible, evaluation.is_downstream_feasible,
            evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
            upstream_critical_step_index=upstream_critical_step_index,
            downstream_critical_step_index=downstream_critical_step_index
        )
