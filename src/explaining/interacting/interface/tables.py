# Third-party libraries
from dash import dash_table

# Local libraries
from src.utils.language import check_if_language_is_english, check_if_language_is_french
from src.explaining.interacting.interface.assets.styles import UI_TABLE_STYLE_HEADER, UI_TABLE_STYLE_DATA
from src.modeling.instance import Instance
from src.utils.language import LANGUAGE_ENGLISH_KEY
from src.utils.time import convert_time_string_to_nb_minutes, get_hour_format_associated_with_language


def build_employees_data(instance: Instance, language: str = LANGUAGE_ENGLISH_KEY):
    hour_format = get_hour_format_associated_with_language(language)
    return [dict(name=employee.name, level=employee.skill_level,
                 start=employee.get_start_time_LB(False, hour_format), end=employee.get_end_time_UB(False, hour_format))
            for employee in instance.employees]


def build_employees_style_data_conditional(employees_data, reference_instance: Instance):
    employees_data_conditional_style = []
    for row_index, employee_data in enumerate(employees_data):
        reference_employee = reference_instance.get_employee_by_name(employee_data['name'])
        if convert_time_string_to_nb_minutes(employee_data['start']) != reference_employee.start_time_LB:
            employees_data_conditional_style.append({'if': {'column_id': 'start', 'row_index': row_index},
                                                     'backgroundColor': 'dodgerblue', 'color': 'white'})
        if convert_time_string_to_nb_minutes(employee_data['end']) != reference_employee.end_time_UB:
            employees_data_conditional_style.append({'if': {'column_id': 'end', 'row_index': row_index},
                                                     'backgroundColor': 'dodgerblue', 'color': 'white'})
    return employees_data_conditional_style


def build_employees_data_table(instance: Instance, is_current_instance: bool,
                               instance_to_compare_with: Instance = None, editable: bool = False,
                               language: str = LANGUAGE_ENGLISH_KEY):
    table_id = "editable" if editable else ("current" if is_current_instance else "other")
    table_id += "-instance-employees-data-table"
    data = build_employees_data(instance, language)
    data_conditional_style = \
        build_employees_style_data_conditional(data, instance_to_compare_with) if not is_current_instance else None
    if check_if_language_is_english(language):
        columns = [{'name': 'Name', 'id': 'name'}, {'name': 'Skill level', 'id': 'level'},
                   {'name': 'Earliest working time', 'id': 'start', 'editable': editable},
                   {'name': 'Latest working time', 'id': 'end', 'editable': editable}]
    elif check_if_language_is_french(language):
        columns = [{'name': 'Nom', 'id': 'name'}, {'name': 'Niveau', 'id': 'level'},
                   {'name': 'Début de dispo.', 'id': 'start', 'editable': editable},
                   {'name': 'Fin de dispo.', 'id': 'end', 'editable': editable}]
    else:
        raise ValueError(f"Language {language} is not supported.")
    table = dash_table.DataTable(
        id=table_id, data=data, columns=columns, style_as_list_view=True,
        style_header=UI_TABLE_STYLE_HEADER, style_data=UI_TABLE_STYLE_DATA,
        style_cell_conditional=[{'if': {'column_id': 'name'}, 'width': '20%'},
                                {'if': {'column_id': 'level'}, 'width': '20%'},
                                {'if': {'column_id': 'start'}, 'width': '20%'},
                                {'if': {'column_id': 'end'}, 'width': '40%'}],
        style_data_conditional=data_conditional_style
    )
    return table


def build_tasks_data(instance: Instance, language: str = LANGUAGE_ENGLISH_KEY):
    hour_format = get_hour_format_associated_with_language(language)
    return [dict(name=task.name, level=task.skill_level, duration=task.duration,
                 start=task.get_start_time_LB(False, hour_format), end=task.get_end_time_UB(False, hour_format))
            for task in instance.tasks]


def build_tasks_style_data_conditional(tasks_data, reference_instance: Instance):
    tasks_data_conditional_style = []
    for row_index, task_data in enumerate(tasks_data):
        reference_task = reference_instance.get_task_by_name(task_data['name'])
        if convert_time_string_to_nb_minutes(task_data['start']) != reference_task.start_time_LB:
            tasks_data_conditional_style.append({'if': {'column_id': 'start', 'row_index': row_index},
                                                 'backgroundColor': 'dodgerblue', 'color': 'white'})
        if convert_time_string_to_nb_minutes(task_data['end']) != reference_task.end_time_UB:
            tasks_data_conditional_style.append({'if': {'column_id': 'end', 'row_index': row_index},
                                                 'backgroundColor': 'dodgerblue', 'color': 'white'})
        if int(task_data['duration']) != reference_task.duration:
            tasks_data_conditional_style.append({'if': {'column_id': 'duration', 'row_index': row_index},
                                                 'backgroundColor': 'dodgerblue', 'color': 'white'})
    return tasks_data_conditional_style


def build_tasks_data_table(instance: Instance, is_current_instance: bool,
                           instance_to_compare_with: Instance = None, editable: bool = False,
                           language: str = LANGUAGE_ENGLISH_KEY):
    table_id = "editable" if editable else ("current" if is_current_instance else "other")
    table_id += '-instance-tasks-data-table'
    data = build_tasks_data(instance, language)
    if check_if_language_is_english(language):
        columns = [{'name': 'Id', 'id': 'name'}, {'name': 'Skill level', 'id': 'level'},
                   {'name': 'Earliest start time', 'id': 'start', 'editable': editable},
                   {'name': 'Latest end time', 'id': 'end', 'editable': editable},
                   {'name': 'Duration (min)', 'id': 'duration', 'editable': editable}]
    elif check_if_language_is_french(language):
        columns = [{'name': 'Id', 'id': 'name'}, {'name': 'Niveau', 'id': 'level'},
                   {'name': 'Début de dispo.', 'id': 'start', 'editable': editable},
                   {'name': 'Fin de dispo.', 'id': 'end', 'editable': editable},
                   {'name': 'Durée (min)', 'id': 'duration', 'editable': editable}]
    else:
        raise ValueError(f"Language {language} is not supported.")
    style_data_conditional = \
        build_tasks_style_data_conditional(data, instance_to_compare_with) if not is_current_instance else None
    table = dash_table.DataTable(
        id=table_id, data=data, columns=columns, style_as_list_view=True,
        style_header=UI_TABLE_STYLE_HEADER, style_data=UI_TABLE_STYLE_DATA,
        style_cell_conditional=[{'if': {'column_id': 'name'}, 'width': '20%'},
                                {'if': {'column_id': 'level'}, 'width': '20%'},
                                {'if': {'column_id': 'start'}, 'width': '20%'},
                                {'if': {'column_id': 'end'}, 'width': '20%'},
                                {'if': {'column_id': 'duration'}, 'width': '20%'}],
        style_table={'max-height': 400, 'overflowY': 'scroll'},
        style_data_conditional=style_data_conditional
    )
    return table
