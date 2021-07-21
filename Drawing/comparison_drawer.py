###########
# Modules #
###########


# Basic modules
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Project modules
from Definition.solution import *
from Drawing.categories_drawer import *
from Drawing.solution_drawer import *



###########
# Modules #
###########


def createComparisonBetweenSolutionsFigure(solution1: Solution, solution2: Solution):

    nbEmployees = len(solution1.instance.employees)
    nbTasks = len(solution1.instance.tasks)
    nbMinutesUB = 12*60

    categories = dict()
    categories["Realized tasks"] = {'UB': nbTasks, 'unit': "number"}
    for name in ["Average working duration", "Average traveling duration", "Average idle time"]:
        categories[name] = {'UB': nbMinutesUB, 'unit': "minutes"}

    individuals = dict()
    for solution in [solution1, solution2]:
        individuals[solution.name] = [
            solution.KPIs['nbRealizedTasks'],
            solution.KPIs['totalWorkingDuration']/float(nbEmployees),
            solution.KPIs['totalTravelingDuration']/float(nbEmployees),
            solution.KPIs['totalIdleTime']/float(nbEmployees)
            ]

    return createBarChartFigure(categories, individuals)


def drawComparisonBetweenSolutions(solution1: Solution, solution2: Solution):

    # nbEmployees = len(solution1.instance.employees)
    # nbTasks = len(solution1.instance.tasks)
    # nbMinutesUB = 12*60
    #
    # categories = dict()
    # categories["Realized tasks"] = {'UB': nbTasks, 'unit': "number"}
    # for name in ["Average working duration", "Average traveling duration", "Average idle time"]:
    #     categories[name] = {'UB': nbMinutesUB, 'unit': "minutes"}
    #
    # individuals = dict()
    # for solution in [solution1, solution2]:
    #     individuals[solution.name] = [
    #         solution.KPIs['nbRealizedTasks'],
    #         solution.KPIs['totalWorkingDuration']/float(nbEmployees),
    #         solution.KPIs['totalTravelingDuration']/float(nbEmployees),
    #         solution.KPIs['totalIdleTime']/float(nbEmployees)
    #         ]
    #
    # drawBarChart(categories, individuals)
    #showFigures(blockComputation = False)

    fig = createComparisonBetweenSolutionsFigure(solution1, solution2)

    if matplotlib.get_backend() == 'Qt5Agg':
        fig.canvas.manager.window.move(120, 600)
