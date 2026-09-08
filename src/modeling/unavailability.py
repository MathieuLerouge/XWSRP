# Local libraries
from src.modeling.assignedactivity import AssignedActivity
from src.utils.location import Location


##################
# Unavailability #
##################

class Unavailability(AssignedActivity):
    """
    A period during which an employee is unavailable.
    """

    def __init__(self, employee, name: str, start_time: int, end_time: int, location: Location):
        """
        Args:
            employee: Employee this unavailability is registered for.
                Not type-hinted as Employee because importing that module here would create a circular import.
            name: Unique identifier of the unavailability.
            start_time: Start of the unavailability, in minutes since midnight.
            end_time: End of the unavailability, in minutes since midnight.
            location: Location where the employee is unavailable.
        """
        super().__init__(employee, name, (end_time - start_time), start_time, end_time, 0, location)
