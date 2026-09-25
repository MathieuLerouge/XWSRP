# Standard library
from typing import Callable

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.solution import EditableSolution
from src.explaining.computing.templates.common.conflict import TailoredConflictBuilder
from src.explaining.computing.templates.common.preconditions import TransformationPreconditionChecker, \
    EXCHANGING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE, INSERTING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE
from src.explaining.computing.templates.common.runner import MILPTransformationRunner
from src.explaining.computing.templates.common.description import TransformationDescriptionBuilder
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.computing.templates.counterfactual.MILP_model.transformation_with_alterations import \
    MILPModelForTransformationWithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.insertion_with_alterations import \
    MILPModelForInsertionWithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.insertion1 import \
    MILPModelForInsertion1WithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.insertion2 import \
    MILPModelForInsertion2aWithInstanceAlterations, MILPModelForInsertion2bWithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.insertion3 import \
    MILPModelForInsertion3WithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.swap_with_alterations import \
    MILPModelForSwapWithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.swap1 import MILPModelForSwap1WithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.swap2 import \
    MILPModelForSwap2aWithInstanceAlterations, MILPModelForSwap2bWithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.swap3 import MILPModelForSwap3WithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.reordering_with_alterations import \
    MILPModelForReorderingWithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.reordering1 import \
    MILPModelForReordering1aWithInstanceAlterations, MILPModelForReordering1bWithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.reordering2 import \
    MILPModelForReordering2aWithInstanceAlterations, MILPModelForReordering2bWithInstanceAlterations, \
    MILPModelForReordering2cWithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.reordering3 import \
    MILPModelForReordering3WithInstanceAlterations
from src.modeling.employee import Employee


###############################
# All kinds of transformation #
###############################

def describe_insertion(model: MILPModelForInsertionWithInstanceAlterations, employee: Employee,
                       route_description: str) -> dict[str, str]:
    """Describe the insertion the given model computed, in every language."""
    return TransformationDescriptionBuilder.for_inserting_task_in_route(
        model.task_to_insert, employee, route_description)


def describe_swap(model: MILPModelForSwapWithInstanceAlterations, employee: Employee,
                  route_description: str) -> dict[str, str]:
    """Describe the swap the given model computed, in every language."""
    return TransformationDescriptionBuilder.for_replacing_task_in_route(
        model.replaced_task, model.replacing_task, employee, route_description)


def describe_task_repositioning(model: MILPModelForReorderingWithInstanceAlterations, employee: Employee,
                                route_description: str) -> dict[str, str]:
    """Describe the repositioning of the model's moving task, in every language."""
    return TransformationDescriptionBuilder.for_repositioning_task_in_route(
        model.moving_task, employee, route_description)


def describe_reordering(model: MILPModelForReorderingWithInstanceAlterations, employee: Employee,
                        route_description: str) -> dict[str, str]:
    """
    Describe the reordering of the whole route, in every language.

    NB: The model is not read. (Ord,3) asks for another order without naming a task, so the sentence names
    none either, even though the model did pick a pivot task of its own to reorder around.
    """
    return TransformationDescriptionBuilder.for_reordering_route(employee, route_description)


def build_transformation_result_from_milp_model(
        solution: EditableSolution, model: MILPModelForTransformationWithInstanceAlterations,
        describe: Callable[[MILPModelForTransformationWithInstanceAlterations, Employee, str], dict[str, str]]
) -> TransformationResult:
    """
    Build the result of the transformation,
    from the results of the MILP model used to compute it

    :param solution: the solution to explain (EditableSolution)
    :param model: the MILP model used to compute the transformation (MILPModelForTransformationWithInstanceAlterations)
    :param describe: the function wording the transformation the model computed (Callable)
    :return: the result of the applied transformation (TransformationResult)
    """
    # Define key employee and task
    if model.pivot_task_is_new_to_employee is None:
        raise ValueError(f"Unknown MILP model type {type(model)}: it does not say whether the employee "
                         f"is being handed a task they do not already perform")
    key_employee = model.support_sequence.employee
    key_task = model.pivot_task
    # Save whether the transformation is feasible
    transformation_is_skill_feasible = (not model.pivot_task_is_new_to_employee
                                        or key_employee.is_capable_of_performing(key_task))
    transformation_is_feasible = transformation_is_skill_feasible and model.is_support_sequence_feasible
    # Build support instance and support solution
    support_solution = solution.copy(solution.name + "_support")
    support_solution.instance = model.support_instance
    support_sequence = model.support_sequence
    if model.pivot_task_is_new_to_employee and support_solution.get_task_performance_status(key_task):
        support_solution.remove_task(key_task, transformation_is_feasible, transformation_is_feasible)
    if transformation_is_feasible:
        support_sequence.compute_kpis()
    support_solution.replace_sequence_by_another(key_employee, support_sequence, transformation_is_feasible)
    # Build conflict (if any)
    step_index = support_sequence.get_step_index_of(key_task)
    conflict = None
    if not transformation_is_feasible:
        conflict = TailoredConflictBuilder.build_from_start_times(
            key_employee, key_task, support_solution.get_sequence(key_employee), step_index,
            transformation_is_skill_feasible,
            model.pivot_task_start_time_for_backward, model.pivot_task_start_time_for_forward
        )
    # Create description of applied transformation
    support_sequence_activities_names = [step.activity.name for step in support_sequence]
    description_of_support_sequence = "[" + ", ".join(support_sequence_activities_names) + "]"
    descriptions = describe(model, key_employee, description_of_support_sequence)
    return TransformationResult(support_solution, conflict, descriptions, model.support_instance_alterations)


