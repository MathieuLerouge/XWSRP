# Standard library
from typing import Optional

# Local library
from src.modeling.activity import Activity


#########################
# LunchBreakPerformance #
#########################

class LunchBreakPerformance:
    """
    How an employee's lunch break is performed in a solution:
    the activities right before and after it, and its start time.
    """

    def __init__(self, activity_before: Activity, activity_after: Activity, start_time: Optional[int] = None):
        """
        Args:
            activity_before: Activity right before the lunch break.
            activity_after: Activity right after the lunch break.
            start_time: Start time of the lunch break, in minutes since midnight.
        """
        self._activity_before = activity_before
        self._activity_after = activity_after
        self._start_time = start_time

    @property
    def activity_before(self) -> Activity:
        """Activity right before the lunch break."""
        return self._activity_before

    @activity_before.setter
    def activity_before(self, activity_before: Activity):
        self._activity_before = activity_before

    @property
    def activity_after(self) -> Activity:
        """Activity right after the lunch break."""
        return self._activity_after

    @activity_after.setter
    def activity_after(self, activity_after: Activity):
        self._activity_after = activity_after

    @property
    def start_time(self) -> Optional[int]:
        """Start time of the lunch break, in minutes since midnight."""
        return self._start_time

    @start_time.setter
    def start_time(self, start_time: Optional[int]):
        self._start_time = start_time

    def __deepcopy__(self, memo) -> "LunchBreakPerformance":
        # NB: activity_before/activity_after belong to the sequence's own object graph,
        # which Solution.copy() intentionally shares rather than duplicates (see Sequence.copy(), Step.copy()) --
        # deep-copying them here would create divergent Activity objects and defeat that sharing.
        return LunchBreakPerformance(self._activity_before, self._activity_after, self._start_time)
