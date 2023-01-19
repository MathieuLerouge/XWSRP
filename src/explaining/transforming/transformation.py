# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.solution import EditableSolution
from src.explaining.questioning.question import Question, CounterfactualQuestion
from src.explaining.questioning.questions_templates_bank import \
    (WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
     WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3)
from src.explaining.transforming.infeasibility import *
from src.modeling.activity import Activity
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.optimization.localsearch.sequence import SequenceLS
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY


# Local libraries under conditions
from main_configuration import GUROBI_IS_ENABLED
if GUROBI_IS_ENABLED:
    from src.explaining.transforming.category3.category3 import IPModelForCategory3
    from src.explaining.transforming.category3.insertion3 import IPModelForInsertion3
    from src.explaining.transforming.category3.swap3 import IPModelForSwap3
    from src.explaining.transforming.integerprogramming.insertion import IPModelForInsertionAlteringInput
    from src.explaining.transforming.integerprogramming.insertion1 import IPModelForIns1
    from src.explaining.transforming.integerprogramming.insertion2 import IPModelForIns2a
    from src.explaining.transforming.integerprogramming.insertion3 import IPModelForIns3


#############################################
# Contrastive and Scenario - Transformation #
#############################################


def apply_induced_transformation(solution: EditableSolution, question: Question):
    question_template_id = question.template.id
    fields_values = question.fields_values
    if question_template_id == WHY_NOT_INS_1:
        return apply_ins_1(solution, fields_values[0], fields_values[1], fields_values[2])
    elif question_template_id == WHY_NOT_INS_2A:
        return apply_ins_2a(solution, fields_values[0], fields_values[1])
    elif question_template_id == WHY_NOT_INS_2B:
        return apply_ins_2b(solution, fields_values[0])
    elif question_template_id == WHY_NOT_INS_2C:
        return apply_ins_2c(solution, fields_values[0])
    elif question_template_id == WHY_NOT_INS_3:
        return apply_ins_3(solution, fields_values[0], fields_values[1])
    elif question_template_id == WHY_NOT_SWP_1:
        return apply_swp_1(solution, fields_values[0], fields_values[1], fields_values[2])
    elif question_template_id == WHY_NOT_SWP_2A:
        return apply_swp_2a(solution, fields_values[0], fields_values[1])
    elif question_template_id == WHY_NOT_SWP_2B:
        return apply_swp_2b(solution, fields_values[0])
    elif question_template_id == WHY_NOT_SWP_2C:
        return apply_swp_2c(solution, fields_values[0])
    elif question_template_id == WHY_NOT_SWP_3:
        return apply_swp_3(solution, fields_values[0], fields_values[1])
    else:
        raise NotImplementedError(f"The transformation induced by the template {question_template_id} is not handled")


if GUROBI_IS_ENABLED:
    def create_support_solution_and_infeasibility_for_category_3(solution: EditableSolution, employee: Employee,
                                                                 task: Task, model: IPModelForCategory3):
        # Save whether or not the transformation is feasible
        transformation_is_skill_feasible = employee.is_capable_of_performing(task)
        transformation_is_feasible = transformation_is_skill_feasible and (model.pivot_task_time_gap == 0)
        # Create support solution
        support_sequence = SequenceLS.from_Sequence(model.solution_sequence)
        support_solution = solution.copy(solution.name + "_support")
        if support_solution.get_task_performance_status(task):
            support_solution.remove_task(task, transformation_is_feasible, transformation_is_feasible)
        if transformation_is_feasible:
            support_sequence.compute_KPIs()
        support_solution.replace_sequence_by_another(employee, support_sequence, transformation_is_feasible)
        # Create infeasibility if any
        step_index = support_sequence.get_step_index_of(task)
        earliest_start_time_for_upstream = model.pivot_task_start_time_for_backward
        latest_start_time_for_downstream = model.pivot_task_start_time_for_forward
        infeasibility = None
        if not transformation_is_feasible:
            if not transformation_is_skill_feasible:
                infeasibility = SkillInfeasibility(employee, task)
            else:
                sequence = support_solution.get_sequence(employee)
                upstream_critical_step_index = sequence.find_first_critical_step_index_backward_from(step_index - 1)
                downstream_critical_step_index = sequence.find_first_critical_step_index_forward_from(step_index + 1)
                upstream_feasible = earliest_start_time_for_upstream + task.duration <= task.end_time_UB
                downstream_feasible = latest_start_time_for_downstream >= task.start_time_LB
                infeasibility = TimeInfeasibility(
                    employee, task, upstream_feasible, downstream_feasible,
                    earliest_start_time_for_upstream, latest_start_time_for_downstream,
                    upstream_critical_step_index, downstream_critical_step_index
                )
        support_sequence_activities_names = [step.activity.name for step in support_sequence]
        description_of_support_sequence = "[" + ", ".join(support_sequence_activities_names) + "]"
        return support_solution, infeasibility, description_of_support_sequence


