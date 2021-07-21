# TOBEREMOVED

# ###########
# # Modules #
# ###########
#
#
# # Basic modules
# import matplotlib
# matplotlib.use('Qt5Agg')
# import matplotlib.pyplot as plt
# import seaborn as sns
# import numpy as np
#
# # Project modules
# from Definition.solution import *
# from Drawing.categories_drawer import *
#
#
#
# ######################
# # Functions - Routes #
# ######################
#
#
# def createRoutesFigure(solution: Solution, isInUI = False, figureSize = None, dpi = None):
#
#     plt.style.use('seaborn-whitegrid')
#     colors = dict(zip(solution.instance.getEmployeesNames(),
#         sns.color_palette("hls", len(solution.instance.employees))))
#     stepMarkerSize = 20
#     depotMarkerSize = 40
#
#     fig = None
#     if isInUI:
#         fig = plt.figure(figsize = (9, 9), dpi = 40)
#         plt.subplots_adjust(left = 0.15, right = 0.9, top = 0.95, bottom = 0.1)
#     else:
#         fig = plt.figure()
#         plt.title(solution.name)
#
#     ax = plt.axes()
#     if solution.instance.hasGeographicLocations():
#         plt.xlabel("Longitude")
#         plt.ylabel("Latitude")
#     else:
#         plt.xlabel("x")
#         plt.ylabel("y")
#
#     for employeeName, employee in solution.instance.employees.items():
#
#         pathFirstCoordinates = []
#         pathSecondCoordinates = []
#         stepNames = []
#         indicesOfTasksInPath = []
#         indicesOfUnavailabilitiesInPath = []
#
#         pathFirstCoordinates.append(employee.location.coordinates[0])
#         pathSecondCoordinates.append(employee.location.coordinates[1])
#         stepNames.append("")
#
#         for step in solution.sequences[employeeName][1:-1]:
#             stepName = step.activity.name
#             task = solution.instance.getActivity(activityName = stepName, employeeName = employeeName)
#             pathFirstCoordinates.append(task.location.coordinates[0])
#             pathSecondCoordinates.append(task.location.coordinates[1])
#             stepNames.append(stepName)
#             currentIndex = len(stepNames) - 1
#             if task.isEmployeeUnavailability():
#                 indicesOfUnavailabilitiesInPath.append(currentIndex)
#             else:
#                 indicesOfTasksInPath.append(currentIndex)
#
#         pathFirstCoordinates.append(employee.location.coordinates[0])
#         pathSecondCoordinates.append(employee.location.coordinates[1])
#         stepNames.append("")
#
#         if solution.instance.hasGeographicLocations():
#             # Remark: coordinates[0] is a lattitude, coordinates[1] is a longitude
#             pathFirstCoordinates, pathSecondCoordinates = \
#                 pathSecondCoordinates, pathFirstCoordinates
#         pathFirstCoordinates = np.array(pathFirstCoordinates)
#         pathSecondCoordinates = np.array(pathSecondCoordinates)
#
#         ax.plot(pathFirstCoordinates, pathSecondCoordinates,
#             label = employeeName, color = colors[employeeName])
#
#         # plotPath(ax, pathFirstCoordinates, pathSecondCoordinates)
#
#         ax.scatter(pathFirstCoordinates[0],
#             pathSecondCoordinates[0],
#             color = colors[employeeName], alpha = 0.7,
#             marker = 's', s = depotMarkerSize,
#             zorder = 3)
#
#         ax.scatter(pathFirstCoordinates[indicesOfTasksInPath],
#             pathSecondCoordinates[indicesOfTasksInPath],
#             color = colors[employeeName], alpha = 0.7,
#             marker = 'o', s = stepMarkerSize)
#
#         ax.scatter(pathFirstCoordinates[indicesOfUnavailabilitiesInPath],
#             pathSecondCoordinates[indicesOfUnavailabilitiesInPath],
#             color = colors[employeeName], alpha = 0.7,
#             marker = 'X', s = stepMarkerSize)
#
#         for j in range(1, len(stepNames) - 1):
#             ax.annotate(stepNames[j],
#                 (pathFirstCoordinates[j], pathSecondCoordinates[j]),
#                 color = colors[employeeName])
#
#     nonRealizedTasksFirstCoordinates = []
#     nonRealizedTasksSecondCoordinates = []
#     nonRealizedTasksNames = []
#     for taskName, description in solution.tasksDescriptions.items():
#         if not(description['realized']):
#             task = solution.instance.getTask(taskName)
#             nonRealizedTasksFirstCoordinates.append(task.location.coordinates[0])
#             nonRealizedTasksSecondCoordinates.append(task.location.coordinates[1])
#             nonRealizedTasksNames.append(taskName)
#
#     if solution.instance.hasGeographicLocations():
#         # Remark: coordinates[0] is a lattitude, coordinates[1] is a longitude
#         nonRealizedTasksFirstCoordinates, nonRealizedTasksSecondCoordinates = \
#             nonRealizedTasksSecondCoordinates, nonRealizedTasksFirstCoordinates
#
#     ax.scatter(nonRealizedTasksFirstCoordinates, nonRealizedTasksSecondCoordinates,
#         color = 'tab:gray', alpha = 0.7,
#         marker = 'o', s = stepMarkerSize)
#
#     for j in range(len(nonRealizedTasksNames)):
#         ax.annotate(nonRealizedTasksNames[j],
#             (nonRealizedTasksFirstCoordinates[j], nonRealizedTasksSecondCoordinates[j]),
#             color = 'tab:gray')
#
#     plt.legend()
#     plt.draw()
#
#     return fig
#
#
# def drawRoutes(solution: Solution, saveFigures, pathToFolderForOutputs):
#
#     fig = createRoutesFigure(solution)
#
#     if matplotlib.get_backend() == 'Qt5Agg':
#         fig.canvas.manager.window.move(0, 0)
#
#     if saveFigures:
#         pathToPngFile = pathToFolderForOutputs + "/" + solution.name + "Routes"+ ".png"
#         plt.savefig(pathToPngFile)
#
#
#
# #########################
# # Functions - Schedules #
# #########################
#
#
# def createSchedulesFigure(solution: Solution, isInUI = False):
#
#     colors = dict(zip(solution.instance.getEmployeesNames(), sns.color_palette("hls", len(solution.instance.employees))))
#
#     fig = None
#     if isInUI:
#         fig = plt.figure(figsize = (9, 9), dpi = 40)
#         plt.subplots_adjust(left = 0.15, right = 0.9, top = 0.95, bottom = 0.1)
#     else:
#         fig = plt.figure()
#         plt.title(solution.name)
#
#     ax = plt.axes()
#     ax.invert_yaxis()
#     maxTimeValue = 0
#     minTimeValue = 24*60
#     for sequence in solution.sequences.values():
#         maxTimeValue = max(maxTimeValue, sequence[-1].startTime)
#         minTimeValue = min(minTimeValue, sequence[0].startTime)
#     timeValuesRangeSize = maxTimeValue - minTimeValue
#     maxTimeValue += np.ceil(timeValuesRangeSize*0.05)
#     minTimeValue -= np.ceil(timeValuesRangeSize*0.05)
#     ax.set_xlim(minTimeValue, maxTimeValue)
#     plt.xlabel("Time (in min)")
#     plt.ylabel("Employees")
#
#     for employeeIndex, (employeeName, sequence) in enumerate(solution.sequences.items()):
#
#         employee = solution.instance.getEmployee(employeeName)
#         lunchBreakDescription = None
#         if solution.instance.hasLunchBreaks():
#             lunchBreakDescription = solution.lunchBreaksDescriptions[employeeName]
#
#         barColor = colors[employeeName]
#         #r, g, b = barColor
#         #txtColor = 'white' if r*g*b < 0.5 else 'darkgrey'
#         txtColor = 'black'
#         hatchColor = 'white'
#
#         if len(sequence) > 2:
#
#             # Draw tasks and unavailabilities
#             for step in sequence[1:-1]:
#                 taskName = step.activity.name
#                 barLeftSide = step.startTime
#                 barWidth = step.endTime - step.startTime
#                 barCenter = barLeftSide + barWidth/2
#                 task = solution.instance.getActivity(activityName = taskName, employeeName = employeeName)
#                 if task.isEmployeeUnavailability():
#                     ax.barh(y = employeeName, left = barLeftSide, width = barWidth,
#                         height = 0.5, color = barColor,
#                         edgecolor = hatchColor, hatch = "//")
#                 else:
#                     ax.barh(y = employeeName, left = barLeftSide, width = barWidth,
#                         height = 0.5, color = barColor)
#                 ax.text(x = barCenter, y = employeeIndex, s = taskName,
#                     ha = 'center', va = 'center',
#                     color = txtColor)
#
#             # Draw displacements
#             for stepIndex, step in enumerate(sequence[:-1]):
#                 barLeftSide = step.endTime
#                 barWidth = int(np.ceil(solution.computeTravelingDuration(step, sequence[stepIndex + 1])))
#                 if barWidth > 0:
#                     if solution.instance.hasLunchBreaks() and \
#                         lunchBreakDescription['stepBefore'] == step.activity.name and \
#                         lunchBreakDescription['startTime'] < barLeftSide + barWidth:
#                         bar1LeftSide = barLeftSide
#                         bar1Width = lunchBreakDescription['startTime'] - barLeftSide
#                         if bar1Width > 0:
#                             bar1Center = bar1LeftSide + bar1Width/2
#                             ax.barh(y = employeeName, left = bar1LeftSide, width = bar1Width,
#                                 height = 0.25, color = 'darkgrey')
#                             ax.text(x = bar1Center, y = employeeIndex, s = str(bar1Width),
#                                 ha = 'center', va = 'center',
#                                 color = txtColor)
#                         bar2LeftSide = lunchBreakDescription['startTime'] + solution.instance.lunchBreakDuration
#                         bar2Width = barWidth - bar1Width
#                         if bar2Width > 0:
#                             bar2Center = bar2LeftSide + bar2Width/2
#                             ax.barh(y = employeeName, left = bar2LeftSide, width = bar2Width,
#                                 height = 0.25, color = 'darkgrey')
#                             ax.text(x = bar2Center, y = employeeIndex, s = str(bar2Width),
#                                 ha = 'center', va = 'center',
#                                 color = txtColor)
#                     else:
#                         barCenter = barLeftSide + barWidth/2
#                         ax.barh(y = employeeName, left = barLeftSide, width = barWidth,
#                             height = 0.25, color = 'darkgrey')
#                         ax.text(x = barCenter, y = employeeIndex, s = str(barWidth),
#                             ha = 'center', va = 'center',
#                             color = txtColor)
#
#             # Draw lunch breaks
#             if solution.instance.hasLunchBreaks():
#                 lunchBreakDescription = solution.lunchBreaksDescriptions[employeeName]
#                 barLeftSide = lunchBreakDescription['startTime']
#                 barWidth = solution.instance.lunchBreakDuration
#                 barCenter = barLeftSide + barWidth/2
#                 ax.barh(y = employeeName, left = barLeftSide, width = barWidth,
#                     height = 0.5, color = barColor,
#                     edgecolor = hatchColor, hatch = "/")
#                 ax.text(x = barCenter, y = employeeIndex, s = "LB",
#                     ha = 'center', va = 'center',
#                     color = txtColor)
#
#     plt.draw()
#
#     return fig
#
#
#
# def drawSchedules(solution: Solution, saveFigures, pathToFolderForOutputs):
#
#     fig = createSchedulesFigure(solution)
#
#     if matplotlib.get_backend() == 'Qt5Agg':
#         fig.canvas.manager.window.move(1000, 0)
#
#     if saveFigures:
#         pathToPngFile = pathToFolderForOutputs + "/" + solution.name + "Schedules"+ ".png"
#         plt.savefig(pathToPngFile)
#
#
#
# ####################
# # Functions - KPIs #
# ####################
#
#
# # def drawKPIs(solution: Solution, saveFigures = False, pathToFolderForOutputs = None):
# #
# #     categoriesNames = ["realized tasks rate", "average working duration rate",
# #         "average traveling duration rate", "average idle time rate"]
# #     nbMinutes = 24*60
# #     nbEmployees = len(solution.instance.employees)
# #     nbTasks = len(solution.instance.tasks)
# #
# #     individuals = dict()
# #     individuals[solution.name] = [
# #         solution.KPIs['nbRealizedTasks']/float(nbTasks),
# #         solution.KPIs['totalWorkingDuration']/float(nbMinutes)/nbEmployees,
# #         solution.KPIs['totalTravelingDuration']/float(nbMinutes)/nbEmployees,
# #         solution.KPIs['totalIdleTime']/float(nbMinutes)/nbEmployees
# #         ]
# #
# #     pathToOutput = None
# #     if saveFigures:
# #         pathToOutput = pathToFolderForOutputs + "/" + solution.name + "KPIs"+ ".png"
# #     drawRadarGraph(categoriesNames, individuals, saveFigures, pathToOutput)
#
#
# def createKPIsFigure(solution: Solution):
#
#     nbEmployees = len(solution.instance.employees)
#     nbTasks = len(solution.instance.tasks)
#     nbMinutesUB = 12*60
#
#     categories = dict()
#     categories["Realized tasks"] = {'UB': nbTasks, 'unit': "number"}
#     for name in ["Avg. working dur.", "Avg. traveling dur.", "Avg. idle time"]:
#         categories[name] = {'UB': nbMinutesUB, 'unit': "minutes"}
#
#     individuals = dict()
#     individuals[solution.name] = [
#         solution.KPIs['nbRealizedTasks'],
#         solution.KPIs['totalWorkingDuration']/float(nbEmployees),
#         solution.KPIs['totalTravelingDuration']/float(nbEmployees),
#         solution.KPIs['totalIdleTime']/float(nbEmployees)
#         ]
#
#     return createBarChartFigure(categories, individuals)
#
#
#
# def drawKPIs(solution: Solution, saveFigures = False, pathToFolderForOutputs = None):
#
#     fig = createKPIsFigure(solution)
#
#     if matplotlib.get_backend() == 'Qt5Agg':
#         fig.canvas.manager.window.move(120, 600)
#
#     if saveFigures:
#         pathToPngFile = pathToFolderForOutputs + "/" + solution.name + "KPIs"+ ".png"
#         plt.savefig(pathToPngFile)
#
#
#
# ####################
# # Functions - Both #
# ####################
#
#
# def drawSolution(solution: Solution, showFigures = True, blockComputation = False,
#     saveFigures = False, pathToFolderForOutputs = None):
#
#     if saveFigures:
#         plt.rcParams['figure.dpi'] = 300
#
#     drawRoutes(solution, saveFigures, pathToFolderForOutputs)
#     drawSchedules(solution, saveFigures, pathToFolderForOutputs)
#     drawKPIs(solution, saveFigures, pathToFolderForOutputs)
#
#     if showFigures:
#         plt.show(block = blockComputation)
#
#
# def showFigures(blockComputation = False):
#     plt.show(block = blockComputation)
#
#
# def closeFigures():
#     plt.close('all')
