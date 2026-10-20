# Standard library
from typing import Callable, Optional, cast

# Local libraries
from src.explaining.interacting.interface.cli.colors import bold, gray, green, red, yellow
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

    The title is in bold, the details in gray, the warnings in orange, and the done line in green (red if the step
    failed).

    It also records each step's short title and elapsed time,
    for a summary of where the time went.
    """

    def __init__(self, output: Callable[[str], None] = print, use_colors: bool = True):
        """
        Args:
            output: Outputs each line, printing it to the terminal by default.
            use_colors: Whether to style each line with the ANSI codes of its role, or output it as plain text.
        """
        self._output = output
        self._use_colors = use_colors
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

    def _write(self, line: str, style: Callable[[str], str]):
        """
        Output a line, styled.

        Args:
            line: The line to output.
            style: Styles the line, when colors are used.
        """
        self._output(style(line) if self._use_colors else line)

    def _on_step_started(self, title: str, short_title: str):
        self._current_short_title = short_title
        self._output("")
        self._write(f"⏵ {title}", bold)

    def _on_step_info(self, label: str, value: str):
        self._write(f" ⎿ {label}: {value}", gray)

    def _on_step_warning(self, message: str):
        self._write(f"⚠ {message}", yellow)

    def _on_step_done(self, elapsed_time: float):
        self._step_times.append((cast(str, self._current_short_title), elapsed_time))
        self._write(f"✓ Done in {elapsed_time:.3f}s", green)

    def _on_step_failed(self, error: Exception, elapsed_time: float):
        self._step_times.append((cast(str, self._current_short_title), elapsed_time))
        # NB: Falls back on the exception's class name, which is all an exception raised without a message has.
        reason = str(error) or type(error).__name__
        self._write(f"✗ Failed in {elapsed_time:.3f}s: {reason}", red)
