# Local libraries modules
from model.activity import Activity
from model.step import Step, BRACKET_LEFT_STRING, BRACKET_RIGHT_STRING
from utils.time import convert_nb_minutes_to_time_string


# Class StepLS
class StepLS(Step):

    def __init__(self, activity: Activity, arrival_time: int = None, start_time: int = None, end_time: int = None,
                 BTS: int = None, FTS: int = None):
        super().__init__(activity, arrival_time, start_time, end_time)
        self._BTS = BTS
        self._FTS = FTS

    def __repr__(self):
        representation = f"{BRACKET_LEFT_STRING}{self._activity.name}: "
        if self._arrival_time is not None:
            representation += f"Ta = {convert_nb_minutes_to_time_string(self._arrival_time)}, "
        representation += f"Ts = {convert_nb_minutes_to_time_string(self._start_time)}"
        if self._end_time is not None:
            representation += f", Te = {convert_nb_minutes_to_time_string(self._end_time)}"
        if self._BTS is not None:
            representation += f", BTS = {self._BTS}, FTS = {self._FTS}"
        representation += f"{BRACKET_RIGHT_STRING}"
        return representation

    @classmethod
    def from_Step(cls, step: Step):
        return cls(step.activity, step.arrival_time, step.start_time, step.end_time)

    @property
    def BTS(self):
        return self._BTS

    @BTS.setter
    def BTS(self, BTS: int):
        self._BTS = BTS

    @property
    def FTS(self):
        return self._FTS

    @FTS.setter
    def FTS(self, FTS: int):
        self._FTS = FTS

    def clear(self):
        super().clear()
        self._BTS = None
        self._FTS = None

    def copy(self):
        return StepLS(self._activity, self._arrival_time, self._start_time, self._end_time, self._BTS, self._FTS)
