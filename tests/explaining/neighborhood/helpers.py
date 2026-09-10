# Local libraries
from src.modeling.instance import Instance
from src.modeling.solution import Solution


def build_solution_with_task_performances(instance: Instance, name: str,
                                          task_performances: dict[str, tuple[str, int]]) -> Solution:
    """
    Builds a Solution over instance where each task named in task_performances is marked performed,
    assigned, and started as given, and every other task of the instance is left non-performed;
    sequences are then derived from these task performances (unlike tests.modeling.helpers.build_solution,
    which sets sequences directly and leaves task performances at their default of "not performed",
    a mismatch this package's tests can't tolerate since Neighborhood/Mapper read task performances,
    not sequences, to decide what's already performed).

    Args:
        instance: Instance the solution belongs to.
        name: Name of the solution.
        task_performances: Mapping from task name to (employee name, start time), for every task that
            should be performed.

    Returns:
        Solution: The built solution.
    """
    solution = Solution(instance, name=name)
    for task_name, (employee_name, start_time) in task_performances.items():
        task = instance.get_task_by_name(task_name)
        employee = instance.get_employee_by_name(employee_name)
        solution.set_task_performance_status(task, True)
        solution.set_task_assignee(task, employee)
        solution.set_task_start_time(task, start_time)
    solution.compute_sequences_based_on_tasks_performances()
    return solution
