# Local libraries
from src.utils.location import Location
from src.utils.time import convert_nb_minutes_to_time_string, TWELVE_HOURS_FORMAT
from src.utils.timeset import TimeInterval, TimeIntervalUnion


# Class Activity
class Activity:

    def __init__(self, name: str, duration: int = 0, start_time_lb: int = None, end_time_ub: int = None,
                 skill_level: int = 0, location: Location = None):
        self._name = name
        self._employee = None
        self._duration = duration
        self._start_time_lb = start_time_lb
        self._end_time_ub = end_time_ub
        self._TWs = TimeIntervalUnion([TimeInterval(lower_bound=start_time_lb, upper_bound=end_time_ub)])
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

    def get_duration(self, as_integer: bool = True):
        if as_integer:
            return self._duration
        else:
            return str(self._duration) + "min"

    @property
    def start_time_lb(self):
        return self._start_time_lb

    def get_start_time_lb(self, as_integer: bool = True, hour_format: str = TWELVE_HOURS_FORMAT):
        if as_integer:
            return self._start_time_lb
        else:
            return convert_nb_minutes_to_time_string(self._start_time_lb, hour_format)

    @property
    def end_time_ub(self):
        return self._end_time_ub

    def get_end_time_ub(self, as_integer: bool = True, hour_format: str = TWELVE_HOURS_FORMAT):
        if as_integer:
            return self._end_time_ub
        else:
            return convert_nb_minutes_to_time_string(self._end_time_ub, hour_format)

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
