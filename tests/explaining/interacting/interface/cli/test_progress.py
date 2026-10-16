# Third-party library
import pytest

# Local library
from src.explaining.interacting.interface.cli.progress import CLIProgressReporter


def build_reporter_writing_into(lines: list[str]) -> CLIProgressReporter:
    """Return a reporter appending each line it outputs to the given list, wrapped in brackets as its colorizing."""
    return CLIProgressReporter(colorize=lambda line: f"[{line}]", output=lines.append)


def test_a_step_is_printed_as_a_title_its_details_and_a_done_line():
    lines: list[str] = []
    with build_reporter_writing_into(lines).step("Extracting the neighborhood") as step:
        step.info("Scope", "Ellen's sequence and T2")
    assert lines[:2] == ["[⏵ Extracting the neighborhood]", "[ ⎿ Scope: Ellen's sequence and T2]"]
    assert lines[2].startswith("[✓ Done in ") and lines[2].endswith("s]")
    assert lines[3] == "", "A blank line, left uncolorized, separates a step from the next one"


def test_a_failed_step_is_printed_with_its_reason():
    lines: list[str] = []
    with pytest.raises(ValueError):
        with build_reporter_writing_into(lines).step("Solving"):
            raise ValueError("the model is infeasible")
    assert lines[1].startswith("[✗ Failed in ") and lines[1].endswith("s: the model is infeasible]")


def test_a_failed_step_with_no_message_is_printed_with_its_exception_name():
    lines: list[str] = []
    with pytest.raises(ValueError):
        with build_reporter_writing_into(lines).step("Solving"):
            raise ValueError()
    assert lines[1].endswith("s: ValueError]")
