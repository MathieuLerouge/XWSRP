# Third-party libraries
from dash import dcc
import numpy as np
import plotly.express as px
import plotly.graph_objs as go

# Local libraries
from src.explaining.interacting.interface.assets.styles import UI_FONT_COLOR, UI_PANEL_CONTENT_COLOR, UI_LINE_COLOR, \
    UI_CONFLICT_TASK_COLOR, UI_CONFLICT_BOUND_COLOR
from src.explaining.transforming.infeasibility import Infeasibility, TimeInfeasibility
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.modeling.task import Task
from src.utils.language import LANGUAGE_ENGLISH_KEY, check_if_language_is_english, check_if_language_is_french
from src.utils.time import convert_nb_minutes_to_time_string, get_hour_format_associated_with_language


# Global variables
OPACITY_DEGREE = .4


def compute_employees_colors(instance: Instance):
    """
    Compute a list of color values that can then be associated respectively to the employees.
    """
    # See https://plotly.com/python/builtin-colorscales/ for various color scales
    # Interesting color scales: agsunset from 0 to .8; turbo from .1 to .9; sunsetdark from 0 to 1;
    # rainbow from 0 to .9; viridis from 0 to .9;
    nb_employees = instance.nb_employees
    return px.colors.sample_colorscale('agsunset', [n/(nb_employees - 1)*(.8 - 0) + 0 for n in range(nb_employees)])


