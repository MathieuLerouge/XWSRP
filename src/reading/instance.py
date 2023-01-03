# Standard library
import json

# Third party library
import pandas as pd

# Local libraries
from src.modeling.instance import Instance
from src.utils.constants import *
from src.utils.files import create_instance_file_path, identify_meta_data_in_instance_file_path, \
    get_project_directory_path
from src.utils.location import Location
from src.utils.time import convert_time_string_to_nb_minutes


def extract_instance_from_json_file(file_path: str):
    """
    Extract the instance stored in the given json file

    :param file_path: path of the file which includes the extension .json (str)
    :return: the instance (Instance)
    """
    if ".json" not in file_path:
        raise FileNotFoundError(f"The given file path {file_path} does not have a json extension")
    with open(file_path) as json_file:
        instance_dictionary = json.load(json_file)
        instance = Instance.from_dict(instance_dictionary)
    return instance


# TODO Add sheet_name with lunch_break to instances?
# TODO Add sheet_name with speed to instances?
def extract_instance_from_xlsx_file(file_path: str, ignore_employees_unavailabilities: bool = False,
                                    ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False,
                                    ignore_version: bool = False):
    """
    Extract the instance stored in the given file

    :param file_path: name of the file which includes the extension .xls (str)
    :param ignore_employees_unavailabilities: boolean indicating whether or not employees unavailabilities
    must be ignored, which overrides the assumption of the version if any (bool)
    :param ignore_tasks_unavailabilities: boolean indicating whether or not tasks unavailabilities
    must be ignored, which overrides the assumption of the version if any (bool)
    :param ignore_lunch_breaks: boolean indicating whether or not lunch breaks
    must be ignored, which overrides the assumption of the version if any (bool)
    :param ignore_version: boolean indicating whether or not the version must be ignored (bool)
    :return:
    """

    # Create an empty instance
    data = identify_meta_data_in_instance_file_path(file_path)
    region_name, instance_version = data[CORE_KEY], data['version']
    if instance_version is None:
        instance_name = f"{INSTANCE_FILE_NAME_PREFIX}{region_name}"
    else:
        instance_name = f"{INSTANCE_FILE_NAME_PREFIX}{region_name}{INSTANCE_VERSION_STRING}{instance_version}"
    instance = Instance(name=instance_name)

    # Extract file's sheets
    instance_data = dict()
    sheet_names = ['Employees', 'Employees Unavailabilities', 'Tasks', 'Tasks Unavailabilities']
    for sheet_name in sheet_names:
        instance_data[sheet_name] = pd.read_excel(file_path, sheet_name=sheet_name)

    # Read the sheet "Employees"
    for _, employee_data in instance_data['Employees'].iterrows():
        instance.add_employee(
            name=employee_data['EmployeeName'],
            start_time_LB=convert_time_string_to_nb_minutes(employee_data['WorkingStartTime']),
            end_time_UB=convert_time_string_to_nb_minutes(employee_data['WorkingEndTime']),
            location=Location(employee_data['Latitude'], employee_data['Longitude']),
            skill_level=employee_data['Level']
        )

    # Read the sheet "Employees Unavailabilities"
    if not ignore_employees_unavailabilities:
        for _, employeeUnavailabilityData in instance_data['Employees Unavailabilities'].iterrows():
            employee_name = employeeUnavailabilityData['EmployeeName']
            instance.get_employee_by_name(employee_name).add_unavailability(
                location=Location(
                    first_coordinate=employeeUnavailabilityData['Latitude'],
                    second_coordinate=employeeUnavailabilityData['Longitude']
                ),
                start_time=convert_time_string_to_nb_minutes(employeeUnavailabilityData['Start']),
                end_time=convert_time_string_to_nb_minutes(employeeUnavailabilityData['End'])
            )

    # Read the sheet "Tasks"
    for _, task_data in instance_data['Tasks'].iterrows():
        instance.add_task(
            name=task_data['TaskId'],
            start_time_LB=convert_time_string_to_nb_minutes(task_data['OpeningTime']),
            end_time_UB=convert_time_string_to_nb_minutes(task_data['ClosingTime']),
            duration=int(task_data['TaskDuration']),
            location=Location(
                first_coordinate=task_data['Latitude'],
                second_coordinate=task_data['Longitude']
            ),
            skill_level=task_data['Level']
        )

    # Read the sheet "Tasks Unavailabilities"
    if not ignore_tasks_unavailabilities:
        for _, task_unavailability_data in instance_data['Tasks Unavailabilities'].iterrows():
            task_name = task_unavailability_data['TaskId']
            instance.get_task_by_name(task_name).apply_unavailability(
                unavailability_start_time=convert_time_string_to_nb_minutes(task_unavailability_data['Start']),
                unavailability_end_time=convert_time_string_to_nb_minutes(task_unavailability_data['End'])
            )

    # Add lunch breaks if needed
    if not ignore_lunch_breaks and instance_version in [2, 3]:
        instance.set_lunch_break(
            lunch_break_lower_bound=convert_time_string_to_nb_minutes("12:00pm"),
            lunch_break_upper_bound=convert_time_string_to_nb_minutes("2:00pm"),
            lunch_break_duration=60
        )

    # Add speed
    instance.speed = 5/6

    # Update instance
    instance.update()

    return instance


def extract_instance_from_file(file_path: str, ignore_employees_unavailabilities: bool = False,
                               ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False,
                               ignore_version: bool = False):
    if ".json" in file_path:
        return extract_instance_from_json_file(file_path)
    elif ".xls" in file_path:
        return extract_instance_from_xlsx_file(file_path, ignore_employees_unavailabilities,
                                               ignore_tasks_unavailabilities, ignore_lunch_breaks, ignore_version)
    else:
        raise ValueError("The file must be a JSON or XLSX file")


# Main function
def main():
    version = 2
    regions_names = ["Australia", "Austria", "Bordeaux", "Poland", "Spain"]
    for region_name in regions_names:
        file_name = "../" + create_instance_file_path(region_name, version)
        print()
        print("Extraction of " + region_name)
        example_instance = extract_instance_from_file(file_name)
        print(example_instance)
        print(example_instance.employees)
        print(example_instance.tasks)


if __name__ == '__main__':
    regions_names = ["Australia", "Austria", "Bordeaux", "Poland", "Spain"]
    instances_directory = get_project_directory_path() + "/data/instances/instancesV1"
    for region_name in regions_names:
        file_name = "../" + create_instance_file_path(region_name, version)
        print()
        print("Extraction of " + region_name)
        example_instance = extract_instance_from_file(file_name)
        print(example_instance)
        print(example_instance.employees)
        print(example_instance.tasks)
    main()
