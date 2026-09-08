# Local libraries
from src.modeling.solution import Solution
from src.modeling.task import Task
from src.utils.constants import LINE_BREAK_STRING, DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
from src.utils.files import make_absolute_path_from_relative_one
from src.utils.timeset import TimeInterval, convert_nb_minutes_to_time_string


##################################
# Constraints satisfaction check #
##################################


def check_covering_constraints(solution: Solution):
    """
    Check that, in the provided solution, all tasks of the instance are performed by an employee

    :param solution: solution to check
    :return: a tuple containing a boolean indicating whether the solution satisfies the covering constraints
    and a string containing the checking text
    """
    satisfaction = True
    checking_text = ""
    non_performed_tasks_names = [task.name for task in solution.instance.tasks
                                 if not (solution.get_task_performance_status(task))]
    if not (bool(non_performed_tasks_names)):
        satisfaction = False
        for task_name in non_performed_tasks_names:
            checking_text += f"In the provided solution, the task {task_name} is not performed " \
                             f"while all tasks must be performed. {LINE_BREAK_STRING}"
    if not satisfaction:
        checking_text = checking_text.removesuffix(LINE_BREAK_STRING)
    return satisfaction, checking_text


def check_time_windows_constraints(solution: Solution):
    """
    Check that, in the provided solution, all tasks are performed within their time windows

    :param solution: solution to check
    :return: a tuple containing a boolean indicating whether the solution satisfies the time windows constraints
    and a string containing the checking text
    """

    # Initialize satisfaction boolean and checking text
    satisfaction = True
    checking_text = ""

    # Check that tasks are performed within availability time windows
    for task in solution.instance.tasks:
        if solution.get_task_performance_status(task):
            start_time = solution.get_task_start_time(task)
            end_time = start_time + task.duration
            # - Task
            task_available_when_performed = False
            for availability_TW in task.time_windows.intervals:
                if availability_TW.contain_all([start_time, end_time]):
                    task_available_when_performed = True
                    break
            if not task_available_when_performed:
                satisfaction = False
                checking_text += f"In the provided solution, the task {task.name} is supposed to be performed over "\
                                 f"{TimeInterval(start_time, end_time)} while it is available only over " \
                                 f"{task.time_windows.as_string()}. {LINE_BREAK_STRING}"
            # - Employee
            employee = solution.get_task_assignee(task)
            if start_time < employee.start_time_lb:
                satisfaction = False
                checking_text += f"In the provided solution, the task {task.name} is supposed to be performed over " \
                                 f"{TimeInterval(start_time, end_time)} by employee {employee.name} " \
                                 f"while he/she must start working at " \
                                 f"{convert_nb_minutes_to_time_string(employee.start_time_lb)}.{LINE_BREAK_STRING}"
            if employee.end_time_ub < end_time:
                satisfaction = False
                checking_text += f"In the provided solution, the task {task.name} is supposed to be performed over "\
                                 f"{TimeInterval(start_time, end_time)} by employee {employee.name} "\
                                 f"while he/she must end working at "\
                                 f"{convert_nb_minutes_to_time_string(employee.end_time_ub)}."\
                                 f"{LINE_BREAK_STRING}"
            for unavailability in employee.unavailabilities:
                if (unavailability.time_windows[0].contain(start_time) or
                        unavailability.time_windows[0].contain(end_time)):
                    satisfaction = False
                    checking_text += f"In the provided solution, the task {task.name} is supposed to be performed " \
                                     f"over {TimeInterval(start_time, end_time)} by employee {employee.name} " \
                                     f"while he/she is unavailable over {unavailability.time_windows[0]} " \
                                     f"due to his/her unavailability {unavailability.name}.{LINE_BREAK_STRING}"

    # Check that lunch breaks are taken within dedicated time windows
    if solution.instance.has_lunch_break:
        for employee in solution.instance.employees:
            lunch_break_start_time = solution.get_employee_lunch_break_start_time(employee)
            lunch_break_end_time = lunch_break_start_time + solution.instance.lunch_break_duration
            if (lunch_break_start_time < solution.instance.lunch_break_time_lb or
                    solution.instance.lunch_break_time_ub < lunch_break_end_time):
                satisfaction = False
                lunch_break_TW = TimeInterval(solution.instance.lunch_break_time_lb,
                                              solution.instance.lunch_break_time_ub)
                checking_text += f"In the provided solution, {employee.name} is supposed to have a lunch break over "\
                                 f"{TimeInterval(lunch_break_start_time, lunch_break_end_time)} " \
                                 f"while lunch break must be within {lunch_break_TW}.{LINE_BREAK_STRING}"

    if not satisfaction:
        checking_text = checking_text.removesuffix(LINE_BREAK_STRING)

    return satisfaction, checking_text


