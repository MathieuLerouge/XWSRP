###########
# Modules #
###########


# Basic modules
from os import walk


# Project modules
from Checking.solution_checker import *
from Definition.solution import *
from Drawing.solution_drawer import *
from Explanation.explainer import *
from Explanation.explainer_UI import *
from Extraction.instance_extraction import *
from Extraction.solution_extractor import *
from Optimization.solution_for_LS import *
from Tools.display import *
from explanations import *



####################
# Variables to set #
####################


# Set instance-related parameters
relativePathToInstances = "Explanation/Instances"
# regionName = "Bordeaux"
regionName = "Austria"
# regionName = "Poland"
# regionName = "Ukraine"
ignoreEmployeesUnavailabilitiesToggle = False
ignoreTasksUnavailabilitiesToggle = True
ignoreLunchBreaksToggle = True
lunchBreakStartTime = convert_time_string_to_nb_minutes("12:00pm")
lunchBreakEndTime = convert_time_string_to_nb_minutes("2:00pm")
lunchBreakDuration = 60

# Set solution-related parameters
relativePathToInputs = "Explanation/SolutionsToExplain"



#############
# Functions #
#############


def runExplaining(regionName):

    # Deduce instance name and path to file
    instanceName = "Instance" + regionName
    relativePathToInstanceFile = relativePathToInstances + "/" + instanceName + ".xlsx"

    # Create instance
    instance = extractInstanceFromFile(
        instanceFilePath = relativePathToInstanceFile, regionName = regionName,
        ignoreEmployeesUnavailabilities = ignoreEmployeesUnavailabilitiesToggle,
        ignoreTasksUnavailabilities = ignoreTasksUnavailabilitiesToggle
    )
    instance.speed = 5/6
    if not(ignoreLunchBreaksToggle):
        instance.setLunchBreakParameters(lunchBreakDuration = lunchBreakDuration,
            lunchBreakStartTime = lunchBreakStartTime, lunchBreakEndTime = lunchBreakEndTime
        )

    # Deduce solution files
    _, _, fileNames = next(walk(relativePathToInputs))
    solutionFileNames = []
    for fileName in fileNames:
        if regionName in fileName:
            solutionFileNames.append(fileName)

    # Go through all solution files
    if len(solutionFileNames) == 0:
        print("There is no solution file for " + regionName)
        print("")
    else:
        solutionFileName = solutionFileNames[0]

        print("")
        printTitleFrame("Extracting")
        print("")

        # Extract solution
        print("Extraction of " + solutionFileName)
        pathToSolutionFile = relativePathToInputs + "/" + solutionFileName
        solution = extractSolutionFromTxtFile(pathToSolutionFile, instance)
        if ".txt" in fileName:
            solution.name = solutionFileName[:-4]
        else:
            solution.name = solutionFileName
        print("Completion of " + solutionFileName)
        solution.updateTimesAccordingToTasksDescriptions()
        print("")

        print("")
        printTitleFrame("Checking")
        print("")

        # Check solution
        print("Checking of " + solutionFileName)
        if not(checkFeasibility(solution)):
            print("Solution is not feasible")
            return False
        print("")

        # Draw solution
        solution.updateKPIs()
        solution = SolutionForLS.fromSolution(solution)
        solution.updateTimeSlacks()
        explainer = Explainer(solution)
        explainerUI = ExplainerUI(explainer)
        explainerUI.show()


def main():
    runExplaining(regionName)
    print("")


if __name__ == '__main__':
    main()
