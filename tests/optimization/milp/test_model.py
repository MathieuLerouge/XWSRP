# Third-party library
import pytest

# Local libraries
from src.feasibility.checker import FeasibilityChecker
from src.optimization.milp.model import Model
from src.optimization.milp.solver.solver import SOLVER_GUROBI, SOLVER_HIGHS
from src.importing.instance import extract_instance_from_file

# Global variables
_SMALL_INSTANCE_PATH = "data/evaluation/instances/instance_evaluation_1.xlsx"
_SOLVING_TIME_LIMIT = 15


def solve_small_instance(solver_name: str):
    instance = extract_instance_from_file(_SMALL_INSTANCE_PATH, True, True, True)
    model = Model(instance)
    model.solving_time_limit = _SOLVING_TIME_LIMIT
    model.solve(mute=True, solver_name=solver_name)
    return model


#################
# Solve - HIGHS #
#################

def test_solve_with_highs_finds_a_feasible_solution():
    model = solve_small_instance(SOLVER_HIGHS)
    assert model.has_solution
    checker = FeasibilityChecker(model.solution)
    assert checker.is_feasible(), checker.report()
    assert model.objective_value < 0


##################
# Solve - GUROBI #
##################

def test_solve_with_gurobi_finds_a_feasible_solution():
    gurobipy = pytest.importorskip("gurobipy")
    try:
        model = solve_small_instance(SOLVER_GUROBI)
        assert model.has_solution
        checker = FeasibilityChecker(model.solution)
        assert checker.is_feasible(), checker.report()
        assert model.objective_value < 0
    except (gurobipy.GurobiError, RuntimeError) as error:
        pytest.skip(f"gurobipy is installed but not usable: {error}")


##############
# Statistics #
##############

def test_statistics_describe_the_built_model_before_solving():
    instance = extract_instance_from_file(_SMALL_INSTANCE_PATH, True, True, True)
    model = Model(instance)
    statistics = model.statistics
    assert statistics.nb_variables == model._model.nvariables()
    assert statistics.nb_constraints == model._model.nconstraints()
    assert statistics.nb_objectives == 1
    assert statistics.build_time > 0
    assert statistics.solve_time is None


def test_statistics_group_constraints_by_family():
    instance = extract_instance_from_file(_SMALL_INSTANCE_PATH, True, True, True)
    model = Model(instance)
    nb_constraints_by_family = model.statistics.nb_constraints_by_family
    assert nb_constraints_by_family["SkillLevelConstraint"] == len(model._data.tasks_indices)
    assert model.statistics.count_constraints_in_families_starting_with("SkillLevel") == len(
        model._data.tasks_indices
    )


def test_statistics_record_solve_time_once_solved():
    model = solve_small_instance(SOLVER_HIGHS)
    assert model.statistics.solve_time > 0