def check_sequence_constraints(solution: Solution, tolerance_in_minutes: int = 0):
    """
    Check that, in the provided solution, employees' schedules are consistent time-wise

    :param solution: solution to check
    :param tolerance_in_minutes: tolerance in minutes to consider that two times are equal
    :return: a tuple containing a boolean indicating whether the solution satisfies the sequence constraints
    and a string containing the checking text
    """

    # Initialize satisfaction boolean and checking text
    satisfaction = True
    checking_text = ""

    for employee in solution.instance.employees:
        sequence = solution[employee.name]
        if len(sequence) > 2:

            # Check start-to-first-step sequence (if first step is a task)
            first_step = sequence[1]
            if isinstance(first_step.activity, Task):
                if sequence[0].start_time < employee.start_time_lb - tolerance_in_minutes:
                    satisfaction = False
                    checking_text += f"In the provided solution, {employee.name} is supposed to perform " \
                                     f"the task {first_step.activity.name} at " \
                                     f"{convert_nb_minutes_to_time_string(first_step.start_time)}, " \
                                     f"which means that he/she is supposed to leave their initial location at " \
                                     f"{convert_nb_minutes_to_time_string(sequence[0].start_time)}. " \
                                     f"However, he/she must not start to work before " \
                                     f"{convert_nb_minutes_to_time_string(employee.start_time_lb)}." \
                                     f"{LINE_BREAK_STRING}"

            # Check step-to-step sequence (including unavailabilities)
            for previous_step_index, step in enumerate(sequence[1: -1]):
                if step.arrival_time > step.start_time + tolerance_in_minutes:
                    satisfaction = False
                    previous_step = sequence[previous_step_index]
                    if (solution.instance.has_lunch_break and
                            solution.get_activity_after_employee_lunch(employee) == step.activity):
                        supposing_traveling_duration = (step.start_time - previous_step.end_time -
                                                        solution.instance.lunch_break_duration)
                        checking_text += f"In the provided solution, {employee.name} is supposed to perform " \
                                         f"{previous_step.activity.name} at " \
                                         f"{convert_nb_minutes_to_time_string(previous_step.start_time)}, " \
                                         f"then have a lunch break and perform {step.activity.name} at " \
                                         f"{convert_nb_minutes_to_time_string(step.start_time)}. " \
                                         f"It means that {employee.name} is supposed to travel from " \
                                         f"{previous_step.activity.name} to {step.activity.name} " \
                                         f"in less than {supposing_traveling_duration}min. " \
                                         f"However, such a travel takes " \
                                         f"{solution.compute_traveling_duration(previous_step, step)}min." \
                                         f"{LINE_BREAK_STRING}"
                    else:
                        checking_text += f"In the provided solution, {employee.name} is supposed to perform " \
                                         f"{previous_step.activity.name} at " \
                                         f"{convert_nb_minutes_to_time_string(previous_step.start_time)}, " \
                                         f"then perform {step.activity.name} at " \
                                         f"{convert_nb_minutes_to_time_string(step.start_time)}. " \
                                         f"It means that {employee.name} is supposed to travel from " \
                                         f"{previous_step.activity.name} to {step.activity.name} " \
                                         f"in less than {step.start_time - previous_step.end_time}min. " \
                                         f"However, such a travel takes " \
                                         f"{solution.compute_traveling_duration(previous_step, step)}min." \
                                         f"{LINE_BREAK_STRING}"

            # Check last-step-to-end sequence (if last step is a task)
            last_step = sequence[-2]
            if isinstance(last_step.activity, Task):
                if sequence[-1].arrival_time > employee.end_time_ub + tolerance_in_minutes:
                    satisfaction = False
                    checking_text += f"In the provided solution, {employee.name} is supposed perform " \
                                     f"{last_step.activity.name} at " \
                                     f"{convert_nb_minutes_to_time_string(last_step.start_time)} " \
                                     f"and then go to his/her final location, " \
                                     f"which means that he/she is supposed to be at his/her final location at " \
                                     f"{convert_nb_minutes_to_time_string(sequence[-1].arrival_time)}. " \
                                     f"However, {employee.name} must end to work no later than " \
                                     f"{convert_nb_minutes_to_time_string(employee.end_time_ub)}." \
                                     f"{LINE_BREAK_STRING}"

    if not satisfaction:
        checking_text = checking_text.removesuffix(LINE_BREAK_STRING)

    return satisfaction, checking_text


