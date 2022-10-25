#! /usr/bin/env python3
# coding: utf-8


# Standard library
from os import path

# Local libraries
from src.reading.instance import extract_instance_from_file
from src.modeling.solution import Solution
from src.utils.files import find_instance_filename_corresponding_to_solution, find_specific_solutions_files_names
from src.utils.time import convert_time_string_to_nb_minutes


def extract_solution_from_file(filename: str, ignore_employees_unavailabilities: bool = False,
                               ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False,
                               ignore_instance_version: bool = False, ignore_solving_method: bool = False):

    # Check if file exists
    if not path.exists(filename):
        raise FileNotFoundError(f"The given solution file {filename} does not exists")

    # Find the corresponding instance
    instance_filename = find_instance_filename_corresponding_to_solution(
        filename, ignore_instance_version=ignore_instance_version, ignore_solving_method=ignore_solving_method
    )
    instance = extract_instance_from_file(
        instance_filename, ignore_employees_unavailabilities, ignore_tasks_unavailabilities, ignore_lunch_breaks,
        ignore_instance_version
    )

    # Initialize an empty solution adapted to the instance
    solution_name = filename.split('/')[-1].split('.')[0]
    solution = Solution(instance=instance, name=solution_name)

    # Read lines of the solution file
    with open(filename, 'r') as file:
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
        if not(task_name in instance.tasks_names):
            raise ValueError(f"The task {task_name} is not in the tasks set")
        else:
            task = instance.get_task_by_name(task_name)
            task_is_realized = int(words[1]) == 1
            solution.set_task_performance_status(task, task_is_realized)
            if task_is_realized:
                solution.set_task_assignee(task, instance.get_employee_by_name(words[2]))
                if not(":" in words[3]):
                    solution.set_task_start_time(task, int(float(words[3])))
                else:
                    print("The format of the tasks' start times is wrong")
                    solution.set_task_start_time(task, convert_time_string_to_nb_minutes(int(words[3])))
        line_index += 1

    # Compute the sequences based on tasks realizations
    solution.compute_sequences_based_on_tasks_performances()

    return solution


def main():
    instance_version = 2
    regions_names = ["Australia", "Austria", "Bordeaux", "Poland", "Spain"]
    for region_name in regions_names:
        solutions_files_names = find_specific_solutions_files_names(instance_version, region_name)
        for solution_file_name in solutions_files_names:
            print()
            print("Extraction of " + region_name)
            solution = extract_solution_from_file(solution_file_name)
            print(solution)


if __name__ == '__main__':
    main()
