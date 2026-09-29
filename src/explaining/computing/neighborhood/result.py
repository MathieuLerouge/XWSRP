# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.neighborhood.description import NeighborhoodDescriptionBuilder
from src.explaining.computing.neighborhood.extractor import ConflictExtractor
from src.explaining.computing.neighborhood.model import NeighborhoodModel
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.computing.templates.common.solver import TransformationModelSolver
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.templates.recognizer import Recognizer
from src.explaining.question.predefined.question import ContrastiveQuestion
from src.modeling.employee import Employee


def solve_neighborhood_into_transformation_result(
        neighborhood: Neighborhood, solving_time_limit: Optional[int] = None
) -> tuple[ContrastiveQuestion, TransformationResult]:
    """
    Run the neighborhood computation pipeline over a neighborhood, from its operators to a phrasable result:
    decide whether a skill conflict already settles the question,
    otherwise build the MILP and solve it, then describe whichever of the two happened.

    NB: It is what both the tailored-neighborhood route (via Mapper) and the free-text one (via the llm Extractor) run,
    so that the two differ only in how the neighborhood was obtained.

    Args:
        neighborhood: The neighborhood the question induced.
        solving_time_limit: The solving time limit in seconds, or None for no limit.

    Returns:
        A pair made of the recognized question and the result of the transformation it induced,
        ready to be handed together to the explanation layer's create_explanation.

    Raises:
        NeighborhoodError: if the neighborhood is not one the question catalogue induces,
            so that no explanation template exists to phrase an answer from.
        NotImplementedError: if no NeighborhoodModel can be built for the neighborhood.
        InfeasibleModelException: if the model has no feasible solution.
        UnboundedModelException: if the model is unbounded.
        TimeLimitReachedWithSolutionException: if the solving time limit was reached, with an incumbent found.
        TimeLimitReachedWithoutSolutionException: if the solving time limit was reached with no incumbent.
    """
    if ConflictExtractor.extract_from_neighborhood(neighborhood) is not None:
        return build_transformation_result_from_neighborhood(neighborhood, None)
    model = NeighborhoodModel(neighborhood)
    if solving_time_limit is not None:
        model.solving_time_limit = solving_time_limit
    TransformationModelSolver.solve_or_raise(model)
    return build_transformation_result_from_neighborhood(neighborhood, model)


def build_transformation_result_from_neighborhood(
        neighborhood: Neighborhood, model: Optional[NeighborhoodModel] = None
) -> tuple[ContrastiveQuestion, TransformationResult]:
    """
    Build, from a neighborhood and the model solved from it, everything the explanation layer needs.

    This is the neighborhood computation pipeline's counterpart to the tailored pipeline's
    build_transformation_result_from_milp_model.
    The extra step it takes is recovering the question the neighborhood came from:
    the explanation layer phrases an explanation from that question's template,
    which the tailored pipeline is handed and this one has to recognize.

    Pass model=None for a neighborhood blocked by a skill conflict.
    No model is built - every pairing its operators opened being skill-infeasible leaves no arrangement to search -
    so the support solution reported is the given one, unchanged.

    Args:
        neighborhood: The neighborhood the question induced.
        model: The model solved from it, or None when a skill conflict blocked it before any was built.

    Returns:
        A pair made of the recognized question and the result of the transformation it induced,
        ready to be handed together to explanation's create_explanation.

    Raises:
        NeighborhoodError: if the neighborhood is not one the question catalogue induces,
            so that no explanation template exists to phrase an answer from.
        AttributeError: if the given model hasn't been solved yet, or found no feasible solution.
    """
    question = Recognizer.recognize(neighborhood)
    if question is None:
        raise NeighborhoodError(
            "The neighborhood matches no question template, so no explanation can be phrased from it"
        )
    skill_conflict = ConflictExtractor.extract_from_neighborhood(neighborhood)
    if model is None:
        if skill_conflict is None:
            raise NeighborhoodError(
                "A neighborhood no skill conflict blocks needs its solved model to be described"
            )
        descriptions = NeighborhoodDescriptionBuilder.build_for_skill_conflict(question, skill_conflict)
        return question, TransformationResult(neighborhood.solution, skill_conflict, descriptions)
    conflict = skill_conflict if skill_conflict is not None else ConflictExtractor.extract_from_solved_model(model)
    descriptions = NeighborhoodDescriptionBuilder.build_from_solved_model(question, neighborhood, model)
    support_solution = model.solution
    _reorder_support_sequences_to_solved_routes(neighborhood, model)
    if conflict is None:
        support_solution.compute_kpis()
    return question, TransformationResult(support_solution, conflict, descriptions)


def _reorder_support_sequences_to_solved_routes(neighborhood: Neighborhood, model: NeighborhoodModel):
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
