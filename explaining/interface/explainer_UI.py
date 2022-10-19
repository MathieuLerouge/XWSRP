# Standard libraries
import re
import sys
import time

# Third-party libraries
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from PyQt5 import QtWidgets

# Local libraries
from drawing.constants import *
from drawing.KPIs import create_KPIs_comparison_figure
from drawing.figuresmanager import FiguresManager
from drawing.routes import create_routes_figure
from drawing.schedules import create_schedules_figure
from explaining._constants_deprecated import *
from explaining._explainer_deprecated import ExplainerDeprecated


# Global variables
QUESTION_WITH_EMPLOYEE_KEYS = [
    WHY_REALIZING_INSTEAD_OF_KEY, WHY_NOT_REALIZING_INSTEAD_OF_KEY,
    WHY_NOT_PERFORMING_JUST_AFTER_KEY, WHY_NOT_PERFORMING_BETWEEN_KEY, WHY_NOT_PERFORMING_IN_ADDITION_KEY,
    WHY_NOT_REALIZING_AT_ANOTHER_TIME_KEY,
    WHAT_IF_INSERTING_KEY, WHAT_IF_REALIZING_KEY, WHAT_IF_REORDERING_KEY,
    HOW_REALIZING_IN_ADDITION_KEY
]
QUESTION_WITHOUT_EMPLOYEE_KEYS = [WHY_NOT_REALIZED_KEY]


