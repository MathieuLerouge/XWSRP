# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.solution import EditableSolution
from src.explaining.computing.templates.common.preconditions import TransformationPreconditionChecker, \
    EXCHANGING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE
from src.explaining.computing.templates.common.runner import MILPTransformationRunner
from src.explaining.computing.templates.counterfactual.extraction import build_transformation_result_from_milp_model
from src.explaining.computing.templates.common.description import TransformationDescriptionBuilder
from src.explaining.computing.templates.common.result import TransformationResult
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
