# Local libraries
from utils.location import Location
from utils.timeset import TimeInterval, TimeIntervalUnion


# Class Activity
class Activity:

    def __init__(self, name: str, duration: int = 0, start_time_LB: int = None, end_time_UB: int = None,
                 skill_level: int = 0, location: Location = None):
        self._name = name
        self._employee = None
        self._duration = duration
        self._start_time_LB = start_time_LB
        self._end_time_UB = end_time_UB
        self._TWs = TimeIntervalUnion(
            [TimeInterval(lower_bound=start_time_LB, upper_bound=end_time_UB)]
        )
        self._skill_level = skill_level
        self._location = location

    @property
    def name(self):
        return self._name

    @property
    def employee(self):
        return self._employee

    @property
    def duration(self):
        return self._duration

    @property
    def start_time_LB(self):
        return self._start_time_LB

    @property
    def end_time_UB(self):
        return self._end_time_UB

    @property
    def TWs(self):
        return self._TWs

    @property
    def location(self):
        return self._location

    @property
    def skill_level(self):
        return self._skill_level

    def distance_to(self, activity):
        try:
            return self.location.distance_to(activity.location)
        except Exception as error:
            if isinstance(error, AttributeError):
                raise AttributeError(f"This activity {self} has no location")
            else:
                raise ValueError(f"The given activity {activity} has no location")
