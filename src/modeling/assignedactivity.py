# Local libraries
from src.modeling.activity import Activity
# from model.employee import Employee
# Remark: it is not possible to import Employee, otherwise there is a circular import
from src.utils.location import Location


# Class AssignedActivity
class AssignedActivity(Activity):

    # Remark: it is not possible to specify employee input type (Employee), otherwise there is a circular import
    def __init__(self, employee, name: str, duration: int = 0, start_time_LB: int = None, end_time_UB: int = None,
                 skill_level: int = 0, location: Location = None):
        super().__init__(name, duration, start_time_LB, end_time_UB, skill_level, location)
        self._employee = employee

    def __eq__(self, activity):
        if isinstance(activity, AssignedActivity):
            return self.employee == activity.employee and self.name == activity.name
        else:
            return False

    def __hash__(self):
        return hash(f"{self._employee.name}_{self._name}")

    def __repr__(self):
        return f"{self._employee.name}_{self._name}"
