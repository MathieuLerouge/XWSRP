# Third-party libraries
from dash import dcc, html

# Local libraries
from src.explaining.interacting.explainer import check_if_language_is_french
from src.explaining.interacting.interface.figures import build_routes_figure, build_schedules_figure, \
    build_instance_metrics_figures, build_solution_metrics_figures
from src.explaining.interacting.interface.tables import build_tasks_data_table, build_employees_data_table
from src.explaining.interacting.interface.tools import convert_from_string_to_html
from src.explaining.transforming.infeasibility import Infeasibility
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.utils.constants import LINE_BREAK_STRING
from src.utils.language import LANGUAGE_ENGLISH_KEY, check_if_language_is_english


def build_panel_banner(panel_title: str):
    """
    Build the banner of a typical panel.
    """
    return html.Div(className="panel-banner", children=panel_title)


def build_text_panel(panel_title: str, panel_text: str, bottom_margin: bool = False):
    """
    Build a panel containing a text
    NB: the text is converted from a string to HTML, so string line breaks are converted to HTML line breaks

    :param panel_title: the title of the panel (str)
    :param panel_text: the text to display (str)
    :param bottom_margin: whether to add a bottom margin to the panel (bool)
    :return: the panel (html.Div)
    """
    if bottom_margin:
        class_name = 'panel-with-bottom-margin'
    else:
        class_name = 'panel'
    panel_text = convert_from_string_to_html(panel_text.removesuffix(f"{LINE_BREAK_STRING}"))
    panel = html.Div(
        className=class_name,
        children=[
            build_panel_banner(panel_title),
            html.Div(className='text', children=panel_text, style=dict(padding='1rem'))
        ]
    )
    return panel


def build_employees_data_panel(instance: Instance, is_current_instance: bool,
                               instance_to_compare_with: Instance = None, panel_title: str = "Employees data",
                               panel_title_prefix: str = "", panel_title_suffix: str = "", bottom_margin: bool = False,
                               editable: bool = False, language: str = LANGUAGE_ENGLISH_KEY):
    """
    Build a panel containing a table with data about the employees.
    """
    if panel_title == "Employees data":
        if check_if_language_is_french(language):
            panel_title = "Données relatives aux employés"
    panel_title = panel_title_prefix + panel_title + panel_title_suffix
    if bottom_margin:
        class_name = 'panel-with-bottom-margin'
    else:
        class_name = 'panel'
    panel = html.Div(
        id="employees-panel", className=class_name,
        children=[
            build_panel_banner(panel_title),
            build_employees_data_table(instance, is_current_instance, instance_to_compare_with, editable, language)
        ]
    )
    return panel


def build_tasks_data_panel(instance: Instance, is_current_instance: bool,
                           instance_to_compare_with: Instance = None, panel_title: str = "Tasks data",
                           panel_title_prefix: str = "", panel_title_suffix: str = "", bottom_margin: bool = False,
                           editable: bool = False, language: str = LANGUAGE_ENGLISH_KEY):
    """
    Build a panel containing a table with data about the tasks.
    """
    if panel_title == "Tasks data":
        if check_if_language_is_french(language):
            panel_title = "Données relatives aux tâches"
    panel_title = panel_title_prefix + panel_title + panel_title_suffix
    if bottom_margin:
        class_name = 'panel-with-bottom-margin'
    else:
        class_name = 'panel'
    panel = html.Div(
        id="tasks-panel", className=class_name,
        children=[
            build_panel_banner(panel_title),
            build_tasks_data_table(instance, is_current_instance, instance_to_compare_with, editable, language)
        ]
    )
    return panel


def build_routes_figure_panel(solution: Solution, is_current_solution: bool, panel_title: str = "Employees' routes",
                              panel_title_prefix: str = "", panel_title_suffix: str = "",
                              infeasibility: Infeasibility = None, language: str = LANGUAGE_ENGLISH_KEY):
    """
    Build a panel containing a map of the employees' routes for a given solution.
    """
    if panel_title == "Employees' routes":
        if check_if_language_is_french(language):
            panel_title = "Itinéraires des employés"
    panel_title = panel_title_prefix + panel_title + panel_title_suffix
    panel = html.Div(
        className='panel',
        children=[
            build_panel_banner(panel_title),
            dcc.Graph(id=f"{'current' if is_current_solution else 'other'}-solution-spatial-representation",
                      className='spatial-representation', style=dict(padding='1rem 0rem 0rem 0rem'),
                      figure=build_routes_figure(solution=solution, infeasibility=infeasibility, language=language),
                      config={'modeBarButtonsToRemove': ['zoom', 'pan', 'select', 'lasso', 'zoomIn', 'zoomOut'],
                              'displaylogo': False})
        ]
    )
    return panel


