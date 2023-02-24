# Standard library
import json

# Third party library
import pandas as pd

# Local libraries
from src.modeling.instance import Instance
from src.utils.constants import *
from src.utils.files import identify_meta_data_in_instance_file_path, get_instance_name_in_instance_file_path
from src.utils.location import Location
from src.utils.time import convert_time_string_to_nb_minutes


#############################
# Extraction from json file #
#############################


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


#############################
# Extraction from xlsx file #
#############################


def create_empty_instance_from_xlsx_file(file_path: str):
    instance_name = get_instance_name_in_instance_file_path(file_path)
    return Instance(name=instance_name)


def complete_instance_from_xlsx_file(instance: Instance, file_path: str,
                                     ignore_employees_unavailabilities: bool = False,
                                     ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False):

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
    if not ignore_lunch_breaks:
        instance.set_lunch_break(
            lunch_break_lower_bound=convert_time_string_to_nb_minutes("12:00pm"),
            lunch_break_upper_bound=convert_time_string_to_nb_minutes("2:00pm"),
            lunch_break_duration=60
        )

    # Add speed
    instance.speed = 5 / 6

    # Update instance
    instance.update()

    return instance


# TODO Add sheet_name with lunch_break to instances?
# TODO Add sheet_name with speed to instances?
def extract_instance_from_xlsx_file(file_path: str, ignore_employees_unavailabilities: bool = False,
                                    ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False):
    """
    Extract the instance stored in the given file

    :param file_path: name of the file which includes the extension .xls (str)
    :param ignore_employees_unavailabilities: boolean indicating whether employees unavailabilities
    must be ignored, which overrides the assumption of the version if any (bool)
    :param ignore_tasks_unavailabilities: boolean indicating whether tasks unavailabilities
    must be ignored, which overrides the assumption of the version if any (bool)
    :param ignore_lunch_breaks: boolean indicating whether lunch breaks
    must be ignored, which overrides the assumption of the version if any (bool)
    :return:
    """

    # Create an empty instance
    # TODO update function (case)
    instance_name = get_instance_name_in_instance_file_path(file_path)
    data = identify_meta_data_in_instance_file_path(file_path)
    instance_version = data[META_DATA_VERSION_KEY]
    instance = Instance(name=instance_name)
    instance.version = instance_version

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


#####################################
# Extraction from json or xlsx file #
#####################################


def extract_instance_from_file(file_path: str, ignore_employees_unavailabilities: bool = False,
                               ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False):
    if ".json" in file_path:
        return extract_instance_from_json_file(file_path)
    elif ".xls" in file_path:
        return extract_instance_from_xlsx_file(file_path, ignore_employees_unavailabilities,
                                               ignore_tasks_unavailabilities, ignore_lunch_breaks)
    else:
        raise ValueError("The file must be a JSON or XLSX file")
