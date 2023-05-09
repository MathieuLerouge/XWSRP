import numpy as np

from src.reading.solution import extract_solution_from_file
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.utils.constants import DEFAULT_INPUTS_DIRECTORY_RELATIVE_PATH
from src.utils.files import get_paths_of_solutions_files_in_given_directory
from src.utils.time import convert_nb_minutes_to_time_string

X_AXIS_LEFT = 1
X_AXIS_RIGHT = 8
Y_AXIS_BOTTOM = 1
Y_AXIS_TOP = 8

MIN_LONGITUDE = 14.25
MAX_LONGITUDE = 16.25
MIN_LATITUDE = 47
MAX_LATITUDE = 48.5
NB_STEPS_LONGITUDE = 8
NB_STEPS_LATITUDE = 6

MIN_HOUR = 7
MAX_HOUR = 12+7
MIN_MINUTES = MIN_HOUR*60
MAX_MINUTES = MAX_HOUR*60


def convert_longitude_to_x(longitude):
    return np.round(
        ((longitude - MIN_LONGITUDE)/(MAX_LONGITUDE - MIN_LONGITUDE))*(X_AXIS_RIGHT - X_AXIS_LEFT) + X_AXIS_LEFT,
        3
    )


def convert_latitude_to_y(latitude):
    return np.round(
        ((latitude - MIN_LATITUDE)/(MAX_LATITUDE - MIN_LATITUDE))*(Y_AXIS_TOP - Y_AXIS_BOTTOM) + Y_AXIS_BOTTOM,
        3
    )


def convert_minutes_to_x(nb_minutes):
    return np.round(
        ((nb_minutes - MIN_MINUTES) / (MAX_MINUTES - MIN_MINUTES)) * (Y_AXIS_TOP - Y_AXIS_BOTTOM) + Y_AXIS_BOTTOM,
        3
    )


def write_in_curly_brackets(x):
    return "{" + x + "}"


