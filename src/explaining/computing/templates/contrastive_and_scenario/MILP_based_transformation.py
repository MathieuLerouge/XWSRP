# Local libraries
from src.explaining.modeling.solution import EditableSolution
from src.explaining.computing.templates.common.description import TransformationDescriptions
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.computing.templates.contrastive_and_scenario.MILP_model.category3 import MILPModelForCategory3
from src.explaining.computing.templates.contrastive_and_scenario.MILP_model.insertion3 import MILPModelForInsertion3
from src.explaining.computing.templates.contrastive_and_scenario.MILP_model.reordering3 import MILPModelForReordering3
from src.explaining.computing.templates.contrastive_and_scenario.MILP_model.swap3 import MILPModelForSwap3
from src.explaining.computing.conflict.conflict import SkillConflict
from src.explaining.computing.templates.common.conflict_builder import TailoredConflictBuilder
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.optimization.heuristics.sequence import SequenceForHeuristics
from src.explaining.computing.templates.common.runner import MILPTransformationRunner


###################################################################################
# All kinds of transformation - Extraction of explanation content from MILP model #
###################################################################################

def extract_support_sequence_and_conflict(solution: EditableSolution, employee: Employee,
                                          task: Task, model: MILPModelForCategory3):
    """
    Extract the support solution, the conflict if any and the support sequence as a text,
    from the results of the MILP model used to compute the transformation

    :param solution: the solution to transform (EditableSolution)
    :param employee: the employee concerned by the transformation (Employee)
    :param task: the task concerned by the transformation (Task)
    :param model: the MILP model used to compute the transformation (MILPModelForCategory3)
    :return: a tuple containing the support solution (EditableSolution), the conflict if any (Conflict) and
    the support sequence as a text (str)
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
    earliest_start_time_for_upstream = model.pivot_task_start_time_for_backward
    latest_start_time_for_downstream = model.pivot_task_start_time_for_forward
    conflict = None
    if not transformation_is_feasible:
        if transformation_is_skill_feasible:
            support_sequence = support_solution.get_sequence(employee)
        conflict = TailoredConflictBuilder.build_from_start_times(
            employee, task, support_sequence, step_index, transformation_is_skill_feasible,
            earliest_start_time_for_upstream, latest_start_time_for_downstream
        )
    support_sequence_activities_names = [step.activity.name for step in support_sequence]
    description_of_support_sequence = "[" + ", ".join(support_sequence_activities_names) + "]"
    # Return explanation content
    return support_solution, conflict, description_of_support_sequence


############################
# Insertion transformation #
############################

def apply_ins_3(solution: EditableSolution, employee_name: str, task_name: str, time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ins,3) contrastive question:
    "Why is employee {Employee} not performing task {Task} in addition to their activities?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task to be inserted mentioned in the question (str)
    :param time_limit: the time limit in seconds for the explanation computation (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    if employee.is_capable_of_performing(task):
        sequence = solution.get_sequence(employee)
        model = MILPModelForInsertion3(sequence, task)
        if time_limit is not None:
            model.solving_time_limit = time_limit
        # model.warm_start()
        MILPTransformationRunner.solve_or_raise(model)
        support_solution, conflict, description_of_support_sequence = \
            extract_support_sequence_and_conflict(solution, employee, task, model)
    else:
        support_solution = solution.copy(solution.name + "_support")
        conflict = SkillConflict(employee, task)
        description_of_support_sequence = ""
    descriptions = TransformationDescriptions.for_insertion_route(task, employee, description_of_support_sequence)
    return TransformationResult(support_solution, conflict, descriptions)


#######################
# Swap transformation #
#######################

def apply_swp_3(solution: EditableSolution, employee_name: str, task_name: str, time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Swp,3) contrastive question:
    "Why is employee {Employee} not performing task {Task} instead of any of their already-performed tasks
    (even if it means changing their order)?

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :param time_limit: the time limit in seconds for the explanation computation (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    if employee.is_capable_of_performing(task):
        sequence = solution.get_sequence(employee)
        model = MILPModelForSwap3(sequence, task)
        if time_limit is not None:
            model.solving_time_limit = time_limit
        MILPTransformationRunner.solve_or_raise(model)
        support_solution, conflict, description_of_support_sequence = \
            extract_support_sequence_and_conflict(solution, employee, task, model)
        leaving_task = model.leaving_task
        descriptions = TransformationDescriptions.for_swap_and_rerouting(
            leaving_task, task, employee, description_of_support_sequence
        )
    else:
        support_solution = solution.copy(solution.name + "_support")
        conflict = SkillConflict(employee, task)
        descriptions = TransformationDescriptions.none()
    return TransformationResult(support_solution, conflict, descriptions)


#############################
# Reordering transformation #
#############################

def apply_ord_3(solution: EditableSolution, employee_name: str, time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ord,3) contrastive question:
    "Why is employee {Employee} not performing the activities of their route in another order?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param time_limit: the time limit in seconds for computing the transformation (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    sequence = solution.get_sequence(employee)
    model = MILPModelForReordering3(sequence)
    if time_limit is not None:
        model.solving_time_limit = time_limit
    MILPTransformationRunner.solve_or_raise(model)
    pivot_task = model.pivot_task
    support_solution, conflict, description_of_support_sequence = \
        extract_support_sequence_and_conflict(solution, employee, pivot_task, model)
    descriptions = TransformationDescriptions.for_reordering_route(employee, description_of_support_sequence)
    return TransformationResult(support_solution, conflict, descriptions)
