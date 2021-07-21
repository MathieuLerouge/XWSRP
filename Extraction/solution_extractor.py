###########
# Modules #
###########


# Project modules
from Tools.time import *
from Definition.solution import *



##########################
# Functions - Extraction #
##########################


def extractSolutionFromTxtFile(relativePathToTxtFile, instance):

    # Read lines of the solution file
    with open(relativePathToTxtFile, 'r') as file:
        fileLines = [line for line in file]

    # Initialize an empty solution adapted to the instance
    solution = Solution(instance = instance)
    #solution.initializeTasksDescription()

    # Check the header of the paragraph about tasks
    lineIndex = 0
    firstWord = fileLines[lineIndex].split(';')[0]
    if firstWord != "taskId":
        if firstWord in instance.tasks.keys():
            print("The header of the paragraph about tasks is missing")
        else:
            print("The header of the paragraph about tasks is wrong")
            lineIndex += 1
    else:
        lineIndex += 1

    # Read the data in paragraph about tasks
    while (lineIndex < len(fileLines)) and (len(fileLines[lineIndex]) > 4):
        words = fileLines[lineIndex].split(';')
        taskName = words[0]
        if not(taskName in instance.tasks.keys()):
            print(f"Task {taskName} is not in the tasks set")
        else:
            taskDescription = solution.tasksDescriptions[taskName]
            taskDescription['realized'] = True if int(words[1]) == 1 else False
            if taskDescription['realized']:
                taskDescription['employeeName'] = words[2]
                if not(":" in words[3]):
                    taskDescription["startTime"] = int(float(words[3]))
                else:
                    print("Task start time format is wrong")
                    taskDescription["startTime"] = convert_time_string_to_nb_minutes(words[3])
        lineIndex += 1

    return solution