def check_skill_constraints(solution: Solution):
    """
    Check that, in the provided solution, tasks are performed by employees with the required skills

    :param solution: solution to check
    :return: a tuple containing a boolean indicating whether the solution satisfies the skill constraints
    and a string containing the checking text
    """
    satisfaction = True
    checking_text = ""
    for task in solution.instance.tasks:
        if solution.get_task_performance_status(task):
            employee = solution.get_task_assignee(task)
            if not employee.is_capable_of_performing(task):
                satisfaction = False
                checking_text += f"In the provided solution, {employee.name} is supposed to perform task " \
                                 f"{task.name}, which has a skill level equal to {task.skill_level}, " \
                                 f"while he/she has a skill level which is equal to {employee.skill_level}." \
                                 f"{LINE_BREAK_STRING}"
    if not satisfaction:
        checking_text = checking_text.removesuffix(LINE_BREAK_STRING)
    return satisfaction, checking_text


##############################
# Solution feasibility check #
##############################


def check_feasibility(solution: Solution, covering: bool = False, time_windows: bool = True,
                      sequence: bool = True, skill: bool = True, tolerance_in_minutes: int = 0):
    """
    Check that the provided solution is feasible

    :param solution: solution to check
    :param covering: whether to check the task covering constraints
    :param time_windows: whether to check the time windows constraints
    :param sequence: whether to check the sequence constraints
    :param skill: whether to check the skill constraints
    :param tolerance_in_minutes: tolerance in minutes to consider when checking the time windows constraints
    :return: a tuple containing a boolean indicating whether the solution is feasible
    and a string containing the checking text
    """
    feasible = True
    checking_text = ""
    checks_toggles = [covering, time_windows, sequence, skill]
    checks_functions = [lambda x: check_covering_constraints(x), lambda x: check_time_windows_constraints(x),
                        lambda x: check_sequence_constraints(x, tolerance_in_minutes),
                        lambda x: check_skill_constraints(x)]
    for check_index, toggle in enumerate(checks_toggles):
        if toggle:
            satisfaction, text = checks_functions[check_index](solution)
            feasible &= satisfaction
            if not satisfaction:
                checking_text += text + LINE_BREAK_STRING
    if feasible:
        checking_text = "The provided solution is feasible"
    else:
        checking_text = ("The given solution is not feasible" + LINE_BREAK_STRING +
                         checking_text.removesuffix(LINE_BREAK_STRING))
    return feasible, checking_text


###################################
# Solution feasibility check file #
###################################


def create_solution_feasibility_check_file_path(solution: Solution, outputs_directory_relative_path: str = None):
    """
    Create a file path for the text file of the solution feasibility check

    :param solution: solution to check
    :param outputs_directory_relative_path: relative path to the outputs directory
    :return: the file path
    """
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
    return make_absolute_path_from_relative_one(f"{outputs_directory_relative_path}/{solution.name}Checks.txt")


def create_multiple_solution_feasibility_checks_file_path(outputs_directory_relative_path: str = None):
    """
    Create a file path for the text file of multiple solution feasibility checks

    :param outputs_directory_relative_path: relative path to the outputs directory
    :return: the file path
    """
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
    return make_absolute_path_from_relative_one(f"{outputs_directory_relative_path}/SolutionsChecks.txt")
