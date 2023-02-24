# Local libraries
from src.reading.solution import extract_solution_from_file
from src.utils.constants import INPUTS_DIRECTORY_RELATIVE_PATH
from src.utils.files import get_paths_of_solutions_files_in_given_directory


def main():
    try:
        solution_file_path = get_paths_of_solutions_files_in_given_directory()[0]
    except IndexError:
        raise FileNotFoundError(f"There are no solutions files found in directory {INPUTS_DIRECTORY_RELATIVE_PATH}")
    solution = extract_solution_from_file(solution_file_path, True, True, True)
    for employee in solution.instance.employees:
        print(employee.name, ": ", employee.start_time_LB, employee.end_time_UB)
    for task in solution.instance.tasks:
        print(task.name, ": ", task.start_time_LB, task.end_time_UB)


if __name__ == '__main__':
    main()
