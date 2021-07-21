# TODO:
# Remove section about writing lunch breaks descriptions

###########
# Modules #
###########


# Project modules
from Definition.solution import *
from Tools.global_variables import *



#############
# Functions #
#############


def writeSolution(solution: Solution, pathToFolderForOutputs):

    # Open file
    relativePathToTxtFileName = pathToFolderForOutputs + "/" + solution.name + ".txt"
    file = open(relativePathToTxtFileName, "w")

    # Write solution's data about tasks
    file.write("taskId;performed;employeeName;startTime;" + lineBreak)
    for taskName, taskDescription in solution.tasksDescriptions.items():
        lineString = taskName + ";"
        if taskDescription['realized']:
            lineString += "1;"
            lineString += taskDescription['employeeName'] + ";"
            lineString += str(taskDescription['startTime'])  + ";"
        else:
            lineString += "0;;;"
        file.write(lineString + lineBreak)

    # Write solution's data about employees' lunch breaks
    # if solution.instance.hasLunchBreaks():
    #     file.write(lineBreak)
    #     file.write("employeeName;lunchBreakStartTime;" + lineBreak)
    #     for employeeName, lunchBreakDescription in solution.lunchBreaksDescriptions.items():
    #         lineString = employeeName + ";"
    #         lineString += str(lunchBreakDescription['startTime']) + ";"
    #         file.write(lineString + lineBreak)

    # Close file
    file.close()



def writeSolutionAnalysis(solution: Solution, pathToFolderForOutputs):

    # Open file
    relativePathToTxtFileName = pathToFolderForOutputs + "/" + solution.name + "Analysis" + ".txt"
    file = open(relativePathToTxtFileName, "w")

    # Write solution performances indicators
    if solution.KPIs == None:
        solution.computeKPIs()
    file.write("Number of realized tasks: " + str(solution.KPIs['nbRealizedTasks']) + lineBreak)
    file.write("Total working duration (in min): " + str(solution.KPIs['totalWorkingDuration']) + lineBreak)
    file.write("Total traveling duration (in min): " + str(solution.KPIs['totalTravelingDuration']) + lineBreak)
    file.write("Total traveling distance (in km): " + str(solution.KPIs['totalTravelingDistance']) + lineBreak)
    file.write("Total idle time (in min): " + str(solution.KPIs['totalIdleTime']) + lineBreak)
    file.write(lineBreak)

    # Write about solving method
    if solution.optimization != None:
        file.write("Optimization method id: " + str(solution.optimization['methodId']) + lineBreak)
        file.write("Optimization run time (in s): " + str(solution.optimization['solvingRunTime']) + lineBreak)
        if solution.optimization['methodId'] in [IPModelType1Id, IPModelType2Id]:
            file.write("Objective function parameters: " + str([p if p != None else 0 for p in solution.optimization['parameters']]) + lineBreak)
            file.write("Optimality gap (in %): " + str(np.round(solution.optimization['optimalityGap']*100, 3)) + lineBreak)
            file.write("Objective value: " + str(solution.optimization['objectiveValue']) + lineBreak)
        file.write(lineBreak)

    # Write about employees' sequences
    file.write(str(solution))

    # Close file
    file.close()
