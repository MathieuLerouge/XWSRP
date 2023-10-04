# Standard libraries
import pathlib
import warnings

# Third-party libraries
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import numpy as np

# Local libraries
from src.explaining.interacting.interface.figures import build_map_figure, build_routes_figure, \
    build_schedules_figure, build_instance_metrics_figures, build_solution_metrics_figures
from src.explaining.interacting.interface.panels import build_routes_figure_panel, build_schedules_figure_panel, \
    build_instance_metrics_panel, build_solution_metrics_panel, build_tasks_data_panel, build_panel_banner, \
    build_employees_data_panel, build_text_panel
from src.explaining.interacting.interface.tables import build_tasks_data_conditional_style, build_tasks_data, \
    build_employees_data_conditional_style, build_employees_data
from src.explaining.interacting.interface.tools import convert_from_string_to_html
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.questioning.questions_templates_bank import *
from src.explaining.interacting.explainer import Explainer
from src.modeling.solution import Solution
from src.utils.constants import LINE_BREAK_STRING
from src.utils.time import convert_time_string_to_nb_minutes, get_hour_format_associated_with_language, \
    convert_nb_minutes_to_time_string

# Commands to remove future warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Global variables
HOME_TAB = 'home-tab'
INSTANCE_DESCRIPTION_TAB = 'instance-description-tab'
EXPLAINER_TAB = 'explainer-tab'


#########################
# Class ExplainerWebGUI #
#########################