def build_map_figure(instance: Instance, solution: Solution = None, infeasibility: Infeasibility = None,
                     mode: str = 'all', language: str = LANGUAGE_ENGLISH_KEY):
    """
    Build a typical map figure that be used for displaying the locations of the employees, the ones of the task
    or the routes of the employees.
    """

    hour_format = get_hour_format_associated_with_language(language)

    def _create_task_description_in_routes_figure(task_to_describe: Task, is_performed: bool = None):
        if is_performed is None:
            if check_if_language_is_english(language):
                return (f"<b>{task_to_describe.name}</b><br>"
                        f"Skill level: {task_to_describe.skill_level}<br>"
                        f"Duration: {task_to_describe.get_duration(as_integer=False)}<br>"
                        f"Availability: {task_to_describe.TWs.as_string(hour_format)}<br>")
            elif check_if_language_is_french(language):
                return (f"<b>{task_to_describe.name}</b><br>"
                        f"Niveau : {task_to_describe.skill_level}<br>"
                        f"Durée : {task_to_describe.get_duration(as_integer=False)}<br>"
                        f"Disponibilité : {task_to_describe.TWs.as_string(hour_format)}<br>")
            else:
                raise ValueError(f"Unknown language: {language}")
        elif is_performed:
            if check_if_language_is_english(language):
                return (f"<b>Performing {task_to_describe.name}</b> <br>"
                        f"Task skill level: {task_to_describe.skill_level}<br>"
                        f"Task duration: {task_to_describe.get_duration(as_integer=False)}<br>"
                        f"Availability: {task_to_describe.TWs.as_string(hour_format)}")
            elif check_if_language_is_french(language):
                return (f"<b>Réalisation de {task_to_describe.name}</b> <br>"
                        f"Niveau de la tâche : {task_to_describe.skill_level}<br>"
                        f"Durée de la tâche : {task_to_describe.get_duration(as_integer=False)}<br>"
                        f"Disponibilité : {task_to_describe.TWs.as_string(hour_format)}")
            else:
                raise ValueError(f"Unknown language: {language}")
        else:
            if check_if_language_is_english(language):
                return (f"<b>{task_to_describe.name} not performed</b><br>"
                        f"Skill level: {task_to_describe.skill_level}<br>"
                        f"Duration: {task_to_describe.get_duration(as_integer=False)}<br>"
                        f"Availability: {task_to_describe.TWs.as_string(hour_format)}")
            elif check_if_language_is_french(language):
                return (f"<b>{task_to_describe.name} non-réalisée</b><br>"
                        f"Niveau : {task_to_describe.skill_level}<br>"
                        f"Durée : {task_to_describe.get_duration(as_integer=False)}<br>"
                        f"Disponibilité : {task_to_describe.TWs.as_string(hour_format)}")
            else:
                raise ValueError(f"Unknown language: {language}")

    def _compute_map_zoom_and_center(locations_longitudes: list[float], locations_latitudes: list[float],
                                     projection: str = 'mercator', width_to_height: float = 2.0):
        """
        Compute proper zoom and center for a plotly mapbox.

        :param locations_longitudes: list of longitudes in degrees of the locations
        :param locations_latitudes: list of latitudes in degrees of the locations
        :param projection: str, only accepting 'mercator' at the moment,
            raises `NotImplementedError` if other is passed
        :param width_to_height: float, expected ratio of final graph's with to height,
            used to select the constrained axis.

        :return:
        zoom: float, from 1 to 20
        center: dict, gps position with 'lon' and 'lat' keys
        """
        longitudes_max, longitudes_min = max(locations_longitudes), min(locations_longitudes)
        latitudes_max, latitudes_min = max(locations_latitudes), min(locations_latitudes)
        locations_center = {'lon': round((longitudes_max + longitudes_min) / 2, 6),
                            'lat': round((latitudes_max + latitudes_min) / 2, 6)}
        longitude_zoom_range = np.array([
            0.0007, 0.0014, 0.003, 0.006, 0.012, 0.024, 0.048, 0.096, 0.192, 0.3712, 0.768, 1.536,
            3.072, 6.144, 11.8784, 23.7568, 47.5136, 98.304, 190.0544, 360.0
        ])
        if projection == 'mercator':
            margin = 3  # 1.2
            height = (latitudes_max - latitudes_min) * margin * width_to_height
            width = (longitudes_max - longitudes_min) * margin
            longitude_zoom = np.interp(width, longitude_zoom_range, range(20, 0, -1))
            latitude_zoom = np.interp(height, longitude_zoom_range, range(20, 0, -1))
            map_zoom = round(min(longitude_zoom, latitude_zoom), 2)
        else:
            raise NotImplementedError(f"{projection} projection is not implemented")
        return map_zoom, locations_center

    if solution is not None:
        instance = solution.instance

    latitudes, longitudes = [], []
    for task in instance.tasks:
        latitudes.append(task.location.get_latitude(radians=False))
        longitudes.append(task.location.get_longitude(radians=False))
    zoom, center = _compute_map_zoom_and_center(longitudes, latitudes)

    colors = compute_employees_colors(instance)
    fig = px.scatter_mapbox(lat=[], lon=[], hover_name=[], zoom=zoom, center=center)

    # Case where the map figure is supposed to display information about the instance
    if solution is None:

        show_tasks = (mode == 'all') or ('tasks' in mode)
        show_employees = (mode == 'all') or ('employees' in mode)

        # Case where the map figure is supposed to display tasks locations
        if show_tasks:
            texts, latitudes, latitudes, descriptions = [], [], [], []
            for task in instance.tasks:
                texts.append(f"{task.name}<br><br> ")
                latitudes.append(task.location.get_latitude(radians=False))
                longitudes.append(task.location.get_longitude(radians=False))
                descriptions.append(_create_task_description_in_routes_figure(task))
            fig.add_trace(go.Scattermapbox(
                mode="markers+text", marker=dict(color=colors[0], size=9),
                lat=latitudes, lon=longitudes, hoverinfo='text', hovertext=descriptions, text=texts,
                showlegend=False
            ))

        # Case where the map figure is supposed to display employees locations
        if show_employees:
            for i, employee in enumerate(instance.employees):
                latitude = employee.location.get_latitude(radians=False)
                longitude = employee.location.get_longitude(radians=False)
                if check_if_language_is_english(language):
                    label = f"{employee.name}'s home<br><br> "
                    description = f"<b>{employee.name}</b> <br>" \
                                  f"Skill level: {employee.skill_level} <br>" \
                                  f"WH: {employee.TW.as_string(hour_format)}"
                elif check_if_language_is_french(language):
                    label = f"Domicile de {employee.name}<br><br> "
                    description = f"<b>{employee.name}</b> <br>" \
                                  f"Niveau : {employee.skill_level} <br>" \
                                  f"Horaires de l'employé : <br>{employee.TW.as_string(hour_format)}"
                else:
                    raise ValueError(f"Unknown language: {language}")
                # NB: Scattermapbox can not handle marker symbol other than circles
                fig.add_trace(go.Scattermapbox(
                    mode='markers+text', marker=dict(color=colors[i], size=12),
                    lat=[latitude], lon=[longitude],
                    hoverinfo='text', hovertext=[description], text=[label],
                    showlegend=False
                ))

    # Case where the map figure is supposed to display information about the solution
    else:
        if mode != 'all':
            raise NotImplementedError(f"The mode {mode} is not handled")
        non_performed_tasks_names, non_performed_tasks_latitudes, non_performed_tasks_longitudes, \
            non_performed_tasks_descriptions = [], [], [], []
        for task in instance.tasks:
            if not (solution.get_task_performance_status(task)):
                non_performed_tasks_names.append(task.name)
                non_performed_tasks_latitudes.append(task.location.get_latitude(radians=False))
                non_performed_tasks_longitudes.append(task.location.get_longitude(radians=False))
                non_performed_tasks_descriptions.append(
                    _create_task_description_in_routes_figure(task, is_performed=False)
                )
        fig.add_trace(go.Scattermapbox(
            name="None", mode='markers+text', marker=dict(color='grey', size=9),
            opacity=(1 if infeasibility is None else OPACITY_DEGREE),
            lat=non_performed_tasks_latitudes, lon=non_performed_tasks_longitudes,
            hoverinfo='text+name', hovertext=non_performed_tasks_descriptions,
            text=[name + "<br><br> " for name in non_performed_tasks_names],
            showlegend=False
        ))
        for i, employee in enumerate(solution.instance.employees):
            sequence = solution.get_sequence(employee)
            route_steps_latitudes = [employee.location.get_latitude(radians=False)]
            route_steps_longitudes = [employee.location.get_longitude(radians=False)]
            route_steps_descriptions = [""]
            route_steps_names = [""]
            route_steps_marker_sizes = [12]
            for step in sequence[1:-1]:
                activity = step.activity
                route_steps_latitudes.append(activity.location.get_latitude(radians=False))
                route_steps_longitudes.append(activity.location.get_longitude(radians=False))
                route_steps_descriptions.append(
                    _create_task_description_in_routes_figure(activity, is_performed=True)
                )
                route_steps_names.append(activity.name)
                route_steps_marker_sizes.append(9)
            route_steps_latitudes.append(employee.location.get_latitude(radians=False))
            route_steps_longitudes.append(employee.location.get_longitude(radians=False))
            if check_if_language_is_english(language):
                route_steps_descriptions.append(f"<b>{employee.name}'s home</b> <br>"
                                                f"Employee skill level: {employee.skill_level}")
                route_steps_names.append("Home")
            elif check_if_language_is_french(language):
                route_steps_descriptions.append(f"<b>Domicile de l'employé</b> <br>"
                                                f"Niveau de l'employé : {employee.skill_level}")
                route_steps_names.append("Domicile")
            else:
                raise ValueError(f"Unknown language: {language}")
            route_steps_marker_sizes.append(12)
            if infeasibility is None:
                fig.add_trace(go.Scattermapbox(
                    name=employee.name, mode='markers+lines+text',
                    marker=dict(color=colors[i], size=route_steps_marker_sizes),
                    lat=route_steps_latitudes, lon=route_steps_longitudes,
                    hoverinfo='text+name', hovertext=route_steps_descriptions,
                    text=[name + "<br><br> " for name in route_steps_names]
                ))
            else:
                if employee.name == infeasibility.conflicting_employee.name:
                    fig.add_trace(go.Scattermapbox(
                        name=employee.name, mode='markers+lines+text',
                        line=dict(width=2),
                        marker=dict(color=colors[i], size=route_steps_marker_sizes),
                        lat=route_steps_latitudes, lon=route_steps_longitudes,
                        hoverinfo='text+name', hovertext=route_steps_descriptions,
                        text=[name + "<br><br> " for name in route_steps_names]
                    ))
                else:
                    fig.add_trace(go.Scattermapbox(
                        name=employee.name, mode='markers+lines+text', opacity=OPACITY_DEGREE,
                        marker=dict(color=colors[i], size=route_steps_marker_sizes),
                        lat=route_steps_latitudes, lon=route_steps_longitudes,
                        hoverinfo='text+name', hovertext=route_steps_descriptions,
                        text=[name + "<br><br> " for name in route_steps_names]
                    ))

    fig.update_layout(
        mapbox_style="mapbox://styles/mathieu-lerouge/cl2nlkbiz002v14rvw77fv32q",
        mapbox_accesstoken='pk.eyJ1IjoibWF0aGlldS1sZXJvdWdlIiwiYSI6ImNsMm5sajY4bDIxZGIzaXA5MDNscjFoa2UifQ'
                           '.SHh5_g--Pv6LEy6P3mk7eQ',
        # Another possible map box style is the open street map one, which does not require any access token.
        # However, with this style, names do not show up, then it should be used only if the token is an issue.
        # mapbox_style="open-street-map"
        margin={"r": 10, "t": 0, "l": 10, "b": 10},
        legend=dict(traceorder='normal', orientation='h', xanchor='center', x=0.5, y=1.15,
                    font=dict(family='Arial', size=14, color=UI_FONT_COLOR)),
        paper_bgcolor=UI_PANEL_CONTENT_COLOR
    )
    return fig


