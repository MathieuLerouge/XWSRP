###########
# Modules #
###########

# Basic modules
from os import walk

# Project modules
from Drawing.solution_drawer import *
from Extraction.instance_extraction import *
from Extraction.solution_extractor import *
from Tools.display import *
from solution_checker import *



####################
# Variables to set #
####################

# Set instance-related parameters
relativePathToInstancesSets = "Instances"
#instancesSetName = "InstancesV1"
#regionNames = ["GuineaGolf", "Bordeaux", "Poland", "Italy", "Finland"]
#modelType = 1
instancesSetName = "InstancesV2"
regionNames = ["Australia", "Bordeaux", "Austria", "Poland", "Spain"]
modelType = 2
# instancesSetName = "InstancesV3"
# regionNames = ["Columbia", "Romania", "Ukraine"]
# modelType = 2
#regionNames = ["Bordeaux"]

# Set constraints-checking-related parameters
toleranceInMinutes = 1

# Set solution-related parameters
relativePathToInputs = "Checking/SolutionsToCheck"
relativePathToOutputs = "Checking/SolutionsChecksAndAnalysis"
showFiguresToggle = True
saveFiguresToggle = False
showAnalysisToggle = True
saveAnalysisToggle = False



#############
# Functions #
#############


def runChecking(regionName):

    # Deduce instance name and path to file
    regionNameSuffix = instancesSetName[-2:]
    regionName += regionNameSuffix
    instanceName = "Instance" + regionName
    relativePathToInstanceFile = relativePathToInstancesSets + "/" + instancesSetName + "/" + instanceName + ".xlsx"

    # Create instance
    instance = extractInstanceFromFile(
        instanceFilePath = relativePathToInstanceFile,
        regionName = regionName
    )
    instance.speed = 5/6
    if modelType == 2:
        instance.setLunchBreakParameters(
            lunchBreakStartTime = convert_time_string_to_nb_minutes("12:00pm"),
            lunchBreakEndTime = convert_time_string_to_nb_minutes("2:00pm"),
            lunchBreakDuration = 60
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
        for solutionFileName in solutionFileNames:

            # Extract solution
            print("Extraction of " + solutionFileName)
            pathToSolutionFile = relativePathToInputs + "/" + solutionFileName
            solution = extractSolutionFromTxtFile(pathToSolutionFile, instance)
            if ".txt" in fileName:
                solution.name = solutionFileName[:-4]
            else:
                solution.name = solutionFileName
            print("")

            # Complete solution with sequences and lunch lunch breaks
            print("Completion of " + solutionFileName)
            solution.computeSequencesAndLunchBreaks()
            print("")
            # print(solution)
            # print("")

            # Check solution
            print("Checking of " + solutionFileName)
            if checkFeasibility(solution, toleranceInMinutes):
                print("All constraints are satisfied")
            print("")

            # Show solution
            if showFiguresToggle or saveFiguresToggle:
                print("Representation of " + solutionFileName)
                print("")
                drawSolution(solution,
                    showFigures = showFiguresToggle, blockComputation = showFiguresToggle,
                    saveFigures = saveFiguresToggle, pathToFolderForOutputs = relativePathToOutputs)

            # Write solution analysis
            if saveAnalysisToggle:
                print("Analysis of " + solutionFileName)
                print("")
                solution.computeKPIs()
                writeSolutionAnalysis(solution, pathToFolderForOutputs = relativePathToOutputs)



def main():
    print("")
    for regionName in regionNames :
        print("")
        printTitleFrame(regionName)
        print("")
        runChecking(regionName)
        print("")


if __name__ == '__main__':
    main()
