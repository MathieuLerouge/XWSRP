# Third-party library
import pytest

# Local libraries
from src.explaining.interacting.interface.cli.colors import bold, gray, green, red, yellow
from src.explaining.interacting.interface.cli.progress import CLIProgressReporter


def build_reporter_writing_into(lines: list[str]) -> CLIProgressReporter:
    """Return a reporter appending each line it outputs to the given list, as plain text."""
    return CLIProgressReporter(output=lines.append, use_colors=False)


def test_a_step_is_printed_as_a_title_its_details_and_a_done_line():
    lines: list[str] = []
    with build_reporter_writing_into(lines).step("Extracting the neighborhood") as step:
        step.info("Scope", "Ellen's sequence and T2")
    assert lines[0] == "", "A blank line separates a step from whatever was output before it"
    assert lines[1:3] == ["⏵ Extracting the neighborhood", " ⎿ Scope: Ellen's sequence and T2"]
    assert lines[3].startswith("✓ Done in ") and lines[3].endswith("s")
    assert len(lines) == 4


def test_each_line_is_styled_by_its_role():
    lines: list[str] = []
    reporter = CLIProgressReporter(output=lines.append)
    with reporter.step("Solving") as step:
        step.info("Solver", "highs")
        step.warning("1 lower-priority level(s) not solved")
    with pytest.raises(ValueError):
        with reporter.step("Solving"):
            raise ValueError("the model is infeasible")
    assert lines[1] == bold("⏵ Solving")
    assert lines[2] == gray(" ⎿ Solver: highs")
    assert lines[3] == yellow("⚠ 1 lower-priority level(s) not solved")
    assert lines[4].startswith(green("✓ Done in ")[:-len("\033[0m")])
    assert lines[-1].startswith(red("✗ Failed in ")[:-len("\033[0m")])
    assert lines[0] == lines[5] == "", "The blank lines between steps are left unstyled"


def test_the_time_of_every_ended_step_is_recorded_until_taken():
    reporter = CLIProgressReporter(output=lambda line: None)
    with reporter.step("Building the NeighborhoodModel"):
        pass
    with pytest.raises(ValueError):
        with reporter.step("Solving the NeighborhoodModel", short_title="solve"):
            raise ValueError()
    assert [short_title for short_title, _ in reporter.take_step_times()] == ["building", "solve"]
    assert reporter.take_step_times() == [], "Taking the step times forgets them"


def test_a_failed_step_is_printed_with_its_reason():
    lines: list[str] = []
    with pytest.raises(ValueError):
        with build_reporter_writing_into(lines).step("Solving"):
            raise ValueError("the model is infeasible")
    assert lines[2].startswith("✗ Failed in ") and lines[2].endswith("s: the model is infeasible")


def test_a_failed_step_with_no_message_is_printed_with_its_exception_name():
    lines: list[str] = []
    with pytest.raises(ValueError):
        with build_reporter_writing_into(lines).step("Solving"):
            raise ValueError()
    assert lines[2].endswith("s: ValueError")