def build_routes_figure(solution: Solution, infeasibility: Infeasibility = None, language: str = LANGUAGE_ENGLISH_KEY):
    """
    Build a map figure of the employees' routes.
    """
    return build_map_figure(solution.instance, solution=solution, infeasibility=infeasibility, language=language)


def create_home_description_in_schedules_figure(activity: Activity, time_as_string: str,
                                                language: str = LANGUAGE_ENGLISH_KEY):
    hour_format = get_hour_format_associated_with_language(language)
    if check_if_language_is_english(language):
        if isinstance(activity, Departure):
            text_first_line = "Leaving home"
        elif isinstance(activity, ComeBack):
            text_first_line = "Returning home"
        else:
            raise TypeError(f"The activity {activity} must either a Departure or a ComeBack")
        return (f"<b>{text_first_line}</b><br>"
                f"Time: <b>{time_as_string}</b><br>"
                f"Employee working hours: {activity.employee.TW.as_string(hour_format)}<br>")
    elif check_if_language_is_french(language):
        if isinstance(activity, Departure):
            text_first_line = "Départ domicile"
        elif isinstance(activity, ComeBack):
            text_first_line = "Retour domicile"
        else:
            raise TypeError(f"The activity {activity} must either a Departure or a ComeBack")
        return (f"<b>{text_first_line}</b><br>"
                f"Heure : <b>{time_as_string}</b><br>"
                f"Horaires de l'employé : <br>{activity.employee.TW.as_string(hour_format)}<br>")
    else:
        raise ValueError(f"Unknown language: {language}")


