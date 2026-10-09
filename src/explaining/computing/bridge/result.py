# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.bridge.description import NeighborhoodDescriptionBuilder
from src.explaining.computing.neighborhood.extractor import ConflictExtractor
from src.explaining.computing.neighborhood.model import NeighborhoodModel
from src.explaining.computing.neighborhood.solving import (
    reorder_support_sequences_to_solved_routes, solve_neighborhood
)
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.templates.recognizer import Recognizer
from src.explaining.question.predefined.question import ContrastiveQuestion


def solve_neighborhood_into_transformation_result(
        neighborhood: Neighborhood, solving_time_limit: Optional[int] = None
) -> tuple[ContrastiveQuestion, TransformationResult]:
    """
    Answer a neighborhood with the neighborhood pipeline, in the form the template-based explanation layer reads:
    solve it (see solve_neighborhood), then recognize the question template it stands for
    and describe whichever of a skill conflict or a solved model settled it.

    NB: It is the bridge both the tailored-neighborhood route (via Mapper) and, until it is answered
    without any template, the free-text one (via the llm Extractor) run,
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
    model, _ = solve_neighborhood(neighborhood, solving_time_limit)
    return build_transformation_result_from_neighborhood(neighborhood, model)


def build_transformation_result_from_neighborhood(
        neighborhood: Neighborhood, model: Optional[NeighborhoodModel] = None
) -> tuple[ContrastiveQuestion, TransformationResult]:
    """
    Build, from a neighborhood and the model solved from it, everything the explanation layer needs.

    This is the bridge's counterpart to the tailored pipeline's build_transformation_result_from_milp_model.
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
    reorder_support_sequences_to_solved_routes(neighborhood, model)
    if conflict is None:
        support_solution.compute_kpis()
    return question, TransformationResult(support_solution, conflict, descriptions)
