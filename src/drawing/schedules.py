# Third party libraries
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import seaborn as sns

# Local libraries
from src.drawing.routes import ROUTES_FIGURE_WIDTH
from src.modeling.solution import Solution
from src.modeling.unavailability import Unavailability
from src.utils.time import convert_nb_minutes_to_time_string


# Global variables
# - figure parameters
TXT_COLOR = 'black'
HATCH_COLOR = 'white'
# - figure parameters by default
# SCHEDULES_FIGURE_DPI_DEFAULT = 300
SCHEDULES_FIGURE_WIDTH = 640
SCHEDULES_FIGURE_HEIGHT = 524
# - figure parameters for UI
SCHEDULES_FIGURE_DPI_FOR_UI = 80


# Create schedules figure
def create_schedules_figure(solution: Solution, figure_id: str = None,
                            infeasibility=None, critical_bounds=None, for_UI: bool = False) -> Figure:

    # Create a new figure if needed
    if figure_id is None:
        figure = plt.figure()
    else:
        figure = plt.figure(figure_id)
    if for_UI:
        figure.dpi = SCHEDULES_FIGURE_DPI_FOR_UI
        plt.subplots_adjust(left=0.15, right=0.9, top=0.95, bottom=0.1)
    ax = figure.add_subplot()

    # Define axis
    ax.invert_yaxis()
    max_time_value = 0
    min_time_value = 24 * 60
    for employee in solution.instance.employees:
        sequence = solution.get_sequence(employee)
        max_time_value = max(max_time_value, sequence[-1].start_time)
        min_time_value = min(min_time_value, sequence[0].start_time)
    time_values_range_size = max_time_value - min_time_value
    max_time_value += np.ceil(time_values_range_size * 0.05)
    min_time_value -= np.ceil(time_values_range_size * 0.05)
    ax.set_xlim(min_time_value, max_time_value)
    ax.set_xlabel("Time")
    ax.set_xticks([h * 60 for h in range(7, 20)])
    ax.set_xticklabels([convert_nb_minutes_to_time_string(h * 60).replace(':00', '') for h in range(7, 20)])
    ax.set_ylabel("Employees")
    employees_names = solution.instance.employees_names
    ax.set_yticks(range(len(employees_names)))
    ax.set_yticklabels(employees_names)

    # Draw employees' schedules
    colors = dict(zip(solution.instance.employees_names, sns.color_palette("hls", solution.instance.nb_employees)))
    for employee_index, employee in enumerate(solution.instance.employees):

        sequence = solution.get_sequence(employee)
        bar_color = colors[employee.name]

        if len(sequence) > 2:

            # Draw tasks and unavailabilities
            for step in sequence[1:-1]:
                activity_name = step.activity.name
                bar_left_side = step.start_time
                bar_width = step.end_time - step.start_time
                bar_center_x = bar_left_side + bar_width / 2
                bar_center_y = employee_index
                bar_height = 0.4
                if infeasibility is not None and infeasibility['employee_name'] == employee.name and \
                        infeasibility['task_name'] == step.activity.name:
                    bar_center_y += -0.4 if employee_index > 0 else 0.4
                    bar_height /= 2
                task = solution.instance.get_hypothetical_activity_by_names(activity_name=activity_name,
                                                                            employee_name=employee.name)
                if isinstance(task, Unavailability):
                    ax.barh(y=bar_center_y, left=bar_left_side, width=bar_width,
                            height=bar_height, color=bar_color, edgecolor=HATCH_COLOR, hatch="//")
                else:
                    ax.barh(y=bar_center_y, left=bar_left_side, width=bar_width, height=bar_height, color=bar_color)
                ax.text(x=bar_center_x, y=bar_center_y, s=activity_name, ha='center', va='center', color=TXT_COLOR)
                if (critical_bounds is not None and employee.name in critical_bounds.keys() and
                        step.activity.name in critical_bounds[employee.name].keys()):
                    if critical_bounds[employee.name][step.activity.name] == 'LB':
                        ax.plot([bar_left_side, bar_left_side],
                                [bar_center_y - 3 * bar_height / 2, bar_center_y + 3 * bar_height / 2],
                                color=bar_color, linestyle='-')
                    elif critical_bounds[employee.name][step.activity.name] == 'UB':
                        ax.plot([bar_left_side + bar_width, bar_left_side + bar_width],
                                [bar_center_y - 3 * bar_height / 2, bar_center_y + 3 * bar_height / 2],
                                color=bar_color, linestyle='-')

            bar_height = 0.4
            if critical_bounds is not None and employee.name in critical_bounds.keys():
                if 'Start' in critical_bounds[employee.name].keys():
                    ax.plot([sequence[0].start_time, sequence[0].start_time],
                            [employee_index - 3 * bar_height / 2, employee_index + 3 * bar_height / 2],
                            color='darkgrey', linestyle='-')
                elif 'End' in critical_bounds[employee.name].keys():
                    ax.plot([sequence[0].end_time_UB, sequence[0].end_time_UB],
                            [employee_index - 3 * bar_height / 2, employee_index + 3 * bar_height / 2],
                            color='darkgrey', linestyle='-')

            # Draw displacements
            for step_index, step in enumerate(sequence[:-1]):
                bar_left_side = step.end_time
                bar_width = int(np.ceil(solution.compute_traveling_duration(step, sequence[step_index + 1])))
                bar_height = 0.2
                if bar_width > 0:
                    if solution.instance.has_lunch_break and \
                            solution.get_activity_before_employee_lunch(employee) == step.activity and \
                            solution.get_employee_lunch_break_start_time(employee) < bar_left_side + bar_width:
                        bar1_left_side = bar_left_side
                        bar1_width = solution.get_employee_lunch_break_start_time(employee) - bar_left_side
                        if bar1_width > 0:
                            bar1_center = bar1_left_side + bar1_width / 2
                            ax.barh(y=employee.name, left=bar1_left_side, width=bar1_width, height=bar_height,
                                    color='darkgrey')
                            ax.text(x=bar1_center, y=employee_index, s=str(bar1_width), ha='center', va='center',
                                    color=TXT_COLOR)
                        bar2_left_side = (solution.get_employee_lunch_break_start_time(employee) +
                                          solution.instance.lunch_break_duration)
                        bar2_width = bar_width - bar1_width
                        if bar2_width > 0:
                            bar2_center = bar2_left_side + bar2_width / 2
                            ax.barh(y=employee.name, left=bar2_left_side, width=bar2_width, height=bar_height,
                                    color='darkgrey')
                            ax.text(x=bar2_center, y=employee_index, s=str(bar2_width), ha='center', va='center',
                                    color=TXT_COLOR)
                    else:
                        bar_center_x = bar_left_side + bar_width / 2
                        bar_center_y = employee_index
                        if infeasibility is not None and infeasibility['employee_name'] == employee.name:
                            if infeasibility['task_name'] == step.activity.name:
                                bar_center_y += -0.4 if employee_index > 0 else 0.4
                                bar_height /= 2
                                ax.plot([bar_center_x + bar_width / 2, sequence[step_index + 1].start_time],
                                        [bar_center_y - bar_height / 2, employee_index], color='darkgrey',
                                        linestyle='--')
                            elif infeasibility['task_name'] == sequence[step_index + 1].activity.name:
                                bar_center_y += -0.4 if employee_index > 0 else 0.4
                                bar_left_side = sequence[step_index + 1].start_time - bar_width
                                bar_center_x = bar_left_side + bar_width / 2
                                bar_height /= 2
                                ax.plot([bar_center_x - bar_width / 2, step.end_time],
                                        [bar_center_y - bar_height / 2, employee_index], color='darkgrey',
                                        linestyle='--')
                        ax.barh(y=bar_center_y, left=bar_left_side, width=bar_width, height=bar_height,
                                color='darkgrey')
                        ax.text(x=bar_center_x, y=bar_center_y, s=str(bar_width), ha='center', va='center',
                                color=TXT_COLOR)

            # Draw lunch breaks
            if solution.instance.has_lunch_break:
                bar_left_side = solution.get_employee_lunch_break_start_time(employee)
                bar_width = solution.instance.lunch_break_duration
                bar_center_x = bar_left_side + bar_width / 2
                ax.barh(y=employee.name, left=bar_left_side, width=bar_width, height=bar_height, color=bar_color,
                        edgecolor=HATCH_COLOR, hatch="/")
                ax.text(x=bar_center_x, y=employee_index, s="LB", ha='center', va='center', color=TXT_COLOR)

    # Add title
    if not for_UI:
        plt.title("Schedules of " + solution.name)
        if matplotlib.get_backend() == 'Qt5Agg':
            plt.get_current_fig_manager().window.setGeometry(80 + ROUTES_FIGURE_WIDTH, 50,
                                                             SCHEDULES_FIGURE_WIDTH, SCHEDULES_FIGURE_HEIGHT)

    # Draw
    plt.draw()

    return figure