def main():

    try:
        solution_file_name = get_paths_of_solutions_files_in_given_directory()[0]
    except IndexError:
        raise FileNotFoundError(f"There are no solutions files found in directory {DEFAULT_INPUTS_DIRECTORY_RELATIVE_PATH}")
    solution = extract_solution_from_file(solution_file_name, True, True, True)

    print("%% Spatial %%")
    print()

    nb_steps_x = NB_STEPS_LONGITUDE
    nb_steps_y = NB_STEPS_LATITUDE

    x_axis_left = X_AXIS_LEFT
    x_axis_right = X_AXIS_RIGHT
    y_axis_bottom = Y_AXIS_BOTTOM
    y_axis_top = Y_AXIS_TOP

    width_x_axis = x_axis_right - x_axis_left
    step_x_axis = np.round(width_x_axis / nb_steps_x, 3)
    height_y_axis = y_axis_top - y_axis_bottom
    step_y_axis = np.round(height_y_axis / nb_steps_y, 3)

    node_string = "{longitude}"
    s = f"\draw[->, thick] ({np.round(x_axis_left - step_x_axis/2, 3)},  {y_axis_bottom}) -- " \
        f"({np.round(x_axis_right + step_x_axis/2, 3)}, {y_axis_bottom}) node[pos=.5, yshift=-2em] {node_string};"
    print(s)
    node_string = "{latitude}"
    s = f"\draw[->, thick] ({x_axis_left},  {np.round(y_axis_bottom - step_y_axis/2, 3)}) -- " \
        f"({x_axis_left}, {np.round(y_axis_top + step_y_axis/2, 3)}) node[pos=.5, xshift=-3.25em, rotate=90] {node_string};"
    print(s)
    print()

    print("% Employee's locations")
    node_positions = {
        "Ellen": "right",
        "Alexander": "left",
        "Adam": "above left",
        "Fabian": "left",
        "Carlotta": "above"
    }
    for i, employee in enumerate(solution.instance.employees):
        longitude = np.degrees(employee.location.coordinates[1])
        latitude = np.degrees(employee.location.coordinates[0])
        empty_node_string = "{}"
        node_string = "{\scriptsize $\employee_{" + str(i+1) + "}$}"
        s = f"\\node[rectangle, draw={employee.name}Color, fill={employee.name}Color, inner sep=0pt, minimum size=4pt] " \
            f"(D{i+1}) at ({convert_longitude_to_x(longitude)}, {convert_latitude_to_y(latitude)}) {empty_node_string} " \
            f"node[{node_positions[employee.name]}, color={employee.name}Color] at (D{i + 1}) {node_string};"
        print(s)
    print()

    print("% Tasks")
    node_positions = {
        "T1": "left",
        "T2": "below",
        "T3": "below",
        "T4": "above right",
        "T5": "below left",
        "T6": "left",
        "T7": "above",
        "T8": "right",
        "T9": "above right",
        "T10": "above left",
        "T13": "above right",
        "T14": "right",
        "T16": "below right",
        "T17": "above",
        "T19": "above left",
        "T20": "below right",
        "T21": "left",
        "T22": "above",
        "T24": "below right",
        "T25": "right",
        "T27": "left",
        "T29": "above",
        "T30": "right",
        "T31": "above"
    }
    for task in solution.instance.tasks:
        if task.name not in node_positions:
            node_positions[task.name] = "below"
    tasks_strings_per_employee = {employee_name: [] for employee_name in ["None"] + solution.instance.employees_names}
    for task in solution.instance.tasks:
        employee_name = "None"
        if solution.get_task_performance_status(task):
            employee_name = solution.get_task_assignee(task).name
        longitude = np.degrees(task.location.coordinates[1])
        latitude = np.degrees(task.location.coordinates[0])
        empty_node_string = "{}"
        node_string = "{\\scriptsize $\\task_{" + task.name[1:] + "}$}"
        s = f"\\node[circle, draw={employee_name}Color, fill={employee_name}Color, inner sep=0pt, minimum size=4pt] " \
            f"({task.name}) at ({convert_longitude_to_x(longitude)}, {convert_latitude_to_y(latitude)}) " \
            f"{empty_node_string} node[{node_positions[task.name]}, color={employee_name}Color] " \
            f"at ({task.name}) {node_string};"
        tasks_strings_per_employee[employee_name].append(s)
    for tasks_strings in tasks_strings_per_employee.values():
        for s in tasks_strings:
            print(s)
    print()

    print("% Paths")
    inner_arrows = {
        "Ellen": {"D1": 0.5, "T26": 0.5},
        "Alexander": {"D2": 0.75, "T25": 0.5},
        "Adam": {"D3": 0.25, "T11": 0.75},
        "Fabian": {"T13": 0.5, "T4": 0.5, "T22": 0.6},
        "Carlotta": {"D5": 0.5, "T23": 0.5},
    }
    for employee in solution.instance.employees:
        if employee.name not in inner_arrows:
            inner_arrows[employee.name] = {}
    for i, employee in enumerate(solution.instance.employees):
        sequence = solution.get_sequence(employee)
        initial_s = f"\\draw[thick, color={employee.name}Color] "
        s = initial_s[:]
        node_home_name = f"D{i+1}"
        node_inner_arrow = "{\innerArrow}"
        first_index = 0
        if node_home_name in inner_arrows[employee.name]:
            s += f"({node_home_name}) -- ({sequence[1].activity.name}) " \
                 f"node[sloped, pos={inner_arrows[employee.name][node_home_name]}, allow upside down] " \
                 f"{node_inner_arrow};"
            print(s)
            s = initial_s[:]
            first_index = 1
        for j, step in enumerate(sequence[first_index:]):
            if isinstance(step.activity, ComeBack):
                s += f"(D{i+1});"
                print(s)
            elif isinstance(step.activity, Departure):
                s += f"(D{i+1}) -- "
            elif step.activity.name in inner_arrows[employee.name]:
                s += f"({step.activity.name});"
                print(s)
                s = initial_s[:]
                if isinstance(sequence[first_index+j+1].activity, ComeBack):
                    s += f"({step.activity.name}) -- (D{i+1}) " \
                         f"node[sloped, pos={inner_arrows[employee.name][step.activity.name]}, allow upside down] " \
                         f"{node_inner_arrow};"
                    print(s)
                    break
                else:
                    s += f"({step.activity.name}) -- ({sequence[first_index + j + 1].activity.name}) " \
                         f"node[sloped, pos={inner_arrows[employee.name][step.activity.name]}, allow upside down] " \
                         f"{node_inner_arrow};"
                    print(s)
                    s = initial_s[:]
            else:
                s += f"({step.activity.name}) -- "

    print()
    print("%% Temporal %%")
    print()

    nb_steps_x = MAX_HOUR - MIN_HOUR
    nb_steps_y = 6

    x_axis_left = X_AXIS_LEFT
    x_axis_right = X_AXIS_RIGHT
    y_axis_bottom = Y_AXIS_BOTTOM
    y_axis_top = Y_AXIS_TOP

    width_x_axis = x_axis_right - x_axis_left
    step_x_axis = np.round(width_x_axis / nb_steps_x, 3)
    height_y_axis = y_axis_top - y_axis_bottom
    step_y_axis = np.round(height_y_axis/nb_steps_y, 3)

    y_axis_per_employee = {
        employee: y_axis_bottom + (solution.instance.nb_employees - i)*step_y_axis
        for i, employee in enumerate(solution.instance.employees)
    }

    print("% Horizontal lines")
    for i, employee in enumerate(solution.instance.employees):
        node_string = "{\\footnotesize \\$employee_{" + str(i+1) + "}$}"
        s = f"\\draw[very thin, gray] ({x_axis_left}, {y_axis_per_employee[employee]}) -- " \
            f"({x_axis_right}, {y_axis_per_employee[employee]}) " \
            f"node[left, {employee.name}Color] at ({x_axis_left}, {y_axis_per_employee[employee]}) " \
            f"{node_string};"
        print(s)
    s = f"\\draw[very thin, gray] ({x_axis_left}, {y_axis_bottom + nb_steps_y*step_y_axis}) -- " \
        f"({x_axis_right}, {y_axis_bottom + nb_steps_y*step_y_axis});"
    print(s)
    print()

    print("% Vertical lines")
    for j in range(MIN_HOUR, MAX_HOUR+1):
        s = f"\\draw[very thin, gray] ({convert_minutes_to_x(j * 60)}, {y_axis_bottom}) -- " \
            f"({convert_minutes_to_x(j * 60)}, {y_axis_top})"
        if j % 2 == 1:
            hour = convert_nb_minutes_to_time_string(j * 60).replace(":00", "")
            if hour[0] == '0':
                hour = hour[1:]
            node_string = "{\\footnotesize " + hour + "}"
            s += f" node[below, black] at ({convert_minutes_to_x(j*60)}, {y_axis_bottom}) {node_string};"
        else:
            s += ";"
        print(s)
    print()

    print("% Axis")
    node_string = "{hour}"
    print(f"\\draw[->, thick] ({np.round(x_axis_left - step_x_axis/2, 3)}, {y_axis_bottom}) -- "
          f"({np.round(x_axis_right + step_x_axis/2, 3)}, {y_axis_bottom}) node[pos=.5, yshift=-2em] {node_string};")
    print()

    print("% Schedules")
    for employee in solution.instance.employees:
        sequence = solution.get_sequence(employee)
        for j, step in enumerate(sequence[:-1]):
            next_step = sequence[j+1]
            s = f"\\node[draw, rectangle, color=gray, fill=gray!20, inner sep=0pt, " \
                "from={" \
                f"{convert_minutes_to_x(step.end_time)},{np.round(y_axis_per_employee[employee] - .1 * step_y_axis, 3)} " \
                f"to {convert_minutes_to_x(next_step.arrival_time)},{np.round(y_axis_per_employee[employee] + .1 * step_y_axis, 3)}" \
                "}] {};"
            print(s)
        for step in sequence[1:-1]:
            task = step.activity
            node_string = "{\\scriptsize $\\task_{" + task.name[1:] + "}$}"
            s = f"\\node[draw, rectangle, color={employee.name}Color, fill={employee.name}Color!20, inner sep=0pt, " \
                "from={" \
                f"{convert_minutes_to_x(step.start_time)},{np.round(y_axis_per_employee[employee] - .25*step_y_axis, 3)} " \
                f"to {convert_minutes_to_x(step.end_time)},{np.round(y_axis_per_employee[employee] + .25*step_y_axis, 3)}" \
                "}] " \
                f"{node_string};"
            print(s)
    print()


if __name__ == '__main__':
    main()
