# Standard libraries
import time
from contextlib import contextmanager
from typing import Callable, Iterator, Optional


################
# ProgressStep #
################

class ProgressStep:
    """
    A step of a computation being reported on, through which the step's details are reported as they become known.
    """

    def __init__(self, report_info: Callable[[str, str], None], report_warning: Callable[[str], None]):
        """
        Args:
            report_info: Reports one detail of the step, given its label and its value's string form.
            report_warning: Reports one warning about the step, given its message.
        """
        self._report_info = report_info
        self._report_warning = report_warning

    def info(self, label: str, value):
        """
        Report one detail of the step.

        Args:
            label: What the detail is.
            value: The detail's value, reported as its string form.
        """
        self._report_info(label, str(value))

    def warning(self, message: str):
        """
        Report something worth flagging about the step, which does not make it fail.

        Args:
            message: What is worth flagging.
        """
        self._report_warning(message)


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
    def step(self, title: str, short_title: Optional[str] = None) -> Iterator[ProgressStep]:
        """
        Report a step for the duration of the with block it opens.

        The step is reported as done when the block ends normally,
        and as failed when it raises, the exception being raised again unchanged:
        a step failing is often an expected outcome (e.g. a neighborhood that cannot be extracted),
        which the caller still has to handle.

        Args:
            title: What the step does.
            short_title: A word or two standing for the step where space is short (e.g. in a summary of step times),
                or None for the title's first word, lowercased (e.g. "extracting" for "Extracting the neighborhood").

        Yields:
            The step, through which its details are reported.
        """
        self._on_step_started(title, short_title if short_title is not None else title.split()[0].lower())
        start_time = time.perf_counter()
        try:
            yield ProgressStep(self._on_step_info, self._on_step_warning)
        except Exception as error:
            self._on_step_failed(error, time.perf_counter() - start_time)
            raise
        self._on_step_done(time.perf_counter() - start_time)

    def _on_step_started(self, title: str, short_title: str):
        """
        Called when a step starts.

        Args:
            title: What the step does.
            short_title: A word or two standing for the step where space is short.
        """

    def _on_step_info(self, label: str, value: str):
        """
        Called for each detail a step reports.

        Args:
            label: What the detail is.
            value: The detail's value.
        """

    def _on_step_warning(self, message: str):
        """
        Called for each warning a step reports.

        Args:
            message: What is worth flagging.
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
