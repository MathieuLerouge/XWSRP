# Standard libraries
import time
from contextlib import contextmanager
from typing import Callable, Iterator


################
# ProgressStep #
################

class ProgressStep:
    """
    A step of a computation being reported on, through which the step's details are reported as they become known.
    """

    def __init__(self, report_info: Callable[[str, str], None]):
        """
        Args:
            report_info: Reports one detail of the step, given its label and its value's string form.
        """
        self._report_info = report_info

    def info(self, label: str, value):
        """
        Report one detail of the step.

        Args:
            label: What the detail is.
            value: The detail's value, reported as its string form.
        """
        self._report_info(label, str(value))


####################
# ProgressReporter #
####################

class ProgressReporter:
    """
    Reports the progress of a computation step by step, as each one starts, details what it found, and ends.

    This base class reports nothing, so that a computation can be handed one whether anyone follows it or not.
    Subclasses report somewhere by overriding the _on_step_* hooks.
    """

    @contextmanager
    def step(self, title: str) -> Iterator[ProgressStep]:
        """
        Report a step for the duration of the with block it opens.

        The step is reported as done when the block ends normally,
        and as failed when it raises, the exception being raised again unchanged:
        a step failing is often an expected outcome (e.g. a neighborhood that cannot be extracted),
        which the caller still has to handle.

        Args:
            title: What the step does.

        Yields:
            The step, through which its details are reported.
        """
        self._on_step_started(title)
        start_time = time.perf_counter()
        try:
            yield ProgressStep(self._on_step_info)
        except Exception as error:
            self._on_step_failed(error, time.perf_counter() - start_time)
            raise
        self._on_step_done(time.perf_counter() - start_time)

    def _on_step_started(self, title: str):
        """
        Called when a step starts.

        Args:
            title: What the step does.
        """

    def _on_step_info(self, label: str, value: str):
        """
        Called for each detail a step reports.

        Args:
            label: What the detail is.
            value: The detail's value.
        """

    def _on_step_done(self, elapsed_time: float):
        """
        Called when a step ends normally.

        Args:
            elapsed_time: The time the step took, in seconds.
        """

    def _on_step_failed(self, error: Exception, elapsed_time: float):
        """
        Called when a step ends by raising.

        Args:
            error: The exception the step raised.
            elapsed_time: The time the step took until it raised, in seconds.
        """
