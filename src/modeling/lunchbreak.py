# Local libraries
from src.modeling.assignedactivity import AssignedActivity
from src.modeling.employee import Employee


# Global variable
LUNCH_BREAK_STRING = "LunchBreak"


##############
# LunchBreak #
##############

class LunchBreak(AssignedActivity):
    """
    An employee's lunch break.
    """

    def __init__(self, employee: Employee, start_time: int, end_time: int):
        """
        Args:
            employee: Employee taking this lunch break.
            start_time: Start of the lunch break, in minutes since midnight.
            end_time: End of the lunch break, in minutes since midnight.
        """
        super().__init__(employee, LUNCH_BREAK_STRING, (end_time - start_time), start_time, end_time)