def create_task_description_in_schedules_figure(task: Task, start_time_as_string: str, end_time_as_string: str,
                                                language: str = LANGUAGE_ENGLISH_KEY):
    hour_format = get_hour_format_associated_with_language(language)
    if check_if_language_is_english(language):
        return (f"<b>Performing {task.name}</b><br>"
                f"Start time: <b>{start_time_as_string}</b><br>"
                f"End time: <b>{end_time_as_string}</b><br>"
                f"Duration: {task.get_duration(as_integer=False)}<br>"
                f"Task availability: {task.TWs.as_string(hour_format)}<br>")
    elif check_if_language_is_french(language):
        return (f"<b>Réalisation de {task.name}</b><br>"
                f"Heure de début : <b>{start_time_as_string}</b><br>"
                f"Heure de fin : <b>{end_time_as_string}</b><br>"
                f"Durée : {task.get_duration(as_integer=False)}<br>"
                f"Disponibilité de la tâche : <br>{task.TWs.as_string(hour_format)}<br>")
    else:
        raise ValueError(f"Unknown language: {language}")


def build_schedules_figure(solution: Solution, infeasibility: Infeasibility = None,
                           language: str = LANGUAGE_ENGLISH_KEY):
    """
    Build a gantt chart of the employees' schedules.
    """
    instance = solution.instance
    colors = compute_employees_colors(instance)
    hour_format = get_hour_format_associated_with_language(language)
    fig = go.Figure(layout=dict(barmode='stack'))
    for i, employee in enumerate(instance.employees):
        sequence = solution.get_sequence(employee)
        # Departure
        start_step = sequence[0]
        fig.add_trace(go.Bar(
            orientation='h', width=.3, marker=dict(color=colors[i]),
            opacity=(OPACITY_DEGREE if infeasibility is not None else 1),
            base=[start_step.start_time - 5], x=[5], y=[employee.name],
            name=employee.name, hoverinfo='text+name',
            hovertext=[create_home_description_in_schedules_figure(
                start_step.activity, start_step. get_start_time(True, hour_format), language)],
            showlegend=False
        ))
        if infeasibility is not None and isinstance(infeasibility, TimeInfeasibility) and \
                infeasibility.conflicting_employee.name == employee.name:
            conflicting_task = infeasibility.conflicting_task
            conflict_index = sequence.get_step_index_of(conflicting_task)
            assert (conflict_index != 0)
            employee_name_bis = employee.name + "2"
            # Steps before conflict (excluding conflict) - Traveling phases
            for step_index, step in enumerate(sequence[:conflict_index]):
                traveling_duration = \
                    int(np.ceil(solution.compute_traveling_duration(step, sequence[step_index + 1])))
                if check_if_language_is_english(language):
                    traveling_text = \
                        f"<b>{traveling_duration}min</b> for traveling <br>" \
                        f"<b>from {step.activity.name} to {sequence[step_index + 1].activity.name}</b>"
                elif check_if_language_is_french(language):
                    step_activity_name = step.activity.name
                    if step_activity_name == "Start":
                        step_activity_name = "Départ"
                    next_step_activity_name = sequence[step_index + 1].activity.name
                    if next_step_activity_name == "Return":
                        next_step_activity_name = "Retour"
                    traveling_text = \
                        f"<b>{traveling_duration}min</b> pour se déplacer <br>" \
                        f"<b>de {step_activity_name} à {next_step_activity_name}</b>"
                else:
                    raise ValueError(f"Unknown language: {language}")
                fig.add_trace(go.Bar(
                    orientation='h', width=.3, marker=dict(color='lightgrey'),
                    base=[step.end_time], x=[traveling_duration], y=[employee.name], name=employee.name,
                    hoverinfo='text', hovertext=traveling_text, showlegend=False
                ))
            # Steps before conflict (excluding conflict) - Steps
            steps_names, steps_hover_texts, steps_start_times, steps_durations = [], [], [], []
            for step in sequence[1:conflict_index]:
                activity = step.activity
                steps_names.append(activity.name)
                steps_hover_texts.append(create_task_description_in_schedules_figure(
                    activity, step.get_start_time(True, hour_format), step.get_end_time(True, hour_format), language
                ))
                steps_start_times.append(step.start_time)
                steps_durations.append(step.activity.duration)
            fig.add_trace(go.Bar(
                orientation='h', width=.8, marker=dict(color=colors[i]),
                base=steps_start_times, x=steps_durations, y=[employee.name for _ in steps_start_times],
                name=employee.name, hoverinfo='text+name', hovertext=steps_hover_texts,
                text=steps_names, insidetextanchor='middle'
            ))
            # Step of conflict - Satisfying upstream constraints
            conflict_step = sequence[conflict_index]
            before_conflict_step = sequence[conflict_index - 1]
            traveling_duration = \
                int(np.ceil(solution.compute_traveling_duration(before_conflict_step, conflict_step)))
            conflict_activity = conflict_step.activity
            conflict_step_earliest_start_time = max(before_conflict_step.end_time + traveling_duration,
                                                    conflict_activity.start_time_LB)
            conflict_step_earliest_end_time = conflict_step_earliest_start_time + conflict_activity.duration
            conflict_step_earliest_start_time_as_string = convert_nb_minutes_to_time_string(
                conflict_step_earliest_start_time, get_hour_format_associated_with_language(language)
            )
            conflict_step_earliest_end_time_as_string = convert_nb_minutes_to_time_string(
                conflict_step_earliest_end_time, get_hour_format_associated_with_language(language)
            )
            step_hover_text = create_task_description_in_schedules_figure(
                conflict_activity, conflict_step_earliest_start_time_as_string,
                conflict_step_earliest_end_time_as_string, language
            )
            fig.add_trace(go.Bar(
                orientation='h', width=.8, marker=dict(color=UI_CONFLICT_TASK_COLOR),
                base=[conflict_step_earliest_start_time], x=[conflict_activity.duration], y=[employee.name],
                name=employee.name, hoverinfo='text+name', hovertext=[step_hover_text],
                text=[conflict_activity.name], insidetextanchor='middle',
                showlegend=False
            ))
            # Step of conflict - Satisfying downstream constraints
            after_conflict_step = sequence[conflict_index + 1]
            traveling_duration = \
                int(np.ceil(solution.compute_traveling_duration(conflict_step, after_conflict_step)))
            conflict_step_latest_end_time = min(after_conflict_step.start_time - traveling_duration,
                                                conflict_activity.end_time_UB)
            conflict_step_latest_start_time = conflict_step_latest_end_time - conflict_activity.duration
            conflict_step_latest_start_time_as_string = convert_nb_minutes_to_time_string(
                conflict_step_latest_start_time, get_hour_format_associated_with_language(language)
            )
            conflict_step_latest_end_time_as_string = convert_nb_minutes_to_time_string(
                conflict_step_latest_end_time, get_hour_format_associated_with_language(language)
            )
            step_hover_text = create_task_description_in_schedules_figure(
                conflict_activity, conflict_step_latest_start_time_as_string,
                conflict_step_latest_end_time_as_string, language
            )
            fig.add_trace(go.Bar(
                orientation='h', width=.8, marker=dict(color=UI_CONFLICT_TASK_COLOR),
                base=[conflict_step_latest_start_time], x=[conflict_activity.duration], y=[employee_name_bis],
                name=employee.name, hoverinfo='text+name', hovertext=[step_hover_text],
                text=[f"{conflict_activity.name}\'"], insidetextanchor='middle',
                showlegend=False
            ))
            # Step of conflict - Traveling phase
            if check_if_language_is_english(language):
                traveling_text = \
                    f"<b>{traveling_duration}min</b> for traveling <br>" \
                    f"<b>from {conflict_activity.name} to {after_conflict_step.activity.name}</b>"
            elif check_if_language_is_french(language):
                traveling_text = \
                    f"<b>{traveling_duration}min</b> pour se déplacer <br>" \
                    f"<b>de {conflict_activity.name} à {after_conflict_step.activity.name}</b>"
            else:
                raise ValueError(f"Unknown language: {language}")
            fig.add_trace(go.Bar(
                orientation='h', width=.3, marker=dict(color='lightgrey'),
                base=[conflict_step_latest_end_time], x=[traveling_duration], y=[employee_name_bis],
                name=employee.name, hoverinfo='text', hovertext=traveling_text, showlegend=False
            ))
            # Steps after conflict (excluding conflict) - Traveling phases
            for step_index, step in enumerate(sequence[conflict_index + 1:-1]):
                step_index += conflict_index + 1
                traveling_duration = \
                    int(np.ceil(solution.compute_traveling_duration(step, sequence[step_index + 1])))
                if check_if_language_is_english(language):
                    traveling_text = \
                        f"<b>{traveling_duration}min</b> for traveling <br>" \
                        f"<b>from {step.activity.name} to {sequence[step_index + 1].activity.name}</b>"
                elif check_if_language_is_french(language):
                    traveling_text = \
                        f"<b>{traveling_duration}min</b> pour se déplacer <br>" \
                        f"<b>de {step.activity.name} à {sequence[step_index + 1].activity.name}</b>"
                else:
                    raise ValueError(f"Unknown language: {language}")
                fig.add_trace(go.Bar(
                    orientation='h', width=.3, marker=dict(color='lightgrey'),
                    base=[step.end_time], x=[traveling_duration], y=[employee_name_bis], name=employee.name,
                    hoverinfo='text', hovertext=traveling_text, showlegend=False
                ))
            # Steps after conflict (excluding conflict) - Steps
            steps_names, steps_hover_texts, steps_start_times, steps_durations = [], [], [], []
            for step in sequence[conflict_index + 1:-1]:
                activity = step.activity
                steps_names.append(activity.name)
                steps_hover_texts.append(create_task_description_in_schedules_figure(
                    activity, step.get_start_time(True, hour_format), step.get_end_time(True, hour_format), language
                ))
                steps_start_times.append(step.start_time)
                steps_durations.append(step.activity.duration)
            fig.add_trace(go.Bar(
                orientation='h', width=.8, marker=dict(color=colors[i]),
                base=steps_start_times, x=steps_durations, y=[employee_name_bis for _ in steps_start_times],
                name=employee.name, hoverinfo='text+name', hovertext=steps_hover_texts,
                text=steps_names, insidetextanchor='middle', showlegend=False
            ))
            # Return
            return_step = sequence[-1]
            fig.add_trace(go.Bar(
                orientation='h', width=.3, marker=dict(color=colors[i]),
                base=[return_step.start_time], x=[5], y=[employee_name_bis],
                name=employee.name, hoverinfo='text+name',
                hovertext=[create_home_description_in_schedules_figure(
                    return_step.activity, return_step.get_start_time(True, hour_format), language)],
                showlegend=False
            ))
            # Critical bounds
            upstream_critical_step_index = infeasibility.upstream_critical_step_index
            upstream_critical_bound_y_suffix = ""
            downstream_critical_step_index = infeasibility.downstream_critical_step_index
            downstream_critical_bound_y_suffix = "2"
            if infeasibility.solution_is_upstream_feasible:
                if not infeasibility.solution_is_downstream_feasible:
                    if conflict_step_earliest_start_time == conflicting_task.start_time_LB:
                        upstream_critical_step_index = conflict_index
            else:
                if infeasibility.solution_is_downstream_feasible:
                    if conflict_step_latest_end_time == conflicting_task.end_time_UB:
                        downstream_critical_step_index = conflict_index
            upstream_critical_step = sequence[upstream_critical_step_index]
            upstream_critical_bound = upstream_critical_step.activity.start_time_LB
            downstream_critical_step = sequence[downstream_critical_step_index]
            downstream_critical_bound = downstream_critical_step.activity.end_time_UB
            if check_if_language_is_english(language):
                lower_bound_text = f"Yielding <b>lower bound</b><br>" \
                                   f"of <b>{upstream_critical_step.activity.name}</b> availability<br>time window"
                upper_bound_text = f"Yielding <b>upper bound</b><br>" \
                                   f"of <b>{downstream_critical_step.activity.name}</b> availability<br>time window"
            elif check_if_language_is_french(language):
                lower_bound_text = f"<b>Borne inférieure</b> de la fenêtre <br>" \
                                   f"de disponibilité de <b>{upstream_critical_step.activity.name}</b> atteinte"
                upper_bound_text = f"<b>Borne supérieure</b> de la fenêtre <br>" \
                                   f"de disponibilité de <b>{downstream_critical_step.activity.name}</b> atteinte"
            else:
                raise ValueError(f"Unknown language: {language}")
            fig.add_trace(go.Bar(
                orientation='h', width=1, marker=dict(color=UI_CONFLICT_BOUND_COLOR),
                base=[upstream_critical_bound - 3], x=[3], y=[employee.name + upstream_critical_bound_y_suffix],
                name=employee.name, hoverinfo='text+name', hovertext=[lower_bound_text], showlegend=False
            ))
            fig.add_trace(go.Bar(
                orientation='h', width=1, marker=dict(color=UI_CONFLICT_BOUND_COLOR),
                base=[downstream_critical_bound], x=[3], y=[employee.name + downstream_critical_bound_y_suffix],
                name=employee.name, hoverinfo='text+name', hovertext=[upper_bound_text], showlegend=False
            ))
        else:
            for step_index, step in enumerate(sequence[:-1]):
                traveling_duration = \
                    int(np.ceil(solution.compute_traveling_duration(step, sequence[step_index + 1])))
                if check_if_language_is_english(language):
                    traveling_text = \
                        f"<b>{traveling_duration}min</b> for traveling <br>" \
                        f"<b>from {step.activity.name} to {sequence[step_index + 1].activity.name}</b>"
                elif check_if_language_is_french(language):
                    step_activity_name = step.activity.name
                    if step_activity_name == "Start":
                        step_activity_name = "Départ"
                    next_step_activity_name = sequence[step_index + 1].activity.name
                    if next_step_activity_name == "Return":
                        next_step_activity_name = "Retour"
                    traveling_text = \
                        f"<b>{traveling_duration}min</b> pour se déplacer <br>" \
                        f"<b>de {step_activity_name} à {next_step_activity_name}</b>"
                else:
                    raise ValueError(f"Unknown language: {language}")
                fig.add_trace(go.Bar(
                    orientation='h', width=.3, marker=dict(color='lightgrey'),
                    opacity=(OPACITY_DEGREE if infeasibility is not None else 1),
                    base=[step.end_time], x=[traveling_duration], y=[employee.name], name=employee.name,
                    hoverinfo='text', hovertext=traveling_text, showlegend=False
                ))
            steps_names, steps_hover_texts, steps_start_times, steps_durations = [], [], [], []
            for step in sequence[1:-1]:
                activity = step.activity
                steps_names.append(activity.name)
                steps_hover_texts.append(create_task_description_in_schedules_figure(
                    activity, step.get_start_time(True, hour_format), step.get_end_time(True, hour_format), language
                ))
                steps_start_times.append(step.start_time)
                steps_durations.append(step.activity.duration)
            fig.add_trace(go.Bar(
                orientation='h', width=.8, marker=dict(color=colors[i]),
                opacity=(OPACITY_DEGREE if infeasibility is not None else 1),
                base=steps_start_times, x=steps_durations,
                y=[employee.name for _ in steps_start_times],
                name=employee.name, hoverinfo='text+name', hovertext=steps_hover_texts,
                text=steps_names, insidetextanchor='middle'
            ))
            return_step = sequence[-1]
            fig.add_trace(go.Bar(
                orientation='h', width=.3, marker=dict(color=colors[i]),
                opacity=(OPACITY_DEGREE if infeasibility is not None else 1),
                base=[return_step.start_time], x=[5], y=[employee.name],
                name=employee.name, hoverinfo='text+name',
                hovertext=[create_home_description_in_schedules_figure(
                    return_step.activity, return_step.get_start_time(True, hour_format), language)],
                showlegend=False
            ))
    hour_format = get_hour_format_associated_with_language(language)
    fig.update_layout(
        margin={"t": 0, "r": 10, "b": 20, "l": 10},
        xaxis=dict(automargin=True, tickmode='array', tickvals=[h * 60 for h in range(4, 22)],
                   ticktext=[convert_nb_minutes_to_time_string(h * 60, hour_format).replace(':00', '')
                             for h in range(4, 22)]),
        yaxis=dict(automargin=True, autorange='reversed', visible=False),
        legend=dict(orientation='h', xanchor='center', x=0.5, y=1.15,
                    font=dict(family='Arial', size=14, color=UI_FONT_COLOR), traceorder='normal'),
        paper_bgcolor=UI_PANEL_CONTENT_COLOR, plot_bgcolor='#637485', font=dict(color=UI_FONT_COLOR)
    )
    return fig


