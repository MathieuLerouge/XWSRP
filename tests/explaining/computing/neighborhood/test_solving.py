# Local libraries
from src.explaining.computing.neighborhood.solving import _report_solve
from src.optimization.milp.solver.solver import SOLVER_HIGHS
from src.optimization.milp.statistics import MilpStatistics
from src.utils.progress import ProgressStep
from tests.optimization.milp.solver.test_outcome import build_outcome


def test_the_solving_step_reports_each_level_solved_and_counts_the_unsolved_ones():
    statistics = MilpStatistics(
        1, 0, 0, 0, {"FlowConstraint": 1}, 3, 0.1, solver_name=SOLVER_HIGHS, solve_time=0.1,
        lexicographic_outcomes=[
            ("feasibility shortfall", build_outcome(0.0, 0.0)),
            ("working duration", build_outcome(is_time_limit=True))
        ]
    )
    reported_details: list[tuple[str, str]] = []
    _report_solve(ProgressStep(lambda label, value: reported_details.append((label, value))), statistics)
    assert reported_details == [
        ("Solver", SOLVER_HIGHS),
        ("Level 1 (feasibility shortfall)", "0 (optimal, 0.100s)"),
        ("Level 2 (working duration)", "no solution (time limit reached, 0.100s)"),
        ("Unsolved levels", "1")
    ]
