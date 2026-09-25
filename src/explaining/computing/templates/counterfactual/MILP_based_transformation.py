# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.solution import EditableSolution
from src.explaining.computing.conflict.conflict import SkillConflict, TimeConflict
from src.explaining.computing.exceptions import ImpossibleTransformationException
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY
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
from src.optimization.heuristics.slacks import SlackTimeComputer
from src.optimization.milp.solver.outcometoexceptionmapper import OutcomeToExceptionMapper


##################################################################################
# All kinds of transformation - Extraction of explanation content from MILP model #
##################################################################################

def extract_explanation_content_from_MILP_model_results(solution: EditableSolution,
                                                       model: MILPModelForTransformationWithInstanceAlterations):
    """
    Extract useful content for the explanation to build,
    from the results of the MILP model used to compute the transformation

    :param solution: the solution to explain (EditableSolution)
    :param model: the MILP model used to compute the transformation (MILPModelForTransformationWithInstanceAlterations)
    :return: a tuple containing the transformed solution (EditableSolution), the conflict (Conflict),
    the texts describing the transformation in various languages (dict) and
    the instance parameter changes (InstanceChanges)
    """
    # Define key employee and task
    key_employee = model.support_sequence.employee
    if isinstance(model, MILPModelForInsertionWithInstanceAlterations):
        key_task = model.task_to_insert
        earliest_start_time_for_upstream = model.task_to_insert_start_time_for_backward
        latest_start_time_for_downstream = model.task_to_insert_start_time_for_forward
    elif isinstance(model, MILPModelForSwapWithInstanceAlterations):
        key_task = model.replacing_task
        earliest_start_time_for_upstream = model.replacing_task_start_time_for_backward
        latest_start_time_for_downstream = model.replacing_task_start_time_for_forward
    elif isinstance(model, MILPModelForReorderingWithInstanceAlterations):
        key_task = model.moving_task
        earliest_start_time_for_upstream = model.moving_task_start_time_for_backward
        latest_start_time_for_downstream = model.moving_task_start_time_for_forward
    else:
        raise ValueError("Unknown MILP model type")
    # Save whether the transformation is feasible
    if (isinstance(model, MILPModelForInsertionWithInstanceAlterations) or
            isinstance(model, MILPModelForSwapWithInstanceAlterations)):
        transformation_is_skill_feasible = key_employee.is_capable_of_performing(key_task)
    else:
        transformation_is_skill_feasible = True
    transformation_is_feasible = transformation_is_skill_feasible and model.is_support_sequence_feasible
    # Build support instance and support solution
    support_solution = solution.copy(solution.name + "_support")
    support_solution.instance = model.support_instance
    support_sequence = model.support_sequence
    if (isinstance(model, MILPModelForInsertionWithInstanceAlterations) or
            isinstance(model, MILPModelForSwapWithInstanceAlterations)):
        if support_solution.get_task_performance_status(key_task):
            support_solution.remove_task(key_task, transformation_is_feasible, transformation_is_feasible)
    if transformation_is_feasible:
        support_sequence.compute_kpis()
    support_solution.replace_sequence_by_another(key_employee, support_sequence, transformation_is_feasible)
    # Build conflict (if any)
    step_index = support_sequence.get_step_index_of(key_task)
    conflict = None
    if not transformation_is_feasible:
        if not transformation_is_skill_feasible:
            conflict = SkillConflict(key_employee, key_task)
        else:
            sequence = support_solution.get_sequence(key_employee)
            upstream_binding_step_index = \
                SlackTimeComputer.find_bts_binding_step_index_from(sequence, step_index - 1)
            downstream_binding_step_index = \
                SlackTimeComputer.find_fts_binding_step_index_from(sequence, step_index + 1)
            upstream_feasible = earliest_start_time_for_upstream + key_task.duration <= key_task.end_time_ub
            downstream_feasible = latest_start_time_for_downstream >= key_task.start_time_lb
            conflict = TimeConflict(
                key_employee, key_task, upstream_feasible, downstream_feasible,
                earliest_start_time_for_upstream, latest_start_time_for_downstream,
                upstream_binding_step_index, downstream_binding_step_index
            )
    # Create description of applied transformation
    support_sequence_activities_names = [step.activity.name for step in support_sequence]
    description_of_support_sequence = "[" + ", ".join(support_sequence_activities_names) + "]"
    if isinstance(model, MILPModelForInsertionWithInstanceAlterations):
        applying_transformation_text_in_various_languages = {
            LANGUAGE_ENGLISH_KEY:
                f"adding {model.task_to_insert.name} in {key_employee.name}'s planning "
                f"according to the following route "
                f"{description_of_support_sequence.replace('Start', 'Home').replace('Return', 'Home')}",
            LANGUAGE_FRENCH_KEY:
                f"ajoutant {model.task_to_insert.name} dans le planning de {key_employee.name} "
                f"selon la route suivante "
                f"{description_of_support_sequence.replace('Start', 'Domicile').replace('Return', 'Domicile')}"
        }
    elif isinstance(model, MILPModelForSwapWithInstanceAlterations):
        applying_transformation_text_in_various_languages = {
            LANGUAGE_ENGLISH_KEY:
                f"replacing {model.replaced_task.name} with {model.replacing_task.name} "
                f"in {key_employee.name}'s planning according to the following route "
                f"{description_of_support_sequence.replace('Start', 'Home').replace('Return', 'Home')}",
            LANGUAGE_FRENCH_KEY:
                f"remplaçant {model.replaced_task.name} par {model.replacing_task.name} "
                f"dans le planning de {key_employee.name} selon la route suivante "
                f"{description_of_support_sequence.replace('Start', 'Domicile').replace('Return', 'Domicile')}"
        }
    elif isinstance(model, MILPModelForReorderingWithInstanceAlterations):
        applying_transformation_text_in_various_languages = {
            LANGUAGE_ENGLISH_KEY:
                f"moving {model.moving_task.name} in {key_employee.name}'s planning "
                f"according to the following route "
                f"{description_of_support_sequence.replace('Start', 'Home').replace('Return', 'Home')}",
            LANGUAGE_FRENCH_KEY:
                f"déplaçant {model.moving_task.name} dans le planning de {key_employee.name} "
                f"selon la route suivante "
                f"{description_of_support_sequence.replace('Start', 'Domicile').replace('Return', 'Domicile')}"
        }
    else:
        raise NotImplementedError(f"text not implemented for MILP model type {type(model)}")
    return (support_solution, conflict, applying_transformation_text_in_various_languages,
            model.support_instance_alterations)


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
    :return: a tuple containing the transformed solution (EditableSolution), the conflict (Conflict),
    the texts describing the transformation in various languages (dict) and
    the instance changes (InstanceChanges)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    activity = solution.instance.get_hypothetical_activity_by_names(activity_name, employee.name)
    sequence = solution.get_sequence(employee)
    model = MILPModelForInsertion1WithInstanceAlterations(sequence, task, activity,
                                                          instance_parameter_alteration_bounds, solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the transformed solution (EditableSolution), the conflict (Conflict),
    the texts describing the transformation in various languages (dict) and
    the instance changes (InstanceChanges)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    sequence = solution.get_sequence(employee)
    model = MILPModelForInsertion2aWithInstanceAlterations(sequence, task, instance_parameter_alteration_bounds,
                                                           solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the transformed solution (EditableSolution), the conflict (Conflict),
    the texts describing the transformation in various languages (dict) and
    the instance changes (InstanceChanges)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    sequence = solution.get_sequence(employee)
    if len(solution.non_performed_tasks) == 0:
        raise ImpossibleTransformationException("Inserting any non-performed task is impossible "
                                                "given a solution performing all the tasks")
    performable_non_performed_tasks = [task for task in solution.non_performed_tasks
                                       if employee.is_capable_of_performing(task)]
    if len(performable_non_performed_tasks) == 0:
        raise ImpossibleTransformationException("All the non-performed task are too much skilled for the employee")
    model = MILPModelForInsertion2bWithInstanceAlterations(sequence, performable_non_performed_tasks,
                                                           instance_parameter_alteration_bounds,
                                                         solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the transformed solution (EditableSolution), the conflict (Conflict),
    the texts describing the transformation in various languages (dict) and
    the instance changes (InstanceChanges)
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    task = solution.instance.get_task_by_name(task_name)
    model = MILPModelForInsertion3WithInstanceAlterations(sequence, task, instance_parameter_alteration_bounds,
                                                          solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the support solution (EditableSolution), the conflict if any (Conflict) and
    the text of the transformation to apply in various languages (dict(str, str))
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    replacing_task = solution.instance.get_task_by_name(task1_name)
    replaced_task = solution.instance.get_task_by_name(task2_name)
    model = MILPModelForSwap1WithInstanceAlterations(sequence, replacing_task, replaced_task,
                                                     instance_parameter_alteration_bounds, solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the support solution (EditableSolution), the conflict if any (Conflict) and
    the text of the transformation to apply in various languages (dict(str, str))
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    replacing_task = solution.instance.get_task_by_name(task_name)
    model = MILPModelForSwap2aWithInstanceAlterations(sequence, replacing_task, instance_parameter_alteration_bounds,
                                                      solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the support solution (EditableSolution), the conflict if any (Conflict) and
    the text of the transformation to apply in various languages (dict(str, str))
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    sequence = solution.get_sequence(employee)
    if len(solution.non_performed_tasks) == 0:
        raise ImpossibleTransformationException("Inserting any non-performed task is impossible "
                                                "given a solution performing all the tasks")
    performable_non_performed_tasks = [task for task in solution.non_performed_tasks
                                       if employee.is_capable_of_performing(task)]
    if len(performable_non_performed_tasks) == 0:
        raise ImpossibleTransformationException("All the non-performed task are too much skilled for the employee")
    model = MILPModelForSwap2bWithInstanceAlterations(sequence, performable_non_performed_tasks,
                                                      instance_parameter_alteration_bounds,
                                                    solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the support solution (EditableSolution), the conflict if any (Conflict) and
    the text of the transformation to apply in various languages (dict(str, str))
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    replacing_task = solution.instance.get_task_by_name(task_name)
    model = MILPModelForSwap3WithInstanceAlterations(sequence, replacing_task, instance_parameter_alteration_bounds,
                                                     solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the support solution (EditableSolution), the conflict if any (Conflict) and
    the text of the transformation to apply in various languages (dict(str, str))
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    moving_task = solution.instance.get_task_by_name(task1_name)
    fixed_task = solution.instance.get_task_by_name(task2_name)
    model = MILPModelForReordering1aWithInstanceAlterations(sequence, moving_task, fixed_task,
                                                            instance_parameter_alteration_bounds, solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the support solution (EditableSolution), the conflict if any (Conflict) and
    the text of the transformation to apply in various languages (dict(str, str))
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    moving_task = solution.instance.get_task_by_name(task1_name)
    fixed_task = solution.instance.get_task_by_name(task2_name)
    model = MILPModelForReordering1bWithInstanceAlterations(sequence, moving_task, fixed_task,
                                                            instance_parameter_alteration_bounds, solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the support solution (EditableSolution), the conflict if any (Conflict) and
    the text of the transformation to apply in various languages (dict(str, str))
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    if sequence.nb_steps <= 3:
        raise ImpossibleTransformationException("Reordering a sequence with 3 activities or fewer is impossible")
    moving_task = solution.instance.get_task_by_name(task_name)
    model = MILPModelForReordering2aWithInstanceAlterations(sequence, moving_task, instance_parameter_alteration_bounds,
                                                            solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the support solution (EditableSolution), the conflict if any (Conflict) and
    the text of the transformation to apply in various languages (dict(str, str))
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    if sequence.nb_steps <= 3:
        raise ImpossibleTransformationException("Reordering a sequence with 3 activities or fewer is impossible")
    moving_task = solution.instance.get_task_by_name(task_name)
    model = MILPModelForReordering2bWithInstanceAlterations(sequence, moving_task, instance_parameter_alteration_bounds,
                                                            solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the support solution (EditableSolution), the conflict if any (Conflict) and
    the text of the transformation to apply in various languages (dict(str, str))
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    if sequence.nb_steps <= 3:
        raise ImpossibleTransformationException("Reordering a sequence with 3 activities or fewer is impossible")
    moving_task = solution.instance.get_task_by_name(task_name)
    model = MILPModelForReordering2cWithInstanceAlterations(sequence, moving_task, instance_parameter_alteration_bounds,
                                                            solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)


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
    :return: a tuple containing the support solution (EditableSolution), the conflict if any (Conflict) and
    the text of the transformation to apply in various languages (dict(str, str))
    """
    sequence = solution.get_sequence(solution.instance.get_employee_by_name(employee_name))
    if sequence.nb_steps <= 3:
        raise ImpossibleTransformationException("Reordering a sequence with 3 activities or fewer is impossible")
    model = MILPModelForReordering3WithInstanceAlterations(sequence, instance_parameter_alteration_bounds,
                                                           solving_time_limit)
    solve_outcome = model.solve(mute=True)
    exception = OutcomeToExceptionMapper.map(solve_outcome)
    if exception is not None:
        raise exception
    return extract_explanation_content_from_MILP_model_results(solution, model)
