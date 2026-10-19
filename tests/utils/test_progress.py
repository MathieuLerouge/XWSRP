# Third-party library
import pytest

# Local library
from src.utils.progress import ProgressReporter


#####################
# RecordingReporter #
#####################

class RecordingReporter(ProgressReporter):
    """Records every hook call, in order, instead of reporting anywhere."""

    def __init__(self):
        """Start with no call recorded."""
        self.calls: list[tuple] = []

    def _on_step_started(self, title: str):
        self.calls.append(("started", title))

    def _on_step_info(self, label: str, value: str):
        self.calls.append(("info", label, value))

    def _on_step_warning(self, message: str):
        self.calls.append(("warning", message))

    def _on_step_done(self, elapsed_time: float):
        self.calls.append(("done",))

    def _on_step_failed(self, error: Exception, elapsed_time: float):
        self.calls.append(("failed", error))


def test_a_step_reports_its_start_its_details_and_its_end_in_order():
    reporter = RecordingReporter()
    with reporter.step("Building") as step:
        step.info("Nb variables", 42)
    assert reporter.calls == [("started", "Building"), ("info", "Nb variables", "42"), ("done",)]


def test_a_warning_is_reported_within_its_step_without_making_it_fail():
    reporter = RecordingReporter()
    with reporter.step("Solving") as step:
        step.warning("1 lower-priority level(s) not solved")
    assert reporter.calls == [("started", "Solving"), ("warning", "1 lower-priority level(s) not solved"), ("done",)]


def test_a_step_that_raises_is_reported_as_failed_and_raises_again():
    reporter = RecordingReporter()
    error = ValueError("no solution")
    with pytest.raises(ValueError, match="no solution"):
        with reporter.step("Solving"):
            raise error
    assert reporter.calls == [("started", "Solving"), ("failed", error)]


def test_the_base_reporter_reports_nothing_but_still_raises():
    with ProgressReporter().step("Solving") as step:
        step.info("Solver", "highs")
        step.warning("1 lower-priority level(s) not solved")
    with pytest.raises(ValueError):
        with ProgressReporter().step("Solving"):
            raise ValueError()
