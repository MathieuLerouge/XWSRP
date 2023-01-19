# Third-party libraries
from dash import dash_table

# Local libraries
from src.utils.language import check_if_language_is_english, check_if_language_is_french
from src.explaining.interacting.interface.assets.styles import UI_TABLE_STYLE_HEADER, UI_TABLE_STYLE_DATA, \
    UI_TABLE_CELL_BACKGROUND_COLOR_BIS
from src.modeling.instance import Instance
from src.utils.language import LANGUAGE_ENGLISH_KEY
from src.utils.time import convert_time_string_to_nb_minutes, get_hour_format_associated_with_language


def build_employees_data(instance: Instance, language: str = LANGUAGE_ENGLISH_KEY):
    """
    Builds the data to display in the employees data table

    :param instance: the instance (Instance)
    :param language: the language (str) (default: English)
    :return: the data to display in the employees data table (list of dict)
    """
    hour_format = get_hour_format_associated_with_language(language)
    return [dict(name=employee.name, level=employee.skill_level,
                 start=employee.get_start_time_LB(False, hour_format), end=employee.get_end_time_UB(False, hour_format))
            for employee in instance.employees]


def build_employees_data_conditional_style(employees_data, reference_instance: Instance):
    """
    Builds the conditional style to apply to the employees data table

    :param employees_data: the employees data (list of dict)
    :param reference_instance: the reference instance (Instance)
    :return: the conditional style to apply to the employees data table (list of dict)
    """
    employees_data_conditional_style = \
        [{'if': {'row_index': 'odd'}, 'backgroundColor': UI_TABLE_CELL_BACKGROUND_COLOR_BIS}]
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
    """
    Builds the employees data table

    :param instance: the instance (Instance)
    :param is_current_instance: whether the instance is the current instance (bool)
    :param instance_to_compare_with: the instance to compare with (Instance) (default: None)
    :param editable: whether the table is editable (bool) (default: False)
    :param language: the language used (str) (default: English)
    :return: the employees data table (dash_table.DataTable)
    """
    table_id = "editable" if editable else ("current" if is_current_instance else "other")
    table_id += "-instance-employees-data-table"
    data = build_employees_data(instance, language)
    if is_current_instance:
        data_conditional_style = [{'if': {'row_index': 'odd'}, 'backgroundColor': UI_TABLE_CELL_BACKGROUND_COLOR_BIS}]
    else:
        data_conditional_style = build_employees_data_conditional_style(data, instance_to_compare_with)
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
    """
    Builds the data to display in the tasks data table

    :param instance: the instance (Instance)
    :param language: the language (str) (default: English)
    :return: the data to display in the tasks data table (list of dict)
    """
    hour_format = get_hour_format_associated_with_language(language)
    return [dict(name=task.name, level=task.skill_level, duration=task.duration,
                 start=task.get_start_time_LB(False, hour_format), end=task.get_end_time_UB(False, hour_format))
            for task in instance.tasks]


def build_tasks_data_conditional_style(tasks_data, reference_instance: Instance):
    """
    Builds the conditional style to apply to the tasks data table

    :param tasks_data: the tasks data (list of dict)
    :param reference_instance: the reference instance (Instance)
    :return: the conditional style to apply to the tasks data table (list of dict)
    """
    tasks_data_conditional_style = [{'if': {'row_index': 'odd'}, 'backgroundColor': UI_TABLE_CELL_BACKGROUND_COLOR_BIS}]
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
    """
    Builds the tasks data table

    :param instance: the instance (Instance)
    :param is_current_instance: whether the instance is the current instance (bool)
    :param instance_to_compare_with: the instance to compare with (Instance) (default: None)
    :param editable: whether the table is editable (bool) (default: False)
    :param language: the language used (str) (default: English)
    :return: the tasks data table (dash_table.DataTable)
    """
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
    if is_current_instance:
        data_conditional_style = [{'if': {'row_index': 'odd'}, 'backgroundColor': UI_TABLE_CELL_BACKGROUND_COLOR_BIS}]
    else:
        data_conditional_style = build_tasks_data_conditional_style(data, instance_to_compare_with)
    table = dash_table.DataTable(
        id=table_id, data=data, columns=columns, style_as_list_view=True,
        style_header=UI_TABLE_STYLE_HEADER, style_data=UI_TABLE_STYLE_DATA,
        style_cell_conditional=[{'if': {'column_id': 'name'}, 'width': '20%'},
                                {'if': {'column_id': 'level'}, 'width': '20%'},
                                {'if': {'column_id': 'start'}, 'width': '20%'},
                                {'if': {'column_id': 'end'}, 'width': '20%'},
                                {'if': {'column_id': 'duration'}, 'width': '20%'}],
        style_table={'max-height': 400, 'overflowY': 'scroll'},
        style_data_conditional=data_conditional_style
    )
    return table
