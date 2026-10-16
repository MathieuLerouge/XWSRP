# Standard library
from typing import Callable

# Local library
from src.utils.progress import ProgressReporter


#######################
# CLIProgressReporter #
#######################

class CLIProgressReporter(ProgressReporter):
    """
    Prints the progress of a computation to the terminal, one block of lines per step:

    ⏵ <title>
     ⎿ <label>: <value>
    ✓ Done in <elapsed time>s
    """

    def __init__(self, colorize: Callable[[str], str] = str, output: Callable[[str], None] = print):
        """
        Args:
            colorize: Formats each line before it is output (e.g. to print it in gray), leaving it as is by default.
            output: Outputs each line, printing it to the terminal by default.
        """
        self._colorize = colorize
        self._output = output

    def _write(self, line: str):
        """
        Output a line, formatted.

        Args:
            line: The line to output.
        """
        self._output(self._colorize(line))

    def _on_step_started(self, title: str):
        self._write(f"⏵ {title}")

    def _on_step_info(self, label: str, value: str):
        self._write(f" ⎿ {label}: {value}")

    def _on_step_done(self, elapsed_time: float):
        self._write(f"✓ Done in {elapsed_time:.3f}s")
        self._output("")

    def _on_step_failed(self, error: Exception, elapsed_time: float):
        # NB: Falls back on the exception's class name, which is all an exception raised without a message has.
        reason = str(error) or type(error).__name__
        self._write(f"✗ Failed in {elapsed_time:.3f}s: {reason}")
        self._output("")
