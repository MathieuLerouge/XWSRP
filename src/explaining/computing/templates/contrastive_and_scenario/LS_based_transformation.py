# Local libraries
from src.explaining.modeling.solution import EditableSolution
from src.explaining.computing.templates.common.conflict import TailoredConflictBuilder
from src.explaining.computing.templates.common.description import TransformationDescriptionBuilder
from src.explaining.computing.templates.common.result import TransformationResult
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.optimization.heuristics.evaluation import ReorderEvaluation
from src.optimization.heuristics.evaluator import Evaluator


##############
# Reordering #
##############

def build_transformation_result_for_reordering(solution: EditableSolution, employee: Employee,
                                               moving_task: Task, fixed_task: Task,
                                               evaluation: ReorderEvaluation):
    """
    Build the result of the transformation the given evaluation evaluated

    :param solution: the solution to explain (EditableSolution)
    :param employee: the employee whose sequence is to be transformed (Employee)
    :param moving_task: the task to be moved within the employee's sequence (Task)
    :param fixed_task: the fixed task before or after which the moving task is inserted (Task)
    :param evaluation: the evaluation of the transformation (ReorderEvaluation)
    :return: the result of the applied transformation (TransformationResult)
    """
    support_sequence = solution.get_sequence(employee)
    if support_sequence.get_step_index_of(moving_task) < support_sequence.get_step_index_of(fixed_task):
        is_moving_task_1_after_task_2 = True
    else:
        is_moving_task_1_after_task_2 = False
    transformation_is_feasible = evaluation.is_feasible
    support_solution = solution.copy(solution.name + "_support")
    conflict = None
    if transformation_is_feasible:
        if is_moving_task_1_after_task_2:
            support_solution.reposition_task_in_sequence_after_activity(moving_task, fixed_task, evaluation.start_time)
        else:
            support_solution.reposition_task_in_sequence_before_activity(moving_task, fixed_task, evaluation.start_time)
    else:
        if not evaluation.is_time_feasible:
            if is_moving_task_1_after_task_2:
                support_solution.reposition_task_in_sequence_after_activity(
                    moving_task, fixed_task, evaluation.start_time,
                    evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
                    False, False
                )
            else:
                support_solution.reposition_task_in_sequence_before_activity(
                    moving_task, fixed_task, evaluation.start_time,
                    evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
                    False, False
                )
            support_sequence = support_solution.get_sequence(employee)
            conflict = TailoredConflictBuilder.build_from_evaluation(
                employee, moving_task, support_sequence,
                support_sequence.get_step_index_of(moving_task), evaluation
            )
        else:
            raise ValueError("The conflict should only be due to time considerations.")
    if is_moving_task_1_after_task_2:
        descriptions = TransformationDescriptionBuilder.for_repositioning_after(moving_task, fixed_task, employee)
    else:
        descriptions = TransformationDescriptionBuilder.for_repositioning_before(moving_task, fixed_task, employee)
    return TransformationResult(support_solution, conflict, descriptions)


def apply_ord_1a(solution: EditableSolution, employee_name: str, task_name_1: str, task_name_2: str):
    """
    Apply induced transformation and get explanation content for answering (Ord,1a) contrastive question:
    "Why is employee {Employee} not performing task {Task1} later in their route, just after task {Task2}?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name_1: the name of the first task mentioned in the question (str)
    :param task_name_2: the name of the second task mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task_1 = solution.instance.get_task_by_name(task_name_1)
    task_2 = solution.instance.get_task_by_name(task_name_2)
    evaluation = Evaluator.evaluate_moving_after_a_task(solution.get_sequence(employee), task_1, task_2)
    return build_transformation_result_for_reordering(solution, employee, task_1, task_2, evaluation)


def apply_ord_1b(solution: EditableSolution, employee_name: str, task_name_1: str, task_name_2: str):
    """
    Apply induced transformation and get explanation content for answering (Ord,1b) contrastive question:
    "Why is employee {Employee} not performing task {Task1} earlier in their route, just before task {Task2}?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name_1: the name of the first task mentioned in the question (str)
    :param task_name_2: the name of the second task mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task_1 = solution.instance.get_task_by_name(task_name_1)
    task_2 = solution.instance.get_task_by_name(task_name_2)
    evaluation = Evaluator.evaluate_moving_before_a_task(solution.get_sequence(employee), task_1, task_2)
    return build_transformation_result_for_reordering(solution, employee, task_1, task_2, evaluation)


def apply_ord_2a(solution: EditableSolution, employee_name: str, task_name: str):
    """
    Apply induced transformation and get explanation content for answering (Ord,2a) contrastive question:
    "Why is employee {Employee} not performing task {Task} later in their route?"

    :param solution: the solution to be transformed (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    moving_task = solution.instance.get_task_by_name(task_name)
    evaluation = Evaluator.find_best_reorder_to_perform_task_later(solution.get_sequence(employee), moving_task)
    fixed_task = evaluation.activity_before
    return build_transformation_result_for_reordering(solution, employee, moving_task, fixed_task,
                                                      evaluation)


def apply_ord_2b(solution: EditableSolution, employee_name: str, task_name: str):
    """
    Apply induced transformation and get explanation content for answering (Ord,2b) contrastive question:
    "Why is employee {Employee} not performing task {Task} earlier in their route?"

    :param solution: the solution to be transformed (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    moving_task = solution.instance.get_task_by_name(task_name)
    evaluation = Evaluator.find_best_reorder_to_perform_task_earlier(solution.get_sequence(employee), moving_task)
    fixed_task = evaluation.activity_after
    return build_transformation_result_for_reordering(solution, employee, moving_task, fixed_task,
                                                      evaluation)


def apply_ord_2c(solution: EditableSolution, employee_name: str, task_name: str):
    """
    Apply induced transformation and get explanation content for answering (Ord,2c) contrastive question:
    "Why is employee {Employee} not performing task {Task} at another position in their route?"

    :param solution: the solution to be transformed (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    moving_task = solution.instance.get_task_by_name(task_name)
    evaluation = Evaluator.find_best_task_reorder(solution.get_sequence(employee), moving_task)
    sequence = solution.get_sequence(employee)
    if sequence.get_step_index_of(moving_task) < sequence.get_step_index_of(evaluation.activity_before):
        fixed_task = evaluation.activity_before
    elif sequence.get_step_index_of(moving_task) > sequence.get_step_index_of(evaluation.activity_after):
        fixed_task = evaluation.activity_after
    else:
        raise ValueError("The moving task is not moved")
    return build_transformation_result_for_reordering(solution, employee, moving_task, fixed_task,
                                                      evaluation)
