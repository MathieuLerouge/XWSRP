# Local libraries
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import SequenceReordering, TaskRepositioning
from src.explaining.neighborhood.restriction import (
    ForbiddenSequence, ImmediatePrecedence, Precedence, PrecedenceChain
)
from src.explaining.questioning.question import ContrastiveQuestion


def map_ord_1a(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Ord,1a) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing task {Task1} later in their planning, just after task {Task2}?"

    Args:
        question: The (Ord,1a) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        repositioning task1 immediately after task2, in the provided employee's otherwise-unchanged sequence.
    """
    solution = question.solution
    instance = solution.instance
    employee_name, task_name_1, task_name_2 = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    task_1 = instance.get_task_by_name(task_name_1)
    task_2 = instance.get_task_by_name(task_name_2)
    operator = TaskRepositioning(employee, task_1)
    employee_tasks = list(solution.get_sequence(employee).get_contained_tasks())
    employee_tasks.remove(task_1)
    restrictions = [PrecedenceChain(employee_tasks), ImmediatePrecedence(task_2, task_1)]
    return Neighborhood(solution=solution, operators=[operator], restrictions=restrictions)


def map_ord_1b(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Ord,1b) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing task {Task1} earlier in their planning, just before task {Task2}?"

    Args:
        question: The (Ord,1b) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        repositioning task1 immediately before task2, in the provided employee's otherwise-unchanged sequence.
    """
    solution = question.solution
    instance = solution.instance
    employee_name, task_name_1, task_name_2 = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    task_1 = instance.get_task_by_name(task_name_1)
    task_2 = instance.get_task_by_name(task_name_2)
    operator = TaskRepositioning(employee, task_1)
    employee_tasks = list(solution.get_sequence(employee).get_contained_tasks())
    employee_tasks.remove(task_1)
    restrictions = [PrecedenceChain(employee_tasks), ImmediatePrecedence(task_1, task_2)]
    return Neighborhood(solution=solution, operators=[operator], restrictions=restrictions)


def map_ord_2a(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Ord,2a) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing task {Task} at a later stage of their planning?"

    Args:
        question: The (Ord,2a) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        repositioning the target task past its current immediate successor, in the provided employee's
        otherwise-unchanged sequence, without pinning its new position any more precisely than that.
    """
    solution = question.solution
    instance = solution.instance
    employee_name, task_name = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    task = instance.get_task_by_name(task_name)
    employee_tasks = list(solution.get_sequence(employee).get_contained_tasks())
    next_task = employee_tasks[employee_tasks.index(task) + 1]
    operator = TaskRepositioning(employee, task)
    employee_tasks.remove(task)
    restrictions = [PrecedenceChain(employee_tasks), Precedence(next_task, task)]
    return Neighborhood(solution=solution, operators=[operator], restrictions=restrictions)


def map_ord_2b(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Ord,2b) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing task {Task} at an earlier stage of their planning?"

    Args:
        question: The (Ord,2b) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        repositioning the target task before its current immediate predecessor, in the provided employee's
        otherwise-unchanged sequence, without pinning its new position any more precisely than that.
    """
    solution = question.solution
    instance = solution.instance
    employee_name, task_name = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    task = instance.get_task_by_name(task_name)
    employee_tasks = list(solution.get_sequence(employee).get_contained_tasks())
    prev_task = employee_tasks[employee_tasks.index(task) - 1]
    operator = TaskRepositioning(employee, task)
    employee_tasks.remove(task)
    restrictions = [PrecedenceChain(employee_tasks), Precedence(task, prev_task)]
    return Neighborhood(solution=solution, operators=[operator], restrictions=restrictions)


def map_ord_2c(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Ord,2c) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing task {Task} at any another stage in their planning?"

    Args:
        question: The (Ord,2c) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        repositioning the target task anywhere but its current position, in the provided employee's
        otherwise-unchanged sequence (only its exact original spot, relative to its current immediate
        predecessor/successor, is excluded).
    """
    solution = question.solution
    instance = solution.instance
    employee_name, task_name = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    task = instance.get_task_by_name(task_name)
    employee_tasks = list(solution.get_sequence(employee).get_contained_tasks())
    index = employee_tasks.index(task)
    original_neighbors = employee_tasks[max(index - 1, 0):index + 2]
    operator = TaskRepositioning(employee, task)
    employee_tasks.remove(task)
    restrictions = [PrecedenceChain(employee_tasks), ForbiddenSequence(employee, original_neighbors)]
    return Neighborhood(solution=solution, operators=[operator], restrictions=restrictions)


def map_ord_3(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Ord,3) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing the activities of their route in another order?"

    Args:
        question: The (Ord,3) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        reordering the provided employee's entire sequence into anything but its current order.
    """
    solution = question.solution
    instance = solution.instance
    employee_name, = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    operator = SequenceReordering(employee)
    employee_tasks = list(solution.get_sequence(employee).get_contained_tasks())
    restrictions = [ForbiddenSequence(employee, employee_tasks)]
    return Neighborhood(solution=solution, operators=[operator], restrictions=restrictions)
