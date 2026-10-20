# Third-party library
import pytest

# Local libraries
from src.optimization.milp.model import Model
from src.optimization.milp.solver.solver import SOLVER_GUROBI, SOLVER_HIGHS
from src.optimization.milp.subproblems.sequencereorderingmodel import SequenceReorderingModel
from src.importing.instance import extract_instance_from_file

# Global variables
_SMALL_INSTANCE_PATH = "data/evaluation/instances/instance_evaluation_1.xlsx"
_SOLVING_TIME_LIMIT = 15


def solved_sequence():
    instance = extract_instance_from_file(_SMALL_INSTANCE_PATH, True, True, True)
    model = Model(instance)
    model.solving_time_limit = _SOLVING_TIME_LIMIT
    model.solve(mute=True, solver_name=SOLVER_HIGHS)
    solution = model.solution
    solution.compute_kpis()
    return solution.get_sequence(instance.employees[0])


###################################
# SequenceReorderingModel - solve #
###################################

def test_sequence_reordering_solve_with_highs_finds_a_valid_sequence():
    model = SequenceReorderingModel(solved_sequence())
    model.solve(mute=True, solver_name=SOLVER_HIGHS)
    assert model.has_solution_sequence


def test_sequence_model_statistics_describe_the_built_model_then_its_solve():
    model = SequenceReorderingModel(solved_sequence())
    statistics = model.statistics
    assert statistics.nb_variables == model._model.nvariables()
    assert statistics.nb_constraints == model._model.nconstraints()
    assert statistics.nb_objectives == 1
    assert statistics.solve_time is None and statistics.solver_name is None
    model.solve(mute=True, solver_name=SOLVER_HIGHS)
    assert statistics.solve_time > 0 and statistics.solver_name == SOLVER_HIGHS


def test_sequence_reordering_solve_with_gurobi_finds_a_valid_sequence():
    gurobipy = pytest.importorskip("gurobipy")
    model = SequenceReorderingModel(solved_sequence())
    try:
        model.solve(mute=True, solver_name=SOLVER_GUROBI)
    except (gurobipy.GurobiError, RuntimeError) as error:
        pytest.skip(f"gurobipy is installed but not usable: {error}")
    assert model.has_solution_sequence
