# Standard library
from typing import Optional, TypeVar

# Local libraries
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import (
    SequenceReordering, TaskDeletion, TaskInsertion, TaskRepositioning
)
from src.explaining.neighborhood.primitive import Primitive
from src.explaining.neighborhood.restriction import (
    ForbiddenBackwardSubsequence, ForbiddenSequence, ImmediatePrecedence, Precedence, PrecedenceChain
)

# Global variables
INSERTION_FAMILY = "(Ins,*)"
SWAP_FAMILY = "(Swp,*)"
REORDERING_FAMILY = "(Ord,*)"

# The kind of primitive _select is asked for, so that it hands back that kind rather than a bare Primitive.
SelectedPrimitive = TypeVar("SelectedPrimitive", bound=Primitive)



#############################
# TemplateComplianceChecker #
#############################

class TemplateComplianceChecker:
    """
    Stateless collection of static methods telling whether a Neighborhood is one of the shapes that
    the tailored per-template pipeline (src/explaining/computing/templates) handles
    - that is, whether it is in the image of Mapper.map over the question catalogue.

    Answers are given by family rather than by template id:
    (Swp,2a) and (Swp,2b) differ only in whether the inserted candidate tasks are performed,
    which cannot be told apart without reading the solution.

    NB: This predicate is strictly narrower than "a Neighborhood NeighborhoodModel can solve".
    """

    @staticmethod
    def match(neighborhood: Neighborhood) -> Optional[str]:
        """
        Return the question family whose shape the given neighborhood has, or None if it has none of them.

        Args:
            neighborhood: The neighborhood to match.

        Returns:
            INSERTION_FAMILY, SWAP_FAMILY or REORDERING_FAMILY,
            or None if the neighborhood is not one the tailored pipeline's question catalogue produces.
        """
        for matches_shape, family in _SHAPES:
            if matches_shape(neighborhood):
                return family
        return None

    @staticmethod
    def is_compliant(neighborhood: Neighborhood) -> bool:
        """
        Return whether the given neighborhood is one the tailored pipeline's question catalogue produces.

        Args:
            neighborhood: The neighborhood to check.

        Returns:
            Whether it has the shape of one of the catalogue's question families.
        """
        return TemplateComplianceChecker.match(neighborhood) is not None


###########
# Helpers #
###########


def _select(primitives: list[Primitive], primitive_type: type[SelectedPrimitive]) -> list[SelectedPrimitive]:
    """
    Return the given primitives that are instances of the given type.

    Args:
        primitives: The operators or restrictions to filter.
        primitive_type: The type to keep.

    Returns:
        The kept primitives, in their original order, typed as that same type so that callers can read
        their own fields off them.
    """
    return [primitive for primitive in primitives if isinstance(primitive, primitive_type)]


def _are_all_of_types(primitives: list[Primitive], primitive_types: tuple[type[Primitive], ...]) -> bool:
    """
    Return whether every one of the given primitives is an instance of one of the given types.

    Args:
        primitives: The operators or restrictions to check.
        primitive_types: The types allowed.

    Returns:
        Whether every primitive is allowed.
    """
    return all(isinstance(primitive, primitive_types) for primitive in primitives)


def _has_template_candidate_sets(insertion: TaskInsertion) -> bool:
    """
    Return whether a TaskInsertion's candidate sets have a shape some template produces:
    both non-empty, and never several candidate employees together with several candidate tasks.

    Args:
        insertion: The TaskInsertion to check.

    Returns:
        Whether its candidate sets have a template-produced shape.
    """
    nb_candidate_employees = len(insertion.candidate_employees)
    nb_candidate_tasks = len(insertion.candidate_tasks)
    if nb_candidate_employees == 0 or nb_candidate_tasks == 0:
        return False
    return nb_candidate_employees == 1 or nb_candidate_tasks == 1


def _matches_insertion_shape(neighborhood: Neighborhood) -> bool:
    """
    Return whether the neighborhood has the shape the (Ins,*) templates produce:
    a lone TaskInsertion, the rest of every targeted employee's sequence kept in its original order,
    and optionally one pinned insertion point.

    Args:
        neighborhood: The neighborhood to check.

    Returns:
        Whether it has the (Ins,*) shape.
    """
    operators = neighborhood.operators
    if len(operators) != 1:
        return False
    insertion = operators[0]
    if not isinstance(insertion, TaskInsertion) or not _has_template_candidate_sets(insertion):
        return False
    restrictions = neighborhood.restrictions
    if not _are_all_of_types(restrictions, (PrecedenceChain, ImmediatePrecedence)):
        return False
    if len(_select(restrictions, PrecedenceChain)) > len(insertion.candidate_employees):
        return False
    immediate_precedences = _select(restrictions, ImmediatePrecedence)
    if len(immediate_precedences) > 1:
        return False
    if immediate_precedences:
        # (Ins,1) pins where one specific task goes, so it only means anything for one specific pairing.
        if len(insertion.candidate_employees) != 1 or len(insertion.candidate_tasks) != 1:
            return False
        if immediate_precedences[0].successor not in insertion.candidate_tasks:
            return False
    return True


