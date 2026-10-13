# Local libraries
from src.explaining.computing.neighborhood.model import NEIGHBORHOOD_CONSTRAINT_FAMILY_PREFIX, NeighborhoodModel
from src.explaining.neighborhood.bridge.mapper import Mapper
from src.explaining.question.predefined.bank import WHY_NOT_INS_1
from src.explaining.question.predefined.question import ContrastiveQuestion
from tests.explaining.computing.helpers import build_austria_solution


def build_neighborhood_model() -> NeighborhoodModel:
    """Build, without solving it, the NeighborhoodModel of (Ins,1) with Ellen performing T27 just after T17."""
    question = ContrastiveQuestion(build_austria_solution(), WHY_NOT_INS_1, ["Ellen", "T27", "T17"])
    return NeighborhoodModel(Mapper.map(question))


##############
# Statistics #
##############

def test_statistics_count_each_lexicographic_objective():
    assert build_neighborhood_model().statistics.nb_objectives == 3


def test_statistics_count_the_variables_pinned_outside_the_scope():
    assert build_neighborhood_model().statistics.nb_fixed_variables > 0


def test_statistics_count_the_neighborhood_constraints():
    statistics = build_neighborhood_model().statistics
    nb_neighborhood_constraints = statistics.count_constraints_in_families_starting_with(
        NEIGHBORHOOD_CONSTRAINT_FAMILY_PREFIX
    )
    assert 0 < nb_neighborhood_constraints < statistics.nb_constraints


def test_statistics_leave_out_the_constraints_the_lexicographic_solve_adds():
    model = build_neighborhood_model()
    model.solve(mute=True)
    # NB: One freezing constraint per objective but the last.
    assert model._model.nconstraints() == model.statistics.nb_constraints + 2
    assert model.statistics.solve_time > 0
