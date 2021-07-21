###########
# Modules #
###########


# Basic modules
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


# Project modules
from Definition.solution import *
from Tools.time import *


# Global variables
figuresKeys = ['routes', 'schedules', 'KPIs']
stepMarkerSize = 20
depotMarkerSize = 40
figureParameters = dict()
figureParameters['routes'] = {'dpi': 80}
figureParameters['schedules'] = {'dpi': 80}
figureParameters['KPIs'] = {'dpi': 60} # 'figsize': (9, 3)



################
# Class Drawer #
################


class Drawer:

    mainSolution = None
    allSolutionsFigures = dict()
    colors = None


    # Assumption: solutions is a set
    def __init__(self, solution = None, solutions = None):

        # Set solutions
        if solution != None:
            self.setMainSolution(solution)
        else:
            self.mainSolution = None
        if solutions != None:
            self.addSolutions(solutions)



    #############
    # Solutions #
    #############


    def hasMainSolution(self):
        return self.mainSolution != None


    # Asumption: main solution is among solutions
    def hasSolutions(self):
        return self.hasMainSolution()


    def isMainSolution(self, solution: Solution):
        return self.hasMainSolution() and self.mainSolution == solution


    def isAmongSolutions(self, solution: Solution):
        return self.hasSolutions() and (solution in self.allSolutionsFigures.keys())


    def setMainSolution(self, solution: Solution):
        if self.hasMainSolution():
            if self.mainSolution != solution:
                self.mainSolution = solution
                self.addSolution(solution)
        else:
            self.colors = dict(zip(solution.instance.getEmployeesNames(), sns.color_palette("hls", len(solution.instance.employees))))
            self.mainSolution = solution
            self.addSolution(solution)


    def addSolution(self, solution: Solution):
        if not(self.hasMainSolution()):
            self.colors = dict(zip(solution.instance.getEmployeesNames(), sns.color_palette("hls", len(solution.instance.employees))))
            self.mainSolution = solution
            self.allSolutionsFigures[solution] = dict()
        elif not(self.isAmongSolutions(solution)):
            self.allSolutionsFigures[solution] = dict()


    def addSolutions(self, solutions):
        for solution in solutions:
            self.addSolution(solution)


    def removeSolution(self, solution: Solution):
        if self.isAmongSolutions(solution):
            self.clearFigures(solution)
            del self.allSolutionsFigures[solution]
            if self.isMainSolution(solution):
                if bool(self.allSolutionsFigures):
                    self.mainSolution = next(iter(self.allSolutionsFigures))
                else:
                    self.mainSolution = None



    ####################
    # Managing figures #
    ####################


    def getFigures(self, solution: Solution, forUI = False):
        routesFigure = self.getFigure(solution, 'routes', forUI)
        schedulesFigure = self.getFigure(solution, 'schedules', forUI)
        KPIsFigure = self.getFigure(solution, 'KPIs', forUI)
        return (routesFigure, schedulesFigure, KPIsFigure)


    def getFigure(self, solution: Solution, key, forUI = False):
        if not(self.isAmongSolutions(solution)):
            self.addSolution(solution)
        if not(self.hasFigure(solution, key)):
            self.updateFigure(solution, key, forUI)
        figure = self.allSolutionsFigures[solution][key]
        if forUI:
            figure.dpi = figureParameters[key]['dpi']
        return figure


    def hasFigures(self, solution: Solution):
        booleans = (False, False, False)
        if self.isAmongSolutions(solution):
            for k, key in enumerate(self.figuresKeys):
                booleans[k] = key in self.allSolutionsFigures[solution].keys()
        return booleans


    def hasFigure(self, solution: Solution, key):
        if self.isAmongSolutions(solution):
            return key in self.allSolutionsFigures[solution].keys()
        else:
            return False


    def updateFigure(self, solution: Solution, key, forUI = False):
        if not(self.isAmongSolutions(solution)):
            self.addSolution(solution)
        figure = None
        if self.hasFigure(solution, key):
            figure = self.allSolutionsFigures[solution][key]
        self.allSolutionsFigures[solution][key] =  self.createFigure(solution, key, forUI, figure)


    def showFigures(self, solution: Solution):
        figure = self.getFigure(solution, key)
        # Or
        figure = self.createFigure(solution, key)
        print("To be coded")


    def showFigure(self, solution: Solution, key):
        figure = self.getFigure(solution, key)
        # Or
        figure = self.createFigure(solution, key)
        print("To be coded")


    def saveFigures(self, solution: Solution):
        for key in self.figuresKeys:
            self.saveFigure(solution, key)


    def saveFigure(self, solution: Solution, key):
        figure = self.getFigure(solution, key)
        # Or
        figure = self.createFigure(solution, key)
        print("To be coded")


    def clearFigures(self, solution: Solution):
        booleans = self.hasFigures(solution)
        for k, boolean in enumerate(booleans):
            if boolean:
                figure = self.allSolutionsFigures[solution][self.figuresKeys[k]]
                figure.clf()
                plt.close(figure)


    def createFigure(self, solution: Solution, key, forUI = False, figure = None):
        plt.style.use('seaborn-whitegrid')
        if key == 'routes':
            return self.createRoutesFigure(solution, forUI = forUI, figure = figure)
        elif key == 'schedules':
            return self.createSchedulesFigure(solution, forUI = forUI, figure = figure)
        elif key == 'KPIs':
            return self.createKPIsFigure(solution, forUI = forUI, figure = figure)
        else:
            print("Wrong key for figure")



    #---------------#
    # Routes figure #
    #---------------#


    def createRoutesFigure(self, solution: Solution, infeasibility = None, forUI = False, figure = None):

        # Create a new figure if needed
        if figure == None:
            figure = plt.figure()
        else:
            plt.figure(figure.number)
            figure.clf()

        # Set parameters
        if forUI:
            plt.subplots_adjust(left = 0.15, right = 0.9, top = 0.95, bottom = 0.1)
            figure.dpi = figureParameters['routes']['dpi']
        else:
            plt.title("Schedules of " + solution.name)
            #figure.suptitle("Schedules of " + solution.name)

        # Create axes
        ax = figure.add_subplot()

        # Define axis
        if solution.instance.hasGeographicLocations():
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
        else:
            plt.xlabel("x")
            plt.ylabel("y")

        # Draw paths
        for employeeName, employee in solution.instance.employees.items():

            pathFirstCoordinates = []
            pathSecondCoordinates = []
            stepNames = []
            indicesOfTasksInPath = []
            indicesOfUnavailabilitiesInPath = []

            pathFirstCoordinates.append(employee.location.coordinates[0])
            pathSecondCoordinates.append(employee.location.coordinates[1])
            stepNames.append("")

            for step in solution.sequences[employeeName][1:-1]:
                stepName = step.activity.name
                task = solution.instance.getActivity(activityName = stepName, employeeName = employeeName)
                pathFirstCoordinates.append(task.location.coordinates[0])
                pathSecondCoordinates.append(task.location.coordinates[1])
                stepNames.append(stepName)
                currentIndex = len(stepNames) - 1
                if task.isEmployeeUnavailability():
                    indicesOfUnavailabilitiesInPath.append(currentIndex)
                else:
                    indicesOfTasksInPath.append(currentIndex)

            pathFirstCoordinates.append(employee.location.coordinates[0])
            pathSecondCoordinates.append(employee.location.coordinates[1])
            stepNames.append("")

            if solution.instance.hasGeographicLocations():
                # Remark: coordinates[0] is a lattitude, coordinates[1] is a longitude
                pathFirstCoordinates, pathSecondCoordinates = \
                    pathSecondCoordinates, pathFirstCoordinates
            pathFirstCoordinates = np.array(pathFirstCoordinates)
            pathSecondCoordinates = np.array(pathSecondCoordinates)

            if infeasibility != None and employeeName == infeasibility['employeeName']:
                stepIndex = solution.getSequence(employee.name).getStepIndexOfActivity(infeasibility['taskName'])
                ax.plot(pathFirstCoordinates[:stepIndex], pathSecondCoordinates[:stepIndex], label = employeeName, color = self.colors[employeeName])
                ax.plot(pathFirstCoordinates[stepIndex - 1: stepIndex + 2], pathSecondCoordinates[stepIndex - 1: stepIndex + 2], color = self.colors[employeeName], linestyle = '--')
                ax.plot(pathFirstCoordinates[stepIndex + 1:], pathSecondCoordinates[stepIndex + 1:], color = self.colors[employeeName])
            else:
                ax.plot(pathFirstCoordinates, pathSecondCoordinates, label = employeeName, color = self.colors[employeeName])

            if len(pathFirstCoordinates) > 2:
                arrowStart = np.array([pathFirstCoordinates[0], pathSecondCoordinates[0]])
                arrowEnd = np.array([pathFirstCoordinates[1], pathSecondCoordinates[1]])
                if np.linalg.norm(arrowEnd - arrowStart, 2) < 1e-10:
                    arrowEnd = np.array([pathFirstCoordinates[2], pathSecondCoordinates[2]])
                arrowEnd = np.mean(np.array([arrowStart, arrowEnd]), axis = 0)
                ax.arrow(arrowStart[0], arrowStart[1], arrowEnd[0] - arrowStart[0], arrowEnd[1] - arrowStart[1],
                    head_width = 0.03, head_length = 0.02, color = self.colors[employeeName], linewidth = 0)

            ax.scatter(pathFirstCoordinates[0], pathSecondCoordinates[0],
                color = self.colors[employeeName], alpha = 0.7, marker = 's', s = depotMarkerSize, zorder = 3)

            ax.scatter(pathFirstCoordinates[indicesOfTasksInPath], pathSecondCoordinates[indicesOfTasksInPath],
                color = self.colors[employeeName], alpha = 0.7, marker = 'o', s = stepMarkerSize)

            ax.scatter(pathFirstCoordinates[indicesOfUnavailabilitiesInPath], pathSecondCoordinates[indicesOfUnavailabilitiesInPath],
                color = self.colors[employeeName], alpha = 0.7, marker = 'X', s = stepMarkerSize)

            for j in range(1, len(stepNames) - 1):
                ax.annotate(stepNames[j], (pathFirstCoordinates[j], pathSecondCoordinates[j]),
                    color = self.colors[employeeName])

        nonRealizedTasksFirstCoordinates = []
        nonRealizedTasksSecondCoordinates = []
        nonRealizedTasksNames = []
        for taskName, description in solution.tasksDescriptions.items():
            if not(description['realized']):
                task = solution.instance.getTask(taskName)
                nonRealizedTasksFirstCoordinates.append(task.location.coordinates[0])
                nonRealizedTasksSecondCoordinates.append(task.location.coordinates[1])
                nonRealizedTasksNames.append(taskName)

        if solution.instance.hasGeographicLocations():
            # Remark: coordinates[0] is a lattitude, coordinates[1] is a longitude
            nonRealizedTasksFirstCoordinates, nonRealizedTasksSecondCoordinates = nonRealizedTasksSecondCoordinates, nonRealizedTasksFirstCoordinates

        ax.scatter(nonRealizedTasksFirstCoordinates, nonRealizedTasksSecondCoordinates,
            color = 'tab:gray', alpha = 0.7, marker = 'o', s = stepMarkerSize)

        for j in range(len(nonRealizedTasksNames)):
            ax.annotate(nonRealizedTasksNames[j], (nonRealizedTasksFirstCoordinates[j], nonRealizedTasksSecondCoordinates[j]),
                color = 'tab:gray')

        plt.legend()
        plt.draw()

        return figure



    #------------------#
    # Schedules figure #
    #------------------#


    def createSchedulesFigure(self, solution: Solution, infeasibility = None, criticalBounds = None, forUI = False, figure = None):

        # Create a new figure if needed
        if figure == None:
            figure = plt.figure()
        else:
            plt.figure(figure.number)
            figure.clf()

        # Set parameters
        if forUI:
            plt.subplots_adjust(left = 0.15, right = 0.9, top = 0.95, bottom = 0.1)
            figure.dpi = figureParameters['schedules']['dpi']
        else:
            plt.title("Schedules of " + solution.name)
            #figure.suptitle("Schedules of " + solution.name)

        # Create axes
        ax = figure.add_subplot()

        # Define axis
        ax.invert_yaxis()
        maxTimeValue = 0
        minTimeValue = 24*60
        for sequence in solution.sequences.values():
            maxTimeValue = max(maxTimeValue, sequence[-1].startTime)
            minTimeValue = min(minTimeValue, sequence[0].startTime)
        timeValuesRangeSize = maxTimeValue - minTimeValue
        maxTimeValue += np.ceil(timeValuesRangeSize*0.05)
        minTimeValue -= np.ceil(timeValuesRangeSize*0.05)
        ax.set_xlim(minTimeValue, maxTimeValue)
        ax.set_xlabel("Time")
        ax.set_xticks([h*60 for h in range(7, 20)])
        ax.set_xticklabels([convert_nb_minutes_to_time_string(h * 60).replace(':00', '') for h in range(7, 20)])
        ax.set_ylabel("Employees")
        employeesNames = list(solution.sequences.keys())
        ax.set_yticks(range(len(employeesNames)))
        ax.set_yticklabels(employeesNames)

        for employeeIndex, (employeeName, sequence) in enumerate(solution.sequences.items()):

            employee = solution.instance.getEmployee(employeeName)
            lunchBreakDescription = None
            if solution.instance.hasLunchBreaks():
                lunchBreakDescription = solution.lunchBreaksDescriptions[employeeName]

            barColor = self.colors[employeeName]
            #r, g, b = barColor
            #txtColor = 'white' if r*g*b < 0.5 else 'darkgrey'
            txtColor = 'black'
            hatchColor = 'white'

            if len(sequence) > 2:

                # Draw tasks and unavailabilities
                for step in sequence[1:-1]:
                    activityName = step.activity.name
                    barLeftSide = step.startTime
                    barWidth = step.endTime - step.startTime
                    barCenterX = barLeftSide + barWidth/2
                    barCenterY = employeeIndex
                    barHeight = 0.4
                    if infeasibility != None and infeasibility['employeeName'] == employeeName and infeasibility['taskName'] == step.activity.name:
                        barCenterY += -0.4 if employeeIndex > 0 else 0.4
                        barHeight /= 2
                    task = solution.instance.getActivity(activityName = activityName, employeeName = employeeName)
                    if task.isEmployeeUnavailability():
                        ax.barh(y = barCenterY, left = barLeftSide, width = barWidth,
                            height = barHeight, color = barColor, edgecolor = hatchColor, hatch = "//")
                    else:
                        ax.barh(y = barCenterY, left = barLeftSide, width = barWidth, height = barHeight, color = barColor)
                    ax.text(x = barCenterX, y = barCenterY, s = activityName, ha = 'center', va = 'center', color = txtColor)
                    if criticalBounds != None and employeeName in criticalBounds.keys() and step.activity.name in criticalBounds[employeeName].keys():
                        if criticalBounds[employeeName][step.activity.name] == 'LB':
                            ax.plot([barLeftSide, barLeftSide], [barCenterY - 3*barHeight/2, barCenterY + 3*barHeight/2], color = barColor, linestyle = '-')
                        elif criticalBounds[employeeName][step.activity.name] == 'UB':
                            ax.plot([barLeftSide + barWidth, barLeftSide + barWidth], [barCenterY - 3*barHeight/2, barCenterY + 3*barHeight/2], color = barColor, linestyle = '-')

                barHeight = 0.4
                if criticalBounds != None and employeeName in criticalBounds.keys():
                    if 'Start' in criticalBounds[employeeName].keys():
                        ax.plot([sequence[0].startTime, sequence[0].startTime], [employeeIndex - 3*barHeight/2, employeeIndex + 3*barHeight/2], color = 'darkgrey', linestyle = '-')
                    elif 'End' in criticalBounds[employeeName].keys():
                        ax.plot([sequence[0].endTime, sequence[0].endTime], [employeeIndex - 3*barHeight/2, employeeIndex + 3*barHeight/2], color = 'darkgrey', linestyle = '-')

                # Draw displacements
                for stepIndex, step in enumerate(sequence[:-1]):
                    barLeftSide = step.endTime
                    barWidth = int(np.ceil(solution.computeTravelingDuration(step, sequence[stepIndex + 1])))
                    barHeight = 0.2
                    if barWidth > 0:
                        if solution.instance.hasLunchBreaks() and \
                            lunchBreakDescription['stepBefore'] == step.activity.name and \
                            lunchBreakDescription['startTime'] < barLeftSide + barWidth:
                            bar1LeftSide = barLeftSide
                            bar1Width = lunchBreakDescription['startTime'] - barLeftSide
                            if bar1Width > 0:
                                bar1Center = bar1LeftSide + bar1Width/2
                                ax.barh(y = employeeName, left = bar1LeftSide, width = bar1Width, height = barHeight, color = 'darkgrey')
                                ax.text(x = bar1Center, y = employeeIndex, s = str(bar1Width), ha = 'center', va = 'center', color = txtColor)
                            bar2LeftSide = lunchBreakDescription['startTime'] + solution.instance.lunchBreakDuration
                            bar2Width = barWidth - bar1Width
                            if bar2Width > 0:
                                bar2Center = bar2LeftSide + bar2Width/2
                                ax.barh(y = employeeName, left = bar2LeftSide, width = bar2Width, height = barHeight, color = 'darkgrey')
                                ax.text(x = bar2Center, y = employeeIndex, s = str(bar2Width), ha = 'center', va = 'center', color = txtColor)
                        else:
                            barCenterX = barLeftSide + barWidth/2
                            barCenterY = employeeIndex
                            if infeasibility != None and infeasibility['employeeName'] == employeeName:
                                if infeasibility['taskName'] == step.activity.name:
                                    barCenterY += -0.4 if employeeIndex > 0 else 0.4
                                    barHeight /= 2
                                    ax.plot([barCenterX + barWidth/2, sequence[stepIndex + 1].startTime], [barCenterY - barHeight/2, employeeIndex], color = 'darkgrey', linestyle = '--')
                                elif infeasibility['taskName'] == sequence[stepIndex + 1].activity.name:
                                    barCenterY += -0.4 if employeeIndex > 0 else 0.4
                                    barLeftSide = sequence[stepIndex + 1].startTime - barWidth
                                    barCenterX = barLeftSide + barWidth/2
                                    barHeight /= 2
                                    ax.plot([barCenterX - barWidth/2, step.endTime], [barCenterY - barHeight/2, employeeIndex], color = 'darkgrey', linestyle = '--')
                            ax.barh(y = barCenterY, left = barLeftSide, width = barWidth, height = barHeight, color = 'darkgrey')
                            ax.text(x = barCenterX, y = barCenterY, s = str(barWidth), ha = 'center', va = 'center', color = txtColor)

                # Draw lunch breaks
                if solution.instance.hasLunchBreaks():
                    lunchBreakDescription = solution.lunchBreaksDescriptions[employeeName]
                    barLeftSide = lunchBreakDescription['startTime']
                    barWidth = solution.instance.lunchBreakDuration
                    barCenterX = barLeftSide + barWidth/2
                    ax.barh(y = employeeName, left = barLeftSide, width = barWidth, height = barHeight, color = barColor, edgecolor = hatchColor, hatch = "/")
                    ax.text(x = barCenterX, y = employeeIndex, s = "LB", ha = 'center', va = 'center', color = txtColor)

        plt.draw()

        return figure



    #-------------#
    # KPIs figure #
    #-------------#


    def createKPIsFigure(self, solution: Solution, forUI = False, figure = None):
        return self.createBarChartFigure([solution], forUI, figure)


    def createKPIsComparaisonFigure(self, solutions, forUI = False, figure = None):
        return self.createBarChartFigure(solutions, forUI, figure)


    def createBarChartFigure(self, solutions, forUI = False, figure = None):

        # Create a new figure if needed
        if figure == None:
            figure = plt.figure()
        else:
            plt.figure(figure.number)
            figure.clf()

        # Set parameters
        if forUI:
            #figure = plt.figure(dpi = figureParameters['KPIs']['dpi'], figsize = figureParameters['KPIs']['figsize'])
            plt.subplots_adjust(top=0.8, bottom=0.2, wspace = 0.5, hspace = 1)
            figure.dpi = figureParameters['KPIs']['dpi']
        else:
            if len(solutions) == 1:
                plt.title("KPIs of " + solutions[0].name)
                #figure.suptitle("KPIs of " + solution.name)
            else:
                plt.title("KPIs comparison")
                #figure.suptitle("KPIs comparison")

        # Create axes
        axes = figure.subplots(nrows = 2, ncols = 2)

        nbMinutesUB = 10*60
        criteriaDescriptions = [{'name': "Realized tasks", 'UB': len(solutions[0].instance.tasks), 'unit': "number"}]
        for name in ["Avg. working dur.", "Avg. traveling dur.", "Avg. idle time"]:
            criteriaDescriptions.append({'name': name, 'UB': nbMinutesUB, 'unit': "minutes"})

        nbEmployees = len(solutions[0].instance.employees)
        criteriaValues = dict()
        for solution in solutions:
            criteriaValues[solution] = [
                solution.KPIs['nbRealizedTasks'],
                solution.KPIs['totalWorkingDuration']/float(nbEmployees),
                solution.KPIs['totalTravelingDuration']/float(nbEmployees),
                solution.KPIs['totalIdleTime']/float(nbEmployees)
            ]

        ax = None
        solutionsColors = dict(zip(solutions, sns.color_palette("husl", len(solutions))))
        for criteriumIndex, criterium in enumerate(criteriaDescriptions):
            ax = axes[criteriumIndex//2, criteriumIndex % 2]
            for solutionIndex, solution in enumerate(solutions):
                bar = ax.bar(solutionIndex + 1, criteriaValues[solution][criteriumIndex], width = 0.5, label = solution.name, color = solutionsColors[solution])
                if solutionIndex > 0:
                    criteriaGain = np.round((criteriaValues[solution][criteriumIndex]/criteriaValues[solutions[0]][criteriumIndex] - 1)*100, 2)
                    ax.text(solutionIndex + 1, criteriaValues[solution][criteriumIndex] + 0.05*criterium['UB'], f"{'+' if criteriaGain >= 0 else ''}{criteriaGain}%",
                        ha = 'center', color = solutionsColors[solution])
                else:
                    ax.text(solutionIndex + 1, criteriaValues[solution][criteriumIndex] + 0.05*criterium['UB'], str(criteriaValues[solution][criteriumIndex]),
                        ha = 'center', color = solutionsColors[solution])
            ax.set_xticklabels([])
            ax.set_ylim(0, criterium['UB'])
            ax.set_ylabel(criterium['unit'])
            ax.set_title(criterium['name'])

        if len(solutions) > 1:
            handles, labels = ax.get_legend_handles_labels()
            figure.legend(handles, labels, loc='lower center')

        plt.draw()

        return figure
