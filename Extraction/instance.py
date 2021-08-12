#! /usr/bin/env python3
# coding: utf-8


# Third party library
import pandas as pd

# Local libraries
from model.instance import Instance
from utils.files import create_instance_filename, extract_data_from_instance_filename
from utils.location import Location
from utils.time import convert_time_string_to_nb_minutes


# TODO Remove region_name in signature
# TODO Add ignore_lunch_break in signature
# TODO Add sheet_name with lunch_break to instances
# TODO Add sheet_name with speed to instances
def extract_instance_from_file(filename: str, ignore_employees_unavailabilities: bool = False,
                               ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False,
                               ignore_version: bool = False):

    # Create an empty instance
    region_name, instance_version = extract_data_from_instance_filename(filename, ignore_version)
    if ignore_version:
        instance_name = region_name
    else:
        instance_name = region_name + f"V{instance_version}"
    instance = Instance(name=instance_name)

    # Extract file's sheets
    instance_data = dict()
    sheet_names = ['Employees', 'Employees Unavailabilities', 'Tasks', 'Tasks Unavailabilities']
    for sheet_name in sheet_names:
        instance_data[sheet_name] = pd.read_excel(filename, sheet_name=sheet_name)

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


# Main function
def main():
    version = 2
    regions_names = ["Australia", "Austria", "Bordeaux", "Poland", "Spain"]
    for region_name in regions_names:
        file_name = "../" + create_instance_filename(region_name, version)
        print()
        print("Extraction of " + region_name)
        instance = extract_instance_from_file(file_name)
        print(instance)
        print(instance.employees)
        print(instance.tasks)


if __name__ == '__main__':
    main()
