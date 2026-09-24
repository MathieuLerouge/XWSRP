# Standard library
from typing import cast, Optional

# Local libraries
from src.explaining.computing.conflict.conflict import SkillConflict, TimeConflict
from src.explaining.computing.exceptions import UnattributableFeasibilityShortfallException
from src.explaining.computing.model import NeighborhoodModel
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import Operator, TaskInsertion, TaskRelocation
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
    Stateless collection of static methods turning a Neighborhood, and the NeighborhoodModel solved from it,
    into the Conflict the answering layer phrases explanations from, without mutating either.

    The two kinds of Conflict are read off at different points of the pipeline,
    because they are visible at different points:
     • a SkillConflict is read off the Neighborhood's own operators, before any model is built.
       NeighborhoodModel never relaxes a skill constraint,
       so a neighborhood whose every candidate pairing is skill-infeasible has no incumbent at all,
       rather than a shortfall to explain;
     • a TimeConflict is read off the solved model's feasibility shortfall.

    NB: This is the neighborhood computation pipeline's counterpart to what the tailored per-template pipeline does
    at the end of each of its transformations.
    """

    ################
    # Neighborhood #
    ################

    @staticmethod
    def _get_candidate_pairings(operator: Operator) -> list[tuple[Employee, Task]]:
        """
        Return the (employee, task) pairings the given operator leaves open for the model to choose between,
        or an empty list if it opens none.

        Only an operator that can hand a task to an employee who does not already perform it opens a pairing:
         • a TaskInsertion (any of its candidate employees may end up with any of its candidate tasks),
         • or a TaskRelocation (its destination employee may end up with its target task).
        TaskDeletion, TaskRepositioning and SequenceReordering all leave every task with whoever already performs it,
        so the given solution having been skill-feasible is enough to know they open no skill conflict.

        Args:
            operator: The operator to read the open pairings off.

        Returns:
            The open pairings, sorted by employee then task name.
        """
        if isinstance(operator, TaskInsertion):
            return sorted(
                ((employee, task)
                 for employee in operator.candidate_employees for task in operator.candidate_tasks),
                key=lambda pairing: (pairing[0].name, pairing[1].name)
            )
        if isinstance(operator, TaskRelocation):
            return [(operator.destination_employee, operator.target_task)]
        return []

    @staticmethod
    def extract_from_neighborhood(neighborhood: Neighborhood) -> Optional[SkillConflict]:
        """
        Return the SkillConflict the given neighborhood is blocked by, or None when it is not blocked by one.

        A neighborhood is blocked by a skill conflict when one of its operators opens pairings and
        every one of them is skill-infeasible.

        WIP: The first blocked operator found is the one reported,
        which is unambiguous for the neighborhood shapes handled today
        - carrying a single operator that opens pairings.

        Args:
            neighborhood: The neighborhood to read the conflict off the operators of.

        Returns:
            The SkillConflict naming the first blocked operator's first clashing pairing,
            or None if no operator is blocked.
        """
        for operator in neighborhood.operators:
            candidate_pairings = ConflictExtractor._get_candidate_pairings(operator)
            if len(candidate_pairings) > 0 and all(
                not employee.is_capable_of_performing(task) for employee, task in candidate_pairings
            ):
                conflicting_employee, conflicting_task = candidate_pairings[0]
                return SkillConflict(conflicting_employee, conflicting_task)
        return None

    #####################
    # NeighborhoodModel #
    #####################

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
        SlackTimeComputer.recompute_time_slacks(route)
        return route, conflicting_task_step_index

    @staticmethod
    def extract_from_solved_model(model: NeighborhoodModel) -> Optional[TimeConflict]:
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
        upstream_binding_step_index = SlackTimeComputer.find_bts_binding_step_index_from(
            route, step_index - 1
        )
        downstream_binding_step_index = SlackTimeComputer.find_fts_binding_step_index_from(
            route, step_index
        ) + 1
        return TimeConflict(
            conflicting_employee, conflicting_task,
            evaluation.is_upstream_feasible, evaluation.is_downstream_feasible,
            evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
            upstream_binding_step_index=upstream_binding_step_index,
            downstream_binding_step_index=downstream_binding_step_index
        )