############################
# Insertion transformation #
############################

def apply_ctf_ins_1(solution: EditableSolution, employee_name: str, task_name: str, activity_name: str,
                    instance_parameter_alteration_bounds: InstanceChanges = None,
                    solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ins,1) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} just after activity {Activity}?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :param activity_name: the name of the activity mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    activity = solution.instance.get_hypothetical_activity_by_names(activity_name, employee.name)
    sequence = solution.get_sequence(employee)
    model = MILPModelForInsertion1WithInstanceAlterations(sequence, task, activity,
                                                          instance_parameter_alteration_bounds, solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_insertion)


def apply_ctf_ins_2a(solution: EditableSolution, employee_name: str, task_name: str,
                     instance_parameter_alteration_bounds: InstanceChanges = None,
                     solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ins,2a) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task}
    between two consecutive activities of their planning?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    sequence = solution.get_sequence(employee)
    model = MILPModelForInsertion2aWithInstanceAlterations(sequence, task, instance_parameter_alteration_bounds,
                                                           solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_insertion)


def apply_ctf_ins_2b(solution: EditableSolution, employee_name: str,
                     instance_parameter_alteration_bounds: InstanceChanges = None,
                     solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ins,2b) counterfactual question:
    "How to make possible that employee {Employee} performs any non-performed task
    between two consecutive activities of their planning?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    sequence = solution.get_sequence(employee)
    performable_non_performed_tasks = TransformationPreconditionChecker.get_performable_non_performed_tasks(
        solution, employee, INSERTING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE
    )
    model = MILPModelForInsertion2bWithInstanceAlterations(sequence, performable_non_performed_tasks,
                                                           instance_parameter_alteration_bounds,
                                                           solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_insertion)


def apply_ctf_ins_3(solution: EditableSolution, employee_name: str, task_name: str,
                    instance_parameter_alteration_bounds: InstanceChanges = None,
                    solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ins,3) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} in addition to their activities?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    task = solution.instance.get_task_by_name(task_name)
    model = MILPModelForInsertion3WithInstanceAlterations(sequence, task, instance_parameter_alteration_bounds,
                                                          solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_insertion)


#######################
# Swap transformation #
#######################

def apply_ctf_swp_1(solution: EditableSolution, employee_name: str, task1_name: str, task2_name: str,
                    instance_parameter_alteration_bounds: InstanceChanges = None,
                    solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Swp,1) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task1} in place of task {Task2}?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task1_name: the name of the first task mentioned in the question (str)
    :param task2_name: the name of the second task mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    replacing_task = solution.instance.get_task_by_name(task1_name)
    replaced_task = solution.instance.get_task_by_name(task2_name)
    model = MILPModelForSwap1WithInstanceAlterations(sequence, replacing_task, replaced_task,
                                                     instance_parameter_alteration_bounds, solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_swap)


def apply_ctf_swp_2a(solution: EditableSolution, employee_name: str, task_name: str,
                     instance_parameter_alteration_bounds: InstanceChanges = None,
                     solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Swp,2a) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} in place of one of their tasks?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    replacing_task = solution.instance.get_task_by_name(task_name)
    model = MILPModelForSwap2aWithInstanceAlterations(sequence, replacing_task, instance_parameter_alteration_bounds,
                                                      solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_swap)


