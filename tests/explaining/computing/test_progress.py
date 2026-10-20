# Standard library
from typing import Callable

# Local libraries
from src.explaining.computing.progress import report_model_size, report_solve
from src.optimization.milp.solver.solver import SOLVER_HIGHS
from src.optimization.milp.statistics import MilpStatistics
from src.utils.progress import ProgressStep
from tests.optimization.milp.solver.test_outcome import build_outcome


def report_into_lists(report: Callable[[ProgressStep], None]) -> tuple[list[tuple[str, str]], list[str]]:
    """Run the given report against a step collecting its details and warnings, and return both."""
    reported_details: list[tuple[str, str]] = []
    reported_warnings: list[str] = []
    report(ProgressStep(lambda label, value: reported_details.append((label, value)), reported_warnings.append))
    return reported_details, reported_warnings


def test_the_building_step_splits_the_constraints_only_given_a_family_prefix():
    statistics = MilpStatistics(1, 0, 0, 0, {"FlowConstraint": 2, "NeighborhoodFreeze": 1}, 3, 0.1)
    details, _ = report_into_lists(lambda step: report_model_size(step, statistics))
    assert ("Constraints", "3") in details
    details, _ = report_into_lists(lambda step: report_model_size(step, statistics, "Neighborhood"))
    assert ("Constraints", "3 (base: 2, neighborhood: 1)") in details
    assert ("NeighborhoodFreeze", "1") in details


def test_the_solving_step_reports_each_level_solved_and_warns_of_the_unsolved_ones():
    statistics = MilpStatistics(
        1, 0, 0, 0, {"FlowConstraint": 1}, 3, 0.1, solver_name=SOLVER_HIGHS, solve_time=0.1,
        lexicographic_outcomes=[
            ("feasibility shortfall", build_outcome(0.0, 0.0)),
            ("working duration", build_outcome(is_time_limit=True))
        ]
    )
    reported_details, reported_warnings = report_into_lists(lambda step: report_solve(step, statistics))
    assert reported_details == [
        ("Solver", SOLVER_HIGHS),
        ("Level 1 (feasibility shortfall)", "0 (optimal, 0.100s)"),
        ("Level 2 (working duration)", "no solution (time limit reached, 0.100s)")
    ]
    assert reported_warnings == ["1 lower-priority level(s) not solved"]
