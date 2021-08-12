# Local libraries
from model.assignedactivity import AssignedActivity
from model.employee import Employee


# Global variable
COMING_BACK_HOME_STRING = "Return"


# Class ComeBack
class ComeBack(AssignedActivity):

    def __init__(self, employee: Employee):
        super().__init__(employee, COMING_BACK_HOME_STRING,
                         start_time_LB=employee.start_time_LB, end_time_UB=employee.end_time_UB,
                         location=employee.location)