def build_instance_metrics_figures(instance: Instance, reference_instance: Instance = None,
                                   horizontal: bool = True, language: str = LANGUAGE_ENGLISH_KEY):
    """
    Build a figure with metrics about the instance.
    """
    comparison_to_reference = False if (reference_instance is None) else True
    reference_instance = instance if (reference_instance is None) else reference_instance
    if check_if_language_is_english(language):
        nb_employee_indicator_title = "# Employees"
        working_time_indicator_title = "Total employees<br>working time"
        nb_tasks_indicator_title = "# Tasks"
        tasks_duration_indicator_title = "Total tasks<br>duration"
    elif check_if_language_is_french(language):
        nb_employee_indicator_title = "# Employés"
        working_time_indicator_title = "Durée totale de travail<br> des employés disponible"
        nb_tasks_indicator_title = "# Tâches"
        tasks_duration_indicator_title = "Durée totale<br>des tâches"
    else:
        raise ValueError(f"Unknown language: {language}")
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        title=dict(text=nb_employee_indicator_title, font=dict(color=UI_FONT_COLOR)),
        mode=f"number{'+delta' if comparison_to_reference else ''}",
        number=dict(font=dict(color=UI_FONT_COLOR)),
        value=instance.nb_employees, delta=dict(reference=reference_instance.nb_employees),
        domain={'row': 0, 'column': 0}))
    fig.add_trace(go.Indicator(
        title=dict(text=working_time_indicator_title, font=dict(color=UI_FONT_COLOR)),
        mode=f"number{'+delta' if comparison_to_reference else ''}",
        number=dict(font=dict(color=UI_FONT_COLOR), suffix='min'),
        value=instance.total_employees_availability_duration,
        delta=dict(reference=reference_instance.total_employees_availability_duration),
        domain={'row': 0 if horizontal else 1, 'column': 2 if horizontal else 0}))
    fig.add_trace(go.Indicator(
        title=dict(text=nb_tasks_indicator_title, font=dict(color=UI_FONT_COLOR)),
        mode=f"number{'+delta' if comparison_to_reference else ''}",
        number=dict(font=dict(color=UI_FONT_COLOR)),
        value=instance.nb_tasks, delta=dict(reference=reference_instance.nb_tasks),
        domain={'row': 0, 'column': 1}))
    fig.add_trace(go.Indicator(
        title=dict(text=tasks_duration_indicator_title, font=dict(color=UI_FONT_COLOR)),
        mode=f"number{'+delta' if comparison_to_reference else ''}",
        number=dict(font=dict(color=UI_FONT_COLOR), suffix='min'),
        value=instance.total_tasks_duration, delta=dict(reference=reference_instance.total_tasks_duration),
        domain={'row': 0 if horizontal else 1, 'column': 3 if horizontal else 1}))
    fig.update_layout(
        grid={'rows': 1 if horizontal else 2, 'columns': 4 if horizontal else 2, 'pattern': 'independent'},
        paper_bgcolor=UI_PANEL_CONTENT_COLOR, font={'color': UI_FONT_COLOR}
    )
    return fig


