# Local libraries
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.utils.constants import LINE_BREAK_STRING


# Class InstanceChanges
from src.utils.time import convert_nb_minutes_to_time_string


class InstanceChanges:

    def __init__(self):
        self._employees_changed_params = dict()
        self._employees_changed_params_as_strings = dict()
        self._employees_params = dict()
        self._employees_params_as_strings = dict()
        self._tasks_changed_params = dict()
        self._tasks_changed_params_as_strings = dict()
        self._tasks_original_params = dict()
        self._tasks_original_params_as_strings = dict()

    @property
    def nb_changes(self):
        return self.nb_employees_changes + self.nb_tasks_changes

    @property
    def nb_employees_changes(self):
        return len(self._employees_params)

    def add_employee_change(self, employee: Employee, start_time_LB: int = None, end_time_UB: int = None,
                            skill_level: int = None):
        if not (start_time_LB is None and end_time_UB is None and skill_level is None):
            if employee.name not in self._employees_changed_params:
                self._employees_params[employee.name] = \
                    dict(start_time_LB=employee.start_time_LB, end_time_UB=employee.end_time_UB,
                         skill_level=employee.skill_level)
                self._employees_params_as_strings[employee.name] = \
                    dict(start_time_LB=employee.get_start_time_LB(as_integer=False),
                         end_time_UB=employee.get_end_time_UB(as_integer=False),
                         skill_level=str(employee.skill_level))
                start_time_LB_as_string = (None if start_time_LB is None
                                           else convert_nb_minutes_to_time_string(start_time_LB))
                end_time_UB_as_string = (None if end_time_UB is None
                                         else convert_nb_minutes_to_time_string(end_time_UB))
                self._employees_changed_params[employee.name] = \
                    dict(start_time_LB=start_time_LB, end_time_UB=end_time_UB, skill_level=skill_level)
                self._employees_changed_params_as_strings[employee.name] = \
                    dict(start_time_LB=None if start_time_LB is None else start_time_LB_as_string,
                         end_time_UB=None if end_time_UB is None else end_time_UB_as_string,
                         skill_level=None if skill_level is None else str(skill_level))
            else:
                if start_time_LB is not None:
                    self._employees_changed_params[employee.name]['start_time_LB'] = start_time_LB
                    self._employees_changed_params_as_strings[employee.name]['start_time_LB'] = \
                        convert_nb_minutes_to_time_string(start_time_LB)
                if end_time_UB is not None:
                    self._employees_changed_params[employee.name]['end_time_UB'] = end_time_UB
                    self._employees_changed_params_as_strings[employee.name]['end_time_UB'] = \
                        convert_nb_minutes_to_time_string(end_time_UB)
                if skill_level is not None:
                    self._employees_changed_params[employee.name]['skill_level'] = skill_level
                    self._employees_changed_params_as_strings[employee.name]['skill_level'] = str(skill_level)

    def is_affecting_employee(self, employee: Employee):
        return employee.name in self._employees_params

    def is_affecting_employee_by_name(self, employee_name: str):
        return employee_name in self._employees_params

    def get_employee_start_time_LB(self, employee: Employee):
        return self._employees_changed_params[employee.name]['start_time_LB']

    def get_employee_start_time_LB_by_name(self, employee_name: str):
        return self._employees_changed_params[employee_name]['start_time_LB']

    def get_employee_end_time_UB(self, employee: Employee):
        return self._employees_changed_params[employee.name]['end_time_UB']

    def get_employee_end_time_UB_by_name(self, employee_name: str):
        return self._employees_changed_params[employee_name]['end_time_UB']

    def get_employee_skill_level(self, employee: Employee):
        return self._employees_changed_params[employee.name]['skill_level']

    def get_employee_skill_level_by_name(self, employee_name: str):
        return self._employees_changed_params[employee_name]['skill_level']

    @property
    def nb_tasks_changes(self):
        return len(self._tasks_original_params)

    def add_task_change(self, task: Task, duration: int = None, start_time_LB: int = None, end_time_UB: int = None,
                        skill_level: int = None):
        if not (duration is None and start_time_LB is None and end_time_UB is None and skill_level is None):
            if task.name not in self._tasks_changed_params:
                self._tasks_original_params[task.name] = \
                    dict(duration=task.duration, start_time_LB=task.start_time_LB,
                         end_time_UB=task.end_time_UB, skill_level=task.skill_level)
                self._tasks_original_params_as_strings[task.name] = \
                    dict(duration=task.get_duration(as_integer=False),
                         start_time_LB=task.get_start_time_LB(as_integer=False),
                         end_time_UB=task.get_end_time_UB(as_integer=False),
                         skill_level=str(task.skill_level))
                self._tasks_changed_params[task.name] = \
                    dict(duration=duration, start_time_LB=start_time_LB,
                         end_time_UB=end_time_UB, skill_level=skill_level)
                start_time_LB_as_string = (None if start_time_LB is None
                                           else convert_nb_minutes_to_time_string(start_time_LB))
                end_time_UB_as_string = (None if end_time_UB is None
                                         else convert_nb_minutes_to_time_string(end_time_UB))
                self._tasks_changed_params_as_strings[task.name] = \
                    dict(duration=None if duration is None else str(duration)+"min",
                         start_time_LB=None if start_time_LB is None else start_time_LB_as_string,
                         end_time_UB=None if end_time_UB is None else end_time_UB_as_string,
                         skill_level=None if skill_level is None else str(skill_level))
            else:
                if duration is not None:
                    self._tasks_changed_params[task.name]['duration'] = duration
                    self._tasks_changed_params_as_strings[task.name]['duration'] = str(duration) + "min"
                if start_time_LB is not None:
                    self._tasks_changed_params[task.name]['start_time_LB'] = start_time_LB
                    self._tasks_changed_params_as_strings[task.name]['start_time_LB'] = \
                        convert_nb_minutes_to_time_string(start_time_LB)
                if end_time_UB is not None:
                    self._tasks_changed_params[task.name]['end_time_UB'] = end_time_UB
                    self._tasks_changed_params_as_strings[task.name]['end_time_UB'] = \
                        convert_nb_minutes_to_time_string(end_time_UB)
                if skill_level is not None:
                    self._tasks_changed_params[task.name]['skill_level'] = skill_level
                    self._tasks_changed_params_as_strings[task.name]['skill_level'] = str(skill_level)

    def is_affecting_task(self, task: Task):
        return task.name in self._tasks_changed_params

    def is_affecting_task_by_name(self, task_name: str):
        return task_name in self._tasks_changed_params

    def get_task_duration(self, task: Task):
        return self._tasks_changed_params[task.name]['duration']

    def get_task_duration_by_name(self, task_name: str):
        return self._tasks_changed_params[task_name]['duration']

    def get_task_start_time_LB(self, task: Task):
        return self._tasks_changed_params[task.name]['start_time_LB']

    def get_task_start_time_LB_by_name(self, task_name: str):
        return self._tasks_changed_params[task_name]['start_time_LB']

    def get_task_end_time_UB(self, task: Task):
        return self._tasks_changed_params[task.name]['end_time_UB']

    def get_task_end_time_UB_by_name(self, task_name: str):
        return self._tasks_changed_params[task_name]['end_time_UB']

    def get_task_skill_level(self, task: Task):
        return self._tasks_changed_params[task.name]['skill_level']

    def get_task_skill_level_by_name(self, task_name: str):
        return self._tasks_changed_params[task_name]['skill_level']

    def as_list_of_strings(self, starting_with_uppercase: bool = False):
        changes_texts = []
        employee_parameters_names = dict(start_time_LB="earliest working time", end_time_UB="latest working time",
                                         skill_level="skill level")
        for employee_name, changes in self._employees_changed_params_as_strings.items():
            for parameter, value in changes.items():
                if value is not None:
                    text = f"{'The' if starting_with_uppercase else 'the'} " \
                           f"{employee_parameters_names[parameter]} of {employee_name} is changed " \
                           f"to {value} instead of {self._employees_params_as_strings[employee_name][parameter]}"
                    changes_texts.append(text)
        task_parameters_names = dict(start_time_LB="earliest start time", end_time_UB="latest end time",
                                     duration="duration", skill_level="skill level")
        for task_name, changes in self._tasks_changed_params_as_strings.items():
            for parameter, value in changes.items():
                if value is not None:
                    text = f"{'The' if starting_with_uppercase else 'the'} " \
                           f"{task_parameters_names[parameter]} of {task_name} is changed " \
                           f"to {value} instead of {self._tasks_original_params_as_strings[task_name][parameter]}"
                    changes_texts.append(text)
        return changes_texts

    def as_string(self, starting_with_uppercase: bool = False):
        text = ""
        if self.nb_changes > 1:
            for change_text in self.as_list_of_strings(starting_with_uppercase):
                text += f"- {change_text};{LINE_BREAK_STRING}"
            text = text.removesuffix(LINE_BREAK_STRING).removesuffix(';') + ". "
        elif self.nb_changes == 1:
            text += self.as_list_of_strings(starting_with_uppercase)[0] + ". "
        return text

    def __repr__(self):
        text = ""
        for change_text in self.as_list_of_strings():
            text += change_text + LINE_BREAK_STRING
        return text.removesuffix(LINE_BREAK_STRING)
