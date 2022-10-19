# Local libraries
from src.modeling.solution import Solution
from src.modeling.task import Task
from src.utils.constants import LINE_BREAK_STRING, OUTPUTS_DIRECTORY
from src.utils.timeset import TimeInterval, convert_nb_minutes_to_time_string

# Global variable
TOLERANCE_IN_MINUTES = 1


def check_covering_constraints(solution: Solution):
    satisfaction = True
    checking_text = ""
    non_realized_tasks_names = [task.name for task in solution.instance.tasks
                                if not (solution.get_task_realization(task))]
    if not (bool(non_realized_tasks_names)):
        satisfaction = False
        for task_name in non_realized_tasks_names:
            checking_text += f"In the given plan, the task {task_name} is not realized" + LINE_BREAK_STRING
    if not satisfaction:
        checking_text = checking_text.removesuffix(LINE_BREAK_STRING)
    return satisfaction, checking_text


def check_time_windows_constraints(solution: Solution):

    # Initialize satisfaction boolean and checking text
    satisfaction = True
    checking_text = ""

    # Check that tasks are realized within availability time windows
    for task in solution.instance.tasks:
        if solution.get_task_realization(task):
            start_time = solution.get_task_start_time(task)
            end_time = start_time + task.duration
            # - Task
            task_available_when_realized = False
            for availability_TW in task.TWs.intervals:
                if availability_TW.contain_all([start_time, end_time]):
                    task_available_when_realized = True
                    break
            if not task_available_when_realized:
                satisfaction = False
                checking_text += (f"In the given plan, the task {task.name} is supposed to "
                                  f"be realized over {TimeInterval(start_time, end_time)} "
                                  f"while it is actually available only over {task.TWs}" +
                                  LINE_BREAK_STRING)
            # - Employee
            employee = solution.get_task_assignee(task)
            if start_time < employee.start_time_LB:
                satisfaction = False
                checking_text += (f"In the given plan, the task {task.name} is supposed to "
                                  f"be realized over {TimeInterval(start_time, end_time)} "
                                  f"by employee {employee.name} "
                                  f"while he/she actually starts working at "
                                  f"{convert_nb_minutes_to_time_string(employee.start_time_LB)}" +
                                  LINE_BREAK_STRING)
            if employee.end_time_UB < end_time:
                satisfaction = False
                checking_text += (f"In the given plan, the task {task.name} is supposed to "
                                  f"be realized over {TimeInterval(start_time, end_time)} "
                                  f"by employee {employee.name} "
                                  f"while he/she actually ends working at "
                                  f"{convert_nb_minutes_to_time_string(employee.end_time_UB)}" +
                                  LINE_BREAK_STRING)
            for unavailability in employee.unavailabilities:
                if unavailability.TWs[0].contain(start_time) or unavailability.TWs[0].contain(end_time):
                    satisfaction = False
                    checking_text += (f"In the given plan, the task {task.name} is supposed to "
                                      f"be realized over {TimeInterval(start_time, end_time)} "
                                      f"by employee {employee.name} "
                                      f"while he/she is actually unavailable over {unavailability.TWs[0]} " +
                                      f"due to his/her unavailability {unavailability.name}" +
                                      LINE_BREAK_STRING)

    # Check that lunch breaks are taken within dedicated time windows
    if solution.instance.has_lunch_break:
        for employee in solution.instance.employees:
            lunch_break_start_time = solution.get_employee_lunch_break_start_time(employee)
            lunch_break_end_time = lunch_break_start_time + solution.instance.lunch_break_duration
            if (lunch_break_start_time < solution.instance.lunch_break_time_LB or
                    solution.instance.lunch_break_time_UB < lunch_break_end_time):
                satisfaction = False
                checking_text += (f"In the given plan, {employee.name} is supposed to take a lunch break over "
                                  f"{TimeInterval(lunch_break_start_time, lunch_break_end_time)} "
                                  f"while lunch break must actually be within "
                                  f"{TimeInterval(solution.instance.lunch_break_time_LB,solution.instance.lunch_break_time_UB)}" +
                                  LINE_BREAK_STRING)

    if not satisfaction:
        checking_text = checking_text.removesuffix(LINE_BREAK_STRING)

    return satisfaction, checking_text


