# Local libraries
from model.activity import Activity
from model.employee import Employee
from model.task import Task


# Class Alterations
class Alterations:

    def __init__(self):
        self._employees_LBs = dict()
        self._employees_UBs = dict()
        self._activities_LBs = dict()
        self._activities_UBs = dict()
        self._tasks_durations = dict()

    @property
    def nb(self):
        return (len(self._employees_LBs) + len(self._employees_UBs) +
                len(self._activities_LBs) + len(self._activities_UBs) + len(self._tasks_durations))

    def get_task_duration(self, task: Task):
        if task.name in self._tasks_durations:
            return self._tasks_durations[task.name]
        else:
            return 0

    def set_employee_LB(self, employee: Employee, LB_alteration: int):
        self._employees_LBs[employee.name] = LB_alteration

    def set_employee_UB(self, employee: Employee, UB_alteration: int):
        self._employees_UBs[employee.name] = UB_alteration

    def set_activity_LB(self, activity: Activity, LB_alteration: int):
        self._activities_LBs[activity.name] = LB_alteration

    def set_activity_UB(self, activity: Activity, UB_alteration: int):
        self._activities_UBs[activity.name] = UB_alteration

    def set_task_duration(self, task: Task, duration_alteration: int):
        self._tasks_durations[task.name] = duration_alteration

    def enumerate(self):
        alterations_texts = []
        for employee_name, value in self._employees_LBs.items():
            time_direction = "earlier" if value < 0 else "later"
            alterations_texts.append(f"shift {employee_name}'s start time by {abs(value)} min {time_direction}")
        for employee_name, value in self._employees_UBs.items():
            time_direction = "earlier" if value < 0 else "later"
            alterations_texts.append(f"shift {employee_name}'s end time by {abs(value)} min {time_direction}")
        for activity_name, value in self._activities_LBs.items():
            time_direction = "earlier" if value < 0 else "later"
            alterations_texts.append(f"shift {activity_name}'s start time by {abs(value)} min {time_direction}")
        for activity_name, value in self._activities_UBs.items():
            time_direction = "earlier" if value < 0 else "later"
            alterations_texts.append(f"shift {activity_name}'s end time by {abs(value)} min {time_direction}")
        for task_name, value in self._tasks_durations.items():
            alter = "reduce" if value < 0 else "increase"
            alterations_texts.append(f"{alter} {task_name}'s duration by {abs(value)} min")
        return alterations_texts
