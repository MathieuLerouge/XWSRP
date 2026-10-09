# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.conflict import SkillConflict
from src.explaining.computing.neighborhood.extractor import ConflictExtractor
from src.explaining.computing.neighborhood.model import NeighborhoodModel
from src.explaining.computing.solver import TransformationModelSolver
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.modeling.employee import Employee


def solve_neighborhood(
        neighborhood: Neighborhood, solving_time_limit: Optional[int] = None
) -> tuple[Optional[NeighborhoodModel], Optional[SkillConflict]]:
    """
    Run the neighborhood computation pipeline over a neighborhood up to the solved model,
    without recognizing it as any question template: decide whether a skill conflict already settles the question,
    otherwise build the MILP and solve it.

    NB: It is what lets a neighborhood outside the question catalogue be answered at all,
    the recognition step being left to the callers that phrase their answer from a template
    (see computing.bridge.result).

    Args:
        neighborhood: The neighborhood the question induced.
        solving_time_limit: The solving time limit in seconds, or None for no limit.

    Returns:
        A pair made of the solved model and the skill conflict blocking the neighborhood:
        (None, the skill conflict) when one blocks it before any model is built, (the solved model, None) otherwise.

    Raises:
        NotImplementedError: if no NeighborhoodModel can be built for the neighborhood.
        InfeasibleModelException: if the model has no feasible solution.
        UnboundedModelException: if the model is unbounded.
        TimeLimitReachedWithSolutionException: if the solving time limit was reached, with an incumbent found.
        TimeLimitReachedWithoutSolutionException: if the solving time limit was reached with no incumbent.
    """
    skill_conflict = ConflictExtractor.extract_from_neighborhood(neighborhood)
    if skill_conflict is not None:
        return None, skill_conflict
    model = NeighborhoodModel(neighborhood)
    if solving_time_limit is not None:
        model.solving_time_limit = solving_time_limit
    TransformationModelSolver.solve_or_raise(model)
    return model, None


def reorder_support_sequences_to_solved_routes(neighborhood: Neighborhood, model: NeighborhoodModel):
    """
    Put the steps of every in-scope employee's support sequence back into the order the solver routed them.

    The model's solution orders each sequence's steps by start time,
    and a feasibility-shortfall task's reported start time is the one its upstream constraints alone imply,
    while the steps after it are timed against the looser value its downstream constraints see.
    As soon as the shortfall is strictly positive those two can cross,
    leaving the sequence in an order the route never had - which is why get_solved_route exists at all.
    The explanation narrates the conflict off this sequence,
    so it is reordered here rather than left for every reader to work around.

    A sequence whose activities are not exactly the solved route's is left alone:
    that is the disconnected-cycle case ConflictExtractor already reports as an unattributable shortfall.

    Args:
        neighborhood: The neighborhood the model was built from, whose scope names the employees to fix.
        model: The solved model, whose solution's sequences are reordered in place.
    """
    if model.feasibility_shortfall == 0:
        return
    for employee in sorted(
            (member for member in neighborhood.scope if isinstance(member, Employee)),
            key=lambda member: member.name
    ):
        sequence = model.solution.get_sequence(employee)
        route = model.get_solved_route(employee)
        steps_by_activity_name = {step.activity.name: step for step in sequence.get_steps(1, sequence.nb_steps - 1)}
        if len(steps_by_activity_name) != len(route) or any(
                activity.name not in steps_by_activity_name for activity in route
        ):
            continue
        for index, activity in enumerate(route):
            sequence[index + 1] = steps_by_activity_name[activity.name]
