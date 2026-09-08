# Local libraries
from src.modeling.assignedactivity import AssignedActivity
from src.modeling.employee import Employee


# Global variable
COMING_BACK_HOME_STRING = "Return"


############
# ComeBack #
############

class ComeBack(AssignedActivity):
    """
    The activity corresponding to an employee returning home at the end of their working day.
    """

    def __init__(self, employee: Employee):
        """
        Args:
            employee: Employee returning home.
        """
        super().__init__(employee, COMING_BACK_HOME_STRING,
                          start_time_lb=employee.start_time_lb, end_time_ub=employee.end_time_ub,
                          location=employee.location)
