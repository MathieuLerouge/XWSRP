# Standard library
import typing

# Local libraries
from model.employee import Employee
from model.task import Task
from model.unavailability import Unavailability
from optimization.localsearch.solution import SolutionLS
from utils.time import convert_nb_minutes_to_time_string


# Comment placement
def comment_placement(solution: SolutionLS, employee: Employee, entering_task: Task, step_before_placement_index: int,
                      step_after_placement_index: int, examination: dict[str, typing.Union[bool, int, None]]):

    # Get steps around the insertion
    sequence = solution.get_sequence(employee)
    step_before_placement = sequence[step_before_placement_index]
    step_after_placement = sequence[step_after_placement_index]

    # Comment the placement feasibility
    comment = ""
    if not examination['is_feasible']:
        entering_task_end_time_for_upstream = examination['earliest_start_time_for_upstream'] + entering_task.duration

        # If the placement is not feasible upstream-wise,
        if not examination['is_upstream_feasible']:
            if step_before_placement_index == 0:
                comment += (
                    f"By performing {entering_task.name} "
                    f"after leaving {step_before_placement.activity.name} at the earliest possible, "
                )
            elif step_before_placement_index == 1:
                comment += (
                    f"By performing {step_before_placement.activity.name} "
                    f"and {entering_task.name} at the earliest possible, "
                )
            else:
                comment += (
                    f"By performing all the activities before {entering_task.name} at the earliest possible, "
                )
            comment += (
                f"{employee.name} can end {entering_task.name} "
                f"at {convert_nb_minutes_to_time_string(entering_task_end_time_for_upstream)} at the earliest, "
                f"while {entering_task.name} must be ended "
                f"by {convert_nb_minutes_to_time_string(entering_task.end_time_UB)}. "
            )

        # If the placement is feasible upstream-wise,
        else:
            earliest_start_time_of_step_after = max(
                step_after_placement.activity.start_time_LB,
                entering_task_end_time_for_upstream +
                solution.instance.compute_traveling_duration(entering_task, step_after_placement.activity)
            )
            comment += (
                f"By performing all the activities before {step_after_placement.activity.name} "
                f"at the earliest possible, "
            )
            if step_after_placement_index == len(sequence) - 1:
                comment += (
                    f"{employee.name} can be at {step_after_placement.activity.name} "
                    f"at {convert_nb_minutes_to_time_string(earliest_start_time_of_step_after)} at the earliest, "
                    f"while he/she must be there "
                    f"by {convert_nb_minutes_to_time_string(step_after_placement.activity.end_time_UB)}."
                )
            elif isinstance(step_after_placement.activity, Unavailability):
                comment += (
                    f"{employee.name} can start {step_after_placement.activity.name} "
                    f"at {convert_nb_minutes_to_time_string(earliest_start_time_of_step_after)} at the earliest, "
                    f"while he/she must start it "
                    f"at {convert_nb_minutes_to_time_string(step_after_placement.activity.start_time_LB)}."
                )
            else:
                comment += (
                    f"{employee.name} can start {step_after_placement.activity.name} "
                    f"at {convert_nb_minutes_to_time_string(earliest_start_time_of_step_after)} at the earliest, "
                    f"while {step_after_placement.activity.name} must be started at "
                    f"{convert_nb_minutes_to_time_string(step_after_placement.start_time + step_after_placement.FTS)} "
                    f"at the latest in order to allow him/her "
                )
                critical_step_index = sequence.find_first_critical_step_index_forward_from(step_after_placement_index)
                critical_step = sequence[critical_step_index]
                if critical_step_index == step_after_placement_index:
                    comment += (
                        f"to end it before "
                        f"{convert_nb_minutes_to_time_string(step_after_placement.activity.end_time_UB)}."
                    )
                elif critical_step_index < len(sequence) - 1:
                    if isinstance(critical_step.activity, Unavailability):
                        comment += (
                            f"to start {critical_step.activity.name} "
                            f"at {convert_nb_minutes_to_time_string(critical_step.activity.start_time_LB)}.")
                    else:
                        comment += (
                            f"to end {critical_step.activity.name} "
                            f"before {convert_nb_minutes_to_time_string(critical_step.activity.end_time_UB)}."
                        )
                else:
                    comment += (
                        f"to be at {sequence[-1].activity.name} "
                        f"by {convert_nb_minutes_to_time_string(sequence[-1].activity.end_time_UB)}."
                    )

    # Return comment
    return comment


#
def examine_placing_at(solution: SolutionLS, employee: Employee, entering_task: Task,
                       step_before_placement_index: int, step_after_placement_index: int):
    """
    Examine the feasibility of placing the given entering task between the given step indices in the given
    employee's sequence; provide a dictionary describing this examination with keys
    'is_feasible', 'is_upstream_feasible', 'is_downstream_feasible'
    'start_time', 'earliest_start_time_for_upstream', 'latest_start_time_for_downstream',
    'traveling_duration_detour' and 'comment'.

    - If the placement is feasible, the value associated to the key 'start_time' is the start time (int)
      that could be applied to the entering task and the text is empty;
    - If the placement is infeasible, the value associated to the key 'start_time' is a proposed start time (int)
      that could be applied to the entering task even though it is infeasible and the text explains why the
      placement is infeasible.

    Assumptions (only checked in debug):

    - 1. the given entering task can be performed by the employee of this sequence;
    - 2. the given entering task must not be already in this sequence;
    - 3. the given index of step before the placement must be
    between 0 (included) and the number of steps - 2 (included);
    - 4. the given index of step after the placement must be
    between 1 (included) and the number of steps - 1 (included);
    - 5. the index of the step before the placement is smaller or equal to
    the one of the step after the placement;
    - 6. the times of this sequence are consistent.

    :param solution: the solution (SolutionLS) for which the examination is done
    :param employee: the employee (Employee) who is figured to perform the entering task
    :param entering_task: the task (Task) that is figured to be inserted
    :param step_before_placement_index: the index of the step (int) before the position
      where the given task would be placed
    :param step_after_placement_index: the index of the step (int) after the position
      where the given task would be placed
    :return: the dictionary with keys 'is_feasible', 'is_upstream_feasible', 'is_downstream_feasible'
    'start_time', 'earliest_start_time_for_upstream', 'latest_start_time_for_downstream',
    'traveling_duration_detour', 'comment'
    """

    # The assumptions are checked when calling examine_placing_between

    # Examine the placement feasibility
    examination = solution.get_sequence(employee).examine_placing_between(
        entering_task, step_before_placement_index, step_after_placement_index
    )

    # Add comment to the examination
    comment = comment_placement(
        solution, employee, entering_task,
        step_before_placement_index, step_after_placement_index, examination
    )
    examination['comment'] = comment

    # Return the examination
    return examination


