# Local libraries
from src.modeling.employee import Employee
from src.utils.location import Location


# Class EditableEmployee
class EditableEmployee(Employee):

    def __init__(self, name: str, start_time_lb: int, end_time_ub: int, location: Location, skill_level: int):
        super().__init__(name, start_time_lb, end_time_ub, location, skill_level)

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
