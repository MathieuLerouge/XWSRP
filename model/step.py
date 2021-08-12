# Local libraries
from model.activity import Activity
from utils.time import convert_nb_minutes_to_time_string


# Global variables
BRACKET_LEFT_STRING = '{'
BRACKET_RIGHT_STRING = '}'


# Class Step
class Step:

    def __init__(self, activity: Activity, arrival_time: int = None, start_time: int = None, end_time: int = None):
        self._activity = activity
        self._arrival_time = arrival_time
        self._start_time = start_time
        self._end_time = end_time

    def __eq__(self, step):
        return isinstance(step, Step) and self.activity.name == step.activity.name and \
               self.start_time == step.start_time and self.end_time == step.end_time

    def __lt__(self, step):
        return self.start_time <= step.start_time and self.end_time <= step.end_time

    def __repr__(self):
        symbol = f"{BRACKET_LEFT_STRING}{self._activity.name}: "
        if self._arrival_time is not None:
            symbol += f"Ta = {convert_nb_minutes_to_time_string(self._arrival_time)}, "
        symbol += f"Ts = {convert_nb_minutes_to_time_string(self._start_time)}"
        if self._end_time is not None:
            symbol += f", Te = {convert_nb_minutes_to_time_string(self._end_time)}"
        symbol += f"{BRACKET_RIGHT_STRING}"
        return symbol

    @property
    def activity(self):
        return self._activity

    @property
    def arrival_time(self):
        return self._arrival_time

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @activity.setter
    def activity(self, activity: Activity):
        self.activity = activity

    @arrival_time.setter
    def arrival_time(self, arrival_time: int):
        self._arrival_time = arrival_time

    @start_time.setter
    def start_time(self, start_time: int):
        self._start_time = start_time
        if self._end_time is None:
            self._end_time = self._start_time + self._activity.duration

    @end_time.setter
    def end_time(self, end_time: int):
        self._end_time = end_time

    # TODO Clear that
    # def set(self, activity: Activity, arrival_time=None, start_time=None, end_time=None):
    #     self._activity = activity
    #     self._arrival_time = arrival_time
    #     self._start_time = start_time
    #     self._end_time = start_time + self.activity.duration if end_time is None else end_time

    def clear(self):
        self._activity = None
        self._arrival_time = None
        self._start_time = None
        self._end_time = None

    def copy(self):
        return Step(self._activity, self._arrival_time, self._start_time, self._end_time)
