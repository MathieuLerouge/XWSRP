# Standard library
from typing import Callable, Optional, cast

# Local library
from src.utils.progress import ProgressReporter


#######################
# CLIProgressReporter #
#######################

class CLIProgressReporter(ProgressReporter):
    """
    Prints the progress of a computation to the terminal, one block of lines per step, each after a blank line:

    ⏵ <title>
     ⎿ <label>: <value>
    ⚠ <warning>
    ✓ Done in <elapsed time>s

    It also records each step's short title and elapsed time,
    for a summary of where the time went.
    """

    def __init__(self, colorize: Callable[[str], str] = str, colorize_warning: Callable[[str], str] = str,
                 output: Callable[[str], None] = print):
        """
        Args:
            colorize: Formats each line before it is output (e.g. to print it in gray), leaving it as is by default.
            colorize_warning: Formats each warning line instead, so that it stands out from the others.
            output: Outputs each line, printing it to the terminal by default.
        """
        self._colorize = colorize
        self._colorize_warning = colorize_warning
        self._output = output
        self._current_short_title: Optional[str] = None
        self._step_times: list[tuple[str, float]] = []

    def take_step_times(self) -> list[tuple[str, float]]:
        """
        Return the short title and elapsed time of every step ended since the last call, in order, and forget them.

        Returns:
            The (short title, elapsed time in seconds) pair of each step, whether it ended done or failed.
        """
        step_times = self._step_times
        self._step_times = []
        return step_times

    def _write(self, line: str):
        """
        Output a line, formatted.

        Args:
            line: The line to output.
        """
        self._output(self._colorize(line))

    def _on_step_started(self, title: str, short_title: str):
        self._current_short_title = short_title
        self._output("")
        self._write(f"⏵ {title}")

    def _on_step_info(self, label: str, value: str):
        self._write(f" ⎿ {label}: {value}")

    def _on_step_warning(self, message: str):
        self._output(self._colorize_warning(f"⚠ {message}"))

    def _on_step_done(self, elapsed_time: float):
        self._step_times.append((cast(str, self._current_short_title), elapsed_time))
        self._write(f"✓ Done in {elapsed_time:.3f}s")

    def _on_step_failed(self, error: Exception, elapsed_time: float):
        # NB: Falls back on the exception's class name, which is all an exception raised without a message has.
        self._step_times.append((cast(str, self._current_short_title), elapsed_time))
        reason = str(error) or type(error).__name__
        self._write(f"✗ Failed in {elapsed_time:.3f}s: {reason}")
