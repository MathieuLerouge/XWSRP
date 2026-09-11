# Local libraries
from src.explaining.neighborhood.constraint import ImmediatePrecedence, SequenceOrderFixed
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import TaskInsertion
from src.explaining.questioning.question import ContrastiveQuestion
from src.explaining.computing.templates.exceptions import ImpossibleTransformationException


def map_ins_1(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Ins,1) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing task {Task} just after activity {Activity}?"

    Args:
        question: The (Ins,1) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        inserting the target task immediately after the provided activity,
        in the provided employee's otherwise-unchanged sequence.
    """
    solution = question.solution
    instance = solution.instance
    employee_name, task_name, activity_name = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    task = instance.get_task_by_name(task_name)
    anchor_activity = instance.get_hypothetical_activity_by_names(activity_name, employee_name)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
    constraints = [SequenceOrderFixed(employee), ImmediatePrecedence(employee, anchor_activity, task)]
    return Neighborhood(solution=solution, operators=[operator], constraints=constraints)


def map_ins_2a(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Ins,2a) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing task {Task} between two consecutive activities of their route?"

    Args:
        question: The (Ins,2a) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        inserting the target task anywhere in the provided employee's otherwise-unchanged sequence.
    """
    solution = question.solution
    instance = solution.instance
    employee_name, task_name = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    task = instance.get_task_by_name(task_name)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
    return Neighborhood(solution=solution, operators=[operator], constraints=[SequenceOrderFixed(employee)])


def map_ins_2b(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Ins,2b) contrastive question to the Neighborhood it induces.
    "Why is employee {Emp.} not performing any non-performed task between two consecutive activities of their route?"

    Args:
        question: The (Ins,2b) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        inserting one of the non-performed tasks anywhere in the provided employee's otherwise-unchanged sequence.

    Raises:
        ImpossibleTransformationException: If the solution performs every task, leaving no candidate
            to insert.
    """
    solution = question.solution
    employee_name, = question.fields_values
    employee = solution.instance.get_employee_by_name(employee_name)
    candidate_tasks = frozenset(solution.non_performed_tasks)
    if len(candidate_tasks) == 0:
        raise ImpossibleTransformationException(
            "Inserting any non-performed task is impossible given a solution performing all the tasks"
        )
    operator = TaskInsertion(frozenset({employee}), candidate_tasks)
    return Neighborhood(solution=solution, operators=[operator], constraints=[SequenceOrderFixed(employee)])


def map_ins_2c(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Ins,2c) contrastive question to the Neighborhood it induces.
    "Why is any employee not performing task {Task} between two consecutive activities of their route?"

    Args:
        question: The (Ins,2c) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        inserting the target task anywhere in one of the instance's employees' otherwise-unchanged sequence,
        the relative order of every employee's already-performed tasks staying fixed.
    """
    solution = question.solution
    task_name, = question.fields_values
    task = solution.instance.get_task_by_name(task_name)
    candidate_employees = frozenset(solution.instance.employees)
    operator = TaskInsertion(candidate_employees, frozenset({task}))
    constraints = [SequenceOrderFixed(employee) for employee in candidate_employees]
    return Neighborhood(solution=solution, operators=[operator], constraints=constraints)


def map_ins_3(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Ins,3) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing task {Task} in addition to their already-performed activities
    (even if it means changing their order)?"

    Args:
        question: The (Ins,3) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        inserting the target task anywhere in the provided employee's sequence,
        the order of their already-performed tasks left free to change too.
    """
    solution = question.solution
    instance = solution.instance
    employee_name, task_name = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    task = instance.get_task_by_name(task_name)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
    return Neighborhood(solution=solution, operators=[operator])
