# Standard library
from typing import cast

# Local libraries
from src.explaining.computing.conflict import SkillConflict
from src.explaining.computing.neighborhood.model import NeighborhoodModel
from src.explaining.computing.templates.common.description import TransformationDescriptionBuilder
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import TaskDeletion, TaskInsertion
from src.explaining.neighborhood.templates.recognizer import filter_primitives
from src.explaining.question.question import ContrastiveQuestion
from src.explaining.question.questions_templates_bank import (
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)
from src.modeling.activity import Activity
from src.modeling.comeback import COMING_BACK_HOME_STRING
from src.modeling.departure import LEAVING_HOME_STRING
from src.modeling.employee import Employee
from src.modeling.task import Task

# The templates whose sentence spells the whole resulting route out rather than naming one position.
# They are exactly the order-free ones: with the rest of the sequence free to move,
# no single anchor would tell the reader where the task ended up.
ROUTE_SPELLING_TEMPLATES_IDS = (WHY_NOT_INS_3, WHY_NOT_SWP_3, WHY_NOT_ORD_3)


##################################
# NeighborhoodDescriptionBuilder #
##################################

class NeighborhoodDescriptionBuilder:
    """
    Stateless collection of static methods wording what a solved NeighborhoodModel did,
    in each of the languages explanations are given in.

    It is the neighborhood computation pipeline's counterpart to the sentence
    each tailored transformation builds at the end of its own run.
    The sentences themselves are not rewritten here: every one of them comes from TransformationDescriptionBuilder,
    so that both pipelines answering the same question word their answer identically.
    What this class adds is reading, off the solved model, the position or route the tailored pipeline knows
    from having applied the change itself.
    """

    @staticmethod
    def build_from_solved_model(question: ContrastiveQuestion, neighborhood: Neighborhood,
                                model: NeighborhoodModel) -> dict[str, str]:
        """
        Return the sentence describing what the solved model settled on, keyed by language.

        Args:
            question: The question the neighborhood was recognized as, whose template picks the wording.
            neighborhood: The neighborhood the model was built from.
            model: The solved model to read the settled-on arrangement off.

        Returns:
            The sentence keyed by language.

        Raises:
            NotImplementedError: if the question's template is not one of the sixteen handled.
        """
        template_id = question.template.id
        if template_id in (WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3):
            return _describe_insertion(neighborhood, model, template_id)
        if template_id in (WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3):
            return _describe_swap(neighborhood, model, template_id)
        if template_id in (WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1):
            return _describe_pinned_repositioning(question, template_id)
        if template_id in (WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2):
            return _describe_free_repositioning(question, neighborhood, model)
        if template_id == WHY_NOT_ORD_3:
            return _describe_reordering(question, model)
        raise NotImplementedError(f"No transformation description is built for template {template_id}")

    @staticmethod
    def build_for_skill_conflict(question: ContrastiveQuestion, skill_conflict: SkillConflict) -> dict[str, str]:
        """
        Return the sentence describing a transformation blocked before any model was built, keyed by language.

        A skill-blocked neighborhood never reaches the solver, so there is no arrangement to name
        - only the pairing that blocked it. The insertion families still say what was being attempted,
        with the route left empty; the others say nothing, which is what their tailored counterparts do too.

        Args:
            question: The question the neighborhood was recognized as.
            skill_conflict: The conflict blocking every pairing the neighborhood's operators opened.

        Returns:
            The sentence keyed by language.
        """
        if question.template.id in (WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3):
            return TransformationDescriptionBuilder.for_inserting_task_in_route(
                skill_conflict.conflicting_task, skill_conflict.conflicting_employee, ""
            )
        return TransformationDescriptionBuilder.none()


###########
# Helpers #
###########


def _describe_solved_route(model: NeighborhoodModel, employee: Employee) -> str:
    """
    Return the given employee's solved route as the bracketed string the route-spelling sentences take.

    The home ends are added back here: get_solved_route reports only what lies between leaving home and coming back,
    whereas the tailored pipeline builds this string off a sequence that carries both.
    Both ends are then renamed to the employee's home by TransformationDescriptionBuilder.

    Args:
        model: The solved model to read the route off.
        employee: The employee whose route is described.

    Returns:
        The route, e.g. "[Start, T7, T3, Return]".
    """
    activities_names = [activity.name for activity in model.get_solved_route(employee)]
    return "[" + ", ".join([LEAVING_HOME_STRING] + activities_names + [COMING_BACK_HOME_STRING]) + "]"


