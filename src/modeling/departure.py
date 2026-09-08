# Local libraries
from src.modeling.assignedactivity import AssignedActivity
from src.modeling.employee import Employee


# Global variable
LEAVING_HOME_STRING = "Start"


#############
# Departure #
#############

class Departure(AssignedActivity):
    """
    The activity corresponding to an employee leaving home at the start of their working day.
    """

    def __init__(self, employee: Employee):
        """
        Args:
            employee: Employee leaving home.
        """
        super().__init__(employee, LEAVING_HOME_STRING,
                          start_time_lb=employee.start_time_lb, end_time_ub=employee.end_time_ub,
                          location=employee.location)