def _matches_swap_shape(neighborhood: Neighborhood) -> bool:
    """
    Return whether the neighborhood has the shape the (Swp,*) templates produce:
    one TaskDeletion and one TaskInsertion over the same employees, removing exactly one task and adding exactly one.

    Args:
        neighborhood: The neighborhood to check.

    Returns:
        Whether it has the (Swp,*) shape.
    """
    operators = neighborhood.operators
    if len(operators) != 2:
        return False
    deletions = _select(operators, TaskDeletion)
    insertions = _select(operators, TaskInsertion)
    if len(deletions) != 1 or len(insertions) != 1:
        return False
    deletion, insertion = deletions[0], insertions[0]
    if deletion.min_nb_removals != 1 or deletion.max_nb_removals != 1:
        return False
    if len(deletion.candidate_tasks) == 0 or deletion.freed_employees != insertion.candidate_employees:
        return False
    if not _has_template_candidate_sets(insertion):
        return False
    restrictions = neighborhood.restrictions
    if not _are_all_of_types(restrictions, (PrecedenceChain, ForbiddenBackwardSubsequence)):
        return False
    precedence_chains = _select(restrictions, PrecedenceChain)
    forbidden_backward_subsequences = _select(restrictions, ForbiddenBackwardSubsequence)
    # NB: A template fixes the surviving tasks' order with one mechanism or the other, never with both.
    if precedence_chains and forbidden_backward_subsequences:
        return False
    if precedence_chains:
        # (Swp,1): the outgoing task is named, so it is the one left out of the order kept fixed.
        if len(precedence_chains) != 1 or len(deletion.candidate_tasks) != 1:
            return False
        outgoing_task = next(iter(deletion.candidate_tasks))
        if outgoing_task in precedence_chains[0].tasks:
            return False
    if len(forbidden_backward_subsequences) > len(deletion.freed_employees):
        return False
    return all(
        restriction.employee in deletion.freed_employees for restriction in forbidden_backward_subsequences
    )


def _matches_repositioning_shape(neighborhood: Neighborhood) -> bool:
    """
    Return whether the neighborhood has the shape the (Ord,1*)/(Ord,2*) templates produce:
    a lone TaskRepositioning, the rest of the employee's order kept fixed,
    and exactly one further restriction forcing the target task somewhere it is not already.

    Args:
        neighborhood: The neighborhood to check.

    Returns:
        Whether it has the (Ord,1*)/(Ord,2*) shape.
    """
    operators = neighborhood.operators
    if len(operators) != 1:
        return False
    repositioning = operators[0]
    if not isinstance(repositioning, TaskRepositioning):
        return False
    restrictions = neighborhood.restrictions
    if not _are_all_of_types(
            restrictions, (PrecedenceChain, ImmediatePrecedence, Precedence, ForbiddenSequence)):
        return False
    precedence_chains = _select(restrictions, PrecedenceChain)
    if len(precedence_chains) != 1:
        return False
    # The repositioned task is the one task whose place is up for grabs, so it is left out of the chain
    # keeping every other task of the employee's sequence where it was.
    if repositioning.target_task in precedence_chains[0].tasks:
        return False
    immediate_precedences = _select(restrictions, ImmediatePrecedence)
    precedences = _select(restrictions, Precedence)
    forbidden_sequences = _select(restrictions, ForbiddenSequence)
    if len(immediate_precedences) + len(precedences) + len(forbidden_sequences) != 1:
        return False
    if immediate_precedences:
        immediate_precedence = immediate_precedences[0]
        return repositioning.target_task in (immediate_precedence.predecessor, immediate_precedence.successor)
    if precedences:
        precedence = precedences[0]
        return repositioning.target_task in (precedence.predecessor, precedence.successor)
    forbidden_sequence = forbidden_sequences[0]
    return (forbidden_sequence.employee == repositioning.employee
            and repositioning.target_task in forbidden_sequence.activities)


def _matches_reordering_shape(neighborhood: Neighborhood) -> bool:
    """
    Return whether the neighborhood has the shape the (Ord,3) template produces: a lone SequenceReordering,
    with the employee's own original sequence forbidden so the solver cannot answer with it unchanged.

    Args:
        neighborhood: The neighborhood to check.

    Returns:
        Whether it has the (Ord,3) shape.
    """
    operators = neighborhood.operators
    if len(operators) != 1:
        return False
    reordering = operators[0]
    if not isinstance(reordering, SequenceReordering):
        return False
    restrictions = neighborhood.restrictions
    if len(restrictions) != 1:
        return False
    forbidden_sequence = restrictions[0]
    if not isinstance(forbidden_sequence, ForbiddenSequence):
        return False
    return forbidden_sequence.employee == reordering.employee


# The shapes the tailored pipeline's question catalogue produces, each paired with the family it belongs to.
_SHAPES = (
    (_matches_insertion_shape, INSERTION_FAMILY),
    (_matches_swap_shape, SWAP_FAMILY),
    (_matches_repositioning_shape, REORDERING_FAMILY),
    (_matches_reordering_shape, REORDERING_FAMILY),
)