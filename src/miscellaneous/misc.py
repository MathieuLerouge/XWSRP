from src.reading.solution import extract_solution_from_file
from src.utils.constants import INPUTS_DIRECTORY
from src.utils.files import get_solutions_files_names


def main():

    try:
        solution_file_name = get_solutions_files_names()[0]
    except IndexError:
        raise FileNotFoundError(f"There are no solutions files found in directory {INPUTS_DIRECTORY}")
    ignore_employees_unavailabilities = True
    ignore_tasks_unavailabilities = True
    ignore_lunch_breaks = True
    ignore_instance_version = True
    ignore_solving_method = True
    solution = extract_solution_from_file(
        solution_file_name, ignore_employees_unavailabilities, ignore_tasks_unavailabilities, ignore_lunch_breaks,
        ignore_instance_version, ignore_solving_method
    )

    for employee in solution.instance.employees:
        print(employee.name, ": ", employee.start_time_LB, employee.end_time_UB)

    for task in solution.instance.tasks:
        print(task.name, ": ", task.start_time_LB, task.end_time_UB)


if __name__ == '__main__':
    main()