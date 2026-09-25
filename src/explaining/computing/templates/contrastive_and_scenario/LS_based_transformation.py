# Local libraries
from src.explaining.modeling.solution import EditableSolution
from src.explaining.computing.conflict.conflict import SkillConflict, TimeConflict
from src.explaining.computing.exceptions import ImpossibleTransformationException
from src.explaining.computing.templates.common.result import TransformationResult
from src.modeling.activity import Activity
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.optimization.heuristics.evaluation import InsertionEvaluation, ReplacementEvaluation, ReorderEvaluation
from src.optimization.heuristics.evaluator import Evaluator
from src.optimization.heuristics.slacks import SlackTimeComputer
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY


#############
# Insertion #
#############

def extract_explanation_content_for_insertion_from_evaluation(solution: EditableSolution, employee: Employee,
                                                               task: Task, activity: Activity,
                                                               evaluation: InsertionEvaluation):
    """
    Extract useful content for the explanation to build from the transformation evaluation

    :param solution: the solution to explain (EditableSolution)
    :param employee: the employee whose sequence is to be transformed (Employee)
    :param task: the task to insert (Task)
    :param activity: the activity after which the task is to be inserted (Activity)
    :param evaluation: the evaluation of the insertion (InsertionEvaluation)
    :return: the result of the applied transformation (TransformationResult)
    """
    transformation_is_feasible = evaluation.is_feasible
    support_solution = solution.copy(solution.name + "_support")
    if support_solution.get_task_performance_status(task):
        support_solution.remove_task(task, transformation_is_feasible, transformation_is_feasible)
    conflict = None
    if transformation_is_feasible:
        support_solution.insert_task_after_activity(task, activity, start_time=evaluation.start_time)
    else:
        if not evaluation.is_time_feasible:
            support_solution.insert_task_after_activity(
                task, activity, evaluation.start_time,
                evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
                False, False, (not evaluation.is_skill_feasible)
            )
        else:
            support_solution.insert_task_after_activity(
                task, activity, evaluation.start_time, None, None, False, False, True
            )
        if not evaluation.is_skill_feasible:
            conflict = SkillConflict(employee, task)
        else:
            sequence = support_solution.get_sequence(employee)
            index = sequence.get_step_index_of(activity) + 1
            upstream_binding_step_index = \
                SlackTimeComputer.find_bts_binding_step_index_from(sequence, index - 1)
            downstream_binding_step_index = \
                SlackTimeComputer.find_fts_binding_step_index_from(sequence, index + 1)
            conflict = TimeConflict(
                employee, task, evaluation.is_upstream_feasible, evaluation.is_downstream_feasible,
                evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
                upstream_binding_step_index=upstream_binding_step_index,
                downstream_binding_step_index=downstream_binding_step_index
            )
    if activity.name == "Start":
        activity_name_in_english = "Home"
        activity_name_in_french = "Domicile"
    else:
        activity_name_in_english = activity.name
        activity_name_in_french = activity.name
    applying_transformation_text_in_various_languages = {
        LANGUAGE_ENGLISH_KEY:
            f"inserting {task.name} just after {activity_name_in_english} in {employee.name}'s planning",
        LANGUAGE_FRENCH_KEY:
            f"insérant {task.name} juste après {activity_name_in_french} dans le planning de {employee.name}",
    }
    return TransformationResult(support_solution, conflict,
                                applying_transformation_text_in_various_languages)


def apply_ins_1(solution: EditableSolution, employee_name: str, task_name: str, activity_name: str):
    """
    Apply induced transformation and get explanation content for answering (Ins,1) contrastive question:
    "Why is employee {Employee} not performing task {Task} just after activity {Activity}?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :param activity_name: the name of the activity mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    activity = solution.instance.get_hypothetical_activity_by_names(activity_name, employee_name)
    evaluation = Evaluator.evaluate_insertion_after(solution.get_sequence(employee), task, activity, False)
    return extract_explanation_content_for_insertion_from_evaluation(solution, employee, task, activity, evaluation)


def apply_ins_2a(solution: EditableSolution, employee_name: str, task_name: str):
    """
    Apply induced transformation and get explanation content for answering (Ins,2a) contrastive question:
    "Why is employee {Employee} not performing task {Task} between two consecutive activities of their planning?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    evaluation = Evaluator.find_best_insertion_between_consecutive_activities(
        solution.get_sequence(employee), task, compute_times_only_if_skill_constraints_satisfied=False)
    activity = evaluation.activity_before_insertion
    return extract_explanation_content_for_insertion_from_evaluation(solution, employee, task, activity, evaluation)


