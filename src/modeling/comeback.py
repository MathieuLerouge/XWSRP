# Local libraries
from src.modeling.assignedactivity import AssignedActivity
from src.modeling.employee import Employee


# Global variable
COMING_BACK_HOME_STRING = "Return"


# Class ComeBack
class ComeBack(AssignedActivity):

    def __init__(self, employee: Employee):
        super().__init__(employee, COMING_BACK_HOME_STRING,
                         start_time_lb=employee.start_time_lb, end_time_ub=employee.end_time_ub,
                         location=employee.location)
