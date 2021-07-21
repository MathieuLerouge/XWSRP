###########
# Modules #
###########

# Project modules
from Drawing.solution_drawer import *
from Extraction.instance_extraction import *
from Optimization.IPModel.IP_model import *
from Writing.solution_writer import *



####################
# Variables to set #
####################

# Set instance-related parameters
relativePathToInstancesSets = "Instances"
#instancesSetName = "InstancesV1"
# regionNames = ["GuineaGolf", "Bordeaux", "Poland", "Italy", "Finland"]
# modelType = 1
instancesSetName = "InstancesV2"
#regionNames = ["Bordeaux", "Australia", "Austria", "Poland", "Spain"]
modelType = 2
# instancesSetName = "InstancesV3"
#regionNames = ["Columbia", "Romania", "Ukraine"]
# modelType = 2
regionNames = ["Bordeaux"]

# Set solution-related parameters
relativePathToSolutionsFolder = "Optimization/Solutions"
writeSolutionToggle = False
drawSolutionToggle = True
showFiguresToggle = True
saveFiguresToggle = False

# Set IP optimization parameters
IPModelType = 2 # (1 or 2)
displayIPModelToggle = False
muteIPModelSolvingToggle = False
solvingTimeLimitInSeconds = 10



#############
# Functions #
#############


def runOptimization(regionName):

    # Deduce instance name and path to file
    regionNameSuffix = instancesSetName[-2:]
    instanceName = "Instance" + regionName + regionNameSuffix
    relativePathToInstanceFile = relativePathToInstancesSets + "/" + instancesSetName + "/" + instanceName + ".xlsx"

    # Create instance
    instance = extractInstanceFromFile(
        instanceFilePath = relativePathToInstanceFile,
        regionName = regionName + regionNameSuffix
    )
    instance.speed = 5/6
    if modelType == 2:
        instance.setLunchBreakParameters(
            lunchBreakStartTime = convert_time_string_to_nb_minutes("12:00pm"),
            lunchBreakEndTime = convert_time_string_to_nb_minutes("2:00pm"),
            lunchBreakDuration = 60
        )

    # Create IP model
    model = IPModel(instance = instance, type = IPModelType)
    if IPModelType == 1:
        model.setObjectiveFunctionParameters(
            minimization = True,
            travelingDurationCoefficient = 1,
            workingDurationCoefficient = None,
            nbRealizedTasksCoefficient = None
        )
    elif IPModelType == 2:
        model.setObjectiveFunctionParameters(
            minimization = False,
            travelingDurationCoefficient = -1,
            workingDurationCoefficient = 10,
            nbRealizedTasksCoefficient = None
        )

    # Display instance name
    print("")
    print("Optimization of " + instanceName)
    print("")

    # Display IP Model
    if displayIPModelToggle:
        model.GRBModel.display()
        print("")

    # Optimize and extract solution if any
    model.setSolvingTimeLimit(solvingTimeLimitInSeconds)
    model.optimize(mute = muteIPModelSolvingToggle)
    solution = model.getSolution()
    solution.computeSequencesAndLunchBreaks()
    solution.computeKPIs()
    print(solution)
    print("")
    print("Number of realized tasks: " + str(solution.KPIs['nbRealizedTasks']))
    print("Total working duration (in min): " + str(solution.KPIs['totalWorkingDuration']))
    print("Total traveling duration (in min): " + str(solution.KPIs['totalTravelingDuration']))
    print("Total traveling distance (in km): " + str(solution.KPIs['totalTravelingDistance']))
    print("Total idle time (in min): " + str(solution.KPIs['totalIdleTime']))
    print("")

    # Write solution
    if writeSolutionToggle:
        writeSolution(solution, pathToFolderForOutputs = relativePathToSolutionsFolder)
        writeSolutionAnalysis(solution, pathToFolderForOutputs = relativePathToSolutionsFolder)

    # Draw solution
    if drawSolutionToggle:
        drawSolution(solution, showFigures = showFiguresToggle, blockComputation = showFiguresToggle,
            saveFigures = saveFiguresToggle, pathToFolderForOutputs = relativePathToSolutionsFolder)


def main():
    for regionName in regionNames :
        runOptimization(regionName)


if __name__ == '__main__':
    main()
