###########
# Modules #
###########


# Basic modules
from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sys
import re
import time
import numpy as np


# Project modules
from Drawing.drawer import *
from Explanation.explainer import *



############################
# Class ExplainerUIContent #
############################


class ExplainerUIContent(QtWidgets.QMainWindow):


    #----------------#
    # Initialization #
    #----------------#


    def __init__(self, geometry, explainer: Explainer):
        super(ExplainerUIContent, self).__init__()

        # Set styles
        self.labelStyle = "font-weight: bold"
        self.textStyle = "background-color: white; padding: 3px; margin: 3px"
        self.titleStyle = "QGroupBox::title{font-size: 24pt; font-weight: bold}"

        # Store explainer and drawer
        self.explainer = explainer
        self.drawer = Drawer(solution = explainer.currentSolution)
        self.newSolution = None

        # Store questions templates
        self.threeFieldsTemplatesIndices = [0, 1]
        self.twoFieldsTemplatesIndices = [2, 3, 4]

        # Define main window
        self.setGeometry(geometry)
        self.setWindowTitle("X-WSRP")
        # self.menuBar = QtWidgets.QMenuBar(self)
        # self.menuBar.setGeometry(0, 0, self.mainWidth, 30)
        # self.setMenuBar(self.menuBar)

        # Define main layout and main widget
        self.mainLayout = QtWidgets.QGridLayout()
        self.mainLayout.setRowStretch(0, 2)
        self.mainLayout.setRowStretch(1, 1)
        self.mainLayout.setColumnStretch(0, 7)
        self.mainLayout.setColumnStretch(1, 2)
        self.mainWidget = QtWidgets.QWidget(self)
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)

        # Setup drawings group
        self.setupDrawingsGroup()

        # Setup question-explaination group
        self.setupQuestionExplanationGroup()

        # Setup history group
        self.setupHistoryGroup()



    #----------------#
    # Drawings group #
    #----------------#


    def setupDrawingsGroup(self):

        # Initialize drawings canvas
        self.routesCanvas = QtWidgets.QWidget()
        self.schedulesCanvas = QtWidgets.QWidget()
        self.KPIsCanvas = QtWidgets.QWidget()

        # Setup the drawings layout
        self.drawingLayout = QtWidgets.QGridLayout()
        self.drawingLayout.setRowStretch(0, 1)
        self.drawingLayout.setColumnStretch(0, 2)
        self.drawingLayout.setColumnStretch(1, 2)
        self.drawingLayout.setColumnStretch(2, 1)

        # Create the drawings
        self.updateDrawingGroup()

        # Create a drawings group and insert it in the main layout
        drawingsGroup = QtWidgets.QGroupBox(self.mainWidget)
        drawingsGroup.setTitle("Drawings")
        drawingsGroup.setStyleSheet(self.titleStyle)
        drawingsGroup.setLayout(self.drawingLayout)
        self.mainLayout.addWidget(drawingsGroup, 0, 0, 1, 2)


    def updateDrawingGroup(self):
        self.routesFigure, self.schedulesFigure, self.KPIsFigure = self.drawer.getFigures(self.explainer.currentSolution, forUI = True)
        self.updateDrawingLayout()


    def updateDrawingLayout(self):
        self.routesCanvas = FigureCanvas(self.routesFigure)
        self.schedulesCanvas = FigureCanvas(self.schedulesFigure)
        self.KPIsCanvas = FigureCanvas(self.KPIsFigure)
        self.drawingLayout.addWidget(self.routesCanvas, 0, 0)
        self.drawingLayout.addWidget(self.schedulesCanvas, 0, 1)
        self.drawingLayout.addWidget(self.KPIsCanvas, 0, 2)


    #-------------------#
    # Explanation group #
    #-------------------#


    def setupQuestionExplanationGroup(self):

        # Initialize the question-explanation group
        QXGroup = QtWidgets.QGroupBox(self.mainWidget)

        # Create the question drop-down list and its (fixed) label
        templateLabel = QtWidgets.QLabel(QXGroup)
        templateLabel.setText("Select template: ")
        templateLabel.setStyleSheet(self.labelStyle)
        self.templateDDList = QtWidgets.QComboBox(QXGroup)
        #self.templateDDList.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        templateQuestionsTexts = [re.sub(r"{\d+}", "_", template) for template in self.explainer.getTemplatesTexts()]
        self.templateDDList.addItems(templateQuestionsTexts)
        self.templateDDList.currentIndexChanged.connect(self.templateDDListChanged)

        # Initialize fields labels and fields drop-down lists
        nbFields = 3
        self.fieldsLabels = [QtWidgets.QLabel() for j in range(nbFields)]
        self.fieldsDDLists = [QtWidgets.QComboBox(QXGroup) for j in range(nbFields)]
        for j in range(nbFields):
            self.fieldsLabels[j].setText("Looooooong pattern")
            self.fieldsLabels[j].setStyleSheet(self.labelStyle)
            labelPolicy = self.fieldsDDLists[j].sizePolicy()
            labelPolicy.setRetainSizeWhenHidden(True);
            self.fieldsDDLists[j].setSizePolicy(labelPolicy)
            self.fieldsDDLists[j].currentTextChanged.connect(lambda: self.fieldDDListChanged(j))
        field2FiltersNames = ["Skill-feasible", "Non-realized", "Employee's", "Non-employee's"]
        self.field2Filters = dict(zip(field2FiltersNames, [QtWidgets.QCheckBox(name) for name in field2FiltersNames]))
        # for filterName in field2FiltersNames:
        #     self.field2Filters[filterName].toggled.connect(lambda: self.filterToggled(filterName))

        # Initialize question label (completed text) and its (fixed) label
        questionLabel = QtWidgets.QLabel(QXGroup)
        questionLabel.setText("Question to explain: ")
        questionLabel.setStyleSheet(self.labelStyle)
        self.questionText = QtWidgets.QLabel(QXGroup)
        self.questionText.setStyleSheet(self.textStyle)
        self.questionText.setWordWrap(True)

        # Initialize explanation label (text) and its (fixed) label
        explanationLabel = QtWidgets.QLabel(QXGroup)
        explanationLabel.setText("Explanation: ")
        explanationLabel.setStyleSheet(self.labelStyle)
        self.explanationText = QtWidgets.QLabel(QXGroup)
        self.explanationText.setStyleSheet(self.textStyle)
        self.explanationText.setWordWrap(True)

        # Create explain button
        self.explainButton = QtWidgets.QPushButton(QXGroup)
        self.explainButton.setText("Explain")
        self.explainButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.explainButton.clicked.connect(self.explainButtonClicked)

        # Create save button
        self.gotItButton = QtWidgets.QPushButton(QXGroup)
        self.gotItButton.setText("Got it")
        self.gotItButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.gotItButton.clicked.connect(self.gotItButtonClicked)
        self.gotItButton.setEnabled(False)

        # Create save button
        self.saveButton = QtWidgets.QPushButton(QXGroup)
        self.saveButton.setText("Save")
        self.saveButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.saveButton.clicked.connect(self.saveButtonClicked)
        self.saveButton.setEnabled(False)

        # Create save button
        self.forgetButton = QtWidgets.QPushButton(QXGroup)
        self.forgetButton.setText("Forget")
        self.forgetButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.forgetButton.clicked.connect(self.forgetButtonClicked)
        self.forgetButton.setEnabled(False)

        # Setup the question layout
        # - First columns
        QXLayout = QtWidgets.QGridLayout()
        for j in range(3):
            shiftDueToFilters = 0 if j < 2 else 2
            QXLayout.setColumnStretch(3*j + shiftDueToFilters, 3)
            QXLayout.setColumnStretch(3*j + 1 + shiftDueToFilters, 2)
        for j in range(2):
            shiftDueToFilters = 0 if j < 1 else 2
            QXLayout.setColumnStretch(3*j + 2 + shiftDueToFilters, 2)
        QXLayout.setColumnStretch(10, 1)
        for i in range(3):
            QXLayout.setRowStretch(4 + i, 1)
        QXLayout.addWidget(templateLabel, 0, 0)
        QXLayout.addWidget(self.templateDDList, 0, 1, 1, 9)
        for j in range(3):
            shiftDueToFilters = 0 if j < 2 else 2
            QXLayout.addWidget(self.fieldsLabels[j], 1, 3*j + shiftDueToFilters, 2, 1)
            QXLayout.addWidget(self.fieldsDDLists[j], 1, 3*j + 1 + shiftDueToFilters, 2, 1)
        QXLayout.addWidget(self.field2Filters["Skill-feasible"], 1, 5)
        QXLayout.addWidget(self.field2Filters["Non-realized"], 1, 6)
        QXLayout.addWidget(self.field2Filters["Employee's"], 2, 5)
        QXLayout.addWidget(self.field2Filters["Non-employee's"], 2, 6)
        QXLayout.addWidget(questionLabel, 3, 0)
        QXLayout.addWidget(self.questionText, 3, 1, 1, 9)
        QXLayout.addWidget(explanationLabel, 4, 0, 3, 1)
        QXLayout.addWidget(self.explanationText, 4, 1, 3, 9)
        # - Last colulmn
        QXLayout.addWidget(self.explainButton, 0, 10, 4, 1)
        QXLayout.addWidget(self.gotItButton, 4, 10)
        QXLayout.addWidget(self.saveButton, 5, 10)
        QXLayout.addWidget(self.forgetButton, 6, 10)

        # Insert the question-explanation group in the main layout
        QXGroup.setTitle("Question - explanation")
        QXGroup.setStyleSheet(self.titleStyle)
        QXGroup.setLayout(QXLayout)
        self.mainLayout.addWidget(QXGroup, 1, 0)

        # Create the fields, texts and button
        self.updateQuestionExplanationGroup()


    def updateQuestionExplanationGroup(self):
        self.templateDDListChanged()


    def templateDDListChanged(self):

        # Clear explanation text
        self.explanationText.setText("")

        # Setup fields depending on the selected question
        if self.explainer.templatesKeys[self.templateDDList.currentIndex()] in ["RealizingInsteadOf", "RealizingJustAfter", \
            "RealizingInAddition", "RealizingAtAnotherTime", "RealizingAtAllCosts", "Realizing"]:

            # Get the name of former selected employee
            employeeName = self.fieldsDDLists[0].currentText()

            # Setup the first field's label and drop-down list for an employee selection
            self.fieldsLabels[0].setText("Select employee: ")
            self.fieldsDDLists[0].setVisible(True)
            self.fieldsDDLists[0].currentTextChanged.disconnect()
            self.fieldsDDLists[0].clear()
            self.fieldsDDLists[0].addItems(list(self.explainer.currentSolution.instance.getEmployeesNames()))
            index = self.fieldsDDLists[0].findText(employeeName)
            if index >= 0:
                self.fieldsDDLists[0].setCurrentIndex(index)
            self.fieldsDDLists[0].currentTextChanged.connect(lambda: self.fieldDDListChanged(0))

            # Setup the second field's label for an activity selection
            self.fieldsLabels[1].setText("Select task: ")
            self.fieldsDDLists[1].setVisible(True)

            # Setup the second field's filters
            self.setDefaultFilters()

            if self.explainer.templatesKeys[self.templateDDList.currentIndex()] in ["RealizingInsteadOf", "RealizingJustAfter"]:

                # Setup the third's field label for an activity selection
                self.fieldsLabels[2].setText("Select activity: ")
                self.fieldsDDLists[2].setVisible(True)

            elif self.explainer.templatesKeys[self.templateDDList.currentIndex()] in ["RealizingInAddition", "RealizingAtAnotherTime", "RealizingAtAllCosts", "Realizing"]:

                # Setup the third's field to be empty
                self.fieldsLabels[2].setText("")
                self.fieldsDDLists[2].setVisible(False)

            # Update the second field drop-down list
            self.fieldDDListChanged(0)

        elif self.explainer.templatesKeys[self.templateDDList.currentIndex()] in ["NotRealized"]:

            # Setup the first field's label and drop-down list for an employee selection
            self.fieldsLabels[0].setText("")
            # self.fieldsDDLists[0].currentTextChanged.disconnect()
            # self.fieldsDDLists[0].clear()
            # self.fieldsDDLists[0].currentTextChanged.connect(lambda: self.fieldDDListChanged(0))
            self.fieldsDDLists[0].setVisible(False)

            # Setup the second field's label for an activity selection
            self.fieldsLabels[1].setText("Select task: ")
            self.fieldsDDLists[1].setVisible(True)

            # Setup the second field's filters
            self.setDefaultFilters()

            # Setup the third's field to be empty
            self.fieldsLabels[2].setText("")
            self.fieldsDDLists[2].setVisible(False)

            # Add the names of all the tasks that are not realized by any employee to the second ddlist
            self.fieldsDDLists[1].currentTextChanged.disconnect()
            self.fieldsDDLists[1].clear()
            filteredTasksNames = self.explainer.currentSolution.getFilteredTasksNames(
                employee = None,
                excludingTasksWithHigherSkills = None,
                excludingRealizedTasks = True,
                excludingNonEmployeesTasks = None,
                excludingEmployeesTasks = None
            )
            self.fieldsDDLists[1].addItems(filteredTasksNames)
            self.fieldsDDLists[1].currentTextChanged.connect(lambda: self.fieldDDListChanged(1))

            # Update the second field drop-down list
            self.fieldDDListChanged(1)

        else:

            # Setup all fields to be empty
            for j in range(3):
                self.fieldsLabels[j].setText("")
                self.fieldsDDLists[j].setVisible(False)
            for filterName in self.field2Filters.keys():
                self.field2Filters[filterName].setVisible(False)

            # Update question text
            self.updateQuestionLabel()


    def fieldDDListChanged(self, DDListIndex):

        # If first drop-down list is changed
        if DDListIndex == 0:

            # Get the name of the selected employee
            employeeName = self.fieldsDDLists[0].currentText()
            taskName = self.fieldsDDLists[1].currentText()

            # Add the names of all the tasks that are not realized by the employee to the second ddlist
            self.fieldsDDLists[1].currentTextChanged.disconnect()
            self.fieldsDDLists[1].clear()
            filteredTasksNames = self.explainer.currentSolution.getFilteredTasksNames(
                employee = self.explainer.currentSolution.instance.getEmployee(employeeName),
                excludingTasksWithHigherSkills = self.field2Filters["Skill-feasible"].isChecked(),
                excludingRealizedTasks = self.field2Filters["Non-realized"].isChecked(),
                excludingNonEmployeesTasks = self.field2Filters["Employee's"].isChecked(),
                excludingEmployeesTasks = self.field2Filters["Non-employee's"].isChecked()
            )
            self.fieldsDDLists[1].addItems(filteredTasksNames)
            index = self.fieldsDDLists[1].findText(taskName)
            if index >= 0:
                self.fieldsDDLists[1].setCurrentIndex(index)
            self.fieldsDDLists[1].currentTextChanged.connect(lambda: self.fieldDDListChanged(1))

            # Add the names of the tasks or activities that are realized by the employee to the third ddlist
            self.fieldsDDLists[2].currentTextChanged.disconnect()
            self.fieldsDDLists[2].clear()
            if self.explainer.templatesKeys[self.templateDDList.currentIndex()] == "RealizingJustAfter":
                realizedActivitiesNames = self.explainer.currentSolution.getSequence(employeeName).getActivitiesNames(
                    includingStart = True, includingEnd = False, includingUnavailabilities = True, alphaOrdered = True)
                self.fieldsDDLists[2].addItems(realizedActivitiesNames)
            else:
                realizedTasksNames = self.explainer.currentSolution.getSequence(employeeName).getTasksNames(alphaOrdered = True)
                self.fieldsDDLists[2].addItems(realizedTasksNames)
            self.fieldsDDLists[2].currentTextChanged.connect(lambda: self.fieldDDListChanged(2))

            # Update question text
            self.updateQuestionLabel()

        # If second drop-down list is changed
        elif DDListIndex == 1:

            # Update question text
            self.updateQuestionLabel()

        # If third drop-down list is changed
        elif DDListIndex == 2:

            # Update question text
            self.updateQuestionLabel()

        else:
            print("There is something wrong!")


    def setDefaultFilters(self, forceSkillFeasibleChecked = False, forceNonRealizedCheck = False, forceNonEmployeeCheck = False):
        if not(self.explainer.templatesKeys[self.templateDDList.currentIndex()] in ["Tightening"]):
            enabled = dict()
            checked = dict()
            if self.explainer.templatesKeys[self.templateDDList.currentIndex()] == "RealizingInsteadOf":
                enabled = {"Skill-feasible": True, "Non-realized": True, "Employee's": False, "Non-employee's": False}
                checked = {"Skill-feasible": False, "Non-realized": False, "Employee's": False, "Non-employee's": True}
            elif self.explainer.templatesKeys[self.templateDDList.currentIndex()] == "RealizingJustAfter":
                enabled = {"Skill-feasible": True, "Non-realized": True, "Employee's": True, "Non-employee's": True}
                checked = {"Skill-feasible": False, "Non-realized": False, "Employee's": False, "Non-employee's": False}
            elif self.explainer.templatesKeys[self.templateDDList.currentIndex()] in ["RealizingInAddition", "RealizingAtAllCosts"]:
                enabled = {"Skill-feasible": True, "Non-realized": True, "Employee's": False, "Non-employee's": False}
                checked = {"Skill-feasible": False, "Non-realized": False, "Employee's": False, "Non-employee's": True}
            elif self.explainer.templatesKeys[self.templateDDList.currentIndex()] in ["RealizingAtAnotherTime", "Realizing"]:
                enabled = {"Skill-feasible": False, "Non-realized": False, "Employee's": False, "Non-employee's": False}
                checked = {"Skill-feasible": False, "Non-realized": False, "Employee's": True, "Non-employee's": False}
            elif self.explainer.templatesKeys[self.templateDDList.currentIndex()] in ["NotRealized"]:
                enabled = {"Skill-feasible": False, "Non-realized": False, "Employee's": False, "Non-employee's": False}
                checked = {"Skill-feasible": False, "Non-realized": True, "Employee's": False, "Non-employee's": False}
            else:
                raise Exception(f"{self.explainer.templatesKeys[self.templateDDList.currentIndex()]} question not treated in setDefaultFilters()")
            checked["Skill-feasible"] = checked["Skill-feasible"] or forceSkillFeasibleChecked
            checked["Non-realized"] = checked["Non-realized"] or forceNonRealizedCheck
            if checked["Non-realized"]:
                enabled["Employee's"] = False
            checked["Non-employee's"] = checked["Non-employee's"] or forceNonEmployeeCheck
            if checked["Non-realized"]:
                enabled["Employee's"] = False
            for filterName in self.field2Filters.keys():
                self.field2Filters[filterName].setVisible(True)
                self.field2Filters[filterName].disconnect()
                self.field2Filters[filterName].setEnabled(enabled[filterName])
                self.field2Filters[filterName].setChecked(checked[filterName])
                #self.field2Filters[filterName].toggled.connect(lambda: self.filterToggled(filterName))
            self.field2Filters["Skill-feasible"].toggled.connect(lambda: self.filterToggled("Skill-feasible"))
            self.field2Filters["Non-realized"].toggled.connect(lambda: self.filterToggled("Non-realized"))
            self.field2Filters["Employee's"].toggled.connect(lambda: self.filterToggled("Employee's"))
            self.field2Filters["Non-employee's"].toggled.connect(lambda: self.filterToggled("Non-employee's"))


    def filterToggled(self, filterName):

        # Handle non-realized filter influence over other filters
        if filterName == "Non-realized":
            if self.field2Filters["Non-realized"].isChecked():
                self.field2Filters["Employee's"].disconnect()
                self.field2Filters["Employee's"].setEnabled(False)
                self.field2Filters["Employee's"].setChecked(False)
                self.field2Filters["Employee's"].toggled.connect(lambda: self.filterToggled("Employee's"))
            else:
                self.setDefaultFilters(forceSkillFeasibleChecked = self.field2Filters["Skill-feasible"].isChecked(),
                    forceNonEmployeeCheck = self.field2Filters["Non-employee's"].isChecked())

        # Handle employee's filter influence over other filters
        elif filterName == "Employee's":
            if self.field2Filters["Employee's"].isChecked():
                enabled = {"Skill-feasible": False, "Non-realized": False, "Non-employee's": False}
                checked = {"Skill-feasible": True, "Non-realized": False, "Non-employee's": False}
                for filterName in enabled.keys():
                    self.field2Filters[filterName].disconnect()
                    self.field2Filters[filterName].setEnabled(enabled[filterName])
                    self.field2Filters[filterName].setChecked(checked[filterName])
                    self.field2Filters[filterName].toggled.connect(lambda: self.filterToggled(filterName))
            else:
                self.setDefaultFilters()

        # Handle employee's filter influence over other filters
        elif filterName == "Non-employee's":
            if self.field2Filters["Non-employee's"].isChecked():
                self.field2Filters["Employee's"].disconnect()
                self.field2Filters["Employee's"].setEnabled(False)
                self.field2Filters["Employee's"].setChecked(False)
                self.field2Filters["Employee's"].toggled.connect(lambda: self.filterToggled("Employee's"))
            else:
                self.setDefaultFilters(forceSkillFeasibleChecked = self.field2Filters["Skill-feasible"].isChecked(),
                    forceNonRealizedCheck = self.field2Filters["Non-realized"].isChecked())

        # Get the name of the selected employee
        employeeName = self.fieldsDDLists[0].currentText()

        # Add the names of all the tasks that are not realized by the employee to the second ddlist
        self.fieldsDDLists[1].currentTextChanged.disconnect()
        self.fieldsDDLists[1].clear()
        filteredTasksNames = self.explainer.currentSolution.getFilteredTasksNames(
            employee = self.explainer.currentSolution.instance.getEmployee(employeeName),
            excludingTasksWithHigherSkills = self.field2Filters["Skill-feasible"].isChecked(),
            excludingRealizedTasks = self.field2Filters["Non-realized"].isChecked(),
            excludingNonEmployeesTasks = self.field2Filters["Employee's"].isChecked(),
            excludingEmployeesTasks = self.field2Filters["Non-employee's"].isChecked()
        )
        self.fieldsDDLists[1].addItems(filteredTasksNames)
        self.fieldsDDLists[1].currentTextChanged.connect(lambda: self.fieldDDListChanged(1))

        # Update question text
        self.updateQuestionLabel()


    def setExplanationAndHistoryEnabled(self, toggle):
        self.templateDDList.setEnabled(toggle)
        for j in range(3):
            self.fieldsDDLists[j].setEnabled(toggle)
        if toggle:
            self.setDefaultFilters()
        else:
            for filterName in self.field2Filters.keys():
                self.field2Filters[filterName].setEnabled(False)
        self.explainButton.setEnabled(toggle)
        self.solutionsHistory.setEnabled(toggle)


    def updateQuestionLabel(self):
        template = self.explainer.getTemplateText(index = self.templateDDList.currentIndex())
        template = template.replace("{0}", self.fieldsDDLists[0].currentText())
        template = template.replace("{1}", self.fieldsDDLists[1].currentText())
        template = template.replace("{2}", self.fieldsDDLists[2].currentText())
        self.questionText.setText(template)


    def explainButtonClicked(self):

        # Disable ddlists and explain button
        self.setExplanationAndHistoryEnabled(False)

        # Compute explanation to template question
        templateIndex = self.templateDDList.currentIndex()
        # nbFields = self.explainer.getTemplateNbFields(index = templateIndex)
        # fieldsValues = [self.fieldsDDLists[j].currentText() for j in range(nbFields)]
        fieldsValues = [self.fieldsDDLists[j].currentText() for j in range(3)]
        timeBeforeComputation = time.time()
        explanation = self.explainer.computeExplanationByIndex(templateIndex, fieldsValues)
        computationDuration = time.time() - timeBeforeComputation
        print("* Question:")
        print(self.questionText.text())
        print("* Explanation:")
        print(explanation.text)
        print(f"(Explanation computed in {np.round(computationDuration, 3)} seconds)")
        print()

        # Update explanation text
        self.explanationText.setText(explanation.text)

        # If the explanation computation has led to a new solution
        if explanation.hasANewSolution():

            # Show new solution
            self.newSolution = explanation.newSolution
            # print(self.explainer.currentSolution.KPIs['totalIdleTime'])
            # print(self.newSolution.KPIs['totalIdleTime'])
            self.newSolution.updateKPIs()
            self.showNewSolution(infeasibility = explanation.infeasibility, criticalBounds = explanation.criticalBounds)

            # Show save and forget buttons or got-it button if feasible or not
            if explanation.newSolutionIsFeasible():
                self.saveButton.setEnabled(True)
                self.forgetButton.setEnabled(True)
            else:
                self.gotItButton.setEnabled(True)

        # If the explanation computation has not led to a new solution
        else:
            # Show got it button
            self.gotItButton.setEnabled(True)


    def gotItButtonClicked(self):

        # Clear explanation text, new solution, enable and disable buttons
        self.answerButtonClicked()

        # Update drawing group
        self.KPIsCanvas.setVisible(True)
        self.schedulesCanvas.setVisible(True)
        self.updateDrawingGroup()


    def saveButtonClicked(self):

        # Save new solution in history
        self.explainer.saveNewSolutionInHistory(self.newSolution)
        self.solutionsHistory.addItem(self.newSolution.name)

        # Clear explanation text, new solution, enable and disable buttons
        self.answerButtonClicked()

        # Set current row to last item and update group
        self.solutionsHistory.setCurrentRow(self.solutionsHistory.count() - 1)


    def forgetButtonClicked(self):

        # Clear explanation text, new solution, enable and disable buttons
        self.answerButtonClicked()

        # Update drawing group
        self.updateDrawingGroup()


    def answerButtonClicked(self):

        # Clear explanation text
        self.explanationText.setText("")

        # Clear new solution
        if self.newSolution != None:
            self.newSolution = None
            self.routesFigure.clf()
            self.schedulesFigure.clf()
            self.KPIsFigure.clf()
            plt.close(self.routesFigure)
            plt.close(self.schedulesFigure)
            plt.close(self.KPIsFigure)

        # Enable explanation and history back
        self.setExplanationAndHistoryEnabled(True)

        # Disable save and forget buttons
        self.gotItButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.forgetButton.setEnabled(False)


    def showNewSolution(self, infeasibility = None, criticalBounds = None):
        if infeasibility == None:
            self.routesFigure = self.drawer.createFigure(self.newSolution, 'routes', forUI = True)
            #self.schedulesFigure = self.drawer.createFigure(self.newSolution, 'schedules', forUI = True)
            self.schedulesFigure = self.drawer.createSchedulesFigure(self.newSolution, criticalBounds = criticalBounds, forUI = True)
            self.KPIsFigure = self.drawer.createKPIsComparaisonFigure([self.explainer.currentSolution, self.newSolution], forUI = True)
        else:
            print(criticalBounds)
            self.routesFigure = self.drawer.createRoutesFigure(self.newSolution, infeasibility = infeasibility, forUI = True)
            self.schedulesFigure = self.drawer.createSchedulesFigure(self.newSolution, infeasibility = infeasibility, criticalBounds = criticalBounds, forUI = True)
            self.KPIsFigure = plt.figure()
        self.updateDrawingLayout()



    #---------------#
    # History group #
    #---------------#


    def setupHistoryGroup(self):

        # Initialize history group
        historyGroup = QtWidgets.QGroupBox(self.mainWidget)

        # Create a history of solutions
        historyLabel = QtWidgets.QLabel()
        historyLabel.setText("Select a solution:")
        historyLabel.setStyleSheet(self.labelStyle)
        self.solutionsHistory = QtWidgets.QListWidget(historyGroup)
        self.solutionsHistory.addItem(self.explainer.currentSolution.name)
        self.solutionsHistory.setCurrentRow(0)
        self.solutionsHistory.itemSelectionChanged.connect(self.selectedSolutionChanged)

        # Setup the history layout
        historyLayout = QtWidgets.QVBoxLayout()
        historyLayout.addWidget(historyLabel)
        historyLayout.addWidget(self.solutionsHistory)

        # Set the history layout within the main layout
        historyGroup.setTitle("Solutions history")
        historyGroup.setStyleSheet(self.titleStyle)
        historyGroup.setLayout(historyLayout)
        self.mainLayout.addWidget(historyGroup, 1, 1)


    def selectedSolutionChanged(self):
        self.explainer.setCurrentSolution(self.solutionsHistory.currentItem().text())
        self.updateDrawingGroup()
        self.updateQuestionExplanationGroup()



#####################
# Class ExplainerUI #
#####################


class ExplainerUI:

    def __init__(self, explainer: Explainer):
        self.application = QtWidgets.QApplication(sys.argv)
        geometry = self.application.desktop().availableGeometry()
        self.content = ExplainerUIContent(geometry, explainer)

    def show(self):
        self.content.show()
        sys.exit(self.application.exec_())





#########
# Draft #
#########


####################
# Class MyComboBox #
####################


# class MyComboBox(QtWidgets.QComboBox):
#
#     def paintEvent(self, event):
#
#         painter = QtWidgets.QStylePainter(self)
#         painter.setPen(self.palette().color(QtGui.QPalette.Text))
#
#         # draw the combobox frame, focusrect and selected etc.
#         opt = QtWidgets.QStyleOptionComboBox()
#         self.initStyleOption(opt)
#         painter.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt)
#
#         if self.currentIndex() < 0:
#             opt.palette.setBrush(
#                 QtGui.QPalette.ButtonText,
#                 opt.palette.brush(QtGui.QPalette.ButtonText).color().lighter(),
#             )
#             if self.placeholderText():
#                 opt.currentText = self.placeholderText()
#
#         # draw the icon and text
#         painter.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, opt)
