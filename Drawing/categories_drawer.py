###########
# Modules #
###########


# Basic modules
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np



#########################
# Functions - Bar Chart #
#########################


# Assumption: groups is a dictionnary
def createBarChartFigure(categories, groups):

    categoriesNames = categories.keys()
    groupsNames = list(groups.keys())

    plt.style.use('seaborn-whitegrid')
    colors = dict(zip(groupsNames, sns.color_palette("hls", len(groups))))

    #fig, axs = plt.subplots(1, 4, figsize=(12, 3))
    fig, axs = plt.subplots(1, 4, figsize=(9, 3), dpi = 30)
    #plt.subplots_adjust(wspace = 1)
    plt.subplots_adjust(top=0.8, bottom=0.2, wspace = 1)

    for categoryIndex, (categoryName, category) in enumerate(categories.items()):
        ax = axs[categoryIndex]
        for groupIndex, groupName in enumerate(groupsNames):
            bar = ax.bar(groupIndex + 1, groups[groupName][categoryIndex], width = 0.5, label = groupName)
            #ax.bar_label(bar, padding = 3)
        ax.set_xticklabels([])
        ax.set_ylim(0, category['UB'])
        ax.set_ylabel(category['unit'])
        ax.set_title(categoryName)

    ax = list(axs)[-1]
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center')

    plt.draw()

    return fig



###########################
# Functions - Radar Graph #
###########################


def drawRadarGraph(categoriesNames, individuals, saveFigures = False, pathToOutput = None):

    plt.style.use('seaborn-whitegrid')
    colors = dict(zip(individuals.keys(),
        sns.color_palette("hls", len(individuals))))

    fig = plt.figure()
    axRadarGraph = plt.axes(polar = True)
    axRadarGraph.set_theta_offset(np.pi/2)
    axRadarGraph.set_theta_direction(-1)

    nbCategories = len(categoriesNames)
    angles = [n/float(nbCategories)*2*np.pi for n in range(nbCategories)]
    angles.append(0)

    axRadarGraph.set_rlabel_position(0)
    plt.xticks(angles[:-1], categoriesNames)
    #plt.xticks(angles, categoriesNames)
    plt.yticks([0.25, 0.5, 0.75], ["25%", "50%", "75%"], color = "grey", size = 7)
    plt.ylim(0, 1)

    for individualName, individualValues in individuals.items():
        values = individualValues + individualValues[:1]
        #values = individualValues
        axRadarGraph.plot(angles, values, linewidth = 1, linestyle = 'solid', label = individualName)
        #axRadarGraph.fill(angles[:-1], values[:-1], colors[individualName], alpha = 0.1)

    plt.legend(loc = 'upper right')

    # if saveFigures:
    #     plt.savefig(pathToOutput)

    plt.draw()
