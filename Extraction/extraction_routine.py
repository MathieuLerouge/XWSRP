###########
# Modules #
###########

# Project modules
from Extraction.instance_extraction import *



####################
# Variables to set #
####################

# Set instance-related parameters
relativePathToInstancesSets = "Instances"
#instancesSetName = "InstancesV1"
#regionNames = ["GuineaGolf", "Bordeaux", "Poland", "Italy", "Finland"]
#modelType = 1
#instancesSetName = "InstancesV2"
#regionNames = ["Australia", "Bordeaux", "Austria", "Poland", "Spain"]
#modelType = 2
instancesSetName = "InstancesV3"
regionNames = ["Columbia", "Romania", "Ukraine"]
modelType = 2


#############
# Functions #
#############


def runExtraction(regionName):

    # Deduce instance name and path to file
    regionNameSuffix = instancesSetName[-2:]
    regionName += regionNameSuffix
    instanceName = "Instance" + regionName
    relativePathToInstanceFile = relativePathToInstancesSets + "/" + instancesSetName + "/" + instanceName + ".xlsx"

    # Display instance name
    print("")
    print("Extraction of " + instanceName)
    print("")

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

    for task in instance.tasks.values():
        print(task.name + ": " + str(task.availabilityTimeWindows))



def main():
    print("")
    for regionName in regionNames :
        runExtraction(regionName)
        print("")


if __name__ == '__main__':
    main()
