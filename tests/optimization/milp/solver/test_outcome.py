# Standard library
from typing import Optional

# Third-party library
import pytest

# Local library
from src.optimization.milp.solver.outcome import Outcome


def build_outcome(objective_value: Optional[float] = None, mip_gap: Optional[float] = None,
                  is_infeasible: bool = False, is_time_limit: bool = False) -> Outcome:
    """Return the outcome of a solve run in 0.1s, with an incumbent if and only if an objective value is given."""
    return Outcome(
        is_infeasible=is_infeasible, is_unbounded=False, is_time_limit=is_time_limit,
        has_incumbent=objective_value is not None, objective_value=objective_value, mip_gap=mip_gap, run_time=0.1
    )


#############
# as_string #
#############

@pytest.mark.parametrize("outcome,expected_text", [
    (build_outcome(125.0, 0.0), "125 (optimal, 0.100s)"),
    (build_outcome(512.0, 0.023, is_time_limit=True), "512 (time limit reached, gap: 2.30%, 0.100s)"),
    (build_outcome(is_time_limit=True), "no solution (time limit reached, 0.100s)"),
    (build_outcome(is_infeasible=True), "no solution (infeasible, 0.100s)"),
])
def test_an_outcome_is_written_with_its_value_status_gap_and_run_time(outcome, expected_text):
    assert outcome.as_string() == expected_text
