# Third-party library
import pytest

# Local libraries
from src.checking.feasibility import check_feasibility
from src.optimization.milp.milpmodel import MILPModel
from src.optimization.milp.solver.solver import SOLVER_GUROBI, SOLVER_HIGHS
from src.reading.instance import extract_instance_from_file

# Global variables
_SMALL_INSTANCE_PATH = "data/evaluation/instances/instance_evaluation_1.xlsx"
_SOLVING_TIME_LIMIT = 15


def solve_small_instance(solver_name: str):
    instance = extract_instance_from_file(_SMALL_INSTANCE_PATH, True, True, True)
    model = MILPModel(instance)
    model.solving_time_limit = _SOLVING_TIME_LIMIT
    model.solve(mute=True, solver_name=solver_name)
    return model


#################
# solve - HIGHS #
#################

def test_solve_with_highs_finds_a_feasible_solution():
    model = solve_small_instance(SOLVER_HIGHS)
    assert model.has_solution
    feasible, checking_text = check_feasibility(model.solution)
    assert feasible, checking_text
    assert model.objective_value < 0


#################
# solve - GUROBI #
#################

def test_solve_with_gurobi_finds_a_feasible_solution():
    gurobipy = pytest.importorskip("gurobipy")
    try:
        model = solve_small_instance(SOLVER_GUROBI)
        assert model.has_solution
        feasible, checking_text = check_feasibility(model.solution)
        assert feasible, checking_text
        assert model.objective_value < 0
    except (gurobipy.GurobiError, RuntimeError) as error:
        pytest.skip(f"gurobipy is installed but not usable: {error}")
