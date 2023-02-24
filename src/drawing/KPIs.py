# Third party libraries
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

# Local library
from src.modeling.solution import Solution


# Global variables
# - figure parameters for UI
KPIS_FIGURE_DPI_FOR_UI = 60


# Create bar chart
def create_bar_chart_figure(solutions: list, figure_id: str = None, for_UI: bool = False) -> Figure:
    """
    Create a bar chart figure with the KPIs of the solutions.

    :param solutions: list of solutions to compare (Solution)
    :param figure_id: id of the figure (str)
    :param for_UI: if True, the figure is created for the UI (bool)
    :return: figure (Figure)
    """

    # Create a new figure if needed
    if figure_id is None:
        figure = plt.figure()
    else:
        figure = plt.figure(figure_id)
    if for_UI:
        figure.dpi = KPIS_FIGURE_DPI_FOR_UI
        plt.subplots_adjust(top=0.8, bottom=0.2, wspace=0.5, hspace=1)
    axes = figure.subplots(nrows=2, ncols=2)

    # Criteria descriptions
    nb_minutes_UB = 10 * 60
    criteria_descriptions = [
        {'name': "Realized tasks", 'UB': solutions[0].instance.nb_tasks, 'unit': "number"}]
    for name in ["Avg. working dur.", "Avg. traveling dur.", "Avg. idle time"]:
        criteria_descriptions.append({'name': name, 'UB': nb_minutes_UB, 'unit': "minutes"})

    # Criteria values
    nb_employees = solutions[0].instance.nb_employees
    criteria_values = dict()
    for solution in solutions:
        criteria_values[solution] = [
            solution.nb_performed_tasks,
            solution.total_working_duration / float(nb_employees),
            solution.total_traveling_duration / float(nb_employees),
            solution.total_idle_time / float(nb_employees)
        ]

    ax = None
    solutions_colors = dict(zip(solutions, sns.color_palette("husl", len(solutions))))
    for criterion_index, criterion in enumerate(criteria_descriptions):
        ax = axes[criterion_index // 2, criterion_index % 2]
        for solution_index, solution in enumerate(solutions):
            ax.bar(solution_index + 1, criteria_values[solution][criterion_index], width=0.5,
                   label=solution.name, color=solutions_colors[solution])
            if solution_index > 0:
                criteria_gain = np.round(
                    (criteria_values[solution][criterion_index] /
                     criteria_values[solutions[0]][criterion_index] - 1) * 100, 2
                )
                ax.text(solution_index + 1, criteria_values[solution][criterion_index] + 0.05 * criterion['UB'],
                        f"{'+' if criteria_gain >= 0 else ''}{criteria_gain}%",
                        ha='center', color=solutions_colors[solution])
            else:
                ax.text(solution_index + 1, criteria_values[solution][criterion_index] + 0.05 * criterion['UB'],
                        str(criteria_values[solution][criterion_index]),
                        ha='center', color=solutions_colors[solution])
        ax.set_xticklabels([])
        ax.set_ylim(0, criterion['UB'])
        ax.set_ylabel(criterion['unit'])
        ax.set_title(criterion['name'])

    if len(solutions) > 1:
        handles, labels = ax.get_legend_handles_labels()
        figure.legend(handles, labels, loc='lower center')

    # Add title
    if not for_UI:
        if len(solutions) == 1:
            figure.suptitle("KPIs of " + solutions[0].name)
        else:
            figure.suptitle("KPIs comparison")

    plt.draw()

    return figure


def create_KPIs_comparison_figure(solutions: list, figure_id: str = None, for_UI=False):
    return create_bar_chart_figure(solutions, figure_id, for_UI)


def create_KPIs_figure(solution: Solution, figure_id: str = None, for_UI=False):
    return create_bar_chart_figure([solution], figure_id, for_UI)