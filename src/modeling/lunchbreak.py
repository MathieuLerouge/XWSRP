# Local libraries
from src.modeling.assignedactivity import AssignedActivity
from src.modeling.employee import Employee


# Global variable
LUNCH_BREAK_STRING = "LunchBreak"


# Class LunchBreak
class LunchBreak(AssignedActivity):

    def __init__(self, employee: Employee, start_time: int, end_time: int):
        super().__init__(employee, LUNCH_BREAK_STRING, (end_time - start_time), start_time, end_time)