def _get_activity_before_in_solved_route(model: NeighborhoodModel, employee: Employee, task: Task,
                                         neighborhood: Neighborhood) -> Activity:
    """
    Return the activity the given task immediately follows in the employee's solved route.

    Args:
        model: The solved model to read the route off.
        employee: The employee whose route is read.
        task: The task whose predecessor is wanted.
        neighborhood: The neighborhood whose given solution the employee's departure step is read off,
            for the case of a task the solver put first.

    Returns:
        The preceding activity, or the employee's departure when the task comes first in the route.

    Raises:
        ValueError: if the solved route does not pass through the task at all.
    """
    route = model.get_solved_route(employee)
    index = _get_index_in_route(route, task, employee)
    if index == 0:
        return neighborhood.solution.get_sequence(employee)[0].activity
    return route[index - 1]


def _get_activity_after_in_solved_route(model: NeighborhoodModel, employee: Employee, task: Task) -> Activity:
    """
    Return the activity the given task is immediately followed by in the employee's solved route.

    Args:
        model: The solved model to read the route off.
        employee: The employee whose route is read.
        task: The task whose successor is wanted.

    Returns:
        The following activity.

    Raises:
        ValueError: if the solved route does not pass through the task at all,
            or if the task is the last of the route and so has no following activity to name.
    """
    route = model.get_solved_route(employee)
    index = _get_index_in_route(route, task, employee)
    if index == len(route) - 1:
        raise ValueError(f"{task.name} ends {employee.name}'s solved route, so no activity follows it")
    return route[index + 1]


def _get_index_in_route(route: list[Activity], task: Task, employee: Employee) -> int:
    """
    Return the position of the given task in the given solved route.

    Args:
        route: The solved route to look the task up in.
        task: The task to locate.
        employee: The employee whose route it is, named in the error when the task is missing.

    Returns:
        The task's index in the route.

    Raises:
        ValueError: if the route does not pass through the task at all.
    """
    for index, activity in enumerate(route):
        if activity == task:
            return index
    raise ValueError(f"{employee.name}'s solved route does not pass through {task.name}")


def _get_inserted_task_and_employee(neighborhood: Neighborhood,
                                    model: NeighborhoodModel) -> tuple[Task, Employee]:
    """
    Return the candidate task the solver inserted, and the candidate employee it handed the task to.

    Every (Ins,*) and (Swp,*) neighborhood constrains exactly one of its TaskInsertion's candidate tasks
    to end up performed by one of its candidate employees, which is what makes the pair well-defined,
    even for the templates offering a whole set of either.

    Args:
        neighborhood: The neighborhood the model was built from.
        model: The solved model to read the arrangement off.

    Returns:
        A pair made of the inserted task and the employee performing it.

    Raises:
        ValueError: if the neighborhood carries no TaskInsertion, or if the solved solution leaves none of
            its candidate tasks with one of its candidate employees.
    """
    insertions = filter_primitives(neighborhood.operators, TaskInsertion)
    if len(insertions) != 1:
        raise ValueError("Exactly one TaskInsertion is needed to say which task was inserted")
    insertion = insertions[0]
    support_solution = model.solution
    for task in sorted(insertion.candidate_tasks, key=lambda candidate: candidate.name):
        if not support_solution.get_task_performance_status(task):
            continue
        assignee = support_solution.get_task_assignee(task)
        if assignee in insertion.candidate_employees:
            return task, assignee
    raise ValueError("The solved solution leaves no candidate task with a candidate employee")


def _get_deleted_task_and_employee(neighborhood: Neighborhood,
                                   model: NeighborhoodModel) -> tuple[Task, Employee]:
    """
    Return the candidate task the solver removed, and the employee whose planning it was removed from.

    The employee is read off the given solution rather than assumed to be the one receiving the incoming task:
    a (Swp,2c) neighborhood offers every employee's performed tasks as removal candidates,
    so the solver may take the outgoing task from one employee and hand the incoming one to another.

    Args:
        neighborhood: The neighborhood the model was built from.
        model: The solved model to read the arrangement off.

    Returns:
        A pair made of the removed task and the employee performing it in the given solution.

    Raises:
        ValueError: if the neighborhood carries no TaskDeletion, or if none of its candidate tasks
            went from performed to not performed.
    """
    deletions = filter_primitives(neighborhood.operators, TaskDeletion)
    if len(deletions) != 1:
        raise ValueError("Exactly one TaskDeletion is needed to say which task was removed")
    given_solution, support_solution = neighborhood.solution, model.solution
    for task in sorted(deletions[0].candidate_tasks, key=lambda candidate: candidate.name):
        if (given_solution.get_task_performance_status(task)
                and not support_solution.get_task_performance_status(task)):
            return task, given_solution.get_task_assignee(task)
    raise ValueError("The solved solution removed none of the candidate tasks from any planning")


