# Local libraries
from model.task import Task
from utils.location import Location


# Class Task
class EditableTask(Task):

    def __init__(self, name: str, duration: int, start_time_LB: int, end_time_UB: int,
                 skill_level: int, location: Location):
        super().__init__(name, duration, start_time_LB, end_time_UB, skill_level, location)

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, duration: int):
        self._duration = duration

    @property
    def start_time_LB(self):
        return self._start_time_LB

    @start_time_LB.setter
    def start_time_LB(self, start_time_LB: int):
        self._start_time_LB = start_time_LB

    @property
    def end_time_UB(self):
        return self._end_time_UB

    @end_time_UB.setter
    def end_time_UB(self, end_time_UB: int):
        self._end_time_UB = end_time_UB

    @property
    def skill_level(self):
        return self._skill_level

    @skill_level.setter
    def skill_level(self, skill_level: int):
        self._skill_level = skill_level