# Class ExplainerUIContent
class ExplainerUIContent(QtWidgets.QMainWindow):
    _label_style = "font-weight: bold"
    _text_style = "background-color: white; padding: 3px; margin: 3px"
    _title_style = "QGroupBox {font-size: 16pt; font-weight: bold;}"
    _ordered_questions_keys = [
        WHY_NOT_PERFORMING_JUST_AFTER_KEY, WHY_NOT_PERFORMING_BETWEEN_KEY, WHY_NOT_PERFORMING_IN_ADDITION_KEY,
        WHY_NOT_REALIZING_INSTEAD_OF_KEY,
        WHY_NOT_REALIZING_AT_ANOTHER_TIME_KEY, WHY_NOT_REALIZED_KEY,
        WHAT_IF_INSERTING_KEY, WHAT_IF_REALIZING_KEY, WHAT_IF_REORDERING_KEY,
        HOW_REALIZING_IN_ADDITION_KEY
    ]
    _nb_fields_for_questions = 3

    def __init__(self, geometry, explainer: ExplainerDeprecated):
        super(ExplainerUIContent, self).__init__()

        # Set the explainer
        self._explainer = explainer
        self._questions_keys = [key for key in self._ordered_questions_keys if key in explainer.questions_keys]
        self._last_explanation_solution = None

        # Set questions templates related variables
        # self.threeFieldsTemplatesIndices = [0, 1]
        # self.twoFieldsTemplatesIndices = [2, 3, 4]

        # Set the figures manager
        self._figures_manager = FiguresManager(explainer.current_solution)
        self._figures = dict()

        # Define main window
        self.setGeometry(geometry)
        self.setWindowTitle("X-WSRP")
        # self.menuBar = QtWidgets.QMenuBar(self)
        # self.menuBar.setGeometry(0, 0, self.mainWidth, 30)
        # self.setMenuBar(self.menuBar)

        # Define main layout and main widget
        self._main_layout = QtWidgets.QGridLayout()
        self._main_layout.setRowStretch(0, 5)
        self._main_layout.setRowStretch(1, 3)
        self._main_layout.setColumnStretch(0, 4)
        self._main_layout.setColumnStretch(1, 1)
        self.mainWidget = QtWidgets.QWidget(self)
        self.mainWidget.setLayout(self._main_layout)
        self.setCentralWidget(self.mainWidget)

        # Setup drawings group
        self._figures_canvas = {
            ROUTES_FIGURE_KEY: QtWidgets.QWidget(),
            SCHEDULES_FIGURE_KEY: QtWidgets.QWidget(),
            KPIS_FIGURE_KEY: QtWidgets.QWidget()
        }
        self._setup_drawings_group()

        # Setup questioning-explanation group
        self._setup_question_explanation_group()

        # Setup history group
        self._setup_history_group()

    @property
    def current_solution(self):
        return self._explainer.current_solution

    @property
    def questions_keys(self):
        return self._questions_keys

    @property
    def _routes_figure(self) -> Figure:
        return self._figures[ROUTES_FIGURE_KEY]

    @_routes_figure.setter
    def _routes_figure(self, routes_figure: Figure):
        self._figures[ROUTES_FIGURE_KEY] = routes_figure

    @property
    def _schedules_figure(self) -> Figure:
        return self._figures[SCHEDULES_FIGURE_KEY]

    @_schedules_figure.setter
    def _schedules_figure(self, schedules_figure: Figure):
        self._figures[SCHEDULES_FIGURE_KEY] = schedules_figure

    @property
    def _KPIs_figure(self) -> Figure:
        return self._figures[KPIS_FIGURE_KEY]

    @_KPIs_figure.setter
    def _KPIs_figure(self, KPIs_figure: Figure):
        self._figures[KPIS_FIGURE_KEY] = KPIs_figure

    @property
    def routes_figure(self) -> Figure:
        return self._figures[ROUTES_FIGURE_KEY]

    @property
    def schedules_figure(self) -> Figure:
        return self._figures[SCHEDULES_FIGURE_KEY]

    @property
    def KPIs_figure(self) -> Figure:
        return self._figures[KPIS_FIGURE_KEY]

    @property
    def _routes_canvas(self) -> QtWidgets.QWidget:
        return self._figures_canvas[ROUTES_FIGURE_KEY]

    @_routes_canvas.setter
    def _routes_canvas(self, canvas: FigureCanvas):
        self._figures_canvas[ROUTES_FIGURE_KEY] = canvas

    @property
    def _schedules_canvas(self) -> QtWidgets.QWidget:
        return self._figures_canvas[SCHEDULES_FIGURE_KEY]

    @_schedules_canvas.setter
    def _schedules_canvas(self, canvas: FigureCanvas):
        self._figures_canvas[SCHEDULES_FIGURE_KEY] = canvas

    @property
    def _KPIs_canvas(self) -> QtWidgets.QWidget:
        return self._figures_canvas[KPIS_FIGURE_KEY]

    @_KPIs_canvas.setter
    def _KPIs_canvas(self, canvas: FigureCanvas):
        self._figures_canvas[KPIS_FIGURE_KEY] = canvas

    #############
    # Questions #
    #############

    def get_question_by_index(self, index):
        return self._explainer.get_question(self.questions_keys[index])

    ##################
    # Drawings group #
    ##################

    def _setup_drawings_group(self):

        # Setup the drawings layout
        self._drawing_layout = QtWidgets.QGridLayout()
        self._drawing_layout.setRowStretch(0, 1)
        self._drawing_layout.setColumnStretch(0, 2)
        self._drawing_layout.setColumnStretch(1, 2)
        self._drawing_layout.setColumnStretch(2, 1)

        # Create the drawings
        self.update_drawing_group()

        # Create a drawings group and insert it in the main layout
        drawings_group = QtWidgets.QGroupBox(self.mainWidget)
        drawings_group.setTitle("Solutions representations")
        drawings_group.setStyleSheet(self._title_style)
        drawings_group.setLayout(self._drawing_layout)
        self._main_layout.addWidget(drawings_group, 0, 0, 1, 2)

    def update_drawing_group(self):
        self._figures = self._figures_manager.get_solution_figures(self.current_solution, True)
        self._update_drawing_layout()

    def _update_drawing_layout(self):
        self._routes_canvas = FigureCanvas(self.routes_figure)
        self._schedules_canvas = FigureCanvas(self.schedules_figure)
        self._KPIs_canvas = FigureCanvas(self.KPIs_figure)
        self._drawing_layout.addWidget(self._routes_canvas, 0, 0)
        self._drawing_layout.addWidget(self._schedules_canvas, 0, 1)
        self._drawing_layout.addWidget(self._KPIs_canvas, 0, 2)

    ################################
    # Question - ExplanationDeprecated group #
    ################################

    def _setup_question_explanation_group(self):

        # Initialize the questioning-explanation group
        QX_group = QtWidgets.QGroupBox(self.mainWidget)

        # Create the questioning drop-down list and its (fixed) label
        template_question_label = QtWidgets.QLabel(QX_group)
        template_question_label.setText("Select template: ")
        template_question_label.setStyleSheet(self._label_style)
        self._question_DD_list = QtWidgets.QComboBox(QX_group)
        self._question_DD_list.addItems(
            [re.sub(r"{\d+}", "_", self._explainer.get_question(key).text) for key in self.questions_keys]
        )
        self._question_DD_list.currentIndexChanged.connect(self._react_to_question_DD_list_change)

        # Initialize fields labels and fields drop-down lists
        self._fields_labels = [QtWidgets.QLabel() for j in range(self._nb_fields_for_questions)]
        self._fields_DD_lists = [QtWidgets.QComboBox(QX_group) for j in range(self._nb_fields_for_questions)]
        for j in range(self._nb_fields_for_questions):
            self._fields_labels[j].setText("Very very long pattern")
            self._fields_labels[j].setStyleSheet(self._label_style)
            label_policy = self._fields_DD_lists[j].sizePolicy()
            label_policy.setRetainSizeWhenHidden(True)
            self._fields_DD_lists[j].setSizePolicy(label_policy)
            self._fields_DD_lists[j].currentTextChanged.connect(lambda: self._react_to_field_DD_list_change(j))
        fields_filters_names = ["skill-feasible", "non-performed", "employee's", "non-employee's"]
        self._fields_filters = dict([(name, QtWidgets.QCheckBox(name)) for name in fields_filters_names])

        # Initialize questioning label (completed text) and its (fixed) label
        filled_question_label = QtWidgets.QLabel(QX_group)
        filled_question_label.setText("Question to explain: ")
        filled_question_label.setStyleSheet(self._label_style)
        self._question_text = QtWidgets.QLabel(QX_group)
        self._question_text.setStyleSheet(self._text_style)
        self._question_text.setWordWrap(True)

        # Initialize explanation label (text) and its (fixed) label
        explanation_label = QtWidgets.QLabel(QX_group)
        explanation_label.setText("ExplanationDeprecated: ")
        explanation_label.setStyleSheet(self._label_style)
        self._explanation_text = QtWidgets.QLabel(QX_group)
        self._explanation_text.setStyleSheet(self._text_style)
        self._explanation_text.setWordWrap(True)

        # Create explain button
        self._explain_button = QtWidgets.QPushButton(QX_group)
        self._explain_button.setText("Explain")
        self._explain_button.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self._explain_button.clicked.connect(self._react_to_explain_button_click)

        # Create got-it button
        self._got_it_button = QtWidgets.QPushButton(QX_group)
        self._got_it_button.setText("Got it")
        self._got_it_button.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self._got_it_button.clicked.connect(self._react_to_got_it_button_click)
        self._got_it_button.setEnabled(False)

        # Create save button
        self._save_button = QtWidgets.QPushButton(QX_group)
        self._save_button.setText("Save")
        self._save_button.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self._save_button.clicked.connect(self._react_to_save_button_click)
        self._save_button.setEnabled(False)

        # Create save button
        self._forget_button = QtWidgets.QPushButton(QX_group)
        self._forget_button.setText("Forget")
        self._forget_button.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self._forget_button.clicked.connect(self._react_to_forget_button_click)
        self._forget_button.setEnabled(False)

        # Setup the questioning layout
        # - First columns
        QX_layout = QtWidgets.QGridLayout()
        for j in range(3):
            shift_due_to_filters = 0 if j < 2 else 2
            QX_layout.setColumnStretch(3 * j + shift_due_to_filters, 3)
            QX_layout.setColumnStretch(3 * j + 1 + shift_due_to_filters, 2)
        for j in range(2):
            shift_due_to_filters = 0 if j < 1 else 2
            QX_layout.setColumnStretch(3 * j + 2 + shift_due_to_filters, 2)
        QX_layout.setColumnStretch(10, 1)
        for i in range(3):
            QX_layout.setRowStretch(4 + i, 1)
        QX_layout.addWidget(template_question_label, 0, 0)
        QX_layout.addWidget(self._question_DD_list, 0, 1, 1, 9)
        for j in range(3):
            shift_due_to_filters = 0 if j < 2 else 2
            QX_layout.addWidget(self._fields_labels[j], 1, 3 * j + shift_due_to_filters, 2, 1)
            QX_layout.addWidget(self._fields_DD_lists[j], 1, 3 * j + 1 + shift_due_to_filters, 2, 1)
        QX_layout.addWidget(self._fields_filters["skill-feasible"], 1, 5)
        QX_layout.addWidget(self._fields_filters["non-performed"], 1, 6)
        QX_layout.addWidget(self._fields_filters["employee's"], 2, 5)
        QX_layout.addWidget(self._fields_filters["non-employee's"], 2, 6)
        QX_layout.addWidget(filled_question_label, 3, 0)
        QX_layout.addWidget(self._question_text, 3, 1, 1, 9)
        QX_layout.addWidget(explanation_label, 4, 0, 3, 1)
        QX_layout.addWidget(self._explanation_text, 4, 1, 3, 9)
        # - Last column
        QX_layout.addWidget(self._explain_button, 0, 10, 4, 1)
        QX_layout.addWidget(self._got_it_button, 4, 10)
        QX_layout.addWidget(self._save_button, 5, 10)
        QX_layout.addWidget(self._forget_button, 6, 10)

        # Insert the questioning-explanation group in the main layout
        QX_group.setTitle("Question - explanation")
        QX_group.setStyleSheet(self._title_style)
        QX_group.setLayout(QX_layout)
        self._main_layout.addWidget(QX_group, 1, 0)

        # Create the fields, texts and button
        self.update_question_explanation_group()

    def update_question_explanation_group(self):
        self._react_to_question_DD_list_change()

    def _react_to_question_DD_list_change(self):

        # Clear explanation text
        self._explanation_text.setText("")

        # Setup fields depending on the selected questioning
        question = self.get_question_by_index(self._question_DD_list.currentIndex())
        question_key = question.key
        if question.has_field_of_type(0, EMPLOYEE_FIELD_KEY):

            # Get the name of former selected employee
            employee_name = self._fields_DD_lists[0].currentText()

            # Setup the first field's label and drop-down list for an employee selection
            self._fields_labels[0].setText("Select employee: ")
            self._fields_DD_lists[0].setVisible(True)
            self._fields_DD_lists[0].currentTextChanged.disconnect()
            self._fields_DD_lists[0].clear()
            self._fields_DD_lists[0].addItems(list(self.current_solution.instance.employees_names))
            index = self._fields_DD_lists[0].findText(employee_name)
            if index >= 0:
                self._fields_DD_lists[0].setCurrentIndex(index)
            self._fields_DD_lists[0].currentTextChanged.connect(lambda: self._react_to_field_DD_list_change(0))

            # If the template questioning has a second field to fill with a task
            if question.has_field_of_type(1, TASK_FIELD_KEY):

                # Setup the second field's label for an activity selection
                self._fields_labels[1].setText("Select task: ")
                self._fields_DD_lists[1].setVisible(True)

                # Setup the second field's filters
                self._set_default_filters()

                # Setup the third's field label for an activity selection or nothing depending on the questioning
                if question.has_field_of_type(2, ACTIVITY_FIELD_KEY):
                    self._fields_labels[2].setText("Select activity: ")
                    self._fields_DD_lists[2].setVisible(True)
                else:
                    self._fields_labels[2].setText("")
                    self._fields_DD_lists[2].setVisible(False)

                # Update the other fields' drop-down lists by reaction to the first field change
                self._react_to_field_DD_list_change(0)

            # If the template questioning does not have a second field to fill with a task
            else:

                # Set the second and third fields to be empty
                self._fields_labels[1].setText("")
                self._fields_DD_lists[1].setVisible(False)
                for filter_name in self._fields_filters.keys():
                    self._fields_filters[filter_name].setVisible(False)
                self._fields_labels[2].setText("")
                self._fields_DD_lists[2].setVisible(False)

                # Update the questioning text
                self.update_question_label()

        else:

            # Setup the first field's label and drop-down list for an employee selection
            self._fields_labels[0].setText("")
            # self.fieldsDDLists[0].currentTextChanged.disconnect()
            # self.fieldsDDLists[0].clear()
            # self.fieldsDDLists[0].currentTextChanged.connect(lambda: self.fieldDDListChanged(0))
            self._fields_DD_lists[0].setVisible(False)

            # Setup the second field's label for an activity selection
            self._fields_labels[1].setText("Select task: ")
            self._fields_DD_lists[1].setVisible(True)

            # Setup the second field's filters
            self._set_default_filters()

            # Setup the third's field to be empty
            self._fields_labels[2].setText("")
            self._fields_DD_lists[2].setVisible(False)

            # Add to the second DD list the names of all the tasks that are not performed by any employee
            self._fields_DD_lists[1].currentTextChanged.disconnect()
            self._fields_DD_lists[1].clear()
            self._fields_DD_lists[1].addItems(
                self.current_solution.filter_tasks_names(None, False, True, False, False)
            )
            self._fields_DD_lists[1].currentTextChanged.connect(lambda: self._react_to_field_DD_list_change(1))

            # Update the second field drop-down list
            self._react_to_field_DD_list_change(1)

        # else:
        #
        #     # Setup all fields to be empty
        #     for j in range(3):
        #         self._fields_labels[j].setText("")
        #         self._fields_DD_lists[j].setVisible(False)
        #     for filter_name in self._fields_filters.keys():
        #         self._fields_filters[filter_name].setVisible(False)
        #
        #     # Update the questioning text
        #     self.update_question_label()

    def _react_to_field_DD_list_change(self, field_index: int):

        # If first drop-down list is changed
        if field_index == 0:

            # Get the current template questioning and the selected employee
            question = self.get_question_by_index(self._question_DD_list.currentIndex())
            employee = self.current_solution.instance.get_employee_by_name(self._fields_DD_lists[0].currentText())

            # If the current template questioning has a first field which must be filled with a task,
            if question.has_field_of_type(1, TASK_FIELD_KEY):

                # Add to the second DD list the names of all the filtered tasks
                task_name = self._fields_DD_lists[1].currentText()
                self._fields_DD_lists[1].currentTextChanged.disconnect()
                self._fields_DD_lists[1].clear()
                filtered_tasks_names = self.current_solution.filter_tasks_names(
                    employee,
                    self._fields_filters["skill-feasible"].isChecked(),
                    self._fields_filters["non-performed"].isChecked(),
                    self._fields_filters["employee's"].isChecked(),
                    self._fields_filters["non-employee's"].isChecked()
                )
                self._fields_DD_lists[1].addItems(filtered_tasks_names)
                index = self._fields_DD_lists[1].findText(task_name)
                if index >= 0:
                    self._fields_DD_lists[1].setCurrentIndex(index)
                self._fields_DD_lists[1].currentTextChanged.connect(
                    lambda: self._react_to_field_DD_list_change(1)
                )

            # If the current template questioning has a first field which must be filled with a task,
            if question.has_field_of_type(2, ACTIVITY_FIELD_KEY):

                # Add to the third DD list the names of the tasks or activities that are performed by the employee
                self._fields_DD_lists[2].currentTextChanged.disconnect()
                self._fields_DD_lists[2].clear()
                if self.get_question_by_index(self._question_DD_list.currentIndex()).key == \
                        WHY_NOT_PERFORMING_JUST_AFTER_KEY:
                    performed_activities_names = [
                        activity.name
                        for activity in self.current_solution.get_sequence(employee).get_contained_activities(
                            True, False, True, True
                        )
                    ]
                    self._fields_DD_lists[2].addItems(performed_activities_names)
                else:
                    performed_tasks_names = [
                        task.name for task in self.current_solution.get_sequence(employee).get_contained_tasks(True)
                    ]
                    self._fields_DD_lists[2].addItems(performed_tasks_names)
                self._fields_DD_lists[2].currentTextChanged.connect(lambda: self._react_to_field_DD_list_change(2))

            # Update questioning text
            self.update_question_label()

        # If second or third drop-down list is changed
        elif field_index in [1, 2]:

            # Update questioning text
            self.update_question_label()

        # If anything else,
        else:
            raise Exception("There is something wrong with the reaction to questioning field change")

    def _set_default_filters(self, force_skill_feasible_checked: bool = False,
                             force_non_realized_check: bool = False,
                             force_non_employee_check: bool = False):
        question = self.get_question_by_index(self._question_DD_list.currentIndex())
        question_key = question.key
        if question.has_field_of_type(1, TASK_FIELD_KEY):
            if question_key == WHY_NOT_REALIZING_INSTEAD_OF_KEY:
                enabled = {"skill-feasible": True, "non-performed": True, "employee's": False, "non-employee's": False}
                checked = {"skill-feasible": False, "non-performed": False, "employee's": False, "non-employee's": True}
            elif question_key == WHY_NOT_PERFORMING_JUST_AFTER_KEY:
                enabled = {"skill-feasible": True, "non-performed": True, "employee's": True, "non-employee's": True}
                checked = {"skill-feasible": False, "non-performed": False, "employee's": False, "non-employee's": False}
            elif question_key in [WHY_NOT_PERFORMING_BETWEEN_KEY, WHY_NOT_PERFORMING_IN_ADDITION_KEY,
                                  WHAT_IF_INSERTING_KEY, WHAT_IF_REALIZING_KEY, HOW_REALIZING_IN_ADDITION_KEY]:
                enabled = {"skill-feasible": True, "non-performed": True, "employee's": False, "non-employee's": False}
                checked = {"skill-feasible": False, "non-performed": False, "employee's": False, "non-employee's": True}
            elif question_key in [WHY_NOT_REALIZING_AT_ANOTHER_TIME_KEY, "Realizing"]:
                enabled = {"skill-feasible": False, "non-performed": False, "employee's": False, "non-employee's": False}
                checked = {"skill-feasible": False, "non-performed": False, "employee's": True, "non-employee's": False}
            elif question_key in [WHY_NOT_REALIZED_KEY]:
                enabled = {"skill-feasible": False, "non-performed": False, "employee's": False, "non-employee's": False}
                checked = {"skill-feasible": False, "non-performed": True, "employee's": False, "non-employee's": False}
            else:
                raise Exception(f"There is something wrong with default filter and questioning with {question_key}")
            checked["skill-feasible"] = checked["skill-feasible"] or force_skill_feasible_checked
            checked["non-performed"] = checked["non-performed"] or force_non_realized_check
            if checked["non-performed"]:
                enabled["employee's"] = False
            checked["non-employee's"] = checked["non-employee's"] or force_non_employee_check
            if checked["non-performed"]:
                enabled["employee's"] = False
            for filter_name in self._fields_filters.keys():
                self._fields_filters[filter_name].setVisible(True)
                self._fields_filters[filter_name].disconnect()
                self._fields_filters[filter_name].setEnabled(enabled[filter_name])
                self._fields_filters[filter_name].setChecked(checked[filter_name])
                # self._fields_filters[filter_name].toggled.connect(
                # lambda: self._react_to_filter_toggle(filter_name))
            self._fields_filters["skill-feasible"].toggled.connect(
                lambda: self._react_to_filter_toggle("skill-feasible")
            )
            self._fields_filters["non-performed"].toggled.connect(
                lambda: self._react_to_filter_toggle("non-performed")
            )
            self._fields_filters["employee's"].toggled.connect(
                lambda: self._react_to_filter_toggle("employee's")
            )
            self._fields_filters["non-employee's"].toggled.connect(
                lambda: self._react_to_filter_toggle("non-employee's")
            )

    def _react_to_filter_toggle(self, filter_key: str):

        # Handle non-performed filter influence over other filters
        if filter_key == "non-performed":
            if self._fields_filters["non-performed"].isChecked():
                self._fields_filters["employee's"].disconnect()
                self._fields_filters["employee's"].setEnabled(False)
                self._fields_filters["employee's"].setChecked(False)
                self._fields_filters["employee's"].toggled.connect(lambda: self._react_to_filter_toggle("employee's"))
            else:
                self._set_default_filters(
                    self._fields_filters["skill-feasible"].isChecked(), False,
                    self._fields_filters["non-employee's"].isChecked()
                )

        # Handle employee's filter influence over other filters
        elif filter_key == "employee's":
            if self._fields_filters["employee's"].isChecked():
                enabled = {"skill-feasible": False, "non-performed": False, "non-employee's": False}
                checked = {"skill-feasible": True, "non-performed": False, "non-employee's": False}
                for filter_key in enabled.keys():
                    self._fields_filters[filter_key].disconnect()
                    self._fields_filters[filter_key].setEnabled(enabled[filter_key])
                    self._fields_filters[filter_key].setChecked(checked[filter_key])
                    self._fields_filters[filter_key].toggled.connect(lambda: self._react_to_filter_toggle(filter_key))
            else:
                self._set_default_filters()

        # Handle employee's filter influence over other filters
        elif filter_key == "non-employee's":
            if self._fields_filters["non-employee's"].isChecked():
                self._fields_filters["employee's"].disconnect()
                self._fields_filters["employee's"].setEnabled(False)
                self._fields_filters["employee's"].setChecked(False)
                self._fields_filters["employee's"].toggled.connect(lambda: self._react_to_filter_toggle("employee's"))
            else:
                self._set_default_filters(
                    self._fields_filters["skill-feasible"].isChecked(),
                    self._fields_filters["non-performed"].isChecked(), False
                )

        # Get the _name of the selected employee
        employee_name = self._fields_DD_lists[0].currentText()

        # Add to the second DD list the names of all the _tasks that are not performed by the employee
        self._fields_DD_lists[1].currentTextChanged.disconnect()
        self._fields_DD_lists[1].clear()
        filtered_tasks_names = self.current_solution.filter_tasks_names(
            self.current_solution.instance.get_employee_by_name(employee_name),
            self._fields_filters["skill-feasible"].isChecked(),
            self._fields_filters["non-performed"].isChecked(),
            self._fields_filters["employee's"].isChecked(),
            self._fields_filters["non-employee's"].isChecked()
        )
        self._fields_DD_lists[1].addItems(filtered_tasks_names)
        self._fields_DD_lists[1].currentTextChanged.connect(lambda: self._react_to_field_DD_list_change(1))

        # Update questioning text
        self.update_question_label()

    def _set_explanation_and_history_enabled(self, toggle: bool):
        self._question_DD_list.setEnabled(toggle)
        for j in range(3):
            self._fields_DD_lists[j].setEnabled(toggle)
        if toggle:
            self._set_default_filters()
        else:
            for filter_name in self._fields_filters.keys():
                self._fields_filters[filter_name].setEnabled(False)
        self._explain_button.setEnabled(toggle)
        self._solutions_history.setEnabled(toggle)

    def update_question_label(self):
        question = self.get_question_by_index(self._question_DD_list.currentIndex())
        for i in range(question.nb_fields):
            question.fields[i].name = self._fields_DD_lists[i].currentText()
        self._question_text.setText(question.text)

    def _react_to_explain_button_click(self):

        # Disable DD lists and explain button
        self._set_explanation_and_history_enabled(False)

        # Compute explanation to template questioning
        question_key = self.get_question_by_index(self._question_DD_list.currentIndex()).key
        fields_values = dict(
            [(j, self._fields_DD_lists[j].currentText()) for j in range(self._nb_fields_for_questions)]
        )
        time_before_computation = time.time()
        explanation = self._explainer.compute_explanation_deprecated(question_key, fields_values)
        print(explanation.solution)
        computation_duration = time.time() - time_before_computation
        print("* Question:")
        print(self._question_text.text())
        print("* ExplanationDeprecated:")
        print(explanation.text)
        print(f"(ExplanationDeprecated computed in {np.round(computation_duration, 3)} seconds)")
        print()

        # Update explanation text
        self._explanation_text.setText(explanation.text)

        # If the explanation computation has led to a new solution
        if explanation.has_new_solution:

            # Show new solution
            self._last_explanation_solution = explanation.solution
            self._show_last_explanation_solution(explanation.infeasibility, explanation.critical_bounds)

            # Show save and forget buttons or got-it button if feasible or not
            if explanation.solution_is_feasible:
                self._save_button.setEnabled(True)
                self._forget_button.setEnabled(True)
            else:
                self._got_it_button.setEnabled(True)

        # If the explanation computation has not led to a new solution
        else:
            # Show got it button
            self._got_it_button.setEnabled(True)

    def _react_to_got_it_button_click(self):

        # Clear explanation text, new solution, enable and disable buttons
        self._react_to_any_answer_button_click()

        # Update drawing group
        self._KPIs_canvas.setVisible(True)
        self._schedules_canvas.setVisible(True)
        self.update_drawing_group()

    def _react_to_save_button_click(self):

        # Save new solution in history
        self._explainer.store_last_explanation_feasible_solution()
        self._solutions_history.addItem(self._last_explanation_solution.name)

        # Clear explanation text, new solution, enable and disable buttons
        self._react_to_any_answer_button_click()

        # Set current row to last item and update group
        self._solutions_history.setCurrentRow(self._solutions_history.count() - 1)

    def _react_to_forget_button_click(self):

        # Clear explanation text, new solution, enable and disable buttons
        self._react_to_any_answer_button_click()

        # Update drawing group
        self.update_drawing_group()

    def _react_to_any_answer_button_click(self):

        # Clear explanation text
        self._explanation_text.setText("")

        # Clear last explanation solution
        if self._last_explanation_solution is not None:
            self._last_explanation_solution = None
            self._routes_figure.clf()
            self._schedules_figure.clf()
            self._KPIs_figure.clf()
            plt.close(self._routes_figure)
            plt.close(self._schedules_figure)
            plt.close(self._KPIs_figure)

        # Enable explanation and history back
        self._set_explanation_and_history_enabled(True)

        # Disable save and forget buttons
        self._got_it_button.setEnabled(False)
        self._save_button.setEnabled(False)
        self._forget_button.setEnabled(False)

    def _show_last_explanation_solution(self, infeasibility=None, critical_bounds=None):
        if infeasibility is None:
            self._routes_figure = create_routes_figure(
                self._last_explanation_solution, for_UI=True
            )
            self._schedules_figure = create_schedules_figure(
                self._last_explanation_solution, critical_bounds=critical_bounds, for_UI=True
            )
            self._KPIs_figure = create_KPIs_comparison_figure(
                [self.current_solution, self._last_explanation_solution], for_UI=True
            )
        else:
            self._routes_figure = create_routes_figure(
                self._last_explanation_solution, infeasibility=infeasibility, for_UI=True
            )
            self._schedules_figure = create_schedules_figure(
                self._last_explanation_solution,
                infeasibility=infeasibility, critical_bounds=critical_bounds, for_UI=True
            )
            self._KPIs_figure = plt.figure()
        self._update_drawing_layout()

    #################
    # History group #
    #################

    def _setup_history_group(self):

        # Initialize history group
        history_group = QtWidgets.QGroupBox(self.mainWidget)

        # Create a history of inputs
        history_label = QtWidgets.QLabel()
        history_label.setText("Select a solution:")
        history_label.setStyleSheet(self._label_style)
        self._solutions_history = QtWidgets.QListWidget(history_group)
        self._solutions_history.addItem(self.current_solution.name)
        self._solutions_history.setCurrentRow(0)
        self._solutions_history.itemSelectionChanged.connect(self._react_to_selected_solution_change)

        # Setup the history layout
        history_layout = QtWidgets.QVBoxLayout()
        history_layout.addWidget(history_label)
        history_layout.addWidget(self._solutions_history)

        # Set the history layout within the main layout
        history_group.setTitle("Solutions history")
        history_group.setStyleSheet(self._title_style)
        history_group.setLayout(history_layout)
        self._main_layout.addWidget(history_group, 1, 1)

    def _react_to_selected_solution_change(self):
        self._explainer.set_current_solution_by_name(self._solutions_history.currentItem().text())
        self.update_drawing_group()
        self.update_question_explanation_group()


# Class ExplainerUI
class ExplainerUI:

    def __init__(self, explainer: ExplainerDeprecated):
        self._application = QtWidgets.QApplication(sys.argv)
        self._content = ExplainerUIContent(self._application.desktop().availableGeometry(), explainer)

    def display(self):
        self._content.show()
        sys.exit(self._application.exec_())