def _describe_insertion(neighborhood: Neighborhood, model: NeighborhoodModel,
                        template_id: str) -> dict[str, str]:
    """
    Describe what an (Ins,*) neighborhood's solved model settled on.

    Args:
        neighborhood: The neighborhood the model was built from.
        model: The solved model.
        template_id: The identifier of the recognized question template.

    Returns:
        The sentence keyed by language.
    """
    task, employee = _get_inserted_task_and_employee(neighborhood, model)
    if template_id in ROUTE_SPELLING_TEMPLATES_IDS:
        return TransformationDescriptionBuilder.for_inserting_task_in_route(
            task, employee, _describe_solved_route(model, employee)
        )
    activity = _get_activity_before_in_solved_route(model, employee, task, neighborhood)
    return TransformationDescriptionBuilder.for_inserting_task_after_activity(task, activity, employee)


def _describe_swap(neighborhood: Neighborhood, model: NeighborhoodModel, template_id: str) -> dict[str, str]:
    """
    Describe what a (Swp,*) neighborhood's solved model settled on.

    Args:
        neighborhood: The neighborhood the model was built from.
        model: The solved model.
        template_id: The identifier of the recognized question template.

    Returns:
        The sentence keyed by language.
    """
    replacing_task, employee = _get_inserted_task_and_employee(neighborhood, model)
    leaving_task, leaving_employee = _get_deleted_task_and_employee(neighborhood, model)
    if leaving_employee != employee:
        return TransformationDescriptionBuilder.for_replacing_task_of_another_employee(
            leaving_task, leaving_employee, replacing_task, employee
        )
    if template_id in ROUTE_SPELLING_TEMPLATES_IDS:
        return TransformationDescriptionBuilder.for_replacing_task_in_route(
            leaving_task, replacing_task, employee, _describe_solved_route(model, employee)
        )
    return TransformationDescriptionBuilder.for_replacing_task_with_another(leaving_task, replacing_task, employee)


def _describe_pinned_repositioning(question: ContrastiveQuestion, template_id: str) -> dict[str, str]:
    """
    Describe an (Ord,1a)/(Ord,1b) repositioning, which the question itself pins entirely.

    The model is not read: both the moving task and the one it is moved next to are named by the question,
    and the template says which side of it the move lands on.

    Args:
        question: The recognized question.
        template_id: The identifier of the recognized question template.

    Returns:
        The sentence keyed by language.
    """
    instance = question.solution.instance
    employee_name, moving_task_name, fixed_task_name = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    moving_task = instance.get_task_by_name(moving_task_name)
    fixed_task = instance.get_task_by_name(fixed_task_name)
    if template_id == WHY_NOT_ORD_LAT_1:
        return TransformationDescriptionBuilder.for_repositioning_after(moving_task, fixed_task, employee)
    return TransformationDescriptionBuilder.for_repositioning_before(moving_task, fixed_task, employee)


def _describe_free_repositioning(question: ContrastiveQuestion, neighborhood: Neighborhood,
                                 model: NeighborhoodModel) -> dict[str, str]:
    """
    Describe an (Ord,2a)/(Ord,2b)/(Ord,2c) repositioning, whose landing position is the solver's to pick.

    Which side of its new neighbor the sentence names is read off the direction the task actually moved,
    the way the tailored pipeline reads it off the sequence:
    a task that moved later is named after the task it now follows,
    one that moved earlier before the task it now precedes.

    Args:
        question: The recognized question.
        neighborhood: The neighborhood the model was built from.
        model: The solved model.

    Returns:
        The sentence keyed by language.

    Raises:
        ValueError: if the solved route leaves the moving task exactly where it already stood.
    """
    instance = question.solution.instance
    employee_name, moving_task_name = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    moving_task = instance.get_task_by_name(moving_task_name)
    given_tasks = list(neighborhood.solution.get_sequence(employee).get_contained_tasks())
    solved_route = model.get_solved_route(employee)
    given_index = given_tasks.index(moving_task)
    solved_index = _get_index_in_route(solved_route, moving_task, employee)
    if solved_index > given_index:
        fixed_task = _get_activity_before_in_solved_route(model, employee, moving_task, neighborhood)
        return TransformationDescriptionBuilder.for_repositioning_after(
            moving_task, cast(Task, fixed_task), employee
        )
    if solved_index < given_index:
        fixed_task = _get_activity_after_in_solved_route(model, employee, moving_task)
        return TransformationDescriptionBuilder.for_repositioning_before(
            moving_task, cast(Task, fixed_task), employee
        )
    raise ValueError(f"{moving_task.name} stands at the same position in {employee.name}'s solved route")


def _describe_reordering(question: ContrastiveQuestion, model: NeighborhoodModel) -> dict[str, str]:
    """
    Describe an (Ord,3) reordering of a whole route.

    NB: No task is named, even though the model did pick a pivot task of its own to reorder around,
    since the question asks for another order without naming one either.

    Args:
        question: The recognized question.
        model: The solved model.

    Returns:
        The sentence keyed by language.
    """
    employee_name, = question.fields_values
    employee = question.solution.instance.get_employee_by_name(employee_name)
    return TransformationDescriptionBuilder.for_reordering_route(
        employee, _describe_solved_route(model, employee)
    )