#
def examine_insertion_at(solution: SolutionLS, employee: Employee, entering_task: Task, step_index: int):
    """
    Examine the feasibility of the insertion of the given entering task at the given step index in the given
    employee's sequence; provide a dictionary describing this examination which has keys:
    'is_feasible', 'is_upstream_feasible', 'is_downstream_feasible'
    'start_time', 'earliest_start_time_for_upstream', 'latest_start_time_for_downstream',
    'traveling_duration_detour' and 'comment'.

    - If the insertion is feasible, the value associated to the key 'start_time' is the start time (int)
      that could be applied to the entering task and the text is empty;
    - If the insertion is infeasible, the value associated to the key 'start_time' is a proposed start time (int)
      that could be applied to the entering task even though it is infeasible and the text explains why the
      insertion is infeasible.

    Assumptions (only checked in debug):

    - 1. the given entering task can be performed by the employee of this sequence;
    - 2. the given entering task must not be already in this sequence;
    - 3. the given step index must be between 1 (included) and the number of steps - 1 (included);
    - 4. the times of this sequence are consistent.

    :param solution: the solution (SolutionLS) for which the examination is done
    :param employee: the employee (Employee) who is figured to perform the entering task
    :param entering_task: the task (Task) that is figured to be inserted
    :param step_index: the index of the step (int) where the given task would be inserted
    :return: the dictionary with keys 'is_feasible', 'is_upstream_feasible', 'is_downstream_feasible'
    'start_time', 'earliest_start_time_for_upstream', 'latest_start_time_for_downstream',
    'traveling_duration_detour', 'comment'
    """

    # The assumptions are checked when calling examine_insertion_at

    # Examine the insertion feasibility
    examination = solution.examine_insertion_at(entering_task, employee, step_index)

    # Add comment to the examination
    step_before_placement_index = step_index - 1
    step_after_placement_index = step_before_placement_index + 1
    comment = comment_placement(
        solution, employee, entering_task,
        step_before_placement_index, step_after_placement_index, examination
    )
    examination['comment'] = comment

    # Return the examination
    return examination


# Examine the best insertion
def examine_best_insertion(solution: SolutionLS, entering_task: Task, employee: Employee = None,
                           tabu_indices: list[int] = None):
    """
    Examine which insertion of the given entering task in the given employee's sequence is the best
    among the insertions at indices that are not tabu.

    The entering task must not be performed by the employee, otherwise a ValueError is raised.
    The entering task may be performed by another employee however.

    :param solution:
    :param entering_task:
    :param employee:
    :param tabu_indices:
    :return:
    """

    if solution.get_sequence(employee).contains(entering_task):
        raise ValueError(f"The entering task {entering_task.name} is performed by the employee {employee.name}")

    # Examine the best insertion
    examination = solution.examine_best_insertion_deprecated(entering_task, employee, tabu_indices)
    if employee is None:
        employee = examination['employee']

    # Add comment to the examination
    if employee is None:
        examination['comment'] = (
            f"None of the employees is capable of performing the task {entering_task} "
            f"due to capacities or time windows."
        )
    else:
        step_before_placement_index = examination['step_index_for_insertion'] - 1
        step_after_placement_index = step_before_placement_index + 1
        examination['comment'] = comment_placement(
            solution, employee, entering_task, step_before_placement_index,
            step_after_placement_index, examination
        )

    # Return the examination
    return examination


# Examine the insertion of a task in an employee's planning in addition to their activities
def examine_insertion_in_addition(solution: SolutionLS, employee: Employee, task: Task):
    if solution.get_sequence(employee).contains(task):
        raise ValueError(f"The task {task.name} to add is performed by the employee {employee.name}")
    examination = solution.examine_best_insertion_in_addition(employee, task)
    solution_with_entering_task = examination['solution']
    step_index = examination['step_index_for_insertion']
    step_before_placement = step_index - 1
    step_after_placement = step_index + 1
    examination['comment'] = comment_placement(
        solution_with_entering_task, employee, task,
        step_before_placement, step_after_placement, examination
    )
    return examination


# Examine best insertion when the task is the only one to be assign to the employee
def examine_best_insertion_when_isolated(solution: SolutionLS, employee: Employee, task: Task):
    examination = solution.examine_best_insertion_when_alone(employee, task)
    solution_with_isolated_task = examination['solution']
    step_index = examination['step_index_for_insertion']
    step_before_placement = step_index - 1
    step_after_placement = step_index + 1
    examination['comment'] = comment_placement(
        solution_with_isolated_task, employee, task,
        step_before_placement, step_after_placement, examination
    )
    return examination
