# Standard library
from typing import Callable, TypeVar

# Local libraries
from src.explaining.computing.templates.common.conflict import TailoredConflictBuilder
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.computing.templates.contrastive_and_scenario.milp.base import TransformationBaseModel
from src.explaining.modeling.solution import EditableSolution
from src.modeling.employee import Employee
from src.optimization.heuristics.sequence import SequenceForHeuristics

# Type variable for a subclass of TransformationBaseModel
SolvedMILPModel = TypeVar("SolvedMILPModel", bound=TransformationBaseModel)


def build_transformation_result_from_milp_model(
        solution: EditableSolution, model: TransformationBaseModel,
        describe: Callable[[SolvedMILPModel, Employee, str], dict[str, str]]
) -> TransformationResult:
    """
    Build the result of the transformation, from the results of the MILP model used to compute it.

    Shared by the three (*,3) transformations.
    What they do differently is the sentence they word the resulting route into,
    which is why the caller hands over the function doing that rather than this one telling the kinds apart.

    Args:
        solution: The solution to explain.
        model: The solved MILP model used to compute the transformation.
        describe: The function wording the transformation the model computed.

    Returns:
        The result of the applied transformation, which alters no instance parameter.

    Raises:
        ValueError: if the model does not say whether its pivot task is new to the employee, which is
            what decides both the skill check and whether the task's current performer gives it up.
    """
    if model.pivot_task_is_new_to_employee is None:
        raise ValueError(f"Unknown MILP model type {type(model).__name__}: it does not say whether the "
                         f"employee is being handed a task they do not already perform")
    # Define key employee and task
    employee = model.employee
    task = model.pivot_task
    # Save whether the transformation is feasible
    transformation_is_skill_feasible = (not model.pivot_task_is_new_to_employee
                                        or employee.is_capable_of_performing(task))
    transformation_is_feasible = transformation_is_skill_feasible and (model.pivot_task_time_gap == 0)
    # Build support solution
    support_sequence = SequenceForHeuristics.from_sequence(model.solution_sequence)
    support_solution = solution.copy(solution.name + "_support")
    if model.pivot_task_is_new_to_employee and support_solution.get_task_performance_status(task):
        support_solution.remove_task(task, transformation_is_feasible, transformation_is_feasible)
    if transformation_is_feasible:
        support_sequence.compute_kpis()
    support_solution.replace_sequence_by_another(employee, support_sequence, transformation_is_feasible)
    # Build conflict (if any)
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
    # Create description of applied transformation
    support_sequence_activities_names = [step.activity.name for step in support_sequence]
    description_of_support_sequence = "[" + ", ".join(support_sequence_activities_names) + "]"
    descriptions = describe(model, employee, description_of_support_sequence)
    return TransformationResult(support_solution, conflict, descriptions)
