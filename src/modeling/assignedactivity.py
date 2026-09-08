# Standard library
from typing import Optional

# Local libraries
from src.modeling.activity import Activity
# from model.employee import Employee
# NB: it is not possible to import Employee, otherwise there is a circular import
from src.utils.location import Location


####################
# AssignedActivity #
####################

class AssignedActivity(Activity):
    """
    An activity that has been assigned to an employee.
    """

    def __init__(self, employee, name: str, duration: int = 0, start_time_lb: Optional[int] = None,
                 end_time_ub: Optional[int] = None, skill_level: int = 0, location: Optional[Location] = None):
        """
        Args:
            employee: Employee the activity is assigned to.
                Not type-hinted as Employee because importing that module here would create a circular import.
            name: Unique identifier of the activity.
            duration: Duration of the activity, in minutes.
            start_time_lb: Lower bound, in minutes since midnight, of the activity's time window.
            end_time_ub: Upper bound, in minutes since midnight, of the activity's time window.
            skill_level: Skill level required to perform the activity.
            location: Location where the activity takes place.
        """
        super().__init__(name, duration, start_time_lb, end_time_ub, skill_level, location)
        self._employee = employee

    def __eq__(self, activity):
        if isinstance(activity, AssignedActivity):
            return self.employee == activity.employee and self.name == activity.name
        else:
            return False

    def __hash__(self):
        return hash(f"{self._employee.name}_{self._name}")
