# Standard library
from os import path

# Local libraries
from src.reading.instance import extract_instance_from_file
from src.modeling.solution import Solution
from src.utils.constants import META_DATA_CORE_KEY, SOLUTION_NAME_PREFIX
from src.utils.files import find_instance_file_path_corresponding_to_solution, \
    get_solutions_files_paths_given_meta_data, identify_meta_data_in_solution_file_path
from src.utils.time import convert_time_string_to_nb_minutes


def initialize_solution_from_file(solution_file_path: str, ignore_employees_unavailabilities: bool = False,
                                  ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False):
    # Check that the path exists
    if not path.exists(solution_file_path):
        raise FileNotFoundError(f"The given solution file {solution_file_path} does not exists")
    # Extract corresponding instance
    instance_file_path = find_instance_file_path_corresponding_to_solution(solution_file_path)
    instance = extract_instance_from_file(
        instance_file_path, ignore_employees_unavailabilities, ignore_tasks_unavailabilities, ignore_lunch_breaks
    )
    # Initialize a solution
    meta_data = identify_meta_data_in_solution_file_path(solution_file_path)
    solution = Solution(instance, SOLUTION_NAME_PREFIX + meta_data[META_DATA_CORE_KEY])
    return solution


def complete_solution_from_file(solution: Solution, solution_file_path: str):
    # Define some variable
    instance = solution.instance
    # Read lines of the solution file
    with open(solution_file_path, 'r') as file:
        file_lines = [line for line in file]
    # Check the header of the paragraph about tasks
    line_index = 0
    first_word = file_lines[line_index].split(';')[0]
    if first_word != "taskId":
        if first_word in instance.tasks_names:
            print("The header of the paragraph about tasks is missing")
        else:
            print("The header of the paragraph about tasks is wrong")
            line_index += 1
    else:
        line_index += 1
    # Read the data in paragraph about tasks
    while (line_index < len(file_lines)) and (len(file_lines[line_index]) > 4):
        words = file_lines[line_index].split(';')
        task_name = words[0]
        if not (task_name in instance.tasks_names):
            raise ValueError(f"The task {task_name} is not in the tasks set")
        else:
            task = instance.get_task_by_name(task_name)
            task_is_realized = int(words[1]) == 1
            solution.set_task_performance_status(task, task_is_realized)
            if task_is_realized:
                solution.set_task_assignee(task, instance.get_employee_by_name(words[2]))
                if not (":" in words[3]):
                    solution.set_task_start_time(task, int(float(words[3])))
                else:
                    print("The format of the tasks' start times is wrong")
                    solution.set_task_start_time(task, convert_time_string_to_nb_minutes(words[3]))
        line_index += 1
    solution.compute_sequences_based_on_tasks_performances()
    return solution


def extract_solution_from_file(solution_file_path: str, ignore_employees_unavailabilities: bool = False,
                               ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False):
    solution = initialize_solution_from_file(solution_file_path, ignore_employees_unavailabilities,
                                             ignore_tasks_unavailabilities, ignore_lunch_breaks)
    return complete_solution_from_file(solution, solution_file_path)


# def extract_solution_from_file(solution_file_path: str, ignore_employees_unavailabilities: bool = False,
#                                ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False):
#     if not path.exists(solution_file_path):
#         raise FileNotFoundError(f"The given solution file {solution_file_path} does not exists")
#
#     # Extract corresponding instance
#     instance_file_path = find_instance_file_path_corresponding_to_solution(solution_file_path)
#     instance = extract_instance_from_file(
#         instance_file_path, ignore_employees_unavailabilities, ignore_tasks_unavailabilities, ignore_lunch_breaks
#     )
#
#     # Initialize a solution
#     meta_data = identify_meta_data_in_solution_file_path(solution_file_path)
#     solution = Solution(instance=instance, name=SOLUTION_NAME_PREFIX + meta_data[META_DATA_CORE_KEY])
#
#     # Read lines of the solution file
#     with open(solution_file_path, 'r') as file:
#         file_lines = [line for line in file]
#
#     # Check the header of the paragraph about tasks
#     line_index = 0
#     first_word = file_lines[line_index].split(';')[0]
#     if first_word != "taskId":
#         if first_word in instance.tasks_names:
#             print("The header of the paragraph about tasks is missing")
#         else:
#             print("The header of the paragraph about tasks is wrong")
#             line_index += 1
#     else:
#         line_index += 1
#
#     # Read the data in paragraph about tasks
#     while (line_index < len(file_lines)) and (len(file_lines[line_index]) > 4):
#         words = file_lines[line_index].split(';')
#         task_name = words[0]
#         if not(task_name in instance.tasks_names):
#             raise ValueError(f"The task {task_name} is not in the tasks set")
#         else:
#             task = instance.get_task_by_name(task_name)
#             task_is_realized = int(words[1]) == 1
#             solution.set_task_performance_status(task, task_is_realized)
#             if task_is_realized:
#                 solution.set_task_assignee(task, instance.get_employee_by_name(words[2]))
#                 if not(":" in words[3]):
#                     solution.set_task_start_time(task, int(float(words[3])))
#                 else:
#                     print("The format of the tasks' start times is wrong")
#                     solution.set_task_start_time(task, convert_time_string_to_nb_minutes(int(words[3])))
#         line_index += 1
#
#     # Compute the sequences based on tasks realizations
#     solution.compute_sequences_based_on_tasks_performances()
#
#     return solution


def main():
    version = 2
    regions_names = ["Australia", "Austria", "Bordeaux", "Poland", "Spain"]
    for region_name in regions_names:
        solutions_files_paths = get_solutions_files_paths_given_meta_data(region_name, version)
        for solution_file_path in solutions_files_paths:
            print()
            print("Extraction of " + region_name)
            solution = extract_solution_from_file(solution_file_path)
            print(solution)


if __name__ == '__main__':
    main()
