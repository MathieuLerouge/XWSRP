# Local libraries
from src.modeling.task import Task
from src.utils.location import Location


# Class Task
class EditableTask(Task):

    def __init__(self, name: str, duration: int, start_time_lb: int, end_time_ub: int,
                 skill_level: int, location: Location):
        super().__init__(name, duration, start_time_lb, end_time_ub, skill_level, location)

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, duration: int):
        self._duration = duration

    @property
    def start_time_lb(self):
        return self._start_time_lb

    @start_time_lb.setter
    def start_time_lb(self, start_time_lb: int):
        self._start_time_lb = start_time_lb

    @property
    def end_time_ub(self):
        return self._end_time_ub

    @end_time_ub.setter
    def end_time_ub(self, end_time_ub: int):
        self._end_time_ub = end_time_ub

    @property
    def skill_level(self):
        return self._skill_level

    @skill_level.setter
    def skill_level(self, skill_level: int):
        self._skill_level = skill_level
