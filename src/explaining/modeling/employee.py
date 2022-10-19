# Local libraries
from src.modeling.employee import Employee
from src.utils.location import Location


# Class EditableEmployee
class EditableEmployee(Employee):

    def __init__(self, name: str, start_time_LB: int, end_time_UB: int, location: Location, skill_level: int):
        super().__init__(name, start_time_LB, end_time_UB, location, skill_level)

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