def build_solution_metrics_figures(solution, reference_solution=None, horizontal=True, 
                                   language: str = LANGUAGE_ENGLISH_KEY):
    """
    Build a figure with metrics about the solution.
    """
    comparison_to_reference = False if (reference_solution is None) else True
    reference_solution = solution if (reference_solution is None) else reference_solution
    instance = solution.instance
    if check_if_language_is_english(language):
        nb_performed_tasks_indicator_title = "# Performed tasks"
        nb_working_time_indicator_title = "Total working time"
        nb_total_traveling_time_indicator_title = "Total traveling time"
    elif check_if_language_is_french(language):
        nb_performed_tasks_indicator_title = "# Tâches réalisées"
        nb_working_time_indicator_title = "Durée totale de travail"
        nb_total_traveling_time_indicator_title = "Durée totale de déplacement"
    else:
        raise ValueError(f"Unknown language: {language}")
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        title=dict(text=nb_performed_tasks_indicator_title, font=dict(color=UI_FONT_COLOR)),
        mode=f"gauge+number{'+delta' if comparison_to_reference else ''}",
        gauge=dict(axis=dict(range=[0, instance.nb_tasks], tickcolor=UI_LINE_COLOR),
                   bordercolor=UI_LINE_COLOR),
        number=dict(font=dict(color=UI_FONT_COLOR)),
        value=solution.nb_performed_tasks, delta=dict(reference=reference_solution.nb_performed_tasks),
        domain={'row': 0, 'column': 0})
    )
    fig.add_trace(go.Indicator(
        title=dict(text=nb_working_time_indicator_title, font=dict(color=UI_FONT_COLOR)),
        mode=f"gauge+number{'+delta' if comparison_to_reference else ''}",
        gauge=dict(axis=dict(range=[0, instance.total_employees_availability_duration],
                             tickcolor=UI_LINE_COLOR), bordercolor=UI_LINE_COLOR),
        number=dict(font=dict(color=UI_FONT_COLOR), suffix='min'),
        value=solution.total_working_duration, delta=dict(reference=reference_solution.total_working_duration),
        domain={'row': 0, 'column': 1})
    )
    fig.add_trace(go.Indicator(
        title=dict(text=nb_total_traveling_time_indicator_title, font=dict(color=UI_FONT_COLOR)),
        mode=f"gauge+number{'+delta' if comparison_to_reference else ''}",
        gauge=dict(axis=dict(range=[0, instance.total_employees_availability_duration],
                             tickcolor=UI_LINE_COLOR), bar=dict(color='red'), bordercolor=UI_LINE_COLOR),
        number=dict(font=dict(color=UI_FONT_COLOR), suffix='min'),
        value=solution.total_traveling_duration,
        delta=dict(reference=reference_solution.total_traveling_duration,
                   increasing=dict(color='red'), decreasing=dict(color='green')),
        domain={'row': 0 if horizontal else 1, 'column': 2 if horizontal else 0})
    )
    fig.update_layout(
        grid={'rows': 1 if horizontal else 2, 'columns': 3 if horizontal else 2, 'pattern': 'independent'},
        paper_bgcolor=UI_PANEL_CONTENT_COLOR, font={'color': UI_FONT_COLOR}
    )
    return fig
