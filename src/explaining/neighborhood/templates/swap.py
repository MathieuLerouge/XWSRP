# Local libraries
from src.explaining.neighborhood.assembler import Assembler
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import TaskDeletion, TaskInsertion
from src.explaining.neighborhood.restriction import ForbiddenBackwardSubsequence, PrecedenceChain
from src.explaining.questioning.question import ContrastiveQuestion
from src.explaining.computing.exceptions import ImpossibleTransformationException


def map_swp_1(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Swp,1) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing task {Task1} rather than task {Task2}?"

    Args:
        question: The (Swp,1) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        removing task2 and inserting task1 in its place, in the provided employee's otherwise-unchanged
        sequence.
    """
    solution = question.solution
    instance = solution.instance
    employee_name, task_name_1, task_name_2 = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    task_1 = instance.get_task_by_name(task_name_1)
    task_2 = instance.get_task_by_name(task_name_2)
    operators = [
        TaskDeletion(frozenset({employee}), frozenset({task_2})),
        TaskInsertion(frozenset({employee}), frozenset({task_1}))
    ]
    employee_tasks = list(solution.get_sequence(employee).get_contained_tasks())
    employee_tasks.remove(task_2)
    restrictions = [PrecedenceChain(employee_tasks)]
    return Assembler.assemble(operators, restrictions, solution)


def map_swp_2a(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Swp,2a) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing task {Task} rather than any of their already-performed tasks?"

    Args:
        question: The (Swp,2a) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        removing one of the provided employee's already-performed tasks and inserting the target task in
        its place, the relative order of their other already-performed tasks staying fixed.
    """
    solution = question.solution
    instance = solution.instance
    employee_name, task_name = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    task = instance.get_task_by_name(task_name)
    employee_tasks = list(solution.get_sequence(employee).get_contained_tasks())
    operators = [
        TaskDeletion(frozenset({employee}), frozenset(employee_tasks)),
        TaskInsertion(frozenset({employee}), frozenset({task}))
    ]
    restrictions = [ForbiddenBackwardSubsequence(employee, employee_tasks)]
    return Assembler.assemble(operators, restrictions, solution)


def map_swp_2b(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Swp,2b) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing any non-performed task rather than any of their
    already-performed tasks?"

    Args:
        question: The (Swp,2b) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        removing one of the provided employee's already-performed tasks and inserting one of the
        non-performed tasks in its place, the relative order of their other already-performed tasks
        staying fixed.

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
    employee_tasks = list(solution.get_sequence(employee).get_contained_tasks())
    operators = [
        TaskDeletion(frozenset({employee}), frozenset(employee_tasks)),
        TaskInsertion(frozenset({employee}), candidate_tasks)
    ]
    restrictions = [ForbiddenBackwardSubsequence(employee, employee_tasks)]
    return Assembler.assemble(operators, restrictions, solution)


def map_swp_2c(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Swp,2c) contrastive question to the Neighborhood it induces.
    "Why is any employee not performing task {Task} rather than any of their already-performed tasks?"

    Args:
        question: The (Swp,2c) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        removing one currently-performed task, from any employee, and inserting the target task in its
        place, the relative order of every employee's other already-performed tasks staying fixed.
    """
    solution = question.solution
    task_name, = question.fields_values
    task = solution.instance.get_task_by_name(task_name)
    candidate_employees = frozenset(solution.instance.employees)
    performed_tasks = frozenset(solution.performed_tasks)
    operators = [
        TaskDeletion(candidate_employees, performed_tasks),
        TaskInsertion(candidate_employees, frozenset({task}))
    ]
    restrictions = [
        ForbiddenBackwardSubsequence(employee, list(solution.get_sequence(employee).get_contained_tasks()))
        for employee in candidate_employees
    ]
    return Assembler.assemble(operators, restrictions, solution)


def map_swp_3(question: ContrastiveQuestion) -> Neighborhood:
    """
    Map the (Swp,3) contrastive question to the Neighborhood it induces.
    "Why is employee {Employee} not performing task {Task} rather than any of their already-performed
    tasks (even if it means changing their order)?"

    Args:
        question: The (Swp,3) contrastive question to map.

    Returns:
        The Neighborhood induced by the question:
        removing one of the provided employee's already-performed tasks and inserting the target task
        anywhere in their sequence, the order of their other already-performed tasks left free to change too.
    """
    solution = question.solution
    instance = solution.instance
    employee_name, task_name = question.fields_values
    employee = instance.get_employee_by_name(employee_name)
    task = instance.get_task_by_name(task_name)
    employee_tasks = list(solution.get_sequence(employee).get_contained_tasks())
    operators = [
        TaskDeletion(frozenset({employee}), frozenset(employee_tasks)),
        TaskInsertion(frozenset({employee}), frozenset({task}))
    ]
    return Assembler.assemble(operators, [], solution)