def apply_ctf_swp_2b(solution: EditableSolution, employee_name: str,
                     instance_parameter_alteration_bounds: InstanceChanges = None,
                     solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Swp,2b) counterfactual question:
    "How to make possible that employee {Employee} performs any non-performed task in place of one of their tasks?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    sequence = solution.get_sequence(employee)
    performable_non_performed_tasks = TransformationPreconditionChecker.get_performable_non_performed_tasks(
        solution, employee, EXCHANGING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE
    )
    model = MILPModelForSwap2bWithInstanceAlterations(sequence, performable_non_performed_tasks,
                                                      instance_parameter_alteration_bounds,
                                                      solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_swap)


def apply_ctf_swp_3(solution: EditableSolution, employee_name: str, task_name: str,
                    instance_parameter_alteration_bounds: InstanceChanges = None,
                    solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Swp,3) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} in place of one of their activities?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    replacing_task = solution.instance.get_task_by_name(task_name)
    model = MILPModelForSwap3WithInstanceAlterations(sequence, replacing_task, instance_parameter_alteration_bounds,
                                                     solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_swap)


#############################
# Reordering transformation #
#############################

def apply_ctf_ord_1a(solution: EditableSolution, employee_name: str, task1_name: str, task2_name: str,
                     instance_parameter_alteration_bounds: InstanceChanges = None,
                     solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ord,1a) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task1} later in their route,
    just after task {Task2}?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task1_name: the name of the first task mentioned in the question (str)
    :param task2_name: the name of the second task mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    moving_task = solution.instance.get_task_by_name(task1_name)
    fixed_task = solution.instance.get_task_by_name(task2_name)
    model = MILPModelForReordering1aWithInstanceAlterations(sequence, moving_task, fixed_task,
                                                            instance_parameter_alteration_bounds, solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_task_repositioning)


def apply_ctf_ord_1b(solution: EditableSolution, employee_name: str, task1_name: str, task2_name: str,
                     instance_parameter_alteration_bounds: InstanceChanges = None,
                     solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ord,1b) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task1} earlier in their route,
    just before task {Task2}?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task1_name: the name of the first task mentioned in the question (str)
    :param task2_name: the name of the second task mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    moving_task = solution.instance.get_task_by_name(task1_name)
    fixed_task = solution.instance.get_task_by_name(task2_name)
    model = MILPModelForReordering1bWithInstanceAlterations(sequence, moving_task, fixed_task,
                                                            instance_parameter_alteration_bounds, solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_task_repositioning)


def apply_ctf_ord_2a(solution: EditableSolution, employee_name: str, task_name: str,
                     instance_parameter_alteration_bounds: InstanceChanges = None,
                     solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ord,2a) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} later in their route?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    TransformationPreconditionChecker.check_sequence_is_reorderable(sequence)
    moving_task = solution.instance.get_task_by_name(task_name)
    model = MILPModelForReordering2aWithInstanceAlterations(sequence, moving_task, instance_parameter_alteration_bounds,
                                                            solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_task_repositioning)


def apply_ctf_ord_2b(solution: EditableSolution, employee_name: str, task_name: str,
                     instance_parameter_alteration_bounds: InstanceChanges = None,
                     solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ord,2b) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} earlier in their route?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    TransformationPreconditionChecker.check_sequence_is_reorderable(sequence)
    moving_task = solution.instance.get_task_by_name(task_name)
    model = MILPModelForReordering2bWithInstanceAlterations(sequence, moving_task, instance_parameter_alteration_bounds,
                                                            solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_task_repositioning)


def apply_ctf_ord_2c(solution: EditableSolution, employee_name: str, task_name: str,
                     instance_parameter_alteration_bounds: InstanceChanges = None,
                     solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ord,2c) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} at another position in their route?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    TransformationPreconditionChecker.check_sequence_is_reorderable(sequence)
    moving_task = solution.instance.get_task_by_name(task_name)
    model = MILPModelForReordering2cWithInstanceAlterations(sequence, moving_task, instance_parameter_alteration_bounds,
                                                            solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_task_repositioning)


def apply_ctf_ord_3(solution: EditableSolution, employee_name: str,
                    instance_parameter_alteration_bounds: InstanceChanges = None,
                    solving_time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ord,3) counterfactual question:
    "How to make possible that employee {Employee} performs the activities of their route in another order?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param instance_parameter_alteration_bounds: the allowed variations of instance parameters (InstanceChanges)
    :param solving_time_limit: the solving time limit in seconds (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    TransformationPreconditionChecker.check_sequence_is_reorderable(sequence)
    model = MILPModelForReordering3WithInstanceAlterations(sequence, instance_parameter_alteration_bounds,
                                                           solving_time_limit)
    MILPTransformationRunner.solve_or_raise(model)
    return build_transformation_result_from_milp_model(solution, model, describe_reordering)