class ExplainerWebGUI:

    ####################
    # Fixed parameters #
    ####################

    # Assets-related parameters
    _assets_path = str(pathlib.Path(__file__).parent.resolve()) + '/assets'

    # Questions parameters
    # Note: only the questions which keys are part of the list below can be handled by the UI
    _available_questions_templates_ids = [
        WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
        WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
        WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
    ]

    def __init__(self, explainer: Explainer, title: str = None, subtitle: str = None,
                 tab_on_opening: str = None, enabling_explanations: bool = True):

        #######################
        # Variable parameters #
        #######################

        # Explainer
        self._explainer = explainer
        self._questions_templates = dict([(question_template.id, QUESTIONS_TEMPLATES[question_template.id])
                                          for question_template in self._explainer.activated_questions_templates
                                          if question_template.id in self._available_questions_templates_ids])
        self._available_questions_templates_ids = list(self._questions_templates.keys())
        self._scenario_instance_alterations = InstanceChanges()
        self._counterfactual_instance_alterations = None

        # Application
        self._title = title
        self._subtitle = subtitle
        self._application = dash.Dash(name="XWSRP", assets_folder=self._assets_path, suppress_callback_exceptions=True)
        self._explanations_are_enabled = enabling_explanations
        self._tab_description_panels_are_enabled = False
        self._contrastive_statistics_are_enabled = False
        if not self._explanations_are_enabled:
            self._explanations_representation_are_enabled = False
            self.disable_history()
            self.disable_scenario_explanations()
            self.disable_counterfactual_explanations()
        else:
            self._explanations_representation_are_enabled = True
        if self.language_is_english:
            self._home_tab_title = "Home"
            self._instance_description_tab_title = "Instance description"
            self._instances_comparison_tab_title = "Instances comparison"
            self._solution_description_tab_title = "Solution description"
            self._solutions_comparison_tab_title = "Solutions comparison"
            self._explainer_tab_title = "Solution explanation"
        elif self.language_is_french:
            self._home_tab_title = "Accueil"
            self._instance_description_tab_title = "Description de l'instance"
            self._instances_comparison_tab_title = "Comparaison d'instances"
            self._solution_description_tab_title = "Description de la solution"
            self._solutions_comparison_tab_title = "Comparaison de solutions"
            self._explainer_tab_title = "Explication de la solution"
        else:
            raise NotImplementedError("The language is not supported.")
        self._tab_on_opening = HOME_TAB if tab_on_opening is None else tab_on_opening

        ##########
        # Layout #
        ##########

        def _build_layout():
            """
            Build the layout of the GUI: the banner at the top of the GUI and the layout underneath which is made of
            a vertical bar of navigation tabs on the left and the content of the selected tab on the right.
            """
            if self._explainer.history_is_enabled:
                return html.Div(
                    id="main-container",
                    children=[
                        _build_title_banner(), _build_explorer_banner(),
                        html.Div(id="sub-banner-layout",
                                 children=[_build_navigation_tabs(), html.Div(id="tab-content")]),
                    ],
                )
            else:
                return html.Div(
                    id="main-container",
                    children=[
                        _build_title_banner(),
                        html.Div(id="sub-banner-layout",
                                 children=[_build_navigation_tabs(), html.Div(id="tab-content")]),
                    ],
                )

        ################
        # Title banner #
        ################

        def _build_title_banner():
            """
            Build the title banner at the top of the GUI.
            """
            if title is None:
                self._title = "XWSRP"
            if self.language_is_english:
                if self._subtitle is None:
                    self._subtitle = "Explainer of Workforce Scheduling and Routing Problems solutions"
                banner_subtitle = html.H6(self._subtitle)
            elif self.language_is_french:
                if self._subtitle is None:
                    self._subtitle = \
                        "Outil d'explication des solutions de problèmes de planification de personnel mobile"
                banner_subtitle = html.H6(self._subtitle)
            else:
                raise NotImplementedError(f"Language {self.language} is not supported")
            banner = html.Div(
                id="title-banner",
                children=[
                    html.Div(
                        id="title-banner-text",
                        children=[html.H5(self._title), html.H6(banner_subtitle)],
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
            explorer_title = ""
            if self.language_is_english:
                explorer_title = "Instance & solution explorer"
            elif self.language_is_french:
                explorer_title = "Choix d'instance-solution"
            explorer_banner = html.Div(
                id="explorer-banner",
                children=[
                    html.Div(id='explorer-banner-title', children=explorer_title),
                    html.Div(style=dict(display='flex', flexdirection='row', flex=1),
                             children=[current_instance_dropdown, current_solution_dropdown])
                ]
            )
            return explorer_banner

        if self._explainer.history_is_enabled:
            #
            @self._application.callback(
                Output('home-tab', 'disabled'),
                Output('instance-description-tab', 'disabled'), Output('instances-comparison-tab', 'disabled'),
                Output('solution-description-tab', 'disabled'), Output('solutions-comparison-tab', 'disabled'),
                Output('explainer-tab', 'disabled'), Input('template-question-dropdown', 'disabled'),
            )
            def _update_tab_button_status(template_question_dropdown_disabled: bool):
                if template_question_dropdown_disabled:
                    return True, True, True, True, True, True
                else:
                    return False, False, False, False, False, False
            #
        elif self.explanations_are_enabled:
            #
            @self._application.callback(
                Output('home-tab', 'disabled'), Output('instance-description-tab', 'disabled'),
                Output('solution-description-tab', 'disabled'), Output('explainer-tab', 'disabled'),
                Input('template-question-dropdown', 'disabled'),
            )
            def _update_tab_button_status(template_question_dropdown_disabled: bool):
                if template_question_dropdown_disabled:
                    return True, True, True, True
                else:
                    return False, False, False, False
            #
        else:
            #
            @self._application.callback(
                Output('home-tab', 'disabled'), Output('instance-description-tab', 'disabled'),
                Output('solution-description-tab', 'disabled'), Input('template-question-dropdown', 'disabled'),
            )
            def _update_tab_button_status(template_question_dropdown_disabled: bool):
                if template_question_dropdown_disabled:
                    return True, True, True
                else:
                    return False, False, False

        if self._explainer.history_is_enabled:
            #
            @self._application.callback(
                Output('current-instance-dropdown', 'disabled'),
                Input('template-question-dropdown', 'disabled'),
            )
            def _update_current_instance_dropdown_status(template_question_dropdown_disabled: bool):
                if template_question_dropdown_disabled:
                    return True
                else:
                    return False

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
            available_tabs = [
                dcc.Tab(id=HOME_TAB, className="tab-button",
                        label=self._home_tab_title, value=HOME_TAB,
                        selected_className="tab-button--selected"),
                dcc.Tab(id=INSTANCE_DESCRIPTION_TAB, className="tab-button",
                        label=self._instance_description_tab_title, value=INSTANCE_DESCRIPTION_TAB,
                        selected_className="tab-button--selected"),
                dcc.Tab(id='instances-comparison-tab', className="tab-button",
                        label=self._instances_comparison_tab_title, value='instances-comparison-tab',
                        selected_className="tab-button--selected"),
                dcc.Tab(id="solution-description-tab", className="tab-button",
                        label=self._solution_description_tab_title, value="solution-description-tab",
                        selected_className="tab-button--selected"),
                dcc.Tab(id="solutions-comparison-tab", className="tab-button",
                        label=self._solutions_comparison_tab_title, value="solutions-comparison-tab",
                        selected_className="tab-button--selected"),
                dcc.Tab(id=EXPLAINER_TAB, className="tab-button", label=self._explainer_tab_title,
                        value=EXPLAINER_TAB, selected_className="tab-button--selected")
            ]
            if self._explainer.history_is_enabled:
                activated_tabs = available_tabs
            elif self.explanations_are_enabled:
                activated_tabs = [available_tabs[0], available_tabs[1], available_tabs[3], available_tabs[5]]
            else:
                activated_tabs = [available_tabs[0], available_tabs[1], available_tabs[3]]
            navigation = html.Div(
                id="navigation-left-panel",
                children=[dcc.Tabs(id="tabs-list", parent_className='tabs-buttons', vertical=True,
                                   value=self._tab_on_opening, children=activated_tabs)],
            )
            return navigation

        def _build_tab_content(tab_value: str):
            if tab_value == HOME_TAB:
                return _build_home_tab_content()
            elif tab_value == INSTANCE_DESCRIPTION_TAB:
                return _build_instance_description_tab_content()
            elif tab_value == 'instances-comparison-tab':
                return _build_instance_comparison_tab_content()
            elif tab_value == 'solution-description-tab':
                return _build_solution_description_tab_content()
            elif tab_value == 'solutions-comparison-tab':
                return _build_solution_comparison_tab_content()
            elif tab_value == EXPLAINER_TAB:
                return _build_question_explanation_tab_content()
            else:
                raise ValueError(f"GUI Error: There is no {tab_value} tab.")

        if self._explainer.history_is_enabled:
            #
            @self._application.callback(
                Output('tab-content', 'children'),
                Input('tabs-list', 'value'), Input('current-solution-dropdown', 'value')
            )
            def _update_tab_content(tab_value: str, current_solution_name: str):
                """
                React to the selection of a tab by the end-user
                by building the content corresponding to the selected tab.
                """
                if current_solution_name != self.current_solution.name:
                    self.current_solution = self._explainer.get_solution_by_name(current_solution_name)
                return _build_tab_content(tab_value)
            #
        else:
            #
            @self._application.callback(
                Output('tab-content', 'children'),
                Input('tabs-list', 'value'),
            )
            def _update_tab_content(tab_value: str):
                """
                React to the selection of a tab by the end-user
                by building the content corresponding to the selected tab.
                """
                return _build_tab_content(tab_value)

        ####################
        # Home tab content #
        ####################

        def _build_home_tab_content():
            """
            Build the content of the home tab.
            """
            if self.language_is_english:
                # panel_title = f"About {self._title}"
                panel_title = f"About this tool"
                panel_text = f"\"{self._title}\" is a tool for "
                if self.explanations_are_enabled:
                    panel_text += f"consulting and questioning "
                else:
                    panel_text += f"consulting "
                panel_text += f"the input and output data associated with " \
                              f"a Workforce Scheduling and Routing Problem (WSRP)." \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += f"The tabs bar located on the left of the interface allows the user to " \
                              f"navigate to the different functionalities of the tool." \
                              f"{LINE_BREAK_STRING}"
                panel_text += f"• The \"{self._instance_description_tab_title}\" tab allows to consult " \
                              f"the data of the studied instance." \
                              f"{LINE_BREAK_STRING}"
                if self.history_is_enabled:
                    panel_text += f"• The \"{self._instances_comparison_tab_title}\" tab allows to compare " \
                                  f"the data of two different instances." \
                                  f"{LINE_BREAK_STRING}"
                panel_text += f"• The \"{self._solution_description_tab_title}\" tab allows to consult " \
                              f"the data of the studied solution which has been obtained " \
                              f"thanks to an optimization process." \
                              f"{LINE_BREAK_STRING}"
                if self.history_is_enabled:
                    panel_text += f"• The \"{self._solutions_comparison_tab_title}\" tab allows to compare " \
                                  f"the data of two different solutions." \
                                  f"{LINE_BREAK_STRING}"
                if self.explanations_are_enabled:
                    panel_text += f"• The \"{self._explainer_tab_title}\" tab allows to question " \
                                  f"the content of the studied solution." \
                                  f"{LINE_BREAK_STRING}"
            elif self.language_is_french:
                # panel_title = f"À propos de {self._title}"
                panel_title = f"À propos de cet outil"
                panel_text = f"\"{self._title}\" est un outil qui permet de "
                if self.explanations_are_enabled:
                    panel_text += f"consulter et questionner "
                else:
                    panel_text += f"consulter "
                panel_text += f"les données d'entrée (instances) et de sortie (solutions) associées à " \
                              f"un problème de planification d'employés mobiles." \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += f"La barre d'onglets située à gauche de l'interface permet à l'utilisateur de " \
                              f"naviguer vers les différentes fonctionnalités de l'outil." \
                              f"{LINE_BREAK_STRING}"
                panel_text += f"• L'onglet \"{self._instance_description_tab_title}\" permet de consulter " \
                              f"les données de l'instance étudiée." \
                              f"{LINE_BREAK_STRING}"
                if self.history_is_enabled:
                    panel_text += f"• L'onglet \"{self._instances_comparison_tab_title}\" permet de comparer " \
                                  f"les données de deux instances différentes." \
                                  f"{LINE_BREAK_STRING}"
                panel_text += f"• L'onglet \"{self._solution_description_tab_title}\" permet de consulter " \
                              f"les données de la solution étudiée qui a été obtenue " \
                              f"au moyen d'un processus d'optimisation." \
                              f"{LINE_BREAK_STRING}"
                if self.history_is_enabled:
                    panel_text += f"• L'onglet \"{self._solutions_comparison_tab_title}\" permet de comparer " \
                                  f"les données de deux solutions différentes." \
                                  f"{LINE_BREAK_STRING}"
                if self.explanations_are_enabled:
                    panel_text += f"• L'onglet \"{self._explainer_tab_title}\" permet de questionner " \
                                  f"le contenu de la solution étudiée." \
                                  f"{LINE_BREAK_STRING}"
            else:
                raise NotImplementedError(f"Language {self.language} is not supported")
            return build_text_panel(panel_title, panel_text)

        ####################################
        # Instance description tab content #
        ####################################

        def _build_instance_description_tab_content():
            """
            Build the tab content about the description of the instance.
            By default, the instance that is described is the instance of the current solution.
            """
            instance = self.current_instance
            hour_format = get_hour_format_associated_with_language(self.language)
            first_employee = self.current_instance.employees[0]
            min_skill_level = min([employee.skill_level for employee in self.current_instance.employees])
            max_skill_level = max([employee.skill_level for employee in self.current_instance.employees])
            first_task = self.current_instance.tasks[0]
            if self.language_is_english:
                # Panel about content of any instance
                description_panel_title = "About the generic content of any instance"
                panel_text = "Any instance is composed of data about mobile employees and " \
                             "tasks ordered by customers." \
                             f"{LINE_BREAK_STRING}"
                panel_text += f"The tables and maps below describe the data of the {self._current_instance_in_text()}" \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += f"• Each employee has a first name (in the table, e.g. {first_employee.name}), " \
                              f"working hours (e.g. {str(first_employee.TW.as_string(hour_format))}), " \
                              f"a skill level described by an integer (e.g. {str(first_employee.skill_level)}, " \
                              f"with {str(min_skill_level)} corresponding to a junior level and " \
                              f"{str(max_skill_level)} to a senior level) " \
                              f"as well as a 'home' corresponding to the employee's location " \
                              f"at the beginning and the end of the day (represented in the map as a dot)." \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += f"• Each customer task has an identifier (in the table, e.g. {first_task.name}), " \
                              f"availability hours during which the task can be performed by an employee " \
                              f"(e.g. {str(first_task.TWs.as_string(hour_format))}, " \
                              f"a minimum skill level to have in order to be able to perform the task " \
                              f"(e.g. {str(first_task.skill_level)}), " \
                              f"a duration (e.g. {str(first_task.duration)}min) " \
                              f"as well as a location (represented in the map as a dot)." \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += f"NB: The maps are interactive. " \
                              f"It is possible to zoom in and out as well as move the map. " \
                              f"Besides, some information are displayed when the mouse is over a point."
                # Panels about employees and tasks locations
                employees_locations_map_title = "Employees' locations"
                tasks_locations_map_title = "Tasks' locations"
                # Panels about figures
                metrics_panel_title = "Some key figures about the instance"
            elif self.language_is_french:
                # Panel about content of any instance
                description_panel_title = "À propos du contenu générique d'une instance"
                panel_text = "Toute instance est composée de données portant sur les employés mobiles et " \
                             "sur les tâches commandées par les clients." \
                             f"{LINE_BREAK_STRING}"
                panel_text += f"Les tableaux et cartes ci-dessous décrivent les données de l'" \
                              f"{self._current_instance_in_text()}." \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += f"• Chaque employé possède un prénom " \
                              f"(dans le tableau, par ex. {first_employee.name}), " \
                              f"des horaires de travail (par ex. {str(first_employee.TW.as_string(hour_format))}), " \
                              f"un niveau de compétence décrit par un entier " \
                              f"(par ex. {str(first_employee.skill_level)}, " \
                              f"sachant que {str(min_skill_level)} correspondant un niveau junior et " \
                              f"{str(max_skill_level)} à un niveau senior) " \
                              f"ainsi qu'un 'domicile' correspondant au lieu de début et de fin de journée " \
                              f"de l'employé (représenté par un point sur la carte)." \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += f"• Chaque tâche client possède un identifiant " \
                              f"(dans le tableau, par ex. {first_task.name}), " \
                              f"des horaires de disponibilité pendant lesquels elle peut être réalisée par " \
                              f"un employé (par ex. {str(first_task.TWs.as_string(hour_format))}), " \
                              f"un niveau de compétence minimum à avoir pour pouvoir réaliser la tâche " \
                              f"(par ex. {str(first_task.skill_level)}), " \
                              f"une durée de réalisation (par ex. {str(first_task.duration)}min) " \
                              f"ainsi qu'un lieu (représenté par un point sur la carte)." \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += "NB : Les cartes sont interactives. " \
                              "Il est possible de zoomer-dézoomer et de déplacer le fond de carte. " \
                              "Par ailleurs, des informations sont affichées lorsque la souris est placée " \
                              "au-dessus des points d'intérêts."
                # Panels about employees and tasks locations
                employees_locations_map_title = "Domiciles des employés"
                tasks_locations_map_title = "Lieux des tâches"
                # Panels about figures
                metrics_panel_title = "Quelques chiffres sur l'instance"
            else:
                raise NotImplementedError(f"Language {self.language} is not supported")
            tab_content = html.Div(
                id="instance-description-tab-content",
                children=[
                    (build_text_panel(description_panel_title, panel_text, True)
                     if self.tab_description_panels_are_enabled else None),
                    build_employees_data_panel(self.current_instance, True, bottom_margin=True, language=self.language),
                    build_tasks_data_panel(self.current_instance, True, language=self.language),
                    html.Div(
                        className="representation-panels-side-to-side",
                        children=[
                            html.Div(
                                className='panel',
                                children=[
                                    build_panel_banner(employees_locations_map_title),
                                    dcc.Graph(
                                        id=f"employees-spatial-representation", className="spatial-representation",
                                        figure=build_map_figure(instance, mode='employees', language=self.language)
                                    )
                                ],
                            ),
                            html.Div(
                                className='panel',
                                children=[
                                    build_panel_banner(tasks_locations_map_title),
                                    dcc.Graph(
                                        id=f"tasks-spatial-representation", className="spatial-representation",
                                        figure=build_map_figure(instance, mode='tasks', language=self.language)
                                    )
                                ],
                            )
                        ]
                    ),
                    build_instance_metrics_panel(self.current_instance, True,
                                                 panel_title=metrics_panel_title, language=self.language)
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

            if self._explainer.history_is_disabled:
                raise PermissionError("Instances comparison is not enabled as historizing is disabled")

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
                if self.language_is_english:
                    panel_title = f"{'Other' if enable_other_instance else 'Current'} instance"
                elif self.language_is_french:
                    panel_title = f"{'Autre instance' if enable_other_instance else 'Instance courante'}"
                else:
                    raise ValueError(f"Language '{self.language}' is not supported.")
                line = _build_other_instance_dropdown() if enable_other_instance else \
                    html.Div(className='automated-text', style=dict(flex=1), children=current_instance.name)
                panel = html.Div(
                    className='panel',
                    children=[build_panel_banner(panel_title), html.Div(className='panel-content', children=line)]
                )
                return panel

            if self.language_is_english:
                current_instance_panel_title_prefix = "Current instance - "
                other_instance_panel_title_prefix = "Other instance - "
            elif self.language_is_french:
                current_instance_panel_title_prefix = "Instance courante - "
                other_instance_panel_title_prefix = "Autre instance - "
            else:
                raise ValueError(f"Language '{self.language}' is not supported.")

            tab_content = html.Div(
                id="instances-comparison-tab-content",
                children=[
                    html.Div(
                        className="panels-side-to-side",
                        children=[_build_instance_name_panel(), _build_instance_name_panel(enable_other_instance=True)]
                    ),
                    html.Div(
                        className="panels-side-to-side",
                        children=[build_employees_data_panel(self.current_instance, True,
                                                             panel_title_prefix=current_instance_panel_title_prefix,
                                                             language=self.language),
                                  build_employees_data_panel(other_instance, False,
                                                             instance_to_compare_with=self.current_instance,
                                                             panel_title_prefix=other_instance_panel_title_prefix,
                                                             language=self.language)]
                    ),
                    html.Div(
                        className="panels-side-to-side",
                        children=[build_tasks_data_panel(self.current_instance, True,
                                                         panel_title_prefix=current_instance_panel_title_prefix,
                                                         language=self.language),
                                  build_tasks_data_panel(other_instance, False,
                                                         instance_to_compare_with=self.current_instance,
                                                         panel_title_prefix=other_instance_panel_title_prefix,
                                                         language=self.language)]
                    ),
                    html.Div(
                        className="panels-side-to-side",
                        children=[build_instance_metrics_panel(current_instance, True,
                                                               panel_title_prefix=current_instance_panel_title_prefix,
                                                               horizontal=False, language=self.language),
                                  build_instance_metrics_panel(other_instance, False,
                                                               panel_title_prefix=other_instance_panel_title_prefix,
                                                               horizontal=False, language=self.language)]
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
            employees_data = build_employees_data(other_instance, self.language)
            employees_style_data_conditional = build_employees_data_conditional_style(employees_data, current_instance)
            tasks_data = build_tasks_data(other_instance, self.language)
            tasks_style_data_conditional = build_tasks_data_conditional_style(tasks_data, current_instance)
            return (employees_data, employees_style_data_conditional, tasks_data, tasks_style_data_conditional,
                    build_instance_metrics_figures(instance=other_instance, reference_instance=current_instance,
                                                   horizontal=False, language=self.language))

        ####################################
        # Solution description tab content #
        ####################################

        def _build_solution_description_tab_content():
            """
            Build the tab content about the description of a solution.
            """
            if self.language_is_english:
                description_panel_title = "About the generic content of any solution"
                panel_text = "A solution is made of sets of routes and of schedules. " \
                             "Each employee is assigned to a route and a schedule." \
                             f"{LINE_BREAK_STRING}"
                panel_text += f"The map and the Gantt chart below show respectively " \
                              f"the routes and the schedules of the {self._current_solution_in_text()}" \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += "• A route is a chain of moves performed by an employee " \
                              "(represented in the map as a colored segments). " \
                              "This chain forms a closed loop, which starts from the employee's home (large dot), " \
                              "goes through the tasks to be performed (small dots), " \
                              "and ends back at the employee's home (large dot)." \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += "• A schedule is a sequence of time intervals assigned to an employee. " \
                              "This sequence starts by the employee's departure from home. " \
                              "It alternates between periods of travel (small bars, of variable width and gray) " \
                              "and periods of task performance (large bars, of variable width and colored). " \
                              "The sequence ends with the employee's return to home " \
                              "(small bar, thin and colored at the end of the sequence)." \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += "NB: The direction of the employees' moves could not be represented on the map " \
                              "but it can be deduced from the Gantt chart. " \
                              "Moreover, information is displayed on the map and on the Gantt chart " \
                              "when the mouse is placed over the interesting elements."
                metrics_panel_title = "Some key figures about the solution"
            elif self.language_is_french:
                description_panel_title = "À propos du contenu générique d'une solution"
                panel_text = "Une solution est composée d'ensembles d'itinéraires et d'emplois du temps. " \
                             "Chaque employé est associé à exactement un itinéraire et un emploi du temps." \
                             f"{LINE_BREAK_STRING}"
                panel_text += f"La carte et le diagramme de Gantt ci-dessous décrivent respectivement " \
                              f"les itinéraires et les emplois du temps des employés " \
                              f"pour la {self._current_solution_in_text()}." \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += "• Un itinéraire est un enchaînement de déplacements réalisés par un employé " \
                              "(représenté sur la carte par une ligne brisée colorée). " \
                              "Cet enchaînement forme une boucle qui part du domicile de l'employé (large point), " \
                              "passe par les tâches réalisées par ce dernier (petits points) " \
                              "et revient au domicile (large point)." \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += "• Un emploi du temps est une séquence d'activités réalisées par un employé. " \
                              "Cette séquence commence par l'indication du départ de l'employé (représentée dans " \
                              "le Gantt par une barre de petite hauteur, mince et colorée au début de la séquence). " \
                              "S'alternent ensuite des périodes de déplacements " \
                              "(barres de petite hauteur, de largeurs variables et grises) et " \
                              "des périodes de réalisation de tâches " \
                              "(barres hautes, de largeurs variables et colorées). " \
                              "La séquence se termine enfin par l'indication du retour de l'employé " \
                              "(barre de petite hauteur, mince et colorée à la fin de la séquence)." \
                              f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                panel_text += "NB : Le sens de déplacement des employés n'a pas pu être représenté sur la carte " \
                              "mais il est possible de le déduire à partir du diagramme de Gantt. " \
                              "Par ailleurs, des informations sont affichées sur la carte et sur le diagramme " \
                              "de Gantt lorsque la souris est placée au-dessus des éléments d'intérêt."
                metrics_panel_title = "Qualité de la solution"
            else:
                raise ValueError(f"Language '{self.language}' is not supported.")
            tab_content = html.Div(
                id="solution-description-tab-content",
                children=[
                    (build_text_panel(description_panel_title, panel_text, True)
                     if self.tab_description_panels_are_enabled else None),
                    html.Div(
                        className="representation-panels-side-to-side",
                        children=[build_routes_figure_panel(solution=self.current_solution, is_current_solution=True,
                                                            language=self.language),
                                  build_schedules_figure_panel(solution=self.current_solution, is_current_solution=True,
                                                               language=self.language)]
                    ),
                    build_solution_metrics_panel(self.current_solution, True, with_description=True,
                                                 panel_title=metrics_panel_title, language=self.language)
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

            if self._explainer.history_is_disabled:
                raise PermissionError("Solutions comparison is not enabled as historizing is disabled")

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
                if self.language_is_english:
                    panel_title = f"{'Other' if enable_other_solution else 'Current'} solution"
                elif self.language_is_french:
                    panel_title = f"{'Autre solution' if enable_other_solution else 'Solution courante'}"
                else:
                    raise ValueError(f"Language '{self.language}' is not supported.")
                first_line = html.Div(className='automated-text', style=dict(flex=1, margin='0rem 0rem 1rem 0rem'),
                                      children=instance.name)
                second_line = _build_other_solution_dropdown() if enable_other_solution else \
                    html.Div(className='automated-text', style=dict(flex=1), children=current_solution.name)
                panel = html.Div(
                    className='panel',
                    children=[build_panel_banner(panel_title),
                              html.Div(className='panel-content', children=[first_line, second_line])]
                )
                return panel

            if self.language_is_english:
                current_solution_panel_title_prefix = "Current solution - "
                other_solution_panel_title_prefix = "Other solution - "
            elif self.language_is_french:
                current_solution_panel_title_prefix = "Solution courante - "
                other_solution_panel_title_prefix = "Autre solution - "
            else:
                raise ValueError(f"Language '{self.language}' is not supported.")

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
                            build_routes_figure_panel(solution=current_solution, is_current_solution=True,
                                                      panel_title_prefix=current_solution_panel_title_prefix,
                                                      language=self.language),
                            build_routes_figure_panel(solution=other_solution, is_current_solution=False,
                                                      panel_title_prefix=other_solution_panel_title_prefix,
                                                      language=self.language)
                        ]
                    ),
                    html.Div(
                        className="representation-panels-side-to-side",
                        children=[
                            build_schedules_figure_panel(solution=current_solution, is_current_solution=True,
                                                         panel_title_prefix=current_solution_panel_title_prefix,
                                                         language=self.language),
                            build_schedules_figure_panel(solution=other_solution, is_current_solution=False,
                                                         panel_title_prefix=other_solution_panel_title_prefix,
                                                         language=self.language)
                        ]
                    ),
                    html.Div(
                        className="panels-side-to-side",
                        children=[
                            build_solution_metrics_panel(current_solution, True,
                                                         panel_title_prefix=current_solution_panel_title_prefix,
                                                         horizontal=False, language=self.language),
                            build_solution_metrics_panel(other_solution, False,
                                                         panel_title_prefix=other_solution_panel_title_prefix,
                                                         horizontal=False, language=self.language)
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
                build_routes_figure(solution=other_solution, language=self.language),
                build_schedules_figure(solution=other_solution, language=self.language),
                build_solution_metrics_figures(solution=other_solution, reference_solution=current_solution,
                                               horizontal=False, language=self.language)
            )

        ##################################
        # Explainer tab content - Static #
        ##################################

        def _build_question_explanation_tab_content():
            """
            Build the tab content about the question-explanation.
            """

            # Some variables involved in various blocks of the tab content
            if self.language_is_english:
                contrastive_submit_button_label = "Submit"
                contrastive_ok_button_text = "Return"
            elif self.language_is_french:
                contrastive_submit_button_label = "Soumettre"
                contrastive_ok_button_text = "Retour"
            else:
                raise ValueError(f"Language '{self.language}' is not supported.")

            #########################
            # Explainer description #
            #########################

            def _build_explainer_description_panel():
                first_question_template = self._questions_templates[self._available_questions_templates_ids[0]]
                empty_question_text = first_question_template.text
                relevant_fields_values = dict()
                for field_number in range(3):
                    if field_number < first_question_template.nb_fields:
                        field_valid_value = first_question_template.compute_field_valid_values(
                            self.current_solution, field_number, relevant_fields_values
                        )[0]
                        relevant_fields_values[field_number] = field_valid_value
                relevant_fields_values_list = list(relevant_fields_values.values())
                if len(relevant_fields_values_list) == 1:
                    fields_values_as_text = f"{relevant_fields_values_list[0]}"
                else:
                    fields_values_as_text = ", ".join(relevant_fields_values_list)
                filled_question_text = \
                    first_question_template.complete_text_with_fields_values(relevant_fields_values)
                if self.language_is_french:
                    panel_title = "À propos de l'explication"
                    panel_text = f"La fonctionnalité d'explication permet de poser des questions à propos de la " \
                                 f"{self._current_solution_in_text()} et " \
                                 f"de recevoir en retour des réponses sous forme "
                    if self.explanations_representation_are_enabled:
                        panel_text += "de textes et de figures."
                    else:
                        panel_text += "de textes."
                    panel_text += f"{LINE_BREAK_STRING}"
                    panel_text += f"Sont mis à disposition ci-dessous : " \
                                  f"une représentation des itinéraires et des emplois du temps de la " \
                                  f"{self._current_solution_in_text(False)} identique à celle de l'onglet " \
                                  f"\"{self._solution_description_tab_title}\", "
                    if self.contrastive_statistics_are_enabled:
                        panel_text += f"un block de formulation de questions, un de présentation des réponses et " \
                                      f"un de statistiques sur les questions posées."
                    else:
                        panel_text += f"un block de formulation de questions et un de présentation des réponses."
                    panel_text += f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                    panel_text += f"• En ce qui concerne le block de formulation de questions, " \
                                  f"afin de formuler une question sur la {self._current_solution_in_text(False)}, " \
                                  f"un modèle de question doit être sélectionné parmi les " \
                                  f"{str(self.nb_questions_templates)} disponibles " \
                                  f"(par ex. \"{empty_question_text}\"). " \
                                  f"Puis des valeurs doivent être choisies (par ex. {fields_values_as_text}) " \
                                  f"pour compléter les champs de ce modèle de question. " \
                                  f"En cliquant sur le bouton \"{contrastive_submit_button_label}\", " \
                                  f"une réponse à la question complète (\"{filled_question_text}\") est générée." \
                                  f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                    panel_text += "• En ce qui concerne le block de présentation des réponses, "
                    if self.explanations_representation_are_enabled:
                        panel_text += "une réponse est affichée sous forme de texte, éventuellement accompagnée " \
                                      "de figures pour illustrer le texte. "
                    else:
                        panel_text += "une réponse est affichée sous forme de texte. "
                    panel_text += f"Une fois la réponse lue, cliquer sur le bouton \"{contrastive_ok_button_text}\" " \
                                  f"permet de réinitialiser les blocks de " \
                                  f"formulation de questions et de présentation des réponses. " \
                                  f"Il est alors possible de formuler une nouvelle question." \
                                  f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                    if self.contrastive_statistics_are_enabled:
                        panel_text += f"• Enfin, le block de statistiques permet de consuler " \
                                      f"combien de questions de chaque type ont été posées " \
                                      f"depuis le début de l'utilisation de l'outil." \
                                      f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                    if self.explanations_representation_are_enabled:
                        panel_text += "NB : lorsque l'explication traite d'un conflit temporel, " \
                                      "les figures illustrant le texte explicatif mettent l'accent sur " \
                                      "les éléments critiques impliqués dans le conflit. " \
                                      "Généralement, l'emploi du temps problématique est découpé en deux morceaux, " \
                                      "répartis sur deux lignes et articulés autour d'une tâche critique (en rouge). " \
                                      "Cette tâche est dupliquée intervient sur les deux lignes afin de " \
                                      "représenter l'impossibilité de satisfaire les contraintes temporelles " \
                                      "avant et après la tâche. " \
                                      "Les bornes temporelles problématiques sont également indiquées " \
                                      "par de fines lignes rouges. " \
                                      "Par opposition, les itinéraires et emplois du temps qui ne sont pas concernés " \
                                      "par l'explication sont atténués. " \
                                      "Enfin, des informations sont affichées sur la carte et sur le diagramme " \
                                      "de Gantt lorsque la souris est placée au-dessus des éléments d'intérêt."
                elif self.language_is_english:
                    panel_title = "About the explainer"
                    panel_text = f"The explainer feature allows to ask questions about the " \
                                 f"{self._current_solution_in_text()} and " \
                                 f"to receive back answers in the form of "
                    if self.explanations_representation_are_enabled:
                        panel_text += "texts and figures."
                    else:
                        panel_text += "texts."
                    panel_text += f"{LINE_BREAK_STRING}"
                    panel_text += f"The following are made available below: " \
                                  f"a representation of the routes and schedules of the " \
                                  f"{self._current_solution_in_text(False)} which is identical to that of the tab " \
                                  f"\"{self._solution_description_tab_title}\", " \
                                  f"a question formulation block and an answer presentation block." \
                                  f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                    panel_text += f"• As for the question formulation block, " \
                                  f"in order to formulate a question about the " \
                                  f"{self._current_solution_in_text(False)}, " \
                                  f"a question template must be selected among the " \
                                  f"{str(self.nb_questions_templates)} available (e.g. \"{empty_question_text}\"). " \
                                  f"Then values (e.g. {fields_values_as_text}) " \
                                  f"must be chosen to complete the fields of this question template. " \
                                  f"By clicking on the button \"{contrastive_submit_button_label}\" " \
                                  f"an answer to the completed question (\"{filled_question_text}\") is computed." \
                                  f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                    panel_text += "• As for the answer presentation block, "
                    if self.explanations_representation_are_enabled:
                        panel_text += "an answer is displayed in the form of text, possibly with figures " \
                                      "to illustrate the text. "
                    else:
                        panel_text += "an answer is displayed in the form of text. "
                    panel_text += f"Once the answer has been read, clicking on the button " \
                                  f"\"{contrastive_ok_button_text}\" allows to reset the question formulation " \
                                  f"and answer presentation blocks. " \
                                  f"It is then possible to formulate a new question." \
                                  f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                    if self.contrastive_statistics_are_enabled:
                        panel_text += f"• Finally, the statistics block allows to consult " \
                                      f"how many questions of each type have been asked " \
                                      f"since the beginning of the use of the tool." \
                                      f"{LINE_BREAK_STRING}{LINE_BREAK_STRING}"
                    if self.explanations_representation_are_enabled:
                        panel_text += "NB: when the explanation deals with a temporal conflict, " \
                                      "the figures illustrating the explanatory text emphasize " \
                                      "the critical elements involved in the conflict. " \
                                      "Generally, the problematic schedule is split into two parts, " \
                                      "distributed on two lines and articulated around a critical task (in red). " \
                                      "This task is duplicated on the two lines to represent the impossibility of " \
                                      "satisfying the temporal constraints before and after the task. " \
                                      "The problematic temporal boundaries are also indicated " \
                                      "by thin red lines. " \
                                      "By contrast, the routes and schedules that are not involved " \
                                      "in the explanation are attenuated. " \
                                      "Finally, information is displayed on the map and on the Gantt chart " \
                                      "when the mouse is placed over the elements of interest."
                else:
                    raise ValueError(f"Language '{self.language}' is not supported.")
                return build_text_panel(panel_title, panel_text, True)

            #########################
            # Contrastive / Why-not #
            #########################

            def _build_contrastive_question_block():
                #
                if self.language_is_english:
                    # For representation panels
                    current_solution_prefix = "Current solution - "
                    # For question panel
                    contrastive_question_type = \
                        "" if self.only_contrastive_questions_are_enabled else "'Why not?' "
                    question_panel_title = "Question" if self.only_contrastive_questions_are_enabled \
                        else f"{contrastive_question_type}question"
                    template_question_dropdown_placeholder = "Select a question template"
                    input_1_placeholder = "Fill input 1"
                    input_2_placeholder = "Fill input 2"
                    input_3_placeholder = "Fill input 3"
                    contrastive_question_text_placeholder = \
                        f"Waiting for a {contrastive_question_type}question to be defined..."
                elif self.language_is_french:
                    # For representation panels
                    current_solution_prefix = "Solution courante - "
                    # For question panel
                    contrastive_question_type = \
                        "" if self.only_contrastive_questions_are_enabled else " de type 'Pourquoi pas ?'"
                    question_panel_title = f"Question{contrastive_question_type}"
                    template_question_dropdown_placeholder = "Sélectionner un modèle de question"
                    input_1_placeholder = "Valeur 1"
                    input_2_placeholder = "Valeur 2"
                    input_3_placeholder = "Valeur 3"
                    contrastive_question_text_placeholder = \
                        f"En attente qu'une question{contrastive_question_type} soit définie..."
                else:
                    raise ValueError(f"Unsupported language: {self.language}")

                def _build_contrastive_question_panel():
                    """
                    Build the panel allowing the end-user to submit contrastive questions.
                    """
                    first_line = html.Div(
                        style=dict(display='flex', flexdirection='row'),
                        children=[
                            dcc.Dropdown(id='template-question-dropdown', className='dropdown',
                                         style=dict(flex=1),
                                         options=[{'label': self._questions_templates[key].text,
                                                   'value': key} for key in self._questions_templates.keys()],
                                         placeholder=template_question_dropdown_placeholder),
                            dcc.Dropdown(id='template-input-1', className='dropdown',
                                         style=dict(width='15rem', paddingLeft='1rem'),
                                         placeholder=input_1_placeholder),
                            dcc.Dropdown(id='template-input-2', className='dropdown',
                                         style=dict(width='15rem', paddingLeft='1rem'),
                                         placeholder=input_2_placeholder),
                            dcc.Dropdown(id='template-input-3', className='dropdown',
                                         style=dict(width='15rem', paddingLeft='1rem'),
                                         placeholder=input_3_placeholder),
                        ]
                    )
                    second_line = html.Div(
                        style=dict(paddingTop='1rem', display='flex', flexdirection='row'),
                        children=[
                            html.Div(id='contrastive-question-text', className='empty-automated-text',
                                     style=dict(flex=1, marginRight='1rem'),
                                     children=contrastive_question_text_placeholder),
                            html.Button(id='contrastive-submit-button', className='button',
                                        children=contrastive_submit_button_label, disabled=True)
                        ]
                    )
                    panel = html.Div(
                        id="question-panel", className='panel-with-bottom-margin',
                        children=[build_panel_banner(question_panel_title),
                                  html.Div(className='panel-content', children=[first_line, second_line])]
                    )
                    return panel

                block = \
                    html.Div(children=[
                        html.Div(className='representation-panels-side-to-side',
                                 children=[
                                     build_routes_figure_panel(
                                         solution=self.current_solution, is_current_solution=True,
                                         panel_title_prefix=current_solution_prefix, language=self.language
                                     ),
                                     build_schedules_figure_panel(
                                         solution=self.current_solution, is_current_solution=True,
                                         panel_title_prefix=current_solution_prefix, language=self.language
                                     )
                                 ]),
                        _build_contrastive_question_panel()
                    ])
                return block

            def _build_contrastive_explanation_block():
                #
                def _build_contrastive_explanation_panel():
                    """
                    Build the panel providing to the end-user contrastive explanations.
                    """
                    if self.language_is_english:
                        save_button_text = "Save"
                        what_if_button_text = "What if?"
                        how_to_button_text = "How to?"
                        contrastive_question_type = \
                            "" if self.only_contrastive_questions_are_enabled else "'Why not?' "
                        contrastive_explanation_text_placeholder = \
                            f"Waiting for a {contrastive_question_type}question to be submitted..."
                        contrastive_explanation_panel_title = \
                            ("Explanation" if self.only_contrastive_questions_are_enabled
                             else f"{contrastive_question_type}explanation")
                    elif self.language_is_french:
                        save_button_text = "Enregistrer"
                        what_if_button_text = "Et si ?"
                        how_to_button_text = "Comment ?"
                        contrastive_question_type = \
                            "" if self.only_contrastive_questions_are_enabled else " de type 'Pourquoi pas ?'"
                        contrastive_explanation_text_placeholder = \
                            f"En attente qu'une question{contrastive_question_type} soit soumise..."
                        contrastive_explanation_panel_title = f"Explication{contrastive_question_type}"
                    else:
                        raise ValueError(f"Unsupported language: {self.language}")
                    buttons = \
                        [html.Button(id='contrastive-ok-button', className='button',
                                     children=contrastive_ok_button_text, disabled=True)]
                    if self._explainer.history_is_enabled:
                        buttons.append(
                            html.Button(id='contrastive-save-button', className='button', style=dict(marginTop='1rem'),
                                        children=save_button_text, disabled=True)
                        )
                    if self._explainer.scenario_explanations_are_enabled:
                        buttons.append(
                            html.Button(id='what-if-button', className='button', style=dict(marginTop='1rem'),
                                        children=what_if_button_text, disabled=True)
                        )
                    if self._explainer.counterfactual_explanations_are_enabled:
                        buttons.append(
                            html.Button(id='how-to-button', className='button', style=dict(marginTop='1rem'),
                                        children=how_to_button_text, disabled=True)
                        )
                    panel = html.Div(
                        id='contrastive-explanation-panel', className='panel-with-bottom-margin',
                        children=[
                            build_panel_banner(contrastive_explanation_panel_title),
                            html.Div(
                                className='panel-content', style=dict(display='flex', flexDirection='row'),
                                children=[
                                    html.Div(id='contrastive-explanation-text', className='empty-automated-text',
                                             style=dict(flex=1, height='20rem', marginRight='1rem'),
                                             children=contrastive_explanation_text_placeholder),
                                    html.Div(style=dict(display='flex', flexDirection='column',
                                                        justifyContent='flex-end'),
                                             children=buttons)
                                ]
                            )
                        ]
                    )
                    return panel

                def _build_contrastive_statistics_panel():
                    """
                    Build the panel providing the statistics about contrastive explanations.
                    """
                    #
                    if self.language_is_english:
                        contrastive_question_type = \
                            "" if self.only_contrastive_questions_are_enabled else "'Why not?' "
                        statistics_panel_title = f"Statistics about submitted {contrastive_question_type}questions"
                        template_question_dropdown_placeholder = "Select a question template"
                        label_contrastive_statistics_text = "Number of questions based on such template asked: "
                        contrastive_statistics_text_placeholder = \
                            f"Waiting for a {contrastive_question_type}question template to be selected..."
                    elif self.language_is_french:
                        contrastive_question_type = \
                            "" if self.only_contrastive_questions_are_enabled else " de type 'Pourquoi pas ?'"
                        statistics_panel_title = f"Statistiques sur les questions{contrastive_question_type} soumises"
                        template_question_dropdown_placeholder = "Sélectionner un modèle de question"
                        label_contrastive_statistics_text = "Nombre de questions soumises basées sur ce modèle : "
                        contrastive_statistics_text_placeholder = \
                            f"En attente qu'un modèle de question{contrastive_question_type} soit sélectionné..."
                    else:
                        raise ValueError(f"Unsupported language: {self.language}")
                    first_line = html.Div(
                        style=dict(display='flex', flexdirection='row'),
                        children=[
                            dcc.Dropdown(id='contrastive-statistics-template-question-dropdown', className='dropdown',
                                         style=dict(flex=1),
                                         options=[{'label': self._questions_templates[key].text,
                                                   'value': key} for key in self._questions_templates.keys()],
                                         placeholder=template_question_dropdown_placeholder),
                        ]
                    )
                    second_line = html.Div(
                        style=dict(paddingTop='1rem', display='flex', flexdirection='row'),
                        children=[
                            html.Div(className='text', style=dict(padding='.4rem 1rem'),
                                     children=label_contrastive_statistics_text),
                            html.Div(id='contrastive-statistics-text', className='empty-automated-text',
                                     style=dict(flex=1),
                                     children=contrastive_statistics_text_placeholder)
                        ]
                    )
                    panel = html.Div(
                        id="contrastive-statistics-panel", className='panel-with-bottom-margin',
                        children=[build_panel_banner(statistics_panel_title),
                                  html.Div(className='panel-content', children=[first_line, second_line])]
                    )
                    return panel

                return html.Div(children=[
                    html.Div(id='contrastive-explanation-representation-envelope', style=dict(display='none')),
                    _build_contrastive_explanation_panel(),
                    _build_contrastive_statistics_panel() if self.contrastive_statistics_are_enabled else None
                ])

            ######################
            # Scenario / What-if #
            ######################

            def _build_scenario_block():
                #
                def _build_scenario_editable_employees_data_panel():
                    """
                    Build the panel allowing the end-user to edit the employees data for 'what-if' questions.
                    """
                    if self.language_is_english:
                        panel_title = "Editable employees data for 'What if?' question"
                    elif self.language_is_french:
                        panel_title = "Données relatives aux employés à éditer"
                    else:
                        raise ValueError(f"Unsupported language: {self.language}")
                    panel = html.Div(
                        id='scenario-editable-employees-data-panel',
                        children=build_employees_data_panel(self.current_instance, True, panel_title=panel_title,
                                                            editable=True, language=self.language)
                    )
                    return panel

                def _build_scenario_editable_tasks_data_panel():
                    """
                    Build the panel allowing the end-user to edit the tasks data for 'what-if' questions.
                    """
                    if self.language_is_english:
                        panel_title = "Editable tasks data for 'What if?' question"
                    elif self.language_is_french:
                        panel_title = "Données relatives aux tâches à éditer"
                    else:
                        raise ValueError(f"Unsupported language: {self.language}")
                    panel = html.Div(
                        id='scenario-editable-tasks-data-panel',
                        children=build_tasks_data_panel(self.current_instance, True, panel_title=panel_title,
                                                        editable=True, language=self.language)
                    )
                    return panel

                def _build_scenario_question_panel():
                    """
                    Build the panel allowing the end-user to submit 'what-if' questions.
                    """
                    if self.language_is_english:
                        scenario_question_panel_title = "'What if?' question"
                        scenario_question_text_placeholder = "Waiting for the definition of a 'What if?' question..."
                        submit_button_label = "Submit"
                        reset_button_label = "Reset"
                        cancel_button_label = "Return"
                    elif self.language_is_french:
                        scenario_question_panel_title = "Question de type 'Et si ?'"
                        scenario_question_text_placeholder = \
                            "En attente qu'une question de type 'Et si ?' soit définie..."
                        submit_button_label = "Soumettre"
                        reset_button_label = "Réinit."
                        cancel_button_label = "Retour"
                    else:
                        raise ValueError(f"Unsupported language: {self.language}")
                    buttons = [
                        html.Button(id='scenario-submit-button', className='button',
                                    children=submit_button_label, disabled=True),
                        html.Button(id='scenario-reset-button', className='button', style=dict(marginTop='1rem'),
                                    children=reset_button_label, disabled=True),
                        html.Button(id='scenario-return-button', className='button', style=dict(marginTop='1rem'),
                                    children=cancel_button_label, disabled=False)
                    ]
                    panel = html.Div(
                        id='scenario-question-panel', className='panel-with-bottom-margin',
                        children=[
                            build_panel_banner(scenario_question_panel_title),
                            html.Div(
                                className='panel-content', style=dict(display='flex', flexdirection='row'),
                                children=[
                                    html.Div(id='scenario-question-text', className='empty-automated-text',
                                             style=dict(flex=1, alignItems='end', marginRight='1rem'),
                                             children=scenario_question_text_placeholder),
                                    html.Div(style=dict(display='flex', flexDirection='column',
                                                        justifyContent='flex-end'),
                                             children=buttons)
                                ]
                            )
                        ]
                    )
                    return panel

                def _build_scenario_explanation_panel():
                    """
                    Build the panel providing to the end-user what-if explanations.
                    """
                    if self.language_is_english:
                        scenario_explanation_panel_title = "'What if?' explanation"
                        scenario_explanation_text_placeholder = "Waiting for a 'What if?' question to be submitted..."
                        save_button_text = "Save"
                    elif self.language_is_french:
                        scenario_explanation_panel_title = "Explication de type 'Et si ?'"
                        scenario_explanation_text_placeholder = \
                            "En attente qu'une question de type 'Et si ?' soit soumise..."
                        save_button_text = "Enregistrer"
                    else:
                        raise ValueError(f"Unsupported language: {self.language}")
                    buttons = [html.Button(id='scenario-ok-button', className='button', children="Ok", disabled=True)]
                    if self._explainer.history_is_enabled:
                        buttons.append(
                            html.Button(id='scenario-save-button', className='button', style=dict(marginTop='1rem'),
                                        children=save_button_text, disabled=True)
                        )
                    panel = html.Div(
                        id='scenario-explanation-panel', className='panel-with-bottom-margin',
                        children=[
                            build_panel_banner(scenario_explanation_panel_title),
                            html.Div(
                                className='panel-content', style=dict(display='flex', flexDirection='row'),
                                children=[
                                    html.Div(id='scenario-explanation-text', className='empty-automated-text',
                                             style=dict(flex=1, height='20rem', marginRight='1rem'),
                                             children=scenario_explanation_text_placeholder),
                                    html.Div(
                                        style=dict(display='flex', flexDirection='column', justifyContent='flex-end'),
                                        children=buttons
                                    )
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
                #             build_panel_banner("How-to question"),
                #             html.Div(
                #                 className='panel-content', style=dict(display='flex', flexdirection='row'),
                #                 children=[
                #                     html.Div(id='how-to-question-text', className='empty-automated-text',
                #                              style=dict(flex=1, marginRight='1rem'),
                #                              children="Waiting for the definition of a 'how-to' question..."),
                #                     html.Button(id='how-to-explain-button', className='button', children="Submit",
                #                                 disabled=False)
                #                 ]
                #             )
                #         ]
                #     )
                #     return panel

                def _build_counterfactual_explanation_panel():
                    """
                    Build the panel providing to the end-user 'how-to' explanations.
                    """
                    if self.language_is_english:
                        counterfactual_explanation_panel_title = "'How to? explanation"
                        counterfactual_explanation_text_placeholder = \
                            "Waiting for a 'How to?' question to be submitted..."
                        save_button_text = "Save"
                    elif self.language_is_french:
                        counterfactual_explanation_panel_title = "Explication de type 'comment-faire'"
                        counterfactual_explanation_text_placeholder = \
                            "En attente qu'une question de type 'Comment faire pour?' soit soumise..."
                        save_button_text = "Enregistrer"
                    else:
                        raise ValueError(f"Unsupported language: {self.language}")
                    buttons = [
                        html.Button(id='counterfactual-ok-button', className='button', children="Ok", disabled=True)
                    ]
                    if self._explainer.history_is_enabled:
                        buttons.append(
                            html.Button(id='counterfactual-save-button', className='button',
                                        style=dict(marginTop='1rem'), children=save_button_text, disabled=True)
                        )
                    panel = html.Div(
                        id='counterfactual-explanation-panel', className='panel-with-bottom-margin',
                        children=[
                            build_panel_banner(counterfactual_explanation_panel_title),
                            html.Div(
                                className='panel-content', style=dict(display='flex', flexDirection='row'),
                                children=[
                                    html.Div(id='counterfactual-explanation-text', className='empty-automated-text',
                                             style=dict(flex=1, height='20rem', marginRight='1rem', overflow='scroll'),
                                             children=counterfactual_explanation_text_placeholder),
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

            blocks = [(_build_explainer_description_panel() if self.tab_description_panels_are_enabled else None),
                      _build_contrastive_question_block(), _build_contrastive_explanation_block()]
            if self._explainer.scenario_explanations_are_enabled:
                blocks.append(_build_scenario_block())
            if self._explainer.counterfactual_explanations_are_enabled:
                blocks.append(_build_how_to_block())
            tab_content = html.Div(id="explainer-tab-content", children=blocks)
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
            Output('template-input-3', 'options'), Input('template-question-dropdown', 'value'),
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
            Input('template-question-dropdown', 'value'), Input('template-input-1', 'value'),
            Input('template-input-2', 'value'), Input('template-input-3', 'value')
        )
        def _update_contrastive_question_text(question_template_id: str, input_1: str, input_2: str, input_3: str):
            # Case where the questions templates dropdown is empty
            if question_template_id is None:
                if self.language_is_english:
                    contrastive_question_type = \
                        "" if self.only_contrastive_questions_are_enabled else "'Why not?' "
                    contrastive_question_text_placeholder = \
                        f"Waiting for a {contrastive_question_type}question to be defined..."
                elif self.language_is_french:
                    contrastive_question_type = \
                        "" if self.only_contrastive_questions_are_enabled else " de type 'Pourquoi pas ?'"
                    contrastive_question_text_placeholder = \
                        f"En attente qu'une question{contrastive_question_type} soit définie..."
                else:
                    raise NotImplementedError(f"Language {self.language} is not supported")
                return contrastive_question_text_placeholder, 'empty-automated-text'
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
            Input('contrastive-submit-button', 'n_clicks'), Input('contrastive-ok-button', 'n_clicks'),
            State('template-question-dropdown', 'value'), State('template-input-1', 'value'),
            State('template-input-2', 'value'), State('template-input-3', 'value')
        )
        def _update_contrastive_explanation_text_and_representation(
                contrastive_submit_button_click: int, contrastive_ok_button_click: int,
                question_template_id: str, input_1: str, input_2: str, input_3: str):
            if (contrastive_submit_button_click is None) and (contrastive_ok_button_click is None):
                raise PreventUpdate
            if contrastive_submit_button_click == 1:
                question_template = self._questions_templates[question_template_id]
                fields_values = [value for value in [input_1, input_2, input_3][:question_template.nb_fields]]
                explanation = self._explainer.get_contrastive_explanation(question_template_id, fields_values)
                infeasibility = None if explanation.support_solution_is_feasible else explanation.infeasibility
                explanation_text = convert_from_string_to_html(explanation.text)
                solution = explanation.support_solution
                if self.explanations_representation_are_enabled and \
                        (infeasibility is None or not infeasibility.is_due_to_skill_considerations):
                    explanation_repr_visibility = dict(display='block')
                    if self.language_is_english:
                        # f"{'Feasible' if explanation.support_solution_is_feasible else 'Infeasible'}"
                        panel_title_prefix = \
                            f"{'Feasible' if explanation.support_solution_is_feasible else 'Infeasible'}" \
                            f" solution involved in explanation - "
                        panel_title_suffix = ""
                    elif self.language_is_french:
                        # f"{'faisable' if explanation.support_solution_is_feasible else 'infaisable'} - "
                        # NB: mentioning feasibility in the title does not fit in the panel header
                        panel_title_prefix = "Solution intervenant dans l'explication - "
                        panel_title_suffix = ""
                    else:
                        raise NotImplementedError(f"Language {self.language} is not supported")
                    explanation_repr = html.Div(
                        className='representation-panels-side-to-side',
                        children=[
                            build_routes_figure_panel(
                                solution=solution, is_current_solution=False,
                                panel_title_prefix=panel_title_prefix, panel_title_suffix=panel_title_suffix,
                                infeasibility=infeasibility, language=self.language
                            ),
                            build_schedules_figure_panel(
                                solution=solution, is_current_solution=False,
                                panel_title_prefix=panel_title_prefix, panel_title_suffix=panel_title_suffix,
                                infeasibility=infeasibility, language=self.language
                            )
                        ]
                    )
                else:
                    explanation_repr_visibility = dict(display='none')
                    explanation_repr = html.Div()
                return explanation_text, 'automated-text', explanation_repr_visibility, explanation_repr, None, None
            elif contrastive_ok_button_click == 1:
                if self.language_is_english:
                    contrastive_question_type = \
                        "" if self.only_contrastive_questions_are_enabled else "'why not?' "
                    explanation_text = f"Waiting for a {contrastive_question_type}question to be submitted..."
                elif self.language_is_french:
                    contrastive_question_type = \
                        "" if self.only_contrastive_questions_are_enabled else " de type 'Pourquoi pas ?'"
                    explanation_text = f"En attente qu'une question{contrastive_question_type} soit soumise..."
                else:
                    raise NotImplementedError(f"Language {self.language} is not supported")
                return explanation_text, 'empty-automated-text', dict(display='none'), html.Div(), None, None
            else:
                raise NotImplementedError("There is a problem with contrastive submit button or ok button #clicks")

        def _update_contrastive_ok_button_status_aux(contrastive_explanation_text_style: str,
                                                     what_if_button_click: int = None,
                                                     how_to_button_click: int = None):
            if contrastive_explanation_text_style == 'empty-automated-text':
                return True
            else:
                if what_if_button_click is None and how_to_button_click is None:
                    return False
                elif what_if_button_click == 1 or how_to_button_click == 1:
                    return True
                else:
                    raise NotImplementedError("There is a problem with what-if or how-to buttons #clicks")

        if self._explainer.scenario_explanations_are_disabled:
            #
            if self._explainer.counterfactual_explanations_are_disabled:
                @self._application.callback(
                    Output('contrastive-ok-button', 'disabled'), Input('contrastive-explanation-text', 'className')
                )
                def _update_contrastive_ok_button_status(contrastive_explanation_text_style: str):
                    return _update_contrastive_ok_button_status_aux(contrastive_explanation_text_style, None, None)
            else:
                @self._application.callback(
                    Output('contrastive-ok-button', 'disabled'),
                    Input('contrastive-explanation-text', 'className'), Input('how-to-button', 'n_clicks')
                )
                def _update_contrastive_ok_button_status(contrastive_explanation_text_style: str,
                                                         how_to_button_click: int = None):
                    return _update_contrastive_ok_button_status_aux(contrastive_explanation_text_style,
                                                                    None, how_to_button_click)
        #
        else:
            if self._explainer.counterfactual_explanations_are_enabled:
                @self._application.callback(
                    Output('contrastive-ok-button', 'disabled'), Input('contrastive-explanation-text', 'className'),
                    Input('what-if-button', 'n_clicks'), Input('how-to-button', 'n_clicks')
                )
                def _update_contrastive_ok_button_status(contrastive_explanation_text_style: str,
                                                         what_if_button_click: int, how_to_button_click: int):
                    return _update_contrastive_ok_button_status_aux(contrastive_explanation_text_style,
                                                                    what_if_button_click, how_to_button_click)
            else:
                @self._application.callback(
                    Output('contrastive-ok-button', 'disabled'),
                    Input('contrastive-explanation-text', 'className'), Input('what-if-button', 'n_clicks')
                )
                def _update_contrastive_ok_button_status(contrastive_explanation_text_style: str,
                                                         what_if_button_click: int):
                    return _update_contrastive_ok_button_status_aux(contrastive_explanation_text_style,
                                                                    what_if_button_click, None)

        if self._explainer.history_is_enabled:
            #
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

        if self._explainer.scenario_explanations_are_enabled:
            #
            @self._application.callback(
                Output('what-if-button', 'disabled'), Input('contrastive-ok-button', 'disabled')
            )
            def _update_what_if_buttons_status(contrastive_ok_button_disabled: bool):
                if contrastive_ok_button_disabled:
                    return True
                else:
                    if self._explainer.last_contrastive_explanation.support_solution_is_feasible:
                        return True
                    else:
                        return False

            @self._application.callback(
                Output('what-if-button', 'n_clicks'), Input('scenario-return-button', 'n_clicks'),
            )
            def _reset_what_if_button_click(scenario_cancel_button_click: int):
                if scenario_cancel_button_click is None:
                    raise PreventUpdate
                elif scenario_cancel_button_click == 1:
                    return None
                else:
                    raise NotImplementedError("There is a problem with the scenario ok button #clicks")

        if self._explainer.counterfactual_explanations_are_enabled:
            #
            @self._application.callback(
                Output('how-to-button', 'disabled'), Input('contrastive-ok-button', 'disabled')
            )
            def _update_how_to_buttons_status(contrastive_ok_button_disabled: bool):
                if contrastive_ok_button_disabled:
                    return True
                else:
                    contrastive_explanation = self._explainer.last_contrastive_explanation
                    if contrastive_explanation.support_solution_is_feasible:
                        return True
                    else:
                        if (contrastive_explanation.question.template.id in
                                self._explainer.activated_counterfactual_questions_templates_ids):
                            return False
                        else:
                            return True

            @self._application.callback(
                Output('how-to-button', 'n_clicks'), Input('counterfactual-ok-button', 'n_clicks')
            )
            def _reset_how_to_button_click(counterfactual_ok_button_click: int):
                if counterfactual_ok_button_click is None:
                    raise PreventUpdate
                if counterfactual_ok_button_click == 1:
                    return None
                else:
                    raise NotImplementedError("There is a problem with the scenario ok button #clicks")

        @self._application.callback(
            Output('contrastive-statistics-text', 'children'), Output('contrastive-statistics-text', 'className'),
            Input('contrastive-statistics-template-question-dropdown', 'value'),
            Input('contrastive-explanation-text', 'className')
        )
        def _update_contrastive_statistics_text(question_template_id: str, contrastive_explanation_text_style: str):
            # Case where the questions templates dropdown is empty
            if question_template_id is None:
                if self.language_is_english:
                    contrastive_question_type = \
                        "" if self.only_contrastive_questions_are_enabled else "'Why not?' "
                    contrastive_question_text_placeholder = \
                        f"Waiting for a {contrastive_question_type}question to be selected..."
                elif self.language_is_french:
                    contrastive_question_type = \
                        "" if self.only_contrastive_questions_are_enabled else " de type 'Pourquoi pas ?'"
                    contrastive_question_text_placeholder = \
                        f"En attente qu'un modèle de question{contrastive_question_type} soit sélectionné..."
                else:
                    raise NotImplementedError(f"Language {self.language} is not supported")
                return contrastive_question_text_placeholder, 'empty-automated-text'
            # Case where the questions templates dropdown is non-empty
            else:
                statistics_text = str(self._explainer.get_contrastive_questions_asked_count(question_template_id))
                return statistics_text, 'automated-text'

        ################################################
        # Explainer tab content - Call back - Scenario #
        ################################################

        if self._explainer.scenario_explanations_are_enabled:
            #
            @self._application.callback(
                Output('scenario-question-block', 'style'), Input('what-if-button', 'n_clicks')
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
                Output('scenario-submit-button', 'n_clicks'), Input('scenario-question-block', 'style')
            )
            def _reset_scenario_submit_button_click(scenario_envelope_style):
                if scenario_envelope_style['display'] in ['none', 'block']:
                    return None
                else:
                    raise NotImplementedError("There is a problem with the scenario envelope style")

            @self._application.callback(
                Output('scenario-return-button', 'n_clicks'), Input('scenario-question-block', 'style')
            )
            def _reset_scenario_cancel_button_click(scenario_envelope_style):
                if scenario_envelope_style['display'] in ['none', 'block']:
                    return None
                else:
                    raise NotImplementedError("There is a problem with the scenario envelope style")

            @self._application.callback(
                Output('editable-instance-employees-data-table', 'data'),
                Output('editable-instance-tasks-data-table', 'data'),
                Output('scenario-reset-button', 'n_clicks'),
                Input('editable-instance-employees-data-table', 'data'),
                Input('editable-instance-tasks-data-table', 'data'),
                Input('what-if-button', 'n_clicks'), Input('scenario-reset-button', 'n_clicks')
            )
            def _build_maintain_and_reset_editable_data_tables(employees_data, tasks_data, what_if_button_click: int,
                                                               reset_button_click: int):
                current_instance = self.current_instance
                if reset_button_click is not None:
                    if reset_button_click == 1:
                        return (build_employees_data(current_instance, self.language),
                                build_tasks_data(current_instance, self.language), None)
                    else:
                        raise NotImplementedError("There is a problem with the scenario reset button #clicks")
                if what_if_button_click is None:
                    for row in employees_data:
                        employee = current_instance.get_employee_by_name(row['name'])
                        if (convert_time_string_to_nb_minutes(row['start']) != employee.start_time_LB or
                                convert_time_string_to_nb_minutes(row['end']) != employee.end_time_UB):
                            return (build_employees_data(current_instance, self.language),
                                    build_tasks_data(current_instance, self.language), reset_button_click)
                    for row in tasks_data:
                        task = current_instance.get_task_by_name(row['name'])
                        if (convert_time_string_to_nb_minutes(row['start']) != task.start_time_LB or
                                convert_time_string_to_nb_minutes(row['end']) != task.end_time_UB or
                                row['duration'] != task.duration):
                            return (build_employees_data(current_instance, self.language),
                                    build_tasks_data(current_instance, self.language), reset_button_click)
                    raise PreventUpdate
                elif what_if_button_click == 1:
                    corrected = False
                    hour_format = get_hour_format_associated_with_language(self.language)
                    for row in employees_data:
                        employee = current_instance.get_employee_by_name(row['name'])
                        try:
                            data_in_right_format = convert_nb_minutes_to_time_string(
                                convert_time_string_to_nb_minutes(row['start']), hour_format)
                            if row['start'] != data_in_right_format:
                                row['start'] = data_in_right_format
                                corrected = True
                        except ValueError:
                            row['start'] = convert_nb_minutes_to_time_string(employee.start_time_LB, hour_format)
                            corrected = True
                        try:
                            data_in_right_format = convert_nb_minutes_to_time_string(
                                convert_time_string_to_nb_minutes(row['end']), hour_format)
                            if row['end'] != data_in_right_format:
                                row['end'] = data_in_right_format
                                corrected = True
                        except ValueError:
                            row['end'] = convert_nb_minutes_to_time_string(employee.end_time_UB, hour_format)
                            corrected = True
                    if corrected:
                        return employees_data, tasks_data, reset_button_click
                    for row in tasks_data:
                        task = current_instance.get_task_by_name(row['name'])
                        try:
                            data_in_right_format = convert_nb_minutes_to_time_string(
                                convert_time_string_to_nb_minutes(row['start']), hour_format)
                            if row['start'] != data_in_right_format:
                                row['start'] = data_in_right_format
                                corrected = True
                        except ValueError:
                            row['start'] = convert_nb_minutes_to_time_string(task.start_time_LB, hour_format)
                            corrected = True
                        try:
                            data_in_right_format = convert_nb_minutes_to_time_string(
                                convert_time_string_to_nb_minutes(row['end']), hour_format)
                            if row['end'] != data_in_right_format:
                                row['end'] = data_in_right_format
                                corrected = True
                        except ValueError:
                            row['end'] = convert_nb_minutes_to_time_string(task.end_time_UB, hour_format)
                            corrected = True
                        try:
                            row['duration'] = int(row['duration'])
                        except ValueError:
                            row['duration'] = task.duration
                            corrected = True
                    if corrected:
                        return employees_data, tasks_data, reset_button_click
                    raise PreventUpdate
                else:
                    raise NotImplementedError("There is a problem with the what-if button #clicks")

            @self._application.callback(
                Output('editable-instance-employees-data-table', 'style_data_conditional'),
                Input('editable-instance-employees-data-table', 'data')
            )
            def _update_scenario_employees_data_conditional_style(employees_data):
                return build_employees_data_conditional_style(employees_data, self.current_instance)

            @self._application.callback(
                Output('editable-instance-tasks-data-table', 'style_data_conditional'),
                Input('editable-instance-tasks-data-table', 'data')
            )
            def _update_scenario_tasks_data_style(tasks_data):
                return build_tasks_data_conditional_style(tasks_data, self.current_instance)

            @self._application.callback(
                Output('scenario-question-text', 'children'), Output('scenario-question-text', 'className'),
                Input('editable-instance-employees-data-table', 'data'),
                Input('editable-instance-tasks-data-table', 'data')
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
                        end_time_UB=(None if employee.end_time_UB == end_time_UB else end_time_UB),
                        hour_format=get_hour_format_associated_with_language(self.language)
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
                        duration=(None if task.duration == duration else duration),
                        hour_format=get_hour_format_associated_with_language(self.language)
                    )
                self._scenario_instance_alterations = instance_alterations
                if self.language_is_english:
                    question_text = f"What if tasks data are changed as follows?{LINE_BREAK_STRING}" \
                                    f"{instance_alterations.as_string(True, self.language)}"
                elif self.language_is_french:
                    question_text = f"Et si les données relatives aux tâches étaient modifiées comme suit ?" \
                                    f"{LINE_BREAK_STRING}" \
                                    f"{instance_alterations.as_string(True, self.language)}"
                else:
                    raise NotImplementedError(f"Language {self.language} is not supported")
                question_text = convert_from_string_to_html(question_text)
                return question_text, 'automated-text'

            @self._application.callback(
                Output('scenario-submit-button', 'disabled'),
                Input('scenario-question-text', 'className'), Input('scenario-explanation-text', 'className')
            )
            def _update_scenario_submit_button_status(scenario_question_text_style: str,
                                                      scenario_explanation_text_style: str):
                if scenario_question_text_style == 'empty-automated-text':
                    return True
                elif scenario_question_text_style == 'automated-text':
                    if (self._scenario_instance_alterations.nb_changes == 0 or
                            scenario_explanation_text_style == 'automated-text'):
                        return True
                    else:
                        return False
                else:
                    raise NotImplementedError("There is a problem with the scenario question or explanation "
                                              "texts styles")

            @self._application.callback(
                Output('scenario-reset-button', 'disabled'),
                Input('scenario-question-text', 'className'), Input('scenario-explanation-text', 'className')
            )
            def _update_scenario_reset_button_status(scenario_question_text_style: str,
                                                     scenario_explanation_text_style: str):
                if scenario_question_text_style == 'empty-automated-text':
                    return True
                elif scenario_question_text_style == 'automated-text':
                    if (self._scenario_instance_alterations.nb_changes == 0 or
                            scenario_explanation_text_style == 'automated-text'):
                        return True
                    else:
                        return False
                else:
                    raise NotImplementedError("There is a problem with the scenario question or explanation "
                                              "texts styles")

            @self._application.callback(
                Output('scenario-return-button', 'disabled'), Input('scenario-explanation-text', 'className')
            )
            def _update_scenario_cancel_button_status(scenario_explanation_text_style: str):
                if scenario_explanation_text_style == 'empty-automated-text':
                    return False
                elif scenario_explanation_text_style == 'automated-text':
                    return True
                else:
                    raise NotImplementedError("There is a problem with the scenario explanation text style")

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
                        if self.language_is_english:
                            explanation_text = "Waiting for a 'What if?' question to be submitted..."
                        elif self.language_is_french:
                            explanation_text = "En attente qu'une question de type 'Et si ?' soit soumise..."
                        else:
                            raise NotImplementedError(f"Language {self.language} is not supported")
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
                    if self.language_is_english:
                        panel_title_prefix = \
                            f"{'Feasible' if explanation.support_solution_is_feasible else 'Infeasible'}" \
                            f" solution involved in 'What if?' explanation - "
                        panel_title_suffix = ""
                    elif self.language_is_french:
                        panel_title_prefix = "Solution intervenant dans l'explication - "
                        panel_title_suffix = ""
                    else:
                        raise NotImplementedError(f"Language {self.language} is not supported")
                    explanation_repr = html.Div(
                        className='representation-panels-side-to-side',
                        children=[
                            build_routes_figure_panel(
                                solution=explanation.support_solution, is_current_solution=False,
                                panel_title_prefix=panel_title_prefix, panel_title_suffix=panel_title_suffix,
                                infeasibility=(None if explanation.support_solution_is_feasible
                                               else explanation.infeasibility),
                                language=self.language
                            ),
                            build_schedules_figure_panel(
                                solution=explanation.support_solution, is_current_solution=False,
                                panel_title_prefix=panel_title_prefix, panel_title_suffix=panel_title_suffix,
                                infeasibility=(None if explanation.support_solution_is_feasible
                                               else explanation.infeasibility),
                                language=self.language
                            )
                        ]
                    )
                    return explanation_text, 'automated-text', explanation_repr_visibility, explanation_repr
                else:
                    raise NotImplementedError("There is a problem with the scenario submit button #clicks")

            @self._application.callback(
                Output('scenario-editable-employees-data-panel', 'children'),
                Output('scenario-editable-tasks-data-panel', 'children'),
                Input('scenario-reset-button', 'n_clicks')
            )
            def _reset_scenario_editable_data(scenario_reset_button_click: int):
                if scenario_reset_button_click is None or scenario_reset_button_click == 0:
                    raise PreventUpdate
                elif scenario_reset_button_click == 1:
                    if self.language_is_english:
                        employees_data_panel_title = "Editable employees data for 'What if?' question"
                        tasks_data_panel_title = "Editable tasks data for 'What if?' question"
                    elif self.language_is_french:
                        employees_data_panel_title = "Données relatives aux employés à éditer"
                        tasks_data_panel_title = "Données relatives aux tâches à éditer"
                    else:
                        raise ValueError(f"Unsupported language: {self.language}")
                    return (build_employees_data_panel(self.current_instance, True,
                                                       panel_title=employees_data_panel_title,
                                                       editable=True, language=self.language),
                            build_tasks_data_panel(self.current_instance, True, panel_title=tasks_data_panel_title,
                                                   editable=True, language=self.language))
                else:
                    raise NotImplementedError("There is a problem with scenario ok or reset button #clicks")

            @self._application.callback(
                Output('scenario-ok-button', 'disabled'), Input('scenario-explanation-text', 'className')
            )
            def _update_scenario_ok_button_status(scenario_explanation_text_style: str):
                if scenario_explanation_text_style == 'empty-automated-text':
                    return True
                else:
                    return False

            @self._application.callback(
                Output('scenario-ok-button', 'n_clicks'),
                Input('scenario-explanation-text', 'className')
            )
            def _reset_scenario_ok_button_click(scenario_explanation_text_style: str):
                if scenario_explanation_text_style == 'empty-automated-text':
                    return None
                elif scenario_explanation_text_style == 'automated-text':
                    raise PreventUpdate
                else:
                    raise NotImplementedError("There is a problem with the scenario explanation text style")

            if self._explainer.history_is_enabled:
                #
                @self._application.callback(
                    Output('scenario-save-button', 'disabled'),
                    Input('scenario-explanation-text', 'className'), Input('scenario-save-button', 'n_clicks')
                )
                def _update_scenario_save_button_status(scenario_explanation_text_style: str,
                                                        scenario_save_button_click: int):
                    if scenario_explanation_text_style == 'empty-automated-text':
                        return True
                    elif scenario_explanation_text_style == 'automated-text':
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
                    else:
                        raise NotImplementedError("There is a problem with the scenario explanation text style")

                @self._application.callback(
                    Output('scenario-save-button', 'n_clicks'),
                    Input('scenario-explanation-text', 'className'), State('scenario-save-button', 'n_clicks')
                )
                def _reset_scenario_save_button_click(scenario_explanation_text_style: str,
                                                      scenario_save_button_click: int):
                    if scenario_explanation_text_style == 'empty-automated-text':
                        return None
                    elif scenario_explanation_text_style == 'automated-text':
                        return scenario_save_button_click
                    else:
                        raise NotImplementedError("There is a problem with the scenario explanation text style")

        ######################################################
        # Explainer tab content - Call back - Counterfactual #
        ######################################################

        if self._explainer.counterfactual_explanations_are_enabled:
            #
            @self._application.callback(
                Output('counterfactual-question-block', 'style'), Input('how-to-button', 'n_clicks')
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
                    if self.language_is_english:
                        explanation_text = "Waiting for a 'How to?' question to be submitted..."
                    elif self.language_is_french:
                        explanation_text = "En attente d'une question de type 'Comment faire pour ?'..."
                    else:
                        raise ValueError(f"Unsupported language: {self.language}")
                    return explanation_text, 'empty-automated-text', dict(display='none'), html.Div()
                elif how_to_button_click >= 1:
                    explanation = self._explainer.compute_counterfactual_explanation()
                    explanation_text = convert_from_string_to_html(explanation.text)
                    explanation_repr_visibility = dict(display='block')
                    if self.language_is_english:
                        panel_title_prefix = "Solution involved in 'How to?' explanation - "
                        panel_title_suffix = ""
                    elif self.language_is_french:
                        panel_title_prefix = "Solution intervenant dans l'explication - "
                        panel_title_suffix = ""
                    else:
                        raise ValueError(f"Unsupported language: {self.language}")
                    explanation_repr = html.Div(
                        className='representation-panels-side-to-side',
                        children=[
                            build_routes_figure_panel(
                                solution=explanation.support_solution, is_current_solution=False,
                                panel_title_prefix=panel_title_prefix, panel_title_suffix=panel_title_suffix,
                                language=self.language
                            ),
                            build_schedules_figure_panel(
                                solution=explanation.support_solution, is_current_solution=False,
                                panel_title_prefix=panel_title_prefix, panel_title_suffix=panel_title_suffix,
                                language=self.language
                            )
                        ]
                    )
                    return explanation_text, 'automated-text', explanation_repr_visibility, explanation_repr
                else:
                    raise NotImplementedError("There is a problem with the how-to button #clicks")

            @self._application.callback(
                Output('counterfactual-ok-button', 'disabled'), Input('counterfactual-explanation-text', 'className')
            )
            def _update_counterfactual_ok_button_status(counterfactual_explanation_text_style: str):
                if counterfactual_explanation_text_style == 'empty-automated-text':
                    return True
                else:
                    return False

            @self._application.callback(
                Output('counterfactual-ok-button', 'n_clicks'), Input('counterfactual-question-block', 'style')
            )
            def _reset_counterfactual_ok_button_click(counterfactual_envelope_style):
                if counterfactual_envelope_style['display'] in ['none', 'block']:
                    return None
                else:
                    raise NotImplementedError("There is a problem with the counterfactual envelope style")

            if self._explainer.history_is_enabled:
                #
                @self._application.callback(
                    Output('counterfactual-save-button', 'disabled'),
                    Input('counterfactual-explanation-text', 'className'),
                    Input('counterfactual-save-button', 'n_clicks')
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
                    Input('counterfactual-explanation-text', 'className'),
                    State('counterfactual-save-button', 'n_clicks')
                )
                def _reset_counterfactual_save_button_click(counterfactual_explanation_text_style: str,
                                                            counterfactual_save_button_click: int):
                    if counterfactual_explanation_text_style == 'empty-automated-text':
                        return None
                    else:
                        return counterfactual_save_button_click

        ##########
        # Layout #
        ##########

        self._application.layout = _build_layout()

    ###############
    # Application #
    ###############

    @property
    def application(self):
        return self._application

    def launch(self):
        """
        Launch the web Graphic User Interface of the explainer.
        """
        self._application.run_server(debug=False)

    #################
    # Configuration #
    #################

    @property
    def language(self):
        return self._explainer.language

    @property
    def language_is_english(self):
        return self._explainer.language_is_english

    @property
    def language_is_french(self):
        return self._explainer.language_is_french

    #########################
    # Solution and instance #
    #########################

    @property
    def current_solution(self):
        return self._explainer.current_solution

    @current_solution.setter
    def current_solution(self, solution: Solution):
        self._explainer.current_solution = solution

    def _current_solution_in_text(self, with_name: bool = True):
        if self.history_is_enabled:
            if self.language_is_english:
                text = "current solution"
            elif self.language_is_french:
                text = "solution courante"
            else:
                raise NotImplementedError(f"Unsupported language: {self.language}")
            if with_name:
                text += f" {self._explainer.current_solution.name}"
            return text
        else:
            if self.language_is_english:
                return "studied solution"
            elif self.language_is_french:
                return "solution étudiée"
            else:
                raise NotImplementedError(f"Unsupported language: {self.language}")

    @property
    def current_instance(self):
        return self._explainer.current_instance

    def _current_instance_in_text(self, with_name: bool = True):
        if self.history_is_enabled:
            if self.language_is_english:
                text = f"current instance"
            elif self.language_is_french:
                text = f"instance courante"
            else:
                raise NotImplementedError(f"Unsupported language: {self.language}")
            if with_name:
                text += f" {self._explainer.current_instance.name}"
            return text
        else:
            if self.language_is_english:
                return "studied instance"
            elif self.language_is_french:
                return "instance étudiée"
            else:
                raise NotImplementedError(f"Unsupported language: {self.language}")

    ###################
    # Functionalities #
    ###################

    @property
    def tab_description_panels_are_enabled(self):
        return self._tab_description_panels_are_enabled

    @property
    def tab_description_panels_are_disabled(self):
        return not self._tab_description_panels_are_enabled

    def enable_tab_description_panels(self):
        self._tab_description_panels_are_enabled = True

    def disable_tab_description_panels(self):
        self._tab_description_panels_are_enabled = False

    @property
    def explanations_are_enabled(self):
        return self._explanations_are_enabled

    @property
    def explanations_are_disabled(self):
        return not self._explanations_are_enabled

    # NB: cannot enable/disable explanations while GUI is launched

    # def enable_explanations(self):
    #     self._explanations_are_enabled = True

    # def disable_explanations(self):
    #     self._explanations_are_enabled = False
    #     self.disable_explanations_representation()
    #     self.disable_history()
    #     self.disable_scenario_explanations()
    #     self.disable_counterfactual_explanations()

    @property
    def nb_questions_templates(self):
        return len(self._questions_templates)

    @property
    def contrastive_statistics_are_enabled(self):
        return self._contrastive_statistics_are_enabled

    @property
    def contrastive_statistics_are_disabled(self):
        return not self._contrastive_statistics_are_enabled

    def enable_contrastive_statistics(self):
        self._contrastive_statistics_are_enabled = True

    def disable_contrastive_statistics(self):
        self._contrastive_statistics_are_enabled = False

    @property
    def history_is_enabled(self):
        return self._explainer.history_is_enabled

    @property
    def history_is_disabled(self):
        return self._explainer.history_is_disabled

    def enable_history(self):
        self._explainer.enable_history()

    def disable_history(self):
        self._explainer.disable_history()

    @property
    def scenario_explanations_are_enabled(self):
        return self._explainer.scenario_explanations_are_enabled

    @property
    def scenario_explanations_are_disabled(self):
        return self._explainer.scenario_explanations_are_disabled

    def enable_scenario_explanations(self):
        self._explainer.enable_scenario_explanations()

    def disable_scenario_explanations(self):
        self._explainer.disable_scenario_explanations()

    @property
    def counterfactual_explanations_are_enabled(self):
        return self._explainer.counterfactual_explanations_are_enabled

    @property
    def counterfactual_explanations_are_disabled(self):
        return self._explainer.counterfactual_explanations_are_disabled

    def enable_counterfactual_explanations(self):
        self._explainer.enable_counterfactual_explanations()

    def disable_counterfactual_explanations(self):
        self._explainer.disable_counterfactual_explanations()

    @property
    def only_contrastive_questions_are_enabled(self):
        return (self._explainer.scenario_explanations_are_disabled and
                self._explainer.counterfactual_explanations_are_disabled)

    @property
    def explanations_representation_are_enabled(self):
        return self._explanations_representation_are_enabled

    @property
    def explanations_representation_are_disabled(self):
        return not self._explanations_representation_are_enabled

    def enable_explanations_representation(self):
        self._explanations_representation_are_enabled = True

    def disable_explanations_representation(self):
        self._explanations_representation_are_enabled = False