def apply_ins_2b(solution: EditableSolution, employee_name: str):
    """
    Apply induced transformation and get explanation content for answering (Ins,2b) contrastive question:
    "Why is employee {Employee} not performing any non-performed task
    between two consecutive activities of their planning?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    if len(solution.non_performed_tasks) == 0:
        raise ImpossibleTransformationException("Inserting any non-performed task is impossible "
                                                "given a solution performing all the tasks")
    performable_non_performed_tasks = [task for task in solution.non_performed_tasks
                                       if employee.is_capable_of_performing(task)]
    if len(performable_non_performed_tasks) == 0:
        raise ImpossibleTransformationException("All the non-performed task are too much skilled for the employee")
    evaluation = Evaluator.find_best_insertion_between_consecutive_activities_among_sets(
        solution, performable_non_performed_tasks, [employee], False
    )
    task = evaluation.inserted_task
    activity = evaluation.activity_before_insertion
    return extract_explanation_content_for_insertion_from_evaluation(solution, employee, task, activity, evaluation)


def apply_ins_2c(solution: EditableSolution, task_name: str):
    """
    Apply induced transformation and get explanation content for answering (Ins,2c) contrastive question:
    "Why is any employee not performing task {Task} between two consecutive activities of their planning?"

    :param solution: the solution to explain (EditableSolution)
    :param task_name: the name of the task mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    task = solution.instance.get_task_by_name(task_name)
    evaluation = Evaluator.find_best_insertion_between_consecutive_activities_among_sets(
        solution, [task], solution.instance.employees, False
    )
    employee = evaluation.employee
    activity = evaluation.activity_before_insertion
    return extract_explanation_content_for_insertion_from_evaluation(solution, employee, task, activity, evaluation)


########
# Swap #
########

def extract_explanation_content_for_swap_from_evaluation(solution: EditableSolution, employee: Employee,
                                                          replacing_task: Task, leaving_task: Task,
                                                          evaluation: ReplacementEvaluation):
    """
    Extract useful content for the explanation to build from the transformation evaluation
    
    :param solution: the solution to explain (EditableSolution)
    :param employee: the employee whose sequence is to be transformed (Employee)
    :param replacing_task: the task that will replace the leaving task (Task)
    :param leaving_task: the task that will be replaced by the replacing task (Task)
    :param evaluation: the evaluation of the transformation (ReplacementEvaluation)
    :return: the result of the applied transformation (TransformationResult)
    """
    transformation_is_feasible = evaluation.is_feasible  # Sequence-wise
    support_solution = solution.copy(solution.name + "_support")
    conflict = None
    if transformation_is_feasible:
        support_solution.replace_task_by_another(leaving_task, replacing_task, evaluation.start_time)
    else:
        if not evaluation.is_time_feasible:
            support_solution.replace_task_by_another(
                leaving_task, replacing_task, evaluation.start_time,
                evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
                False, False, (not evaluation.is_skill_feasible)
            )
        else:
            support_solution.replace_task_by_another(
                leaving_task, replacing_task, evaluation.start_time, None, None, False, False, True
            )
        if not evaluation.is_skill_feasible:
            conflict = SkillConflict(employee, replacing_task)
        else:
            sequence = support_solution.get_sequence(employee)
            index = sequence.get_step_index_of(replacing_task)
            upstream_binding_step_index = \
                SlackTimeComputer.find_bts_binding_step_index_from(sequence, index - 1)
            downstream_binding_step_index = \
                SlackTimeComputer.find_fts_binding_step_index_from(sequence, index + 1)
            conflict = TimeConflict(
                employee, replacing_task, evaluation.is_upstream_feasible, evaluation.is_downstream_feasible,
                evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
                upstream_binding_step_index=upstream_binding_step_index,
                downstream_binding_step_index=downstream_binding_step_index
            )
    applying_transformation_text_in_various_languages = {
        LANGUAGE_ENGLISH_KEY:
            f"replacing {leaving_task.name} from {employee.name}'s planning by {replacing_task.name}",
        LANGUAGE_FRENCH_KEY:
            f"remplaçant {leaving_task.name} du planning de {employee.name} par {replacing_task.name}"
    }
    return TransformationResult(support_solution, conflict,
                                applying_transformation_text_in_various_languages)


def apply_swp_1(solution: EditableSolution, employee_name: str, task1_name: str, task2_name: str):
    """
    Apply induced transformation and get explanation content for answering (Swp,1) contrastive question:
    "Why is employee {Employee} not performing task {Task1} in place of task {Task2}?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task1_name: the name of the first task mentioned in the question (str)
    :param task2_name: the name of the second task mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task1 = solution.instance.get_task_by_name(task1_name)
    task2 = solution.instance.get_task_by_name(task2_name)
    evaluation = Evaluator.evaluate_replacing_task_with_another(solution.get_sequence(employee), task2, task1, False)
    return extract_explanation_content_for_swap_from_evaluation(solution, employee, task1, task2, evaluation)


def apply_swp_2a(solution: EditableSolution, employee_name: str, task_name: str):
    """
    Apply induced transformation and get explanation content for answering (Swp,2a) contrastive question:
    "Why is employee {Employee} not performing task {Task} in place of one of their tasks?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param task_name: the name of the task mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    entering_task = solution.instance.get_task_by_name(task_name)
    evaluation = Evaluator.find_best_task_to_be_replaced_with_given_task(
        solution.get_sequence(employee), entering_task, False)
    replaced_task = evaluation.replaced_task
    return extract_explanation_content_for_swap_from_evaluation(solution, employee, entering_task, replaced_task,
                                                                 evaluation)


