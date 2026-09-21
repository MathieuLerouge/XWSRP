# Standard library
from typing import Optional

# Local libraries
from src.modeling.activity import Activity
from src.modeling.step import Step, BRACKET_LEFT_STRING, BRACKET_RIGHT_STRING
from src.utils.time import convert_nb_minutes_to_time_string


#####################
# StepForHeuristics #
#####################

class StepForHeuristics(Step):
    """
    A Step extended with the backward and forward time slacks (BTS/FTS) the heuristics compute and
    maintain to know how much a step's times can shift without violating time-window constraints.
    """

    def __init__(
            self, activity: Activity,
            arrival_time: Optional[int] = None, start_time: Optional[int] = None, end_time: Optional[int] = None,
            bts: Optional[int] = None, fts: Optional[int] = None
    ):
        """
        Args:
            activity: Activity performed during this step.
            arrival_time: Time, in minutes since midnight, the employee arrives at the activity's location.
            start_time: Time, in minutes since midnight, the activity starts.
            end_time: Time, in minutes since midnight, the activity ends.
            bts: The step's Backward Time Slack, in minutes.
            fts: The step's Forward Time Slack, in minutes.
        """
        super().__init__(activity, arrival_time, start_time, end_time)
        self._bts = bts  # Backward Time Slacks
        self._fts = fts  # Forward Time Slacks

    def __repr__(self):
        representation = f"{BRACKET_LEFT_STRING}{self._activity.name}: "
        if self._arrival_time is not None:
            representation += f"Ta = {convert_nb_minutes_to_time_string(self._arrival_time)}({self._arrival_time}), "
        if self._start_time is not None:
            representation += f"Ts = {convert_nb_minutes_to_time_string(self._start_time)}({self._start_time})"
        if self._end_time is not None:
            representation += f", Te = {convert_nb_minutes_to_time_string(self._end_time)}({self._end_time})"
        if self._bts is not None and self._fts is not None:
            representation += f", BTS = {self._bts}, FTS = {self._fts}"
        representation += f"{BRACKET_RIGHT_STRING}"
        return representation

    @classmethod
    def from_step(cls, step: Step):
        return cls(step.activity, step.arrival_time, step.start_time, step.end_time)

    @property
    def bts(self) -> Optional[int]:
        """The step's Backward Time Slack, in minutes."""
        return self._bts

    @bts.setter
    def bts(self, bts: int):
        self._bts = bts

    @property
    def fts(self) -> Optional[int]:
        """The step's Forward Time Slack, in minutes."""
        return self._fts

    @fts.setter
    def fts(self, fts: int):
        self._fts = fts

    def clear(self):
        """Resets the activity, all times, and the BTS/FTS time slacks of this step to None."""
        super().clear()
        self._bts = None
        self._fts = None

    def copy(self):
        return StepForHeuristics(
            self._activity, self._arrival_time, self._start_time, self._end_time, self._bts, self._fts
        )
