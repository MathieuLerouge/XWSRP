# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.conflict.conflict import Conflict
from src.explaining.computing.templates.common.conflict import TailoredConflictBuilder
from src.explaining.computing.templates.contrastive_and_scenario.MILP_model.category3 import MILPModelForCategory3
from src.explaining.modeling.solution import EditableSolution
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.optimization.heuristics.sequence import SequenceForHeuristics


#############################
# SupportSequenceExtraction #
#############################

class SupportSequenceExtraction:
    """
    What the three category-3 transformations read off their solved MILP model.

    Not a TransformationResult yet: the route still has to be worded into the sentence each kind of
    question calls for, which is the one thing the three do differently.
    """

    def __init__(self, support_solution: EditableSolution, conflict: Optional[Conflict],
                 route_description: str):
        """
        Return what was extracted from a solved model.

        Args:
            support_solution: The solution the transformation produced.
            conflict: The conflict standing in the transformation's way, or None when it is feasible.
            route_description: The support sequence written out as "[Start, T7, T3, Return]".
        """
        self._support_solution = support_solution
        self._conflict = conflict
        self._route_description = route_description

    @property
    def support_solution(self) -> EditableSolution:
        """The solution the transformation produced."""
        return self._support_solution

    @property
    def conflict(self) -> Optional[Conflict]:
        """The conflict standing in the transformation's way, or None when it is feasible."""
        return self._conflict

    @property
    def route_description(self) -> str:
        """The support sequence written out as "[Start, T7, T3, Return]"."""
        return self._route_description


def extract_support_sequence_and_conflict(
        solution: EditableSolution, employee: Employee, task: Task, model: MILPModelForCategory3
) -> SupportSequenceExtraction:
    """
    Extract the support solution, the conflict if any and the support sequence as a text.

    Shared by the three category-3 transformations, which differ only in the model they solve and in
    the sentence they word the resulting route into.

    Args:
        solution: The solution to transform.
        employee: The employee concerned by the transformation.
        task: The task concerned by the transformation.
        model: The solved MILP model used to compute the transformation.

    Returns:
        What the transformation produced, for its caller to word into a sentence.
    """
    # Save whether the transformation is feasible
    transformation_is_skill_feasible = employee.is_capable_of_performing(task)
    transformation_is_feasible = transformation_is_skill_feasible and (model.pivot_task_time_gap == 0)
    # Create support solution
    support_sequence = SequenceForHeuristics.from_sequence(model.solution_sequence)
    support_solution = solution.copy(solution.name + "_support")
    if support_solution.get_task_performance_status(task):
        support_solution.remove_task(task, transformation_is_feasible, transformation_is_feasible)
    if transformation_is_feasible:
        support_sequence.compute_kpis()
    support_solution.replace_sequence_by_another(employee, support_sequence, transformation_is_feasible)
    # Create conflict if any
    step_index = support_sequence.get_step_index_of(task)
    conflict = None
    if not transformation_is_feasible:
        if transformation_is_skill_feasible:
            # NB: rebinds the sequence the description below is built from, not just the one the conflict reads.
            support_sequence = support_solution.get_sequence(employee)
        conflict = TailoredConflictBuilder.build_from_start_times(
            employee, task, support_sequence, step_index, transformation_is_skill_feasible,
            model.pivot_task_start_time_for_backward, model.pivot_task_start_time_for_forward
        )
    support_sequence_activities_names = [step.activity.name for step in support_sequence]
    description_of_support_sequence = "[" + ", ".join(support_sequence_activities_names) + "]"
    return SupportSequenceExtraction(support_solution, conflict, description_of_support_sequence)
