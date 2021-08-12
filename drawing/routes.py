# Third party libraries
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import seaborn as sns

# Local libraries
from model.solution import Solution
from model.unavailability import Unavailability


# Global variables
# - symbols sizes
STEP_MARKER_SIZE = 20
DEPOT_MARKER_SIZE = 40
# - figure parameters by default
ROUTES_FIGURE_WIDTH = 640
ROUTES_FIGURE_HEIGHT = 524
# - figure parameters for UI
ROUTES_FIGURE_DPI_FOR_UI = 80
ROUTES_FIGURE_ARROW_HEAD_WIDTH_FOR_UI = 0.003
ROUTES_FIGURE_ARROW_HEAD_LENGTH_FOR_UI = 0.002


# Create routes figure
def create_routes_figure(solution: Solution, figure_id: str = None, infeasibility=None, for_UI: bool = False) -> Figure:

    plt.style.use('seaborn-whitegrid')

    # Create a new figure
    if figure_id is None:
        figure = plt.figure()
    else:
        figure = plt.figure(figure_id)
    if for_UI:
        figure.dpi = ROUTES_FIGURE_DPI_FOR_UI
        plt.subplots_adjust(left=0.15, right=0.9, top=0.95, bottom=0.1)
    ax = figure.add_subplot()

    # Define axis
    if solution.instance.has_geographic_locations:
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
    else:
        plt.xlabel("x")
        plt.ylabel("y")

    # Draw employees' paths
    colors = dict(zip(solution.instance.employees_names, sns.color_palette("hls", solution.instance.nb_employees)))
    for employee in solution.instance.employees:

        path_first_coordinates = []
        path_second_coordinates = []
        step_names = []
        indices_of_tasks_in_path = []
        indices_of_unavailabilities_in_path = []

        path_first_coordinates.append(employee.location.coordinates[0])
        path_second_coordinates.append(employee.location.coordinates[1])
        step_names.append("")

        for step in solution.get_sequence(employee)[1:-1]:
            path_first_coordinates.append(step.activity.location.coordinates[0])
            path_second_coordinates.append(step.activity.location.coordinates[1])
            step_names.append(step.activity.name)
            current_index = len(step_names) - 1
            if isinstance(step.activity, Unavailability):
                indices_of_unavailabilities_in_path.append(current_index)
            else:
                indices_of_tasks_in_path.append(current_index)

        path_first_coordinates.append(employee.location.coordinates[0])
        path_second_coordinates.append(employee.location.coordinates[1])
        step_names.append("")

        if solution.instance.has_geographic_locations:
            path_first_coordinates, path_second_coordinates = path_second_coordinates, path_first_coordinates
        path_first_coordinates = np.array(path_first_coordinates)
        path_second_coordinates = np.array(path_second_coordinates)

        if infeasibility is not None and employee.name == infeasibility['employee_name']:
            infeasible_task = solution.instance.get_task_by_name(infeasibility['task_name'])
            step_index = solution[employee.name].get_step_index_of(infeasible_task)
            ax.plot(path_first_coordinates[:step_index], path_second_coordinates[:step_index], label=employee.name,
                    color=colors[employee.name])
            ax.plot(path_first_coordinates[step_index - 1: step_index + 2],
                    path_second_coordinates[step_index - 1: step_index + 2], color=colors[employee.name],
                    linestyle='--')
            ax.plot(path_first_coordinates[step_index + 1:], path_second_coordinates[step_index + 1:],
                    color=colors[employee.name])
        else:
            ax.plot(path_first_coordinates, path_second_coordinates, label=employee.name,
                    color=colors[employee.name])

        if len(path_first_coordinates) > 2:
            arrow_start = np.array([path_first_coordinates[0], path_second_coordinates[0]])
            arrow_end = np.array([path_first_coordinates[1], path_second_coordinates[1]])
            if np.linalg.norm(arrow_end - arrow_start, 2) < 1e-10:
                arrow_end = np.array([path_first_coordinates[2], path_second_coordinates[2]])
            arrow_end = np.mean(np.array([arrow_start, arrow_end]), axis=0)
            # if for_UI:
            #     ax.arrow(arrow_start[0], arrow_start[1],
            #              arrow_end[0] - arrow_start[0], arrow_end[1] - arrow_start[1],
            #              head_width=ROUTES_FIGURE_ARROW_HEAD_WIDTH_FOR_UI,
            #              head_length=ROUTES_FIGURE_ARROW_HEAD_LENGTH_FOR_UI,
            #              color=colors[employee.name], linewidth=0)
            # TODO Add arrows even if not for UI

        ax.scatter(path_first_coordinates[0], path_second_coordinates[0],
                   color=colors[employee.name], alpha=0.7, marker='s', s=DEPOT_MARKER_SIZE, zorder=3)

        ax.scatter(path_first_coordinates[indices_of_tasks_in_path],
                   path_second_coordinates[indices_of_tasks_in_path],
                   color=colors[employee.name], alpha=0.7, marker='o', s=STEP_MARKER_SIZE)

        ax.scatter(path_first_coordinates[indices_of_unavailabilities_in_path],
                   path_second_coordinates[indices_of_unavailabilities_in_path],
                   color=colors[employee.name], alpha=0.7, marker='X', s=STEP_MARKER_SIZE)

        for j in range(1, len(step_names) - 1):
            ax.annotate(step_names[j], (path_first_coordinates[j], path_second_coordinates[j]),
                        color=colors[employee.name])

    non_realized_tasks_first_coordinates = []
    non_realized_tasks_second_coordinates = []
    non_realized_tasks_names = []
    for task in solution.instance.tasks:
        if not(solution.get_task_realization(task)):
            non_realized_tasks_first_coordinates.append(task.location.coordinates[0])
            non_realized_tasks_second_coordinates.append(task.location.coordinates[1])
            non_realized_tasks_names.append(task.name)

    if solution.instance.has_geographic_locations:
        non_realized_tasks_first_coordinates, non_realized_tasks_second_coordinates = \
            non_realized_tasks_second_coordinates, non_realized_tasks_first_coordinates

    ax.scatter(non_realized_tasks_first_coordinates, non_realized_tasks_second_coordinates,
               color='tab:gray', alpha=0.7, marker='o', s=STEP_MARKER_SIZE)

    for j in range(len(non_realized_tasks_names)):
        ax.annotate(non_realized_tasks_names[j],
                    (non_realized_tasks_first_coordinates[j], non_realized_tasks_second_coordinates[j]),
                    color='tab:gray')

    # Add legend and title
    plt.legend()
    if not for_UI:
        plt.title("Routes of " + solution.name)
        if matplotlib.get_backend() == 'Qt5Agg':
            plt.get_current_fig_manager().window.setGeometry(80, 50, ROUTES_FIGURE_WIDTH, ROUTES_FIGURE_HEIGHT)

    # Draw
    plt.draw()

    return figure
