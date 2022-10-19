# Standard libraries
import pathlib

# Third-party libraries
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import matplotlib.colors as predefined_colors
import numpy as np
import plotly.express as px
import plotly.graph_objs as go

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.questioning.questions_templates_bank import *
from src.explaining.interacting.explainer import Explainer
from src.explaining.transforming.infeasibility import Infeasibility, TimeInfeasibility
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.modeling.task import Task
from src.utils.constants import LINE_BREAK_STRING
from src.utils.time import convert_nb_minutes_to_time_string, convert_time_string_to_nb_minutes


####################
# Global functions #
####################

def convert_from_string_to_html(text: str):
    paragraphs = text.split(LINE_BREAK_STRING)
    html_text = []
    for paragraph in paragraphs[:-1]:
        html_text.append(paragraph)
        html_text.append(html.Br())
    html_text.append(paragraphs[-1])
    return html_text


def create_home_description_in_schedules_figure(activity: Activity, time_as_string: str):
    if isinstance(activity, Departure):
        text_first_line = "Leaving home"
    elif isinstance(activity, ComeBack):
        text_first_line = "Returning home"
    else:
        raise TypeError(f"The activity {activity} must either a Departure or a ComeBack")
    return (f"<b>{text_first_line}</b><br>"
            f"Time: <b>{time_as_string}</b><br>"
            f"---<br>"
            f"WH: {activity.employee.TW}<br>")


def create_task_description_in_schedules_figure(task: Task, start_time_as_string: str, end_time_as_string: str):
    return (f"<b>{task.name}</b><br>"
            f"Start time: <b>{start_time_as_string}</b><br>"
            f"End time: <b>{end_time_as_string}</b><br>"
            f"---<br>"
            f"Duration: {task.get_duration(as_integer=False)}<br>"
            f"ATW: {task.TWs}<br>")


def create_task_description_in_routes_figure(task: Task, is_performed: bool = None):
    if is_performed is None:
        text = (f"<b>{task.name}</b><br>"
                f"Skill level: {task.skill_level}<br>"
                f"Duration: {task.get_duration(as_integer=False)}<br>"
                f"ATW: {task.TWs}<br>")
    elif is_performed:
        text = (f"<b>{task.name}</b> <br>"
                f"Skill level: {task.skill_level}")
    else:
        text = (f"<b>{task.name}</b><br>"
                f"Non-performed<br>"
                f"---<br>"
                f"Skill level: {task.skill_level}<br>"
                f"Duration: {task.get_duration(as_integer=False)}<br>"
                f"ATW: {task.TWs}<br>")
    return text


#########################
# Class ExplainerWebGUI #
#########################

class ExplainerWebGUI:

    ####################
    # Fixed parameters #
    ####################

    # Questions parameters
    # Note: only the questions which keys are part of the list below will be available to the end-user
    _questions_templates_ids = [
        WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
        WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3
    ]

    # Assets-related parameters
    _assets_path = str(pathlib.Path(__file__).parent.resolve()) + '/assets'

    # Style parameters
    # Note: these style parameters must coincide with their corresponding parameters in the .css file about style
    _body_background_color = '#111111'
    _font_color = '#f3f5f4'
    _top_banner_color = '#194572'
    _panel_banner_color = '#353535'
    _panel_content_color = '#252525'
    _line_color = '#4B5460'
    _table_style_data = {'padding-left': '10px', 'border': f'1px solid {_line_color}',
                         'backgroundColor': _body_background_color, 'hover': 'transparent',
                         'color': _font_color, 'textAlign': 'left', 'font-family': 'sans-serif', 'fontSize': 14}
    _table_style_header = {'padding-left': '10px', 'border': f'1px solid {_line_color}',
                           'backgroundColor': _panel_content_color,
                           'color': _font_color, 'textAlign': 'left', 'font-family': 'sans-serif', 'fontSize': 14}
    _conflict_task_color = predefined_colors.TABLEAU_COLORS['tab:red']
    _conflict_bound_color = predefined_colors.CSS4_COLORS['firebrick']

    def __init__(self, explainer: Explainer):

        #######################
        # Variable parameters #
        #######################

        # Explainer
        self._explainer = explainer
        self._questions_templates = dict([(id, QUESTIONS_TEMPLATES[id]) for id in self._questions_templates_ids])
        self._scenario_instance_alterations = InstanceChanges()
        self._counterfactual_instance_alterations = None

        # Dash application
        self._application = dash.Dash(name="XWSRP", assets_folder=self._assets_path, suppress_callback_exceptions=True)

        ##########
        # Layout #
        ##########

        def _build_layout():
            """
            Build the layout of the GUI: the banner at the top of the GUI and the layout underneath which is made of
            a vertical bar of navigation tabs on the left and the content of the selected tab on the right.
            """
            return html.Div(
                id="main-container",
                children=[
                    _build_title_banner(), _build_explorer_banner(),
                    html.Div(id="sub-banner-layout", children=[_build_navigation_tabs(), html.Div(id="tab-content")]),
                ],
            )

        ################
        # Title banner #
        ################

        def _build_title_banner():
            """
            Build the title banner at the top of the GUI.
            """
            banner = html.Div(
                id="title-banner",
                children=[
                    html.Div(
                        id="title-banner-text",
                        children=[
                            html.H5("XWSRP"),
                            html.H6("Explainer of Workforce Scheduling and Routing Problem solutions"),
                        ],
                    ),
                    html.Div(
                        id="title-banner-logo",
                        children=[
                            html.A(
                                html.Img(id="MICS-logo", src=self._application.get_asset_url("MICS_logo_white.png")),
                                href="http://www.mics.centralesupelec.fr/", target="_blank"
                            ),
                            html.A(
                                html.Img(id="CS-logo", src=self._application.get_asset_url("CS_logo.png")),
                                href="https://www.centralesupelec.fr/", target="_blank"
                            ),
                            html.A(
                                html.Img(id="DB-logo", src=self._application.get_asset_url("DB_logo.png")),
                                href="https://decisionbrain.com/", target="_blank"
                            ),
                        ],
                    ),
                ],
            )
            return banner

        ############
        # Explorer #
        ############

        def _build_explorer_banner():
            """
            Build the banner allowing the end-user to choose the current instance and the current solution.
            """
            current_instance_dropdown = dcc.Dropdown(
                id='current-instance-dropdown', className='dropdown', style=dict(flex=1, marginRight='10px'),
                options=[{'label': instance_name, 'value': instance_name}
                         for instance_name in self._explainer.instances_names],
                value=self.current_instance.name, placeholder="Select current instance", clearable=False
            )
            current_solution_dropdown = dcc.Dropdown(
                id='current-solution-dropdown', className='dropdown', style=dict(flex=1, marginRight='10px'),
                options=[{'label': solution.name, 'value': solution.name}
                         for solution in self._explainer.get_solutions_of_instance(self.current_instance)],
                value=self.current_solution.name, placeholder="Select current solution", clearable=False
            )
            explorer_banner = html.Div(
                id="explorer-banner",
                children=[
                    html.Div(id='explorer-banner-title', children="Instance - solution explorer"),
                    html.Div(style=dict(display='flex', flexdirection='row', flex=1),
                             children=[current_instance_dropdown, current_solution_dropdown])
                ]
            )
            return explorer_banner

        @self._application.callback(
            Output('current-instance-dropdown', 'options'),
            Input('current-instance-dropdown', 'disabled'),
            State('current-instance-dropdown', 'options')
        )
        def _update_current_instance_dropdown_options(current_instance_dropdown_disabled: bool,
                                                      current_instances_options):
            if current_instance_dropdown_disabled:
                raise PreventUpdate
            else:
                if len(current_instances_options) == len(self._explainer.instances_names):
                    raise PreventUpdate
                else:
                    return [{'label': instance_name, 'value': instance_name}
                            for instance_name in self._explainer.instances_names]

        @self._application.callback(
            Output('current-solution-dropdown', 'disabled'),
            Input('current-instance-dropdown', 'disabled')
        )
        def _update_current_solution_dropdown_status(current_instance_dropdown_disabled: bool):
            if current_instance_dropdown_disabled:
                return True
            else:
                return False

        @self._application.callback(
            Output('current-solution-dropdown', 'options'),
            Input('current-solution-dropdown', 'disabled'), Input('current-instance-dropdown', 'value'),
            State('current-solution-dropdown', 'options')
        )
        def _update_current_solution_dropdown_options(current_solution_dropdown_disabled: bool,
                                                      current_instance_name: str, current_solutions_options):
            if current_solution_dropdown_disabled:
                raise PreventUpdate
            else:
                solutions = self._explainer.get_solutions_of_instance_by_name(current_instance_name)
                if (current_instance_name == self.current_instance.name and
                        len(current_solutions_options) == len(solutions)):
                    raise PreventUpdate
                else:
                    return [{'label': solution.name, 'value': solution.name} for solution in solutions]

        @self._application.callback(
            Output('current-solution-dropdown', 'value'),
            Input('current-solution-dropdown', 'options'),
            State('current-solution-dropdown', 'value')
        )
        def _update_current_solution_dropdown_value(current_solutions_options, current_solution_name: str):
            if current_solution_name in [option['value'] for option in current_solutions_options]:
                raise PreventUpdate
            else:
                return current_solutions_options[0]['value']

        ##############
        # Navigation #
        ##############

        def _build_navigation_tabs():
            """
            Build the navigation tabs on the left of the GUI.
            """
            navigation = html.Div(
                id="navigation-left-panel",
                children=[
                    dcc.Tabs(
                        id="tabs-list", parent_className='tabs-buttons', vertical=True, value="explainer-tab",
                        children=[
                            dcc.Tab(id="instance-description-tab", className="tab-button",
                                    label="Instance description", value="instance-description-tab",
                                    selected_className="tab-button--selected"),
                            dcc.Tab(id="instances-comparison-tab", className="tab-button",
                                    label="Instances comparison", value="instances-comparison-tab",
                                    selected_className="tab-button--selected"),
                            dcc.Tab(id="solution-description-tab", className="tab-button",
                                    label="Solution description", value="solution-description-tab",
                                    selected_className="tab-button--selected"),
                            dcc.Tab(id="solutions-comparison-tab", className="tab-button",
                                    label="Solutions comparison", value="solutions-comparison-tab",
                                    selected_className="tab-button--selected"),
                            dcc.Tab(id="explainer-tab", className="tab-button",
                                    label="Explainer", value="explainer-tab",
                                    selected_className="tab-button--selected")
                        ],
                    )
                ],
            )
            return navigation

        @self._application.callback(
            Output('tab-content', 'children'),
            Input('tabs-list', 'value'), Input('current-solution-dropdown', 'value')
        )
        def _react_to_tab_selection(tab_value: str, current_solution_name: str):
            """
            React to the selection of a tab by the end-user by building the content corresponding to the selected tab.
            """
            if current_solution_name != self.current_solution.name:
                self.current_solution = self._explainer.get_solution_by_name(current_solution_name)
            if tab_value == "instance-description-tab":
                return _build_instance_description_tab_content()
            elif tab_value == "instances-comparison-tab":
                return _build_instance_comparison_tab_content()
            elif tab_value == "solution-description-tab":
                return _build_solution_description_tab_content()
            elif tab_value == "solutions-comparison-tab":
                return _build_solution_comparison_tab_content()
            elif tab_value == "explainer-tab":
                return _build_question_explanation_tab_content()
            else:
                raise ValueError(f"GUI Error: There is no {tab_value} tab.")

        ####################################
        # Instance description tab content #
        ####################################

        def _build_instance_description_tab_content():
            """
            Build the tab content about the description of the instance.
            By default, the instance that is described is the instance of the current solution.
            """
            instance = self.current_instance
            tab_content = html.Div(
                id="instance-description-tab-content",
                children=[
                    _build_instance_metrics_panel(), _build_employees_data_panel(), _build_tasks_data_panel(),
                    html.Div(
                        className="representation-panels-side-to-side",
                        children=[
                            html.Div(
                                className='panel',
                                children=[
                                    _build_panel_banner("Employees' locations"),
                                    dcc.Graph(
                                        id=f"employees-spatial-representation", className="spatial-representation",
                                        figure=_build_map_figure(instance=instance, mode='employees'))
                                ],
                            ),
                            html.Div(
                                className='panel',
                                children=[
                                    _build_panel_banner("Tasks' locations"),
                                    dcc.Graph(
                                        id=f"tasks-spatial-representation", className="spatial-representation",
                                        figure=_build_map_figure(instance=instance, mode='tasks'))
                                ],
                            )
                        ]
                    )
                ]
            )
            return tab_content

        ###################################
        # Instance comparison tab content #
        ###################################

        def _build_instance_comparison_tab_content():
            """
            Build the tab content about the comparison of two instances.
            One of the instance is the current one, the other can be selected by the end-user.
            """

            current_instance = self.current_instance
            other_instance = current_instance

            def _build_other_instance_dropdown():
                """
                Build a dropdown so that the end-user can select an instance to compare with the current one.
                """
                dropdown = dcc.Dropdown(
                    id='other-instance-dropdown', className='dropdown',
                    options=[{'label': instance_name, 'value': instance_name}
                             for instance_name in self._explainer.instances_names],
                    value=other_instance.name, placeholder="Select other solution", clearable=False
                )
                return dropdown

            def _build_instance_name_panel(enable_other_instance: bool = False):
                """
                Build a panel with
                - if the selection of another instance is disabled, the name of the current instance;
                - else, a dropdown for selecting another instance to compare with the current one.
                """
                panel_title = f"{'Other' if enable_other_instance else 'Current'} instance"
                line = _build_other_instance_dropdown() if enable_other_instance else \
                    html.Div(className='automated-text', style=dict(flex=1), children=current_instance.name)
                panel = html.Div(
                    className='panel',
                    children=[_build_panel_banner(panel_title), html.Div(className='panel-content', children=line)]
                )
                return panel

            tab_content = html.Div(
                id="instances-comparison-tab-content",
                children=[
                    html.Div(
                        className="panels-side-to-side",
                        children=[_build_instance_name_panel(), _build_instance_name_panel(enable_other_instance=True)]
                    ),
                    html.Div(
                        className="panels-side-to-side",
                        children=[_build_employees_data_panel(), _build_employees_data_panel(instance=other_instance)]
                    ),
                    html.Div(
                        className="panels-side-to-side",
                        children=[_build_tasks_data_panel(), _build_tasks_data_panel(instance=other_instance)]
                    ),
                    html.Div(
                        className="panels-side-to-side",
                        children=[
                            _build_instance_metrics_panel(panel_title="Current instance - Metrics", horizontal=False),
                            _build_instance_metrics_panel(panel_title="Other instance - Metrics", horizontal=False,
                                                          instance=other_instance)
                        ]
                    )
                ]
            )
            return tab_content

        @self._application.callback(
            Output('other-instance-employees-data-table', 'data'),
            Output('other-instance-employees-data-table', 'style_data_conditional'),
            Output('other-instance-tasks-data-table', 'data'),
            Output('other-instance-tasks-data-table', 'style_data_conditional'),
            Output('two-by-two-other-instance-metrics-figures', 'figure'),
            Input('other-instance-dropdown', 'value')
        )
        def _react_to_other_instance_dropdown_selection(other_instance_name: str):
            """
            React to the selection by the end-user of another instance to compare with the current instance
            by updating the figures about the other instance.
            """
            current_instance = self.current_instance
            other_instance = self._explainer.get_instance_by_name(other_instance_name)
            employees_data = _build_employees_data(other_instance)
            employees_style_data_conditional = _build_employees_style_data_conditional(employees_data, current_instance)
            tasks_data = _build_tasks_data(other_instance)
            tasks_style_data_conditional = _build_tasks_style_data_conditional(tasks_data, current_instance)
            return (employees_data, employees_style_data_conditional, tasks_data, tasks_style_data_conditional,
                    _build_instance_metrics_figures(instance=other_instance, reference_instance=current_instance,
                                                    horizontal=False))

        ####################################
        # Solution description tab content #
        ####################################

        def _build_solution_description_tab_content():
            """
            Build the tab content about the description of a solution.
            By default, the solution that is described is the current solution.
            """
            tab_content = html.Div(
                id="solution-description-tab-content",
                children=[
                    html.Div(
                        className="representation-panels-side-to-side",
                        children=[_build_routes_figure_panel(), _build_schedules_figure_panel()]
                    ),
                    _build_solution_metrics_panel()
                ]
            )
            return tab_content

        ###################################
        # Solution comparison tab content #
        ###################################

        def _build_solution_comparison_tab_content():
            """
            Build the tab content about the comparison of two solutions of the same instance.
            One of the solution is the current solution, the other can be selected by the end-user.
            """

            current_solution = self.current_solution
            other_solution = current_solution
            instance = current_solution.instance

            def _build_other_solution_dropdown():
                """
                Build a dropdown so that the end-user can select solution to compare with the current one.
                """
                dropdown = dcc.Dropdown(
                    id='other-solution-dropdown', className='dropdown',
                    options=[{'label': solution.name, 'value': solution.name}
                             for solution in self._explainer.get_solutions_of_instance(instance)],
                    value=other_solution.name, placeholder="Select other solution", clearable=False
                )
                return dropdown

            def _build_solution_name_panel(enable_other_solution: bool = False):
                """
                Build a panel with the name of the current instance and
                - if the selection of another solution is disabled, the name of the current solution itself;
                - else, a dropdown for selecting another solution to compare with the current one.
                """
                panel_title = f"{'Other' if enable_other_solution else 'Current'} solution"
                first_line = html.Div(className='automated-text', style=dict(flex=1, margin='0rem 0rem 1rem 0rem'),
                                      children=instance.name)
                second_line = _build_other_solution_dropdown() if enable_other_solution else \
                    html.Div(className='automated-text', style=dict(flex=1), children=current_solution.name)
                panel = html.Div(
                    className='panel',
                    children=[_build_panel_banner(panel_title),
                              html.Div(className='panel-content', children=[first_line, second_line])]
                )
                return panel

            tab_content = html.Div(
                id="solutions-comparison-tab-content",
                children=[
                    html.Div(
                        className="panels-side-to-side",
                        children=[_build_solution_name_panel(), _build_solution_name_panel(enable_other_solution=True)]
                    ),
                    html.Div(
                        className="representation-panels-side-to-side",
                        children=[
                            _build_routes_figure_panel(panel_title_prefix="Current solution - "),
                            _build_routes_figure_panel(panel_title_prefix="Other solution - ",
                                                       solution=other_solution)
                        ]
                    ),
                    html.Div(
                        className="representation-panels-side-to-side",
                        children=[
                            _build_schedules_figure_panel(panel_title_prefix="Current solution - "),
                            _build_schedules_figure_panel(panel_title_prefix="Other solution - ",
                                                          solution=other_solution)
                        ]
                    ),
                    html.Div(
                        className="panels-side-to-side",
                        children=[
                            _build_solution_metrics_panel(panel_title="Current solution - Metrics", horizontal=False),
                            _build_solution_metrics_panel(panel_title="Other solution - Metrics", horizontal=False,
                                                          solution=other_solution)
                        ]
                    )
                ]
            )
            return tab_content

        @self._application.callback(
            Output('other-solution-spatial-representation', 'figure'),
            Output('other-solution-temporal-representation', 'figure'),
            Output('two-by-two-other-solution-metrics-figures', 'figure'),
            Input('other-solution-dropdown', 'value')
        )
        def _react_to_other_solution_dropdown_selection(other_solution_name: str):
            """
            React to the selection by the end-user of another solution to compare with the current solution
            by updating the figures about the other solution.
            """
            current_solution = self.current_solution
            other_solution = self._explainer.get_solution_by_name(other_solution_name)
            return (
                _build_routes_figure(solution=other_solution), _build_schedules_figure(solution=other_solution),
                _build_solution_metrics_figures(solution=other_solution, reference_solution=current_solution,
                                                horizontal=False)
            )

        ##################################
        # Explainer tab content - Static #
        ##################################

        def _build_question_explanation_tab_content():
            """
            Build the tab content about the question-explanation.
            """

            #########################
            # Contrastive / Why-not #
            #########################

            def _build_contrastive_question_block():
                #
                def _build_contrastive_question_panel():
                    """
                    Build the panel allowing the end-user to submit contrastive questions.
                    """
                    first_line = html.Div(
                        style=dict(display='flex', flexdirection='row'),
                        children=[
                            dcc.Dropdown(id='template-question-dropdown', className='dropdown', style=dict(flex=1),
                                         options=[{'label': self._questions_templates[key].text,
                                                   'value': key} for key in self._questions_templates_ids],
                                         placeholder="Select a question template"),
                            dcc.Dropdown(id='template-input-1', className='dropdown',
                                         style=dict(width='15rem', paddingLeft='1rem'),
                                         placeholder="Fill input 1"),
                            dcc.Dropdown(id='template-input-2', className='dropdown',
                                         style=dict(width='15rem', paddingLeft='1rem'),
                                         placeholder="Fill input 2"),
                            dcc.Dropdown(id='template-input-3', className='dropdown',
                                         style=dict(width='15rem', paddingLeft='1rem'),
                                         placeholder="Fill input 3"),
                        ]
                    )
                    second_line = html.Div(
                        style=dict(paddingTop='1rem', display='flex', flexdirection='row'),
                        children=[
                            html.Div(id='contrastive-question-text', className='empty-automated-text',
                                     style=dict(flex=1, marginRight='1rem'),
                                     children="Waiting for the definition of a why-not question..."),
                            html.Button(id='contrastive-submit-button', className='button',
                                        children="Submit", disabled=True)
                        ]
                    )
                    panel = html.Div(
                        id="question-panel", className='panel-with-bottom-margin',
                        children=[_build_panel_banner("Why-not question"),
                                  html.Div(className='panel-content', children=[first_line, second_line])]
                    )
                    return panel

                block = html.Div(children=[
                    html.Div(className='representation-panels-side-to-side',
                             children=[_build_routes_figure_panel(panel_title_prefix="Current solution - "),
                                       _build_schedules_figure_panel(panel_title_prefix="Current solution - ")]),
                    _build_contrastive_question_panel()
                ])
                return block

            def _build_contrastive_explanation_block():
                def _build_contrastive_explanation_panel():
                    """
                    Build the panel providing to the end-user contrastive explanations.
                    """
                    buttons = [
                        html.Button(id='contrastive-ok-button', className='button', style=dict(marginBottom='1rem'),
                                    children="Ok", disabled=True),
                        html.Button(id='contrastive-save-button', className='button', style=dict(marginBottom='1rem'),
                                    children="Save", disabled=True),
                        html.Button(id='what-if-button', className='button', style=dict(marginBottom='1rem'),
                                    children="What if?", disabled=True),
                        html.Button(id='how-to-button', className='button', children="How to?", disabled=True),
                    ]
                    panel = html.Div(
                        id='contrastive-explanation-panel', className='panel-with-bottom-margin',
                        children=[
                            _build_panel_banner("Why-not explanation"),
                            html.Div(
                                className='panel-content', style=dict(display='flex', flexDirection='row'),
                                children=[
                                    html.Div(id='contrastive-explanation-text', className='empty-automated-text',
                                             style=dict(flex=1, height='20rem', marginRight='1rem'),
                                             children="Waiting for a why-not question to be submitted..."),
                                    html.Div(style=dict(display='flex', flexDirection='column',
                                                        justifyContent='flex-end'),
                                             children=buttons)
                                ]
                            )
                        ]
                    )
                    return panel

                block = html.Div(children=[
                    html.Div(id='contrastive-explanation-representation-envelope', style=dict(display='none')),
                    _build_contrastive_explanation_panel()
                ])
                return block

            ######################
            # Scenario / What-if #
            ######################

            def _build_scenario_block():
                #
                def _build_scenario_editable_employees_data_panel():
                    """
                    Build the panel allowing the end-user to edit the employees data for what-if questions.
                    """
                    panel = html.Div(
                        id='scenario-editable-employees-data-panel',
                        children=_build_employees_data_panel(panel_title="Editable employees data for what-if question",
                                                             editable=True)
                    )
                    return panel

                def _build_scenario_editable_tasks_data_panel():
                    """
                    Build the panel allowing the end-user to edit the tasks data for what-if questions.
                    """
                    panel = html.Div(
                        id='scenario-editable-tasks-data-panel',
                        children=_build_tasks_data_panel(panel_title="Editable tasks data for what-if question",
                                                         editable=True)
                    )
                    return panel

                def _build_scenario_question_panel():
                    """
                    Build the panel allowing the end-user to submit what-if questions.
                    """
                    panel = html.Div(
                        id='scenario-question-panel', className='panel-with-bottom-margin',
                        children=[
                            _build_panel_banner("What-if question"),
                            html.Div(
                                className='panel-content', style=dict(display='flex', flexdirection='row'),
                                children=[
                                    html.Div(id='scenario-question-text', className='empty-automated-text',
                                             style=dict(flex=1, alignItems='end', marginRight='1rem'),
                                             children="Waiting for the definition of a what-if question..."),
                                    html.Button(id='scenario-submit-button', className='button',
                                                children="Submit", disabled=True)
                                ]
                            )
                        ]
                    )
                    return panel

                def _build_scenario_explanation_panel():
                    """
                    Build the panel providing to the end-user what-if explanations.
                    """
                    buttons = [
                        html.Button(id='scenario-ok-button', className='button', style=dict(marginBottom='1rem'),
                                    children="Ok", disabled=True),
                        html.Button(id='scenario-save-button', className='button', children="Save", disabled=True),
                    ]
                    panel = html.Div(
                        id='scenario-explanation-panel', className='panel-with-bottom-margin',
                        children=[
                            _build_panel_banner("What-if explanation"),
                            html.Div(
                                className='panel-content', style=dict(display='flex', flexDirection='row'),
                                children=[
                                    html.Div(id='scenario-explanation-text', className='empty-automated-text',
                                             style=dict(flex=1, height='20rem', marginRight='1rem'),
                                             children="Waiting for a what-if question to be submitted..."),
                                    html.Div(
                                        style=dict(display='flex', flexDirection='column', justifyContent='flex-end'),
                                        children=buttons)
                                ]
                            )
                        ]
                    )
                    return panel
                #
                block = html.Div(id='scenario-question-block', style=dict(display='none'), children=[
                    _build_scenario_editable_employees_data_panel(),
                    _build_scenario_editable_tasks_data_panel(),
                    _build_scenario_question_panel(),
                    html.Div(id='scenario-explanation-representation-envelope', style=dict(display='none')),
                    _build_scenario_explanation_panel()
                ])
                return block

            ###########################
            # Counterfactual / How-to #
            ###########################

            def _build_how_to_block():

                # TODO: Choose alterations bounds
                # def _build_how_to_question_panel():
                #     panel = html.Div(
                #         id='how-to-question-panel', className='panel',
                #         children=[
                #             _build_panel_banner("How-to question"),
                #             html.Div(
                #                 className='panel-content', style=dict(display='flex', flexdirection='row'),
                #                 children=[
                #                     html.Div(id='how-to-question-text', className='empty-automated-text',
                #                              style=dict(flex=1, marginRight='1rem'),
                #                              children="Waiting for the definition of a how-to question..."),
                #                     html.Button(id='how-to-explain-button', className='button', children="Submit",
                #                                 disabled=False)
                #                 ]
                #             )
                #         ]
                #     )
                #     return panel

                def _build_counterfactual_explanation_panel():
                    """
                    Build the panel providing to the end-user how-to explanations.
                    """
                    buttons = [
                        html.Button(id='counterfactual-ok-button', className='button', style=dict(marginBottom='1rem'),
                                    children="Ok", disabled=True),
                        html.Button(id='counterfactual-save-button', className='button',
                                    children="Save", disabled=True),
                    ]
                    panel = html.Div(
                        id='counterfactual-explanation-panel', className='panel-with-bottom-margin',
                        children=[
                            _build_panel_banner("How-to explanation"),
                            html.Div(
                                className='panel-content', style=dict(display='flex', flexDirection='row'),
                                children=[
                                    html.Div(id='counterfactual-explanation-text', className='empty-automated-text',
                                             style=dict(flex=1, height='20rem', marginRight='1rem', overflow='scroll'),
                                             children="Waiting for a how-to question to be submitted..."),
                                    html.Div(
                                        style=dict(display='flex', flexDirection='column', justifyContent='flex-end'),
                                        children=buttons)
                                ]
                            )
                        ]
                    )
                    return panel
                #
                # TODO _build_how_to_question_panel() in children?
                block = html.Div(id='counterfactual-question-block', style=dict(display='none'),
                                 children=[
                                     html.Div(id='counterfactual-explanation-representation-envelope',
                                              style=dict(display='none')),
                                     _build_counterfactual_explanation_panel()
                                 ])
                return block

            tab_content = html.Div(
                id="explainer-tab-content",
                children=[
                    _build_contrastive_question_block(), _build_contrastive_explanation_block(),
                    _build_scenario_block(), _build_how_to_block()
                ]
            )
            return tab_content

        ##################################################
        # Explainer tab content - Callback - Contrastive #
        ##################################################

        @self._application.callback(
            Output('template-question-dropdown', 'disabled'), Output('template-question-dropdown', 'value'),
            Input('contrastive-explanation-text', 'className'), State('template-question-dropdown', 'value')
        )
        def _update_contrastive_question_dropdown_value_and_status(contrastive_explanation_text_style: str,
                                                                   question_template_id: str):
            """
            Update the status (enabled/disabled) of the contrastive template question dropdown
            based on the style (empty/non-empty automated text) of the contrastive explanation text

            :param contrastive_explanation_text_style:
            :return:
            """
            if contrastive_explanation_text_style == 'empty-automated-text':
                return False, None
            else:
                return True, question_template_id

        @self._application.callback(
            Output('template-input-1', 'disabled'), Output('template-input-1', 'value'),
            Output('template-input-2', 'disabled'), Output('template-input-2', 'value'),
            Output('template-input-3', 'disabled'), Output('template-input-3', 'value'),
            Input('template-question-dropdown', 'disabled'), Input('template-question-dropdown', 'value'),
            State('template-input-1', 'value'), State('template-input-2', 'value'), State('template-input-3', 'value')
        )
        def _update_inputs_status_and_values(questions_templates_dropdown_disabled: bool, question_template_id: str,
                                             input_1: str, input_2: str, input_3: str):
            # Case where the questions templates dropdown is empty
            if question_template_id is None:
                # All inputs must be empty and disabled
                return True, None, True, None, True, None
            # Case where the questions templates dropdown is non-empty and disabled
            # (because a contrastive question has been submitted)
            elif questions_templates_dropdown_disabled:
                return True, input_1, True, input_2, True, input_3
            # Case where the questions templates dropdown is non-empty and enabled
            # (so that the end-user can define a contrastive question)
            else:
                question_template = self._questions_templates[question_template_id]
                disabled_inputs = [(False if i < question_template.nb_fields else True) for i in range(3)]
                return disabled_inputs[0], None, disabled_inputs[1], None, disabled_inputs[2], None

        @self._application.callback(
            Output('template-input-1', 'options'), Output('template-input-2', 'options'),
            Output('template-input-3', 'options'),
            Input('template-question-dropdown', 'value'),
            Input('template-input-1', 'search_value'), Input('template-input-1', 'value'),
            State('template-input-1', 'options'),
            Input('template-input-2', 'search_value'), Input('template-input-2', 'value'),
            State('template-input-2', 'options'),
            Input('template-input-3', 'search_value'), Input('template-input-3', 'value'),
            State('template-input-3', 'options')
        )
        def _update_inputs_options(question_template_id: str,
                                   input_1_search: str, input_1_value: str, input_1_options: list[dict[str, str]],
                                   input_2_search: str, input_2_value: str, input_2_options: list[dict[str, str]],
                                   input_3_search: str, input_3_value: str, input_3_options: list[dict[str, str]]):
            # Case where the questions templates dropdown is empty
            if question_template_id is None:
                raise PreventUpdate
            # Case where the questions templates dropdown is non-empty...
            solution = self.current_solution
            question_template = self._questions_templates[question_template_id]
            relevant_inputs_search_values = \
                [input_1_search, input_2_search, input_3_search][:question_template.nb_fields]
            is_searching = not np.alltrue([value == "" for value in relevant_inputs_search_values])
            relevant_inputs_values = [input_1_value, input_2_value, input_3_value][:question_template.nb_fields]
            has_chosen_input_value = not np.alltrue([value is None for value in relevant_inputs_values])
            inputs_options = [input_1_options, input_2_options, input_3_options]
            # ... and an input value has been chosen by the end-user
            if has_chosen_input_value:
                for field_number in range(question_template.nb_fields):
                    if relevant_inputs_values[field_number] is None:
                        other_relevant_fields_values = \
                            dict([(i, value) for (i, value) in enumerate(relevant_inputs_values)
                                  if value is not None and i != field_number])
                        inputs_options[field_number] = \
                            [dict(label=value, value=value) for value in question_template.compute_field_valid_values(
                                solution, field_number, other_relevant_fields_values)]
                return inputs_options[0], inputs_options[1], inputs_options[2]
            # ... and the end-user is searching values for an input
            if is_searching:
                field_number = 0
                for i in range(question_template.nb_fields):
                    if relevant_inputs_search_values[i] != "":
                        field_number = i
                        break
                inputs_options[field_number] = [option for option in inputs_options[field_number]
                                                if relevant_inputs_search_values[field_number] in option['label']]
                return inputs_options[0], inputs_options[1], inputs_options[2]
            # ... and the value of questions templates dropdown has just been chosen by the end-user
            fields_options = []
            for field_number in range(3):
                if field_number < question_template.nb_fields:
                    fields_options.append([
                        dict(label=value, value=value)
                        for value in question_template.compute_field_valid_values(solution, field_number)
                    ])
                else:
                    fields_options.append([])
            return fields_options[0], fields_options[1], fields_options[2]

        @self._application.callback(
            Output('contrastive-question-text', 'children'), Output('contrastive-question-text', 'className'),
            Input('template-question-dropdown', 'value'),
            Input('template-input-1', 'value'), Input('template-input-2', 'value'), Input('template-input-3', 'value')
        )
        def _update_contrastive_question_text(question_template_id: str, input_1: str, input_2: str, input_3: str):
            # Case where the questions templates dropdown is empty
            if question_template_id is None:
                return "Waiting for the definition of a why-not question...", 'empty-automated-text'
            # Case where the questions templates dropdown is non-empty
            else:
                question_template = self._questions_templates[question_template_id]
                relevant_inputs = [input_1, input_2, input_3][:question_template.nb_fields]
                fields_values = dict([(i, field_value) for (i, field_value) in enumerate(relevant_inputs)
                                      if field_value is not None])
                return question_template.complete_text_with_fields_values(fields_values), 'automated-text'

        @self._application.callback(
            Output('contrastive-submit-button', 'disabled'),
            Input('template-question-dropdown', 'disabled'), State('template-question-dropdown', 'value'),
            Input('template-input-1', 'value'), Input('template-input-2', 'value'), Input('template-input-3', 'value')
        )
        def _update_contrastive_submit_button_status(template_question_disabled: bool, question_template_id: str,
                                                     input_1: str, input_2: str, input_3: str):
            # Case where the question dropdown is disabled
            if template_question_disabled:
                return True
            # Case where the question dropdown is enabled
            else:
                if question_template_id is None:
                    raise PreventUpdate
                question_template = self._questions_templates[question_template_id]
                relevant_inputs = [input_1, input_2, input_3][:question_template.nb_fields]
                fields_values = dict([(i, field_value) for (i, field_value) in enumerate(relevant_inputs)
                                      if field_value is not None])
                return len(fields_values) != question_template.nb_fields

        @self._application.callback(
            Output('contrastive-explanation-text', 'children'), Output('contrastive-explanation-text', 'className'),
            Output('contrastive-explanation-representation-envelope', 'style'),
            Output('contrastive-explanation-representation-envelope', 'children'),
            Output('contrastive-submit-button', 'n_clicks'), Output('contrastive-ok-button', 'n_clicks'),
            Output('current-instance-dropdown', 'disabled'),
            Input('contrastive-submit-button', 'n_clicks'), Input('contrastive-ok-button', 'n_clicks'),
            State('template-question-dropdown', 'value'),
            State('template-input-1', 'value'), State('template-input-2', 'value'), State('template-input-3', 'value')
        )
        def _update_contrastive_explanation_text_and_representation(
                contrastive_submit_button_click: int, contrastive_ok_button_click: int,
                question_template_id: str, input_1: str, input_2: str, input_3: str):
            if (contrastive_submit_button_click is None) and (contrastive_ok_button_click is None):
                raise PreventUpdate
            if contrastive_submit_button_click == 1:
                question_template = self._questions_templates[question_template_id]
                fields_values = [value for value in [input_1, input_2, input_3][:question_template.nb_fields]]
                explanation = self._explainer.compute_contrastive_explanation(question_template_id, fields_values)
                infeasibility = None if explanation.support_solution_is_feasible else explanation.infeasibility
                explanation_text = convert_from_string_to_html(explanation.text)
                solution = explanation.support_solution
                explanation_repr_visibility = dict(display='block')
                panel_title_prefix = f"{'Feasible' if explanation.support_solution_is_feasible else 'Infeasible'}" \
                                     f" new solution - "
                panel_title_suffix = " (for why-not explanation)"
                explanation_repr = html.Div(
                    className='representation-panels-side-to-side',
                    children=[
                        _build_routes_figure_panel(panel_title_prefix=panel_title_prefix,
                                                   panel_title_suffix=panel_title_suffix,
                                                   solution=solution, infeasibility=infeasibility),
                        _build_schedules_figure_panel(panel_title_prefix=panel_title_prefix,
                                                      panel_title_suffix=panel_title_suffix,
                                                      solution=solution, infeasibility=infeasibility)
                    ]
                )
                return (explanation_text, 'automated-text', explanation_repr_visibility, explanation_repr,
                        None, None, True)
            elif contrastive_ok_button_click == 1:
                explanation_text = "Waiting for a why-not question to be submitted..."
                return explanation_text, 'empty-automated-text', dict(display='none'), html.Div(), None, None, False
            else:
                raise NotImplementedError("There is a problem with contrastive submit button or ok button #clicks")

        @self._application.callback(
            Output('contrastive-ok-button', 'disabled'),
            Input('contrastive-explanation-text', 'className'), Input('what-if-button', 'n_clicks')
        )
        def _update_contrastive_ok_button_status(contrastive_explanation_text_style: str, what_if_button_click: int):
            if contrastive_explanation_text_style == 'empty-automated-text':
                return True
            else:
                if what_if_button_click is None:
                    return False
                elif what_if_button_click == 1:
                    return True
                else:
                    raise NotImplementedError("There is a problem with what-if buttons #clicks")

        @self._application.callback(
            Output('contrastive-save-button', 'disabled'),
            Input('contrastive-explanation-text', 'className'), Input('contrastive-save-button', 'n_clicks')
        )
        def _update_contrastive_save_button_status(contrastive_explanation_text_style: str,
                                                   contrastive_save_button_click: int):
            if contrastive_explanation_text_style == 'empty-automated-text':
                return True
            else:
                if contrastive_save_button_click is None or contrastive_save_button_click == 0:
                    if self._explainer.last_contrastive_explanation.support_solution_is_feasible:
                        return False
                    else:
                        return True
                elif contrastive_save_button_click == 1:
                    self._explainer.save_last_contrastive_support_solution()
                    return True
                else:
                    raise NotImplementedError("There is a problem with contrastive save button #clicks")

        @self._application.callback(
            Output('contrastive-save-button', 'n_clicks'),
            Input('contrastive-explanation-text', 'className'), State('contrastive-save-button', 'n_clicks')
        )
        def _reset_contrastive_save_button_click(contrastive_explanation_text_style: str,
                                                 contrastive_save_button_click: int):
            if contrastive_explanation_text_style == 'empty-automated-text':
                return None
            else:
                return contrastive_save_button_click

        @self._application.callback(
            Output('what-if-button', 'disabled'), Output('how-to-button', 'disabled'),
            Input('contrastive-explanation-text', 'className'),
            Input('what-if-button', 'n_clicks'), Input('how-to-button', 'n_clicks')
        )
        def _update_what_if_and_how_to_buttons_status(contrastive_explanation_text_style: str,
                                                      what_if_button_click: int, how_to_button_click: int):
            if contrastive_explanation_text_style == 'empty-automated-text':
                return True, True
            else:
                if what_if_button_click is None and how_to_button_click is None:
                    if self._explainer.last_contrastive_explanation.support_solution_is_feasible:
                        return True, True
                    else:
                        return False, False
                elif what_if_button_click is not None:
                    if what_if_button_click >= 1:
                        return True, True
                    else:
                        raise NotImplementedError("There is a problem with what-if buttons #clicks")
                elif how_to_button_click >= 1:
                    return True, True
                else:
                    raise NotImplementedError("There is a problem with how-to buttons #clicks")

        @self._application.callback(
            Output('what-if-button', 'n_clicks'),
            Input('scenario-ok-button', 'n_clicks')
        )
        def _reset_what_if_button_click(scenario_ok_button_click: int):
            if scenario_ok_button_click is None:
                raise PreventUpdate
            if scenario_ok_button_click == 1:
                return None
            else:
                raise NotImplementedError("There is a problem with the scenario ok button #clicks")

        @self._application.callback(
            Output('how-to-button', 'n_clicks'),
            Input('counterfactual-ok-button', 'n_clicks')
        )
        def _reset_how_to_button_click(counterfactual_ok_button_click: int):
            if counterfactual_ok_button_click is None:
                raise PreventUpdate
            if counterfactual_ok_button_click == 1:
                return None
            else:
                raise NotImplementedError("There is a problem with the scenario ok button #clicks")

        ################################################
        # Explainer tab content - Call back - Scenario #
        ################################################

        @self._application.callback(
            Output('scenario-question-block', 'style'),
            Input('what-if-button', 'n_clicks')
        )
        def _update_scenario_visibility(what_if_button_click: int):
            if what_if_button_click is None:
                return dict(display='none')
            elif what_if_button_click == 1:
                self._scenario_instance_alterations = InstanceChanges()
                return dict(display='block')
            else:
                raise NotImplementedError("There is a problem with the what-if button #clicks")

        @self._application.callback(
            Output('editable-instance-employees-data-table', 'style_data_conditional'),
            Input('editable-instance-employees-data-table', 'data')
        )
        def _update_scenario_employees_data_style(employees_data):
            return _build_employees_style_data_conditional(employees_data, self.current_instance)

        @self._application.callback(
            Output('editable-instance-tasks-data-table', 'style_data_conditional'),
            Input('editable-instance-tasks-data-table', 'data')
        )
        def _update_scenario_tasks_data_style(tasks_data):
            return _build_tasks_style_data_conditional(tasks_data, self.current_instance)

        @self._application.callback(
            Output('scenario-question-text', 'children'), Output('scenario-question-text', 'className'),
            Input('editable-instance-employees-data-table', 'data'), Input('editable-instance-tasks-data-table', 'data')
        )
        def _update_scenario_question_text(employees_data, tasks_data):
            current_instance = self.current_instance
            instance_alterations = InstanceChanges()
            for row in employees_data:
                employee = current_instance.get_employee_by_name(row['name'])
                start_time_LB = convert_time_string_to_nb_minutes(row['start'])
                end_time_UB = convert_time_string_to_nb_minutes(row['end'])
                instance_alterations.add_employee_change(
                    employee,
                    start_time_LB=(None if employee.start_time_LB == start_time_LB else start_time_LB),
                    end_time_UB=(None if employee.end_time_UB == end_time_UB else end_time_UB)
                )
            for row in tasks_data:
                task = current_instance.get_task_by_name(row['name'])
                start_time_LB = convert_time_string_to_nb_minutes(row['start'])
                end_time_UB = convert_time_string_to_nb_minutes(row['end'])
                duration = int(row['duration'])
                instance_alterations.add_task_change(
                    task,
                    start_time_LB=(None if task.start_time_LB == start_time_LB else start_time_LB),
                    end_time_UB=(None if task.end_time_UB == end_time_UB else end_time_UB),
                    duration=(None if task.duration == duration else duration)
                )
            self._scenario_instance_alterations = instance_alterations
            question_text = f"What-if the data about the tasks are changed as follows?{LINE_BREAK_STRING}" \
                            f"{instance_alterations.as_string(starting_with_uppercase=True)}"
            question_text = convert_from_string_to_html(question_text)
            return question_text, 'automated-text'

        @self._application.callback(
            Output('scenario-submit-button', 'disabled'),
            Input('scenario-question-text', 'className')
        )
        def _update_scenario_submit_button_status(scenario_question_text_style: str):
            if scenario_question_text_style == 'empty-automated-text':
                return True
            elif scenario_question_text_style == 'automated-text':
                return False
            else:
                raise NotImplementedError("There is a problem with the scenario question text style")

        @self._application.callback(
            Output('scenario-submit-button', 'n_clicks'),
            Input('scenario-question-block', 'style')
        )
        def _reset_scenario_submit_button_click(scenario_envelope_style):
            if scenario_envelope_style['display'] in ['none', 'block']:
                return None
            else:
                raise NotImplementedError("There is a problem with the scenario envelope style")

        @self._application.callback(
            Output('scenario-explanation-text', 'children'), Output('scenario-explanation-text', 'className'),
            Output('scenario-explanation-representation-envelope', 'style'),
            Output('scenario-explanation-representation-envelope', 'children'),
            Input('scenario-submit-button', 'n_clicks'), Input('scenario-ok-button', 'n_clicks'),
        )
        def _update_scenario_explanation_text(scenario_submit_click: int, scenario_ok_button_click: int):
            if scenario_submit_click is None and scenario_ok_button_click is None:
                raise PreventUpdate
            elif scenario_ok_button_click is not None:
                if scenario_submit_click >= 1:
                    explanation_text = "Waiting for a what-if question to be submitted..."
                    return explanation_text, 'empty-automated-text', dict(display='none'), html.Div()
                else:
                    raise NotImplementedError("There is a problem with the scenario ok button #clicks")
            elif scenario_submit_click >= 1:
                current_instance = self.current_instance
                scenario_instance = current_instance.copy(current_instance.name + "_scenario")
                scenario_instance.alter(self._scenario_instance_alterations)
                explanation = self._explainer.compute_scenario_explanation(scenario_instance)
                explanation_text = convert_from_string_to_html(explanation.text)
                explanation_repr_visibility = dict(display='block')
                panel_title_prefix = f"{'Feasible' if explanation.support_solution_is_feasible else 'Infeasible'}" \
                                     f" new solution - "
                panel_title_suffix = " (for what-if explanation)"
                explanation_repr = html.Div(
                    className='representation-panels-side-to-side',
                    children=[
                        _build_routes_figure_panel(panel_title_prefix=panel_title_prefix,
                                                   panel_title_suffix=panel_title_suffix,
                                                   solution=explanation.support_solution,
                                                   infeasibility=(None if explanation.support_solution_is_feasible
                                                                  else explanation.infeasibility)),
                        _build_schedules_figure_panel(panel_title_prefix=panel_title_prefix,
                                                      panel_title_suffix=panel_title_suffix,
                                                      solution=explanation.support_solution,
                                                      infeasibility=(None if explanation.support_solution_is_feasible
                                                                     else explanation.infeasibility))
                    ]
                )
                return explanation_text, 'automated-text', explanation_repr_visibility, explanation_repr
            else:
                raise NotImplementedError("There is a problem with the scenario submit button #clicks")

        @self._application.callback(
            Output('scenario-editable-employees-data-panel', 'children'),
            Output('scenario-editable-tasks-data-panel', 'children'),
            Input('scenario-ok-button', 'n_clicks')
        )
        def _reset_scenario_editable_data(scenario_ok_button_click: int):
            if scenario_ok_button_click is None or scenario_ok_button_click == 0:
                raise PreventUpdate
            elif scenario_ok_button_click == 1:
                return (_build_employees_data_panel(panel_title="Editable employees data for what-if question",
                                                    editable=True),
                        _build_tasks_data_panel(panel_title="Editable tasks data for what-if question",
                                                editable=True))
            else:
                raise NotImplementedError("There is a problem with what-if ok button #clicks")

        @self._application.callback(
            Output('scenario-ok-button', 'disabled'),
            Input('scenario-explanation-text', 'className')
        )
        def _update_scenario_ok_button_status(scenario_explanation_text_style: str):
            if scenario_explanation_text_style == 'empty-automated-text':
                return True
            else:
                return False

        @self._application.callback(
            Output('scenario-ok-button', 'n_clicks'),
            Input('scenario-question-block', 'style')
        )
        def _reset_scenario_ok_button_click(scenario_envelope_style):
            if scenario_envelope_style['display'] in ['none', 'block']:
                return None
            else:
                raise NotImplementedError("There is a problem with the scenario envelope style")

        @self._application.callback(
            Output('scenario-save-button', 'disabled'),
            Input('scenario-explanation-text', 'className'), Input('scenario-save-button', 'n_clicks')
        )
        def _update_scenario_save_button_status(scenario_explanation_text_style: str, scenario_save_button_click: int):
            if scenario_explanation_text_style == 'empty-automated-text':
                return True
            else:
                explanation = self._explainer.last_scenario_explanation
                if scenario_save_button_click is None or scenario_save_button_click == 0:
                    if explanation.support_solution_is_feasible:
                        return False
                    else:
                        return True
                elif scenario_save_button_click == 1:
                    self._explainer.save_last_scenario_support_solution()
                    return True
                else:
                    raise NotImplementedError("There is a problem with what-if save button #clicks")

        @self._application.callback(
            Output('scenario-save-button', 'n_clicks'),
            Input('scenario-explanation-text', 'className'), State('scenario-save-button', 'n_clicks')
        )
        def _reset_scenario_save_button_click(scenario_explanation_text_style: str, scenario_save_button_click: int):
            if scenario_explanation_text_style == 'empty-automated-text':
                return None
            else:
                return scenario_save_button_click

        ######################################################
        # Explainer tab content - Call back - Counterfactual #
        ######################################################

        @self._application.callback(
            Output('counterfactual-question-block', 'style'),
            Input('how-to-button', 'n_clicks')
        )
        def _update_counterfactual_visibility(how_to_button_click: int):
            if how_to_button_click is None:
                return dict(display='none')
            elif how_to_button_click == 1:
                self._counterfactual_instance_alterations = None
                return dict(display='block')
            else:
                raise NotImplementedError("There is a problem with the how-to button #clicks")

        @self._application.callback(
            Output('counterfactual-explanation-text', 'children'),
            Output('counterfactual-explanation-text', 'className'),
            Output('counterfactual-explanation-representation-envelope', 'style'),
            Output('counterfactual-explanation-representation-envelope', 'children'),
            Input('how-to-button', 'n_clicks'), Input('counterfactual-ok-button', 'n_clicks')
        )
        def _update_counterfactual_explanation_text(how_to_button_click: int, counterfactual_ok_button_click: int):
            if how_to_button_click is None and counterfactual_ok_button_click is None:
                raise PreventUpdate
            elif counterfactual_ok_button_click is not None:
                explanation_text = "Waiting for a what-if question to be submitted..."
                return explanation_text, 'empty-automated-text', dict(display='none'), html.Div()
            elif how_to_button_click >= 1:
                explanation = self._explainer.compute_counterfactual_explanation()
                explanation_text = convert_from_string_to_html(explanation.text)
                explanation_repr_visibility = dict(display='block')
                panel_title_prefix = f"{'Feasible' if explanation.support_solution_is_feasible else 'Infeasible'}" \
                                     f" new solution - "
                panel_title_suffix = " (for how-to explanation)"
                explanation_repr = html.Div(
                    className='representation-panels-side-to-side',
                    children=[
                        _build_routes_figure_panel(panel_title_prefix=panel_title_prefix,
                                                   panel_title_suffix=panel_title_suffix,
                                                   solution=explanation.support_solution),
                        _build_schedules_figure_panel(panel_title_prefix=panel_title_prefix,
                                                      panel_title_suffix=panel_title_suffix,
                                                      solution=explanation.support_solution)
                    ]
                )
                return explanation_text, 'automated-text', explanation_repr_visibility, explanation_repr
            else:
                raise NotImplementedError("There is a problem with the how-to button #clicks")

        @self._application.callback(
            Output('counterfactual-ok-button', 'disabled'),
            Input('counterfactual-explanation-text', 'className')
        )
        def _update_counterfactual_ok_button_status(counterfactual_explanation_text_style: str):
            if counterfactual_explanation_text_style == 'empty-automated-text':
                return True
            else:
                return False

        @self._application.callback(
            Output('counterfactual-ok-button', 'n_clicks'),
            Input('counterfactual-question-block', 'style')
        )
        def _reset_counterfactual_ok_button_click(counterfactual_envelope_style):
            if counterfactual_envelope_style['display'] in ['none', 'block']:
                return None
            else:
                raise NotImplementedError("There is a problem with the counterfactual envelope style")

        @self._application.callback(
            Output('counterfactual-save-button', 'disabled'),
            Input('counterfactual-explanation-text', 'className'), Input('counterfactual-save-button', 'n_clicks')
        )
        def _update_counterfactual_save_button_status(counterfactual_explanation_text_style: str,
                                                      counterfactual_save_button_click: int):
            if counterfactual_explanation_text_style == 'empty-automated-text':
                return True
            else:
                explanation = self._explainer.last_counterfactual_explanation
                if counterfactual_save_button_click is None or counterfactual_save_button_click == 0:
                    if explanation.support_solution_is_feasible:
                        return False
                    else:
                        return True
                elif counterfactual_save_button_click == 1:
                    self._explainer.save_last_counterfactual_support_solution()
                    return True
                else:
                    raise NotImplementedError("There is a problem with counterfactual save button #clicks")

        @self._application.callback(
            Output('counterfactual-save-button', 'n_clicks'),
            Input('counterfactual-explanation-text', 'className'), State('counterfactual-save-button', 'n_clicks')
        )
        def _reset_counterfactual_save_button_click(counterfactual_explanation_text_style: str,
                                                    counterfactual_save_button_click: int):
            if counterfactual_explanation_text_style == 'empty-automated-text':
                return None
            else:
                return counterfactual_save_button_click

        #######################
        # Typical data tables #
        #######################

        def _build_employees_data(instance: Instance):
            return [dict(name=employee.name, level=employee.skill_level,
                         start=employee.get_start_time_LB(as_integer=False),
                         end=employee.get_end_time_UB(as_integer=False))
                    for employee in instance.employees]

        def _build_employees_style_data_conditional(employees_data, reference_instance: Instance):
            employees_style_data_conditional = []
            for row_index, employee_data in enumerate(employees_data):
                reference_employee = reference_instance.get_employee_by_name(employee_data['name'])
                if convert_time_string_to_nb_minutes(employee_data['start']) != reference_employee.start_time_LB:
                    employees_style_data_conditional.append({'if': {'column_id': 'start', 'row_index': row_index},
                                                             'backgroundColor': 'dodgerblue', 'color': 'white'})
                if convert_time_string_to_nb_minutes(employee_data['end']) != reference_employee.end_time_UB:
                    employees_style_data_conditional.append({'if': {'column_id': 'end', 'row_index': row_index},
                                                             'backgroundColor': 'dodgerblue', 'color': 'white'})
            return employees_style_data_conditional

        def _build_employees_data_table(instance: Instance = None, editable: bool = False):
            comparison_to_reference = instance is not None
            instance_to_describe = instance if comparison_to_reference else self.current_instance
            reference_instance = self.current_instance if comparison_to_reference else None
            table_id = "editable" if editable else ("other" if comparison_to_reference else "current")
            table_id += '-instance-employees-data-table'
            data = _build_employees_data(instance_to_describe)
            style_data_conditional = (_build_employees_style_data_conditional(data, reference_instance)
                                      if comparison_to_reference else None)
            columns = [{'name': 'Name', 'id': 'name'}, {'name': 'Skill level', 'id': 'level'},
                       {'name': 'Earliest working time', 'id': 'start', 'editable': editable},
                       {'name': 'Latest working time', 'id': 'end', 'editable': editable}]
            table = dash_table.DataTable(
                id=table_id, data=data, columns=columns, style_as_list_view=True,
                style_header=self._table_style_header, style_data=self._table_style_data,
                style_cell_conditional=[{'if': {'column_id': 'name'}, 'width': '20%'},
                                        {'if': {'column_id': 'level'}, 'width': '20%'},
                                        {'if': {'column_id': 'start'}, 'width': '20%'},
                                        {'if': {'column_id': 'end'}, 'width': '40%'}],
                style_data_conditional=style_data_conditional
            )
            return table

        def _build_tasks_data(instance: Instance):
            return [dict(name=task.name, level=task.skill_level, duration=task.duration,
                         start=task.get_start_time_LB(as_integer=False), end=task.get_end_time_UB(as_integer=False))
                    for task in instance.tasks]

        def _build_tasks_style_data_conditional(tasks_data, reference_instance: Instance):
            tasks_style_data_conditional = []
            for row_index, task_data in enumerate(tasks_data):
                reference_task = reference_instance.get_task_by_name(task_data['name'])
                if convert_time_string_to_nb_minutes(task_data['start']) != reference_task.start_time_LB:
                    tasks_style_data_conditional.append({'if': {'column_id': 'start', 'row_index': row_index},
                                                         'backgroundColor': 'dodgerblue', 'color': 'white'})
                if convert_time_string_to_nb_minutes(task_data['end']) != reference_task.end_time_UB:
                    tasks_style_data_conditional.append({'if': {'column_id': 'end', 'row_index': row_index},
                                                         'backgroundColor': 'dodgerblue', 'color': 'white'})
                if int(task_data['duration']) != reference_task.duration:
                    tasks_style_data_conditional.append({'if': {'column_id': 'duration', 'row_index': row_index},
                                                         'backgroundColor': 'dodgerblue', 'color': 'white'})
            return tasks_style_data_conditional

        def _build_tasks_data_table(instance: Instance = None, editable: bool = False):
            comparison_to_reference = instance is not None
            instance_to_describe = instance if comparison_to_reference else self.current_instance
            reference_instance = self.current_instance if comparison_to_reference else None
            table_id = "editable" if editable else ("other" if comparison_to_reference else "current")
            table_id += '-instance-tasks-data-table'
            data = _build_tasks_data(instance_to_describe)
            columns = [{'name': 'Name', 'id': 'name'}, {'name': 'Skill level', 'id': 'level'},
                       {'name': 'Earliest start time', 'id': 'start', 'editable': editable},
                       {'name': 'Latest end time', 'id': 'end', 'editable': editable},
                       {'name': 'Duration (min)', 'id': 'duration', 'editable': editable}]
            style_data_conditional = \
                _build_tasks_style_data_conditional(data, reference_instance) if comparison_to_reference else None
            table = dash_table.DataTable(
                id=table_id, data=data, columns=columns, style_as_list_view=True,
                style_header=self._table_style_header, style_data=self._table_style_data,
                style_cell_conditional=[{'if': {'column_id': 'name'}, 'width': '20%'},
                                        {'if': {'column_id': 'level'}, 'width': '20%'},
                                        {'if': {'column_id': 'start'}, 'width': '20%'},
                                        {'if': {'column_id': 'end'}, 'width': '20%'},
                                        {'if': {'column_id': 'duration'}, 'width': '20%'}],
                style_table={'max-height': 400, 'overflowY': 'scroll'},
                style_data_conditional=style_data_conditional
            )
            return table

        ###################
        # Typical figures #
        ###################

        def _compute_employees_colors(instance: Instance):
            """
            Compute a list of color values that can then be associated respectively to the employees.
            """
            # See https://plotly.com/python/builtin-colorscales/ for various color scales
            # Interesting color scales: viridis from 0 to .9; agsunset from 0 to .9; sunsetdark from 0 to 1
            nb_employees = instance.nb_employees
            return px.colors.sample_colorscale('agsunset', [n / (nb_employees - 1) * .9 for n in range(nb_employees)])

        def _build_map_figure(instance: Instance, solution: Solution = None, infeasibility: Infeasibility = None,
                              mode: str = 'all'):
            """
            Build a typical map figure that be used for displaying the locations of the employees, the ones of the task
            or the routes of the employees.
            """

            def _compute_map_zoom_and_center(locations_longitudes: list[float], locations_latitudes: list[float],
                                             projection: str = 'mercator', width_to_height: float = 2.0):
                """
                Compute proper zoom and center for a plotly mapbox.

                :param locations_longitudes: list of longitudes in degrees of the locations
                :param locations_latitudes: list of latitudes in degrees of the locations
                :param projection: str, only accepting 'mercator' at the moment,
                    raises `NotImplementedError` if other is passed
                :param width_to_height: float, expected ratio of final graph's with to height,
                    used to select the constrained axis.

                :return:
                zoom: float, from 1 to 20
                center: dict, gps position with 'lon' and 'lat' keys
                """
                longitudes_max, longitudes_min = max(locations_longitudes), min(locations_longitudes)
                latitudes_max, latitudes_min = max(locations_latitudes), min(locations_latitudes)
                locations_center = {'lon': round((longitudes_max + longitudes_min) / 2, 6),
                                    'lat': round((latitudes_max + latitudes_min) / 2, 6)}
                longitude_zoom_range = np.array([
                    0.0007, 0.0014, 0.003, 0.006, 0.012, 0.024, 0.048, 0.096, 0.192, 0.3712, 0.768, 1.536,
                    3.072, 6.144, 11.8784, 23.7568, 47.5136, 98.304, 190.0544, 360.0
                ])
                if projection == 'mercator':
                    margin = 3  # 1.2
                    height = (latitudes_max - latitudes_min) * margin * width_to_height
                    width = (longitudes_max - longitudes_min) * margin
                    longitude_zoom = np.interp(width, longitude_zoom_range, range(20, 0, -1))
                    latitude_zoom = np.interp(height, longitude_zoom_range, range(20, 0, -1))
                    map_zoom = round(min(longitude_zoom, latitude_zoom), 2)
                else:
                    raise NotImplementedError(f"{projection} projection is not implemented")
                return map_zoom, locations_center

            if solution is not None:
                instance = solution.instance

            latitudes, longitudes = [], []
            for task in instance.tasks:
                latitudes.append(task.location.get_latitude(radians=False))
                longitudes.append(task.location.get_longitude(radians=False))
            zoom, center = _compute_map_zoom_and_center(longitudes, latitudes)

            colors = _compute_employees_colors(instance)
            fig = px.scatter_mapbox(lat=[], lon=[], hover_name=[], zoom=zoom, center=center)

            # Case where the map figure is supposed to display information about the instance
            if solution is None:

                show_tasks = (mode == 'all') or ('tasks' in mode)
                show_employees = (mode == 'all') or ('employees' in mode)

                # Case where the map figure is supposed to display tasks locations
                if show_tasks:
                    texts, latitudes, latitudes, descriptions = [], [], [], []
                    for task in instance.tasks:
                        texts.append(f"{task.name}<br><br> ")
                        latitudes.append(task.location.get_latitude(radians=False))
                        longitudes.append(task.location.get_longitude(radians=False))
                        descriptions.append(create_task_description_in_routes_figure(task))
                    fig.add_trace(go.Scattermapbox(
                        mode="markers+text", marker=dict(color=colors[0], size=9),
                        lat=latitudes, lon=longitudes, hoverinfo='text', hovertext=descriptions, text=texts,
                        showlegend=False
                    ))

                # Case where the map figure is supposed to display employees locations
                if show_employees:
                    for i, employee in enumerate(instance.employees):
                        latitude = employee.location.get_latitude(radians=False)
                        longitude = employee.location.get_longitude(radians=False)
                        description = f"<b>{employee.name}</b> <br>" \
                                      f"Skill level: {employee.skill_level} <br>" \
                                      f"WH: {employee.TW}"
                        # NB: Scattermapbox can not handle marker symbol other than circles
                        fig.add_trace(go.Scattermapbox(
                            mode='markers+text', marker=dict(color=colors[i], size=12),
                            lat=[latitude], lon=[longitude],
                            hoverinfo='text', hovertext=[description], text=[f"{employee.name}'s home<br><br> "],
                            showlegend=False
                        ))

            # Case where the map figure is supposed to display information about the solution
            else:
                if mode != 'all':
                    raise NotImplementedError(f"The mode {mode} is not handled")
                non_performed_tasks_latitudes, non_performed_tasks_longitudes, non_performed_tasks_descriptions = \
                    [], [], []
                for task in instance.tasks:
                    if not (solution.get_task_performance_status(task)):
                        non_performed_tasks_latitudes.append(task.location.get_latitude(radians=False))
                        non_performed_tasks_longitudes.append(task.location.get_longitude(radians=False))
                        non_performed_tasks_descriptions.append(create_task_description_in_routes_figure(task, False))
                fig.add_trace(go.Scattermapbox(
                    name="None", mode='markers', marker=dict(color='grey', size=9),
                    opacity=1 if infeasibility is None else .5,
                    lat=non_performed_tasks_latitudes, lon=non_performed_tasks_longitudes,
                    hoverinfo='text+name', hovertext=non_performed_tasks_descriptions,
                    showlegend=False
                ))
                for i, employee in enumerate(solution.instance.employees):
                    sequence = solution.get_sequence(employee)
                    route_steps_latitudes = [employee.location.get_latitude(radians=False)]
                    route_steps_longitudes = [employee.location.get_longitude(radians=False)]
                    route_steps_descriptions = [""]
                    route_steps_names = [""]
                    route_steps_marker_sizes = [12]
                    for step in sequence[1:-1]:
                        activity = step.activity
                        route_steps_latitudes.append(activity.location.get_latitude(radians=False))
                        route_steps_longitudes.append(activity.location.get_longitude(radians=False))
                        route_steps_descriptions.append(create_task_description_in_routes_figure(activity, True))
                        route_steps_names.append(activity.name)
                        route_steps_marker_sizes.append(9)
                    route_steps_latitudes.append(employee.location.get_latitude(radians=False))
                    route_steps_longitudes.append(employee.location.get_longitude(radians=False))
                    route_steps_descriptions.append(f"<b>{employee.name}'s home</b> <br>"
                                                    f"Skill level: {employee.skill_level}")
                    route_steps_names.append("Home")
                    route_steps_marker_sizes.append(12)
                    if infeasibility is None:
                        fig.add_trace(go.Scattermapbox(
                            name=employee.name, mode='markers+lines+text',
                            marker=dict(color=colors[i], size=route_steps_marker_sizes),
                            lat=route_steps_latitudes, lon=route_steps_longitudes,
                            hoverinfo='text+name', hovertext=route_steps_descriptions,
                            text=[name + "<br><br> " for name in route_steps_names]
                        ))
                    else:
                        if employee.name == infeasibility.conflicting_employee.name:
                            fig.add_trace(go.Scattermapbox(
                                name=employee.name, mode='markers+lines+text',
                                line=dict(width=2),
                                marker=dict(color=colors[i], size=route_steps_marker_sizes),
                                lat=route_steps_latitudes, lon=route_steps_longitudes,
                                hoverinfo='text+name', hovertext=route_steps_descriptions,
                                text=[name + "<br><br> " for name in route_steps_names]
                            ))
                        else:
                            fig.add_trace(go.Scattermapbox(
                                name=employee.name, mode='markers+lines+text', opacity=.5,
                                marker=dict(color=colors[i], size=route_steps_marker_sizes),
                                lat=route_steps_latitudes, lon=route_steps_longitudes,
                                hoverinfo='text+name', hovertext=route_steps_descriptions,
                                text=[name + "<br><br> " for name in route_steps_names]
                            ))

            fig.update_layout(
                mapbox_style="mapbox://styles/mathieu-lerouge/cl2nlkbiz002v14rvw77fv32q",
                mapbox_accesstoken='pk.eyJ1IjoibWF0aGlldS1sZXJvdWdlIiwiYSI6ImNsMm5sajY4bDIxZGIzaXA5MDNscjFoa2UifQ'
                                   '.SHh5_g--Pv6LEy6P3mk7eQ',
                # Another possible map box style is the open street map one, which does not require any access token.
                # However, with this style, names do not show up, then it should be used only if the token is an issue.
                # mapbox_style="open-street-map"
                margin={"r": 10, "t": 0, "l": 10, "b": 10},
                legend=dict(traceorder='normal', orientation='h', xanchor='center', x=0.5, y=1.1,
                            font=dict(family='Arial', size=10, color=self._font_color)),
                paper_bgcolor=self._panel_content_color
            )
            return fig

        def _build_routes_figure(solution: Solution = None, infeasibility: Infeasibility = None):
            """
            Build a map figure of the employees' routes.
            By default, if no other solution is given, the solution that is represented is the current solution.
            """
            if solution is None:
                solution = self.current_solution
            return _build_map_figure(solution.instance, solution=solution, infeasibility=infeasibility)

        def _build_schedules_figure(solution: Solution = None, infeasibility: Infeasibility = None):
            """
            Build a gantt chart of the employees' schedules.
            By default, if no other solution is given, the solution that is represented is the current solution.
            """
            if solution is None:
                solution = self.current_solution
            instance = solution.instance
            colors = _compute_employees_colors(instance)
            fig = go.Figure(layout=dict(barmode='stack'))
            for i, employee in enumerate(instance.employees):
                sequence = solution.get_sequence(employee)
                # Departure
                start_step = sequence[0]
                fig.add_trace(go.Bar(
                    orientation='h', width=.3, marker=dict(color=colors[i]),
                    opacity=(0.5 if infeasibility is not None else 1),
                    base=[start_step.start_time - 5], x=[5], y=[employee.name],
                    name=employee.name, hoverinfo='text+name',
                    hovertext=[create_home_description_in_schedules_figure(
                        start_step.activity, start_step.get_start_time(as_string=True))],
                    showlegend=False
                ))
                if infeasibility is not None and isinstance(infeasibility, TimeInfeasibility) and \
                        infeasibility.conflicting_employee.name == employee.name:
                    conflicting_task = infeasibility.conflicting_task
                    conflict_index = sequence.get_step_index_of(conflicting_task)
                    assert (conflict_index != 0)
                    employee_name_bis = employee.name + "2"
                    # Steps before conflict (excluding conflict) - Traveling phases
                    for step_index, step in enumerate(sequence[:conflict_index]):
                        traveling_duration = \
                            int(np.ceil(solution.compute_traveling_duration(step, sequence[step_index + 1])))
                        fig.add_trace(go.Bar(
                            orientation='h', width=.3, marker=dict(color='lightgrey'),
                            base=[step.end_time], x=[traveling_duration], y=[employee.name], name=employee.name,
                            hoverinfo='text',
                            hovertext=f'<b>{traveling_duration}min</b> for traveling <br>'
                                      f'<b>from {step.activity.name} to {sequence[step_index + 1].activity.name}</b>',
                            showlegend=False
                        ))
                    # Steps before conflict (excluding conflict) - Steps
                    steps_names, steps_hover_texts, steps_start_times, steps_durations = [], [], [], []
                    for step in sequence[1:conflict_index]:
                        activity = step.activity
                        steps_names.append(activity.name)
                        steps_hover_texts.append(create_task_description_in_schedules_figure(
                            activity, step.get_start_time(as_string=True), step.get_end_time(as_string=True)
                        ))
                        steps_start_times.append(step.start_time)
                        steps_durations.append(step.activity.duration)
                    fig.add_trace(go.Bar(
                        orientation='h', width=.8, marker=dict(color=colors[i]),
                        base=steps_start_times, x=steps_durations,
                        y=[employee.name for _ in steps_start_times],
                        name=employee.name, hoverinfo='text+name', hovertext=steps_hover_texts,
                        text=steps_names, insidetextanchor='middle'
                    ))
                    # Step of conflict - Satisfying upstream constraints
                    conflict_step = sequence[conflict_index]
                    before_conflict_step = sequence[conflict_index - 1]
                    traveling_duration = \
                        int(np.ceil(solution.compute_traveling_duration(before_conflict_step, conflict_step)))
                    conflict_activity = conflict_step.activity
                    conflict_step_earliest_start_time = max(before_conflict_step.end_time + traveling_duration,
                                                            conflict_activity.start_time_LB)
                    conflict_step_earliest_end_time = conflict_step_earliest_start_time + conflict_activity.duration
                    conflict_step_earliest_start_time_as_string = \
                        convert_nb_minutes_to_time_string(conflict_step_earliest_start_time)
                    conflict_step_earliest_end_time_as_string = \
                        convert_nb_minutes_to_time_string(conflict_step_earliest_end_time)
                    step_hover_text = create_task_description_in_schedules_figure(
                        conflict_activity, conflict_step_earliest_start_time_as_string,
                        conflict_step_earliest_end_time_as_string
                    )
                    fig.add_trace(go.Bar(
                        orientation='h', width=.8, marker=dict(color=self._conflict_task_color),
                        base=[conflict_step_earliest_start_time], x=[conflict_activity.duration], y=[employee.name],
                        name=employee.name, hoverinfo='text+name', hovertext=[step_hover_text],
                        text=[conflict_activity.name], insidetextanchor='middle',
                        showlegend=False
                    ))
                    # Step of conflict - Satisfying downstream constraints
                    after_conflict_step = sequence[conflict_index + 1]
                    traveling_duration = \
                        int(np.ceil(solution.compute_traveling_duration(conflict_step, after_conflict_step)))
                    conflict_step_latest_end_time = min(after_conflict_step.start_time - traveling_duration,
                                                        conflict_activity.end_time_UB)
                    conflict_step_latest_start_time = conflict_step_latest_end_time - conflict_activity.duration
                    conflict_step_latest_start_time_as_string = \
                        convert_nb_minutes_to_time_string(conflict_step_latest_start_time)
                    conflict_step_latest_end_time_as_string = \
                        convert_nb_minutes_to_time_string(conflict_step_latest_end_time)
                    step_hover_text = create_task_description_in_schedules_figure(
                        conflict_activity, conflict_step_latest_start_time_as_string,
                        conflict_step_latest_end_time_as_string
                    )
                    fig.add_trace(go.Bar(
                        orientation='h', width=.8, marker=dict(color=self._conflict_task_color),
                        base=[conflict_step_latest_start_time], x=[conflict_activity.duration], y=[employee_name_bis],
                        name=employee.name, hoverinfo='text+name', hovertext=[step_hover_text],
                        text=[conflict_activity.name], insidetextanchor='middle',
                        showlegend=False
                    ))
                    # Step of conflict - Traveling phase
                    fig.add_trace(go.Bar(
                        orientation='h', width=.3, marker=dict(color='lightgrey'),
                        base=[conflict_step_latest_end_time], x=[traveling_duration], y=[employee_name_bis],
                        name=employee.name, hoverinfo='text',
                        hovertext=f'<b>{traveling_duration}min</b> for traveling <br>'
                                  f'<b>from {conflict_activity.name} to {after_conflict_step.activity.name}</b>',
                        showlegend=False
                    ))
                    # Steps after conflict (excluding conflict) - Traveling phases
                    for step_index, step in enumerate(sequence[conflict_index + 1:-1]):
                        step_index += conflict_index + 1
                        traveling_duration = \
                            int(np.ceil(solution.compute_traveling_duration(step, sequence[step_index + 1])))
                        fig.add_trace(go.Bar(
                            orientation='h', width=.3, marker=dict(color='lightgrey'),
                            base=[step.end_time], x=[traveling_duration], y=[employee_name_bis],
                            name=employee.name,
                            hoverinfo='text',
                            hovertext=f'<b>{traveling_duration}min</b> for traveling <br>'
                                      f'<b>from {step.activity.name} to {sequence[step_index + 1].activity.name}</b>',
                            showlegend=False
                        ))
                    # Steps after conflict (excluding conflict) - Steps
                    steps_names, steps_hover_texts, steps_start_times, steps_durations = [], [], [], []
                    for step in sequence[conflict_index + 1:-1]:
                        activity = step.activity
                        steps_names.append(activity.name)
                        steps_hover_texts.append(create_task_description_in_schedules_figure(
                            activity, step.get_start_time(as_string=True), step.get_end_time(as_string=True)
                        ))
                        steps_start_times.append(step.start_time)
                        steps_durations.append(step.activity.duration)
                    fig.add_trace(go.Bar(
                        orientation='h', width=.8, marker=dict(color=colors[i]),
                        base=steps_start_times, x=steps_durations, y=[employee_name_bis for _ in steps_start_times],
                        name=employee.name, hoverinfo='text+name', hovertext=steps_hover_texts,
                        text=steps_names, insidetextanchor='middle',
                        showlegend=False
                    ))
                    # Return
                    return_step = sequence[-1]
                    fig.add_trace(go.Bar(
                        orientation='h', width=.3, marker=dict(color=colors[i]),
                        base=[return_step.start_time], x=[5], y=[employee_name_bis],
                        name=employee.name, hoverinfo='text+name',
                        hovertext=[create_home_description_in_schedules_figure(
                            return_step.activity, return_step.get_start_time(as_string=True))],
                        showlegend=False
                    ))
                    # Critical bounds
                    upstream_critical_step_index = infeasibility.upstream_critical_step_index
                    upstream_critical_bound_y_suffix = ""
                    downstream_critical_step_index = infeasibility.downstream_critical_step_index
                    downstream_critical_bound_y_suffix = "2"
                    if infeasibility.solution_is_upstream_feasible:
                        if not infeasibility.solution_is_downstream_feasible:
                            if conflict_step_earliest_start_time == conflicting_task.start_time_LB:
                                upstream_critical_step_index = conflict_index
                    else:
                        if infeasibility.solution_is_downstream_feasible:
                            if conflict_step_latest_end_time == conflicting_task.end_time_UB:
                                downstream_critical_step_index = conflict_index
                    upstream_critical_step = sequence[upstream_critical_step_index]
                    upstream_critical_bound = upstream_critical_step.activity.start_time_LB
                    fig.add_trace(go.Bar(
                        orientation='h', width=1, marker=dict(color=self._conflict_bound_color),
                        base=[upstream_critical_bound - 3], x=[3], y=[employee.name + upstream_critical_bound_y_suffix],
                        name=employee.name, hoverinfo='text+name',
                        hovertext=[f"Yielding <b>lower bound</b><br>"
                                   f"of <b>{upstream_critical_step.activity.name}</b> availability<br>"
                                   f"time window"],
                        showlegend=False
                    ))
                    downstream_critical_step = sequence[downstream_critical_step_index]
                    downstream_critical_bound = downstream_critical_step.activity.end_time_UB
                    fig.add_trace(go.Bar(
                        orientation='h', width=1, marker=dict(color=self._conflict_bound_color),
                        base=[downstream_critical_bound], x=[3], y=[employee.name + downstream_critical_bound_y_suffix],
                        name=employee.name, hoverinfo='text+name',
                        hovertext=["Yielding <b>upper bound</b><br>"
                                   f"of <b>{downstream_critical_step.activity.name}</b> availability<br>"
                                   f"time window"],
                        showlegend=False
                    ))
                else:
                    for step_index, step in enumerate(sequence[:-1]):
                        traveling_duration = \
                            int(np.ceil(solution.compute_traveling_duration(step, sequence[step_index + 1])))
                        fig.add_trace(go.Bar(
                            orientation='h', width=.3, marker=dict(color='lightgrey'),
                            opacity=(0.5 if infeasibility is not None else 1),
                            base=[step.end_time], x=[traveling_duration], y=[employee.name], name=employee.name,
                            hoverinfo='text',
                            hovertext=f'<b>{traveling_duration}min</b> for traveling <br>'
                                      f'<b>from {step.activity.name} to {sequence[step_index + 1].activity.name}</b>',
                            showlegend=False
                        ))
                    steps_names, steps_hover_texts, steps_start_times, steps_durations = [], [], [], []
                    for step in sequence[1:-1]:
                        activity = step.activity
                        steps_names.append(activity.name)
                        steps_hover_texts.append(create_task_description_in_schedules_figure(
                            activity, step.get_start_time(as_string=True), step.get_end_time(as_string=True)
                        ))
                        steps_start_times.append(step.start_time)
                        steps_durations.append(step.activity.duration)
                    fig.add_trace(go.Bar(
                        orientation='h', width=.8, marker=dict(color=colors[i]),
                        opacity=(0.5 if infeasibility is not None else 1),
                        base=steps_start_times, x=steps_durations,
                        y=[employee.name for _ in steps_start_times],
                        name=employee.name, hoverinfo='text+name', hovertext=steps_hover_texts,
                        text=steps_names, insidetextanchor='middle'
                    ))
                    return_step = sequence[-1]
                    fig.add_trace(go.Bar(
                        orientation='h', width=.3, marker=dict(color=colors[i]),
                        opacity=(0.5 if infeasibility is not None else 1),
                        base=[return_step.start_time], x=[5], y=[employee.name],
                        name=employee.name, hoverinfo='text+name',
                        hovertext=[create_home_description_in_schedules_figure(
                            return_step.activity, return_step.get_start_time(as_string=True))],
                        showlegend=False
                    ))
            fig.update_layout(
                margin={"t": 0, "r": 10, "b": 20, "l": 10},
                xaxis=dict(automargin=True, tickmode='array', tickvals=[h * 60 for h in range(7, 20)],
                           ticktext=[convert_nb_minutes_to_time_string(h * 60).replace(':00', '') for h in
                                     range(7, 20)]),
                yaxis=dict(automargin=True, autorange='reversed', visible=False),
                legend=dict(orientation='h', xanchor='center', x=0.5, y=1.1,
                            font=dict(family='Arial', size=10, color=self._font_color), traceorder='normal'),
                paper_bgcolor=self._panel_content_color, plot_bgcolor='#637485', font=dict(color=self._font_color)
            )
            return fig

        def _build_instance_metrics_figures(instance: Instance, reference_instance: Instance = None,
                                            horizontal: bool = True):
            """
            Build a gantt chart of the employees' schedules.
            """
            comparison_to_reference = False if (reference_instance is None) else True
            reference_instance = instance if (reference_instance is None) else reference_instance
            fig = go.Figure()
            fig.add_trace(go.Indicator(
                title=dict(text="# Employees", font=dict(color=self._font_color)),
                mode=f"number{'+delta' if comparison_to_reference else ''}",
                number=dict(font=dict(color=self._font_color)),
                value=instance.nb_employees, delta=dict(reference=reference_instance.nb_employees),
                domain={'row': 0, 'column': 0}))
            fig.add_trace(go.Indicator(
                title=dict(text="Total employees<br>working time", font=dict(color=self._font_color)),
                mode=f"number{'+delta' if comparison_to_reference else ''}",
                number=dict(font=dict(color=self._font_color), suffix='min'),
                value=instance.total_employees_availability_duration,
                delta=dict(reference=reference_instance.total_employees_availability_duration),
                domain={'row': 0 if horizontal else 1, 'column': 2 if horizontal else 0}))
            fig.add_trace(go.Indicator(
                title=dict(text="# Tasks", font=dict(color=self._font_color)),
                mode=f"number{'+delta' if comparison_to_reference else ''}",
                number=dict(font=dict(color=self._font_color)),
                value=instance.nb_tasks, delta=dict(reference=reference_instance.nb_tasks),
                domain={'row': 0, 'column': 1}))
            fig.add_trace(go.Indicator(
                title=dict(text="Total tasks<br>duration", font=dict(color=self._font_color)),
                mode=f"number{'+delta' if comparison_to_reference else ''}",
                number=dict(font=dict(color=self._font_color), suffix='min'),
                value=instance.total_tasks_duration, delta=dict(reference=reference_instance.total_tasks_duration),
                domain={'row': 0 if horizontal else 1, 'column': 3 if horizontal else 1}))
            fig.update_layout(
                grid={'rows': 1 if horizontal else 2, 'columns': 4 if horizontal else 2, 'pattern': 'independent'},
                paper_bgcolor=self._panel_content_color, font={'color': self._font_color}
            )
            return fig

        def _build_solution_metrics_figures(solution, reference_solution=None, horizontal=True):
            """
            Build a gantt chart of the employees' schedules.
            """
            comparison_to_reference = False if (reference_solution is None) else True
            reference_solution = solution if (reference_solution is None) else reference_solution
            instance = solution.instance
            fig = go.Figure()
            fig.add_trace(go.Indicator(
                title=dict(text="# Performed tasks", font=dict(color=self._font_color)),
                mode=f"gauge+number{'+delta' if comparison_to_reference else ''}",
                gauge=dict(axis=dict(range=[0, instance.nb_tasks], tickcolor=self._line_color),
                           bordercolor=self._line_color),
                number=dict(font=dict(color=self._font_color)),
                value=solution.nb_performed_tasks, delta=dict(reference=reference_solution.nb_performed_tasks),
                domain={'row': 0, 'column': 0})
            )
            fig.add_trace(go.Indicator(
                title=dict(text="Total working time", font=dict(color=self._font_color)),
                mode=f"gauge+number{'+delta' if comparison_to_reference else ''}",
                gauge=dict(axis=dict(range=[0, instance.total_employees_availability_duration],
                                     tickcolor=self._line_color), bordercolor=self._line_color),
                number=dict(font=dict(color=self._font_color), suffix='min'),
                value=solution.total_working_duration, delta=dict(reference=reference_solution.total_working_duration),
                domain={'row': 0, 'column': 1})
            )
            fig.add_trace(go.Indicator(
                title=dict(text="Total traveling time", font=dict(color=self._font_color)),
                mode=f"gauge+number{'+delta' if comparison_to_reference else ''}",
                gauge=dict(axis=dict(range=[0, instance.total_employees_availability_duration],
                                     tickcolor=self._line_color), bar=dict(color='red'), bordercolor=self._line_color),
                number=dict(font=dict(color=self._font_color), suffix='min'),
                value=solution.total_traveling_duration,
                delta=dict(reference=reference_solution.total_traveling_duration,
                           increasing=dict(color='red'), decreasing=dict(color='green')),
                domain={'row': 0 if horizontal else 1, 'column': 2 if horizontal else 0})
            )
            fig.update_layout(
                grid={'rows': 1 if horizontal else 2, 'columns': 3 if horizontal else 2, 'pattern': 'independent'},
                paper_bgcolor=self._panel_content_color, font={'color': self._font_color}
            )
            return fig

        ##################
        # Typical panels #
        ##################

        def _build_panel_banner(panel_title: str):
            """
            Build the banner of a typical panel.
            """
            return html.Div(className="panel-banner", children=panel_title)

        def _build_employees_data_panel(panel_title: str = "Employees data", instance: Instance = None,
                                        editable: bool = False):
            """
            Build a panel containing a table with data about the employees.
            """
            panel = html.Div(
                id="employees-panel", className='panel-with-bottom-margin',
                children=[_build_panel_banner(panel_title), _build_employees_data_table(instance, editable)]
            )
            return panel

        def _build_tasks_data_panel(panel_title: str = "Tasks data", panel_title_prefix: str = "",
                                    panel_title_suffix: str = "", instance: Instance = None,
                                    editable: bool = False):
            """
            Build a panel containing a table with data about the tasks.
            """
            panel_title = panel_title_prefix + panel_title + panel_title_suffix
            panel = html.Div(
                id="tasks-panel", className='panel',
                children=[_build_panel_banner(panel_title), _build_tasks_data_table(instance, editable)]
            )
            return panel

        def _build_routes_figure_panel(panel_title: str = "Employees' routes", panel_title_prefix: str = "",
                                       panel_title_suffix: str = "", solution: Solution = None,
                                       infeasibility: Infeasibility = None):
            """
            Build a panel containing a map of the employees' routes for a given solution.
            By default, if no other solution is given, the solution that is represented is the current solution.
            """
            panel_title = panel_title_prefix + panel_title + panel_title_suffix
            solution_to_represent = self.current_solution if (solution is None) else solution
            panel = html.Div(
                className='panel',
                children=[
                    _build_panel_banner(panel_title),
                    dcc.Graph(
                        id=f"{'current' if solution is None else 'other'}-solution-spatial-representation",
                        className='spatial-representation', style=dict(padding='1rem 0rem 0rem 0rem'),
                        figure=_build_routes_figure(solution=solution_to_represent, infeasibility=infeasibility))
                ]
            )
            return panel

        def _build_schedules_figure_panel(panel_title: str = "Employees' schedules", panel_title_prefix: str = "",
                                          panel_title_suffix: str = "", solution: Solution = None,
                                          infeasibility: Infeasibility = None):
            """
            Build a panel containing a gantt chart of the employees' schedules for a given solution.
            By default, if no solution is given, the solution that is represented is the current solution.
            """
            panel_title = panel_title_prefix + panel_title + panel_title_suffix
            solution_to_represent = self.current_solution if (solution is None) else solution
            panel = html.Div(
                className='panel',
                children=[
                    _build_panel_banner(panel_title),
                    dcc.Graph(
                        id=f"{'current' if solution is None else 'other'}-solution-temporal-representation",
                        className="temporal-representation", style=dict(padding='1rem 0rem 1rem 0rem'),
                        figure=_build_schedules_figure(solution=solution_to_represent, infeasibility=infeasibility))
                ]
            )
            return panel

        def _build_instance_metrics_panel(panel_title: str = "Metrics", panel_title_prefix: str = "",
                                          horizontal: bool = True, instance: Instance = None):
            """
            Build a panel containing some metrics data about the instance.
            """
            panel_title = panel_title_prefix + panel_title
            instance_to_describe = self.current_instance if (instance is None) else instance
            reference_instance = None if (instance is None) else self.current_instance
            panel = html.Div(
                className=f'panel',
                children=[
                    _build_panel_banner(panel_title),
                    dcc.Graph(id=f"{'horizontal' if horizontal else 'two-by-two'}-"
                                 f"{'current' if (instance is None) else 'other'}-instance-metrics-figures",
                              figure=_build_instance_metrics_figures(instance_to_describe, reference_instance,
                                                                     horizontal))
                ]
            )
            return panel

        def _build_solution_metrics_panel(panel_title: str = "Metrics", panel_title_prefix: str = "",
                                          horizontal: bool = True, solution: Solution = None):
            """
            Build a panel containing a figure with metrics about the solution.
            If no solution is given, then the metrics of the current solution are represented.
            Else, the metrics of the given solution are represented and compared to the ones of the current solution.
            """
            panel_title = panel_title_prefix + panel_title
            solution_to_describe = self.current_solution if (solution is None) else solution
            reference_solution = None if (solution is None) else self.current_solution
            panel = html.Div(
                className=f'panel',
                children=[
                    _build_panel_banner(panel_title),
                    dcc.Graph(id=f"{'horizontal' if horizontal else 'two-by-two'}-"
                                 f"{'current' if (solution is None) else 'other'}-solution-metrics-figures",
                              figure=_build_solution_metrics_figures(solution_to_describe, reference_solution,
                                                                     horizontal))
                ]
            )
            return panel

        ##########
        # Layout #
        ##########

        self._application.layout = _build_layout()

    ##########
    # Basics #
    ##########

    @property
    def current_solution(self):
        return self._explainer.current_solution

    @current_solution.setter
    def current_solution(self, solution: Solution):
        self._explainer.current_solution = solution

    @property
    def current_instance(self):
        return self._explainer.current_instance

    #######
    # Run #
    #######

    def run(self):
        """
        Run the web Graphic User Interface of the explainer.
        """
        self._application.run_server(debug=True)