def apply_swp_2b(solution: EditableSolution, employee_name: str):
    """
    Apply induced transformation and get explanation content for answering (Swp,2b) contrastive question:
    "Why is employee {Employee} not performing any non-performed task one of their tasks?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    if len(solution.non_performed_tasks) == 0:
        raise ImpossibleTransformationException("Exchanging a task with any non-performed task is impossible "
                                                "given a solution performing all the tasks")
    performable_non_performed_tasks = [task for task in solution.non_performed_tasks
                                       if employee.is_capable_of_performing(task)]
    if len(performable_non_performed_tasks) == 0:
        raise ImpossibleTransformationException("All the non-performed task are too much skilled for the employee")
    evaluation = Evaluator.find_best_replacement_among_sets(
        solution, [employee], performable_non_performed_tasks, False)
    replacing_task = evaluation.replacing_task
    replaced_task = evaluation.replaced_task
    return extract_explanation_content_for_swap_from_evaluation(solution, employee, replacing_task, replaced_task,
                                                                 evaluation)


def apply_swp_2c(solution: EditableSolution, task_name: str):
    """
    Apply induced transformation and get explanation content for answering (Swp,2c) contrastive question:
    "Why is any employee is not performing task {Task} in place of one of their tasks?"

    :param solution: the solution to explain (EditableSolution)
    :param task_name: the name of the task mentioned in the question (str)
    :return: the result of the applied transformation (TransformationResult)
    """
    replacing_task = solution.instance.get_task_by_name(task_name)
    evaluation = Evaluator.find_best_replacement_among_sets(
        solution, solution.performing_employees, [replacing_task], False)
    employee = evaluation.employee
    replaced_task = evaluation.replaced_task
    return extract_explanation_content_for_swap_from_evaluation(solution, employee, replacing_task, replaced_task,
                                                                 evaluation)


##############
# Reordering #
##############

def extract_explanation_content_for_reordering_from_evaluation(solution: EditableSolution, employee: Employee,
                                                                moving_task: Task, fixed_task: Task,
                                                                evaluation: ReorderEvaluation):
    """
    Extract useful content for the explanation to build from the transformation evaluation

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
            index = support_sequence.get_step_index_of(moving_task)
            upstream_binding_step_index = \
                SlackTimeComputer.find_bts_binding_step_index_from(support_sequence, index - 1)
            downstream_binding_step_index = \
                SlackTimeComputer.find_fts_binding_step_index_from(support_sequence, index + 1)
            conflict = TimeConflict(
                employee, moving_task, evaluation.is_upstream_feasible, evaluation.is_downstream_feasible,
                evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
                upstream_binding_step_index=upstream_binding_step_index,
                downstream_binding_step_index=downstream_binding_step_index
            )
        else:
            raise ValueError("The conflict should only be due to time considerations.")
    if is_moving_task_1_after_task_2:
        applying_transformation_text_in_various_languages = {
            LANGUAGE_ENGLISH_KEY:
                f"moving {moving_task.name} just after {fixed_task.name} in {employee.name}'s planning",
            LANGUAGE_FRENCH_KEY:
                f"déplaçant {moving_task.name} juste après {fixed_task.name} dans le planning de {employee.name}"
        }
    else:
        applying_transformation_text_in_various_languages = {
            LANGUAGE_ENGLISH_KEY:
                f"moving {moving_task.name} just before {fixed_task.name} in {employee.name}'s planning",
            LANGUAGE_FRENCH_KEY:
                f"déplaçant {moving_task.name} juste avant {fixed_task.name} dans le planning de {employee.name}"
        }
    return TransformationResult(support_solution, conflict,
                                applying_transformation_text_in_various_languages)


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
    return extract_explanation_content_for_reordering_from_evaluation(solution, employee, task_1, task_2, evaluation)


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
    return extract_explanation_content_for_reordering_from_evaluation(solution, employee, task_1, task_2, evaluation)


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
    return extract_explanation_content_for_reordering_from_evaluation(solution, employee, moving_task, fixed_task,
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
    return extract_explanation_content_for_reordering_from_evaluation(solution, employee, moving_task, fixed_task,
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
    return extract_explanation_content_for_reordering_from_evaluation(solution, employee, moving_task, fixed_task,
                                                                       evaluation)