def build_schedules_figure_panel(solution: Solution, is_current_solution: bool,
                                 panel_title: str = "Employees' schedules",
                                 panel_title_prefix: str = "", panel_title_suffix: str = "",
                                 infeasibility: Infeasibility = None, language: str = LANGUAGE_ENGLISH_KEY):
    """
    Build a panel containing a gantt chart of the employees' schedules for a given solution.
    """
    if panel_title == "Employees' schedules":
        if check_if_language_is_french(language):
            panel_title = "Emplois du temps des employés"
    panel_title = panel_title_prefix + panel_title + panel_title_suffix
    panel = html.Div(
        className='panel',
        children=[
            build_panel_banner(panel_title),
            dcc.Graph(id=f"{'current' if is_current_solution else 'other'}-solution-temporal-representation",
                      className="temporal-representation", style=dict(padding='1rem 0rem 1rem 0rem'),
                      figure=build_schedules_figure(solution=solution, infeasibility=infeasibility, language=language),
                      config={'modeBarButtonsToRemove': ['zoom', 'pan', 'select', 'lasso', 'zoomIn', 'zoomOut',
                                                         'autoScale'],
                              'displaylogo': False})
        ]
    )
    return panel


def build_instance_metrics_panel(instance: Instance, is_current_instance: bool,
                                 instance_to_compare_with: Instance = None, panel_title: str = "Metrics",
                                 panel_title_prefix: str = "", bottom_margin: bool = False,
                                 horizontal: bool = True, language: str = LANGUAGE_ENGLISH_KEY):
    """
    Build a panel containing some metrics data about the instance.
    """
    if panel_title == "Metrics":
        if check_if_language_is_french(language):
            panel_title = "Métriques"
    panel_title = panel_title_prefix + panel_title
    if bottom_margin:
        class_name = 'panel-with-bottom-margin'
    else:
        class_name = 'panel'
    panel = html.Div(
        className=class_name,
        children=[
            build_panel_banner(panel_title),
            dcc.Graph(id=f"{'horizontal' if horizontal else 'two-by-two'}-"
                         f"{'current' if is_current_instance else 'other'}-instance-metrics-figures",
                      figure=build_instance_metrics_figures(instance, instance_to_compare_with, horizontal, language),
                      config={'displayModeBar': False})
        ]
    )
    return panel


def build_solution_metrics_panel(solution: Solution = None, is_current_solution: bool = True,
                                 solution_to_compare_with: Solution = None,
                                 panel_title: str = "Metrics", panel_title_prefix: str = "",
                                 with_description: bool = False,
                                 horizontal: bool = True, language: str = LANGUAGE_ENGLISH_KEY):
    """
    Build a panel containing a figure with metrics about the solution.
    """
    if panel_title == "Metrics":
        if check_if_language_is_french(language):
            panel_title = "Métriques"
    panel_title = panel_title_prefix + panel_title
    if check_if_language_is_english(language):
        description_text = f"We compare solutions based on two objectives. " \
                           f"{LINE_BREAK_STRING}" \
                           f"• First, " \
                           f"we consider that the greater the total duration of employees' work is, " \
                           f"the better the solution is. " \
                           f"{LINE_BREAK_STRING}" \
                           f"• Then, " \
                           f"if several solutions have the same total working duration, " \
                           f"then the smaller the total duration of employees' travel is, " \
                           f"the better the solution is. " \
                           f"{LINE_BREAK_STRING}"
    elif check_if_language_is_french(language):
        description_text = f"Nous comparons les solutions entre elles sur la base de deux objectifs. " \
                           f"{LINE_BREAK_STRING}" \
                           f"• D'abord, " \
                           f"nous considérons que plus la durée totale de travail des employés est grande, " \
                           f"meilleure est la solution. " \
                           f"{LINE_BREAK_STRING}" \
                           f"• Puis, " \
                           f"si plusieurs solutions ont les mêmes durées totales de travail des employés, " \
                           f"alors plus la durée totale de déplacement des employés est petite, " \
                           f"meilleure est la solution. " \
                           f"{LINE_BREAK_STRING}"
    else:
        raise ValueError(f"Unknown language: {language}")
    description_text = convert_from_string_to_html(description_text)
    children = [build_panel_banner(panel_title)]
    if with_description:
        children.append(html.Div(className='text', children=description_text, style=dict(padding='1rem')))
    children.append(
        dcc.Graph(id=f"{'horizontal' if horizontal else 'two-by-two'}-"
                     f"{'current' if is_current_solution else 'other'}-solution-metrics-figures",
                  figure=build_solution_metrics_figures(solution, solution_to_compare_with, horizontal, language),
                  config={'displayModeBar': False})
    )
    panel = html.Div(className='panel', children=children)
    return panel