def check_sequence_constraints(solution: Solution, tolerance_in_minutes: int = 0):

    # Initialize satisfaction boolean and checking text
    satisfaction = True
    checking_text = ""

    for employee in solution.instance.employees:
        sequence = solution[employee.name]
        if len(sequence) > 2:

            # Check start-to-first-step sequence (if first step is a task)
            first_step = sequence[1]
            if isinstance(first_step.activity, Task):
                if sequence[0].start_time < employee.start_time_LB - tolerance_in_minutes:
                    satisfaction = False
                    checking_text += (f"In the given plan, {employee.name} is supposed to "
                                      f"do the task {first_step.activity.name} "
                                      f"at {convert_nb_minutes_to_time_string(first_step.start_time)} "
                                      f"therefore, he/she is supposed to leave its initial location at "
                                      f"{convert_nb_minutes_to_time_string(sequence[0].start_time)} "
                                      f"but he/she actually starts to work not before "
                                      f"{convert_nb_minutes_to_time_string(employee.start_time_LB)}" +
                                      LINE_BREAK_STRING)

            # Check step-to-step sequence (including unavailabilities)
            for previous_step_index, step in enumerate(sequence[1: -1]):
                if step.arrival_time > step.start_time + tolerance_in_minutes:
                    satisfaction = False
                    previous_step = sequence[previous_step_index]
                    if (solution.instance.has_lunch_break and
                            solution.get_activity_after_employee_lunch(employee) == step.activity):
                        supposing_traveling_duration = (step.start_time - previous_step.end_time -
                                                        solution.instance.lunch_break_duration)
                        checking_text += (f"In the given plan, {employee.name} is supposed to "
                                          f"do {previous_step.activity.name} "
                                          f"at {convert_nb_minutes_to_time_string(previous_step.start_time)}, "
                                          f"then take a lunch break and do {step.activity.name} "
                                          f"at {convert_nb_minutes_to_time_string(step.start_time)} "
                                          f"therefore, {employee.name} is supposed to travel "
                                          f"from {previous_step.activity.name} to {step.activity.name} "
                                          f"in less than {supposing_traveling_duration} min "
                                          f"but it actually takes "
                                          f"{solution.compute_traveling_duration(previous_step, step)} min" +
                                          LINE_BREAK_STRING)
                    else:
                        checking_text += (f"In the given plan, {employee.name} is supposed to "
                                          f"do {previous_step.activity.name} at "
                                          f"{convert_nb_minutes_to_time_string(previous_step.start_time)}, "
                                          f"then do {step.activity.name} "
                                          f"at {convert_nb_minutes_to_time_string(step.start_time)} "
                                          f"therefore, {employee.name} is supposed to travel "
                                          f"from {previous_step.activity.name} to {step.activity.name} "
                                          f"in less than {step.start_time - previous_step.end_time} min "
                                          f"but it actually takes "
                                          f"{solution.compute_traveling_duration(previous_step, step)} min" +
                                          LINE_BREAK_STRING)

            # Check last-step-to-end sequence (if last step is a task)
            last_step = sequence[-2]
            if isinstance(last_step.activity, Task):
                if sequence[-1].arrival_time > employee.end_time_UB + tolerance_in_minutes:
                    satisfaction = False
                    checking_text += (f"In the given plan, {employee.name} is supposed to "
                                      f"do {last_step.activity.name} "
                                      f"at {convert_nb_minutes_to_time_string(last_step.start_time)} "
                                      f"and then go at his/her final location, "
                                      f"therefore {employee.name} is supposed to be at his/her final location at "
                                      f"{convert_nb_minutes_to_time_string(sequence[-1].arrival_time)} "
                                      f"but {employee.name} actually ends to work no later than"
                                      f"{convert_nb_minutes_to_time_string(employee.end_time_UB)}" +
                                      LINE_BREAK_STRING)

    if not satisfaction:
        checking_text = checking_text.removesuffix(LINE_BREAK_STRING)

    return satisfaction, checking_text


def check_skill_constraints(solution: Solution):
    satisfaction = True
    checking_text = ""
    for task in solution.instance.tasks:
        if solution.get_task_realization(task):
            employee = solution.get_task_assignee(task)
            if not employee.is_capable_of_performing(task):
                satisfaction = False
                checking_text += (f"In the given plan, {employee.name} is supposed to "
                                  f"do task {task.name}, which has a skill level equal to {task.skill_level}, "
                                  f"but he/she has a skill level which is equal to {employee.skill_level}" +
                                  LINE_BREAK_STRING)
    if not satisfaction:
        checking_text = checking_text.removesuffix(LINE_BREAK_STRING)
    return satisfaction, checking_text


def check_feasibility(solution: Solution, covering: bool = False, time_windows: bool = True,
                      sequence: bool = True, skill: bool = True, tolerance_in_minutes: int = 0):
    feasible = True
    checking_text = ""
    checks_toggles = [covering, time_windows, sequence, skill]
    checks_functions = [lambda x: check_covering_constraints(x),
                        lambda x: check_time_windows_constraints(x),
                        lambda x: check_sequence_constraints(x, tolerance_in_minutes),
                        lambda x: check_skill_constraints(x)]
    for check_index, toggle in enumerate(checks_toggles):
        if toggle:
            satisfaction, text = checks_functions[check_index](solution)
            feasible &= satisfaction
            if not satisfaction:
                checking_text += text + LINE_BREAK_STRING
    if feasible:
        checking_text = "The given solution is feasible"
    else:
        checking_text = ("The given solution is not feasible" + LINE_BREAK_STRING +
                         checking_text.removesuffix(LINE_BREAK_STRING))
    return feasible, checking_text


def create_checking_filename(solution: Solution, output_directory: str = None):
    if output_directory is None:
        output_directory = OUTPUTS_DIRECTORY
    return output_directory + "/" + solution.name + "Checks.txt"