########################################
# Contrastive and Scenario - Insertion #
########################################

def create_support_solution_and_infeasibility_for_insertion(solution: EditableSolution, employee: Employee, task: Task,
                                                            activity: Activity, examination: dict):
    transformation_is_feasible = examination['is_feasible']
    support_solution = solution.copy(solution.name + "_support")
    if support_solution.get_task_performance_status(task):
        support_solution.remove_task(task, transformation_is_feasible, transformation_is_feasible)
    infeasibility = None
    if transformation_is_feasible:
        support_solution.insert_task_after_activity(task, activity, start_time=examination['start_time'])
    else:
        if not examination['is_time_feasible']:
            support_solution.insert_task_after_activity(
                task, activity, examination['start_time'],
                examination['earliest_start_time_for_upstream'], examination['latest_start_time_for_downstream'],
                False, False, (not examination['is_skill_feasible'])
            )
        else:
            support_solution.insert_task_after_activity(
                task, activity, examination['start_time'], None, None, False, False, True
            )
        if not examination['is_skill_feasible']:
            infeasibility = SkillInfeasibility(employee, task)
        else:
            sequence = support_solution.get_sequence(employee)
            index = sequence.get_step_index_of(activity) + 1
            upstream_critical_step_index = sequence.find_first_critical_step_index_backward_from(index - 1)
            downstream_critical_step_index = sequence.find_first_critical_step_index_forward_from(index + 1)
            infeasibility = TimeInfeasibility(
                employee, task, examination['is_upstream_feasible'], examination['is_downstream_feasible'],
                examination['earliest_start_time_for_upstream'], examination['latest_start_time_for_downstream'],
                upstream_critical_step_index=upstream_critical_step_index,
                downstream_critical_step_index=downstream_critical_step_index
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
    return support_solution, infeasibility, applying_transformation_text_in_various_languages


def apply_ins_1(solution: EditableSolution, employee_name: str, task_name: str, activity_name: str):
    """
    Why is the employee {Employee} not performing the task {Task} just after the activity {Activity}?"

    :param solution:
    :param employee_name:
    :param task_name:
    :param activity_name:
    :return:
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    activity = solution.instance.get_hypothetical_activity_by_names(activity_name, employee_name)
    examination = solution.examine_insertion_after(task, employee, activity, False)
    return create_support_solution_and_infeasibility_for_insertion(solution, employee, task, activity, examination)


def apply_ins_2a(solution: EditableSolution, employee_name: str, task_name: str):
    """
    Why is the employee {Employee} not performing the task {Task}
    between two consecutive activities of their planning?

    :param solution:
    :param employee_name:
    :param task_name:
    :return:
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    examination = solution.examine_best_insertion_between_consecutive_activities(task, employee, False)
    index = examination['step_index_for_insertion']
    activity = solution.get_sequence(employee).get_step(index - 1).activity
    return create_support_solution_and_infeasibility_for_insertion(solution, employee, task, activity, examination)


def apply_ins_2b(solution: EditableSolution, employee_name: str):
    """
    Why is the employee {Employee} not performing any non-performed task
    between two consecutive activities of their planning?

    :param solution:
    :param employee_name:
    :return:
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    if len(solution.non_performed_tasks) == 0:
        raise ValueError("There is no non-performed task in the solution.")
    examination = solution.examine_best_insertion_between_consecutive_activities_among_sets(
        solution.non_performed_tasks, [employee], False
    )
    task = solution.instance.get_task_by_name(examination['task_name'])
    index = examination['step_index_for_insertion']
    activity = solution.get_sequence(employee).get_step(index - 1).activity
    return create_support_solution_and_infeasibility_for_insertion(solution, employee, task, activity, examination)


def apply_ins_2c(solution: EditableSolution, task_name: str):
    """
    Why is any employee not performing the task {Task} between two consecutive activities of their planning?

    :param solution:
    :param task_name:
    :return:
    """
    task = solution.instance.get_task_by_name(task_name)
    examination = solution.examine_best_insertion_between_consecutive_activities_among_sets(
        [task], solution.instance.employees, False
    )
    employee = solution.instance.get_employee_by_name(examination['employee_name'])
    index = examination['step_index_for_insertion']
    activity = solution.get_sequence(employee).get_step(index - 1).activity
    return create_support_solution_and_infeasibility_for_insertion(solution, employee, task, activity, examination)


def apply_ins_3(solution: EditableSolution, employee_name: str, task_name: str):
    """
    Why is the employee {Employee} not performing the task {Task} in addition to their activities?

    :param solution:
    :param employee_name:
    :param task_name:
    :return:
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    sequence = solution.get_sequence(employee)
    model = IPModelForInsertion3(sequence, task)
    model.optimize(mute=True)
    support_solution, infeasibility, description_of_support_sequence = \
        create_support_solution_and_infeasibility_for_category_3(solution, employee, task, model)
    applying_transformation_text_in_various_languages = {
        LANGUAGE_ENGLISH_KEY:
            f"adding {task.name} in {employee.name}'s planning according to the following route "
            f"{description_of_support_sequence.replace('Start', 'Home').replace('Return', 'Home')}",
        LANGUAGE_FRENCH_KEY:
            f"ajoutant {task.name} dans le planning de {employee.name} selon la route suivante "
            f"{description_of_support_sequence.replace('Start', 'Domicile').replace('Return', 'Domicile')}",
    }
    return support_solution, infeasibility, applying_transformation_text_in_various_languages


###################################
# Contrastive and Scenario - Swap #
###################################

def create_support_solution_and_infeasibility_for_swap(solution: EditableSolution, employee: Employee,
                                                       task1: Task, task2: Task, examination: dict):
    transformation_is_feasible = examination['is_feasible']  # Sequence-wise
    support_solution = solution.copy(solution.name + "_support")
    infeasibility = None
    if transformation_is_feasible:
        support_solution.replace_task_by_another(task2, task1, start_time=examination['start_time'])
    else:
        if not examination['is_time_feasible']:
            support_solution.replace_task_by_another(
                task2, task1, examination['start_time'],
                examination['earliest_start_time_for_upstream'], examination['latest_start_time_for_downstream'],
                False, False, (not examination['is_skill_feasible'])
            )
        else:
            support_solution.replace_task_by_another(
                task2, task1, examination['start_time'], None, None, False, False, True
            )
        if not examination['is_skill_feasible']:
            infeasibility = SkillInfeasibility(employee, task1)
        else:
            sequence = support_solution.get_sequence(employee)
            index = sequence.get_step_index_of(task1)
            upstream_critical_step_index = sequence.find_first_critical_step_index_backward_from(index - 1)
            downstream_critical_step_index = sequence.find_first_critical_step_index_forward_from(index + 1)
            infeasibility = TimeInfeasibility(
                employee, task1, examination['is_upstream_feasible'], examination['is_downstream_feasible'],
                examination['earliest_start_time_for_upstream'], examination['latest_start_time_for_downstream'],
                upstream_critical_step_index=upstream_critical_step_index,
                downstream_critical_step_index=downstream_critical_step_index
            )
    applying_transformation_text_in_various_languages = {
        LANGUAGE_ENGLISH_KEY:
            f"replacing {task2.name} from {employee.name}'s planning by {task1.name}",
        LANGUAGE_FRENCH_KEY:
            f"remplaçant {task2.name} du planning de {employee.name} par {task1.name}"
    }
    return support_solution, infeasibility, applying_transformation_text_in_various_languages


def apply_swp_1(solution: EditableSolution, employee_name: str, task1_name: str, task2_name: str):
    """
    Why is the employee {Employee} not performing the task {Task1} in place of the task {Task2}?

    :param solution:
    :param employee_name:
    :param task1_name:
    :param task2_name:
    :return:
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task1 = solution.instance.get_task_by_name(task1_name)
    task2 = solution.instance.get_task_by_name(task2_name)
    examination = solution.examine_swap_with_a_task(employee, task1, task2, False)
    return create_support_solution_and_infeasibility_for_swap(solution, employee, task1, task2, examination)


def apply_swp_2a(solution: EditableSolution, employee_name: str, task_name: str):
    """
    Why is the employee {Employee} not performing the task {Task} in place of any of their tasks?

    :param solution:
    :param employee_name:
    :param task_name:
    :return:
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    entering_task = solution.instance.get_task_by_name(task_name)
    examination = solution.examine_swap_with_any_task(employee, entering_task, False)
    index = examination['step_index_for_swap']
    leaving_task = solution.get_sequence(employee).get_step(index).activity
    return create_support_solution_and_infeasibility_for_swap(solution, employee, entering_task, leaving_task,
                                                              examination)


def apply_swp_2b(solution: EditableSolution, employee_name: str):
    """
    Why is the employee {Employee} not performing any non-performed task one of their tasks?

    :param solution:
    :param employee_name:
    :return:
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    if len(solution.non_performed_tasks) == 0:
        raise ValueError("There is no non-performed task in the solution.")
    examination = solution.examine_swap_tasks_among_sets([employee], solution.non_performed_tasks, False)
    entering_task = solution.instance.get_task_by_name(examination['task_name'])
    index = examination['step_index_for_swap']
    leaving_task = solution.get_sequence(employee).get_step(index).activity
    return create_support_solution_and_infeasibility_for_swap(solution, employee, entering_task, leaving_task,
                                                              examination)


def apply_swp_2c(solution: EditableSolution, task_name: str):
    """
    Why is any employee is not performing the task {Task} in place of one of their tasks?

    :param solution:
    :param task_name:
    :return:
    """
    task = solution.instance.get_task_by_name(task_name)
    examination = solution.examine_swap_tasks_among_sets(solution.instance.employees, [task], False)
    employee = solution.instance.get_employee_by_name(examination['employee_name'])
    index = examination['step_index_for_swap']
    leaving_task = solution.get_sequence(employee).get_step(index).activity
    return create_support_solution_and_infeasibility_for_swap(solution, employee, task, leaving_task, examination)


def apply_swp_3(solution: EditableSolution, employee_name: str, task_name: str):
    """
    Why is the employee {Employee} not performing the task {Task} rather than any of their tasks?

    :param solution:
    :param employee_name:
    :param task_name:
    :return:
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    sequence = solution.get_sequence(employee)
    model = IPModelForSwap3(sequence, task)
    model.optimize(mute=True)
    support_solution, infeasibility, description_of_support_sequence = \
        create_support_solution_and_infeasibility_for_category_3(solution, employee, task, model)
    leaving_task = model.leaving_task
    applying_transformation_text_in_various_languages = {
        LANGUAGE_ENGLISH_KEY:
            f"replacing {leaving_task.name} by {task.name} in {employee.name}'s and applying the following route "
            f"{description_of_support_sequence.replace('Start', 'Home').replace('Return', 'Home')}",
        LANGUAGE_FRENCH_KEY:
            f"remplaçant {leaving_task.name} par {task.name} dans le planning de {employee.name} "
            f"et en appliquant la route suivante "
            f"{description_of_support_sequence.replace('Start', 'Domicile').replace('Return', 'Domicile')}"
    }
    return support_solution, infeasibility, applying_transformation_text_in_various_languages


#########################################
# Contrastive and Scenario - Reordering #
#########################################

# TODO
def create_support_solution_and_infeasibility_for_ordering(solution: EditableSolution, employee:Employee, task: Task,
                                                           examination: dict):
    return 0


# TODO
def apply_ord_1a(solution: EditableSolution, employee_name: str, task_name: str):
    """
    Why is the employee {Employee} not performing the task {Task1} in place of the task {Task2}?

    :param solution:
    :param employee_name:
    :param task_name:
    :return:
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    examination = solution.examine_order_later_a_task(employee, task, False)
    return create_support_solution_and_infeasibility_for_ordering(solution, employee, task, examination)


##################
# Counterfactual #
##################


def apply_induced_transformation_bis(solution: EditableSolution, question: CounterfactualQuestion):
    question_template_id = question.template.id
    fields_values = question.fields_values
    if question_template_id == WHY_NOT_INS_1:
        return apply_ins_1_bis(solution, fields_values[0], fields_values[1], fields_values[2], question.instance_slacks)
    elif question_template_id == WHY_NOT_INS_2A:
        return apply_ins_2a_bis(solution, fields_values[0], fields_values[1], question.instance_slacks)
    elif question_template_id == WHY_NOT_INS_3:
        return apply_ins_3_bis(solution, fields_values[0], fields_values[1], question.instance_slacks)
    else:
        raise NotImplementedError(f"The transformation induced by the template {question_template_id} is not handled "
                                  f"for counterfactual questions")


##############################
# Counterfactual - Insertion #
##############################

if GUROBI_IS_ENABLED:
    def create_support_solution_infeasibility_and_alterations(solution: EditableSolution, employee: Employee,
                                                              task: Task, model: IPModelForInsertionAlteringInput):
        # Save whether or not the transformation is feasible
        transformation_is_skill_feasible = employee.is_capable_of_performing(task)
        transformation_is_feasible = transformation_is_skill_feasible and (model.task_to_insert_time_gap == 0)
        # Create support solution
        support_solution = solution.copy(solution.name + "_support")
        support_solution.instance = model.support_instance
        support_sequence = model.support_sequence
        if support_solution.get_task_performance_status(task):
            support_solution.remove_task(task, transformation_is_feasible, transformation_is_feasible)
        if transformation_is_feasible:
            support_sequence.compute_KPIs()
        support_solution.replace_sequence_by_another(employee, support_sequence, transformation_is_feasible)
        # Create infeasibility if any
        step_index = support_sequence.get_step_index_of(task)
        earliest_start_time_for_upstream = model.task_to_insert_start_time_for_backward
        latest_start_time_for_downstream = model.task_to_insert_start_time_for_forward
        infeasibility = None
        if not transformation_is_feasible:
            print("Is this normal?")
            if not transformation_is_skill_feasible:
                infeasibility = SkillInfeasibility(employee, task)
            else:
                sequence = support_solution.get_sequence(employee)
                upstream_critical_step_index = sequence.find_first_critical_step_index_backward_from(step_index - 1)
                downstream_critical_step_index = sequence.find_first_critical_step_index_forward_from(step_index + 1)
                upstream_feasible = earliest_start_time_for_upstream + task.duration <= task.end_time_UB
                downstream_feasible = latest_start_time_for_downstream >= task.start_time_LB
                infeasibility = TimeInfeasibility(
                    employee, task, upstream_feasible, downstream_feasible,
                    earliest_start_time_for_upstream, latest_start_time_for_downstream,
                    upstream_critical_step_index, downstream_critical_step_index
                )
        # Create description of applied transformation
        support_sequence_activities_names = [step.activity.name for step in support_sequence]
        description_of_support_sequence = "[" + ", ".join(support_sequence_activities_names) + "]"
        applying_transformation_text_in_various_languages = {
            LANGUAGE_ENGLISH_KEY:
                f"adding {task.name} in {employee.name}'s planning according to the following route "
                f"{description_of_support_sequence.replace('Start', 'Home').replace('Return', 'Home')}",
            LANGUAGE_FRENCH_KEY:
                f"ajoutant {task.name} dans le planning de {employee.name} selon la route suivante "
                f"{description_of_support_sequence.replace('Start', 'Domicile').replace('Return', 'Domicile')}"
        }
        return (support_solution, infeasibility, applying_transformation_text_in_various_languages,
                model.support_instance_alterations)


def apply_ins_1_bis(solution: EditableSolution, employee_name: str, task_name: str, activity_name: str,
                    instance_slacks: InstanceChanges = None):
    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    activity = solution.instance.get_hypothetical_activity_by_names(activity_name, employee.name)
    sequence = solution.get_sequence(employee)
    model = IPModelForIns1(sequence, task, activity, instance_slacks)
    model.optimize(mute=True)
    return create_support_solution_infeasibility_and_alterations(solution, employee, task, model)


def apply_ins_2a_bis(solution: EditableSolution, employee_name: str, task_name: str,
                     instance_slacks: InstanceChanges = None):
    """
    How to make possible that the employee {Employee} performs the task {Task} between two consecutive activities of
    their planning?

    :param solution:
    :param employee_name:
    :param task_name:
    :param instance_slacks:
    :return:
    """

    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    sequence = solution.get_sequence(employee)

    # Create and run the IP model which aimed at adding a given task to a given sequence
    model = IPModelForIns2a(sequence, task, instance_slacks)
    model.optimize(mute=True)
    return create_support_solution_infeasibility_and_alterations(solution, employee, task, model)


def apply_ins_3_bis(solution: EditableSolution, employee_name: str, task_name: str,
                    instance_slacks: InstanceChanges = None):
    """
    How to make possible that the employee {Employee} performs the task {Task} in addition to their activities?

    :param solution:
    :param employee_name:
    :param task_name:
    :param instance_slacks:
    :return:
    """

    employee = solution.instance.get_employee_by_name(employee_name)
    task = solution.instance.get_task_by_name(task_name)
    sequence = solution.get_sequence(employee)

    # Create and run the IP model which aimed at adding a given task to a given sequence
    model = IPModelForIns3(sequence, task, instance_slacks)
    model.optimize(mute=True)

    return create_support_solution_infeasibility_and_alterations(solution, employee, task, model)

#########################
# Counterfactual - Swap #
#########################


# TODO


###############################
# Counterfactual - Reordering #
###############################


# TODO
