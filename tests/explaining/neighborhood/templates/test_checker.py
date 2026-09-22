# Third-party library
import pytest

# Local libraries
from src.explaining.computing.exceptions import ImpossibleTransformationException
from src.explaining.computing.model import NeighborhoodModel
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import (
    SequenceReordering, TaskDeletion, TaskInsertion, TaskRepositioning
)
from src.explaining.neighborhood.restriction import (
    ForbiddenBackwardSubsequence, ForbiddenSequence, ImmediatePrecedence, Precedence, PrecedenceChain
)
from src.explaining.neighborhood.templates.checker import (
    INSERTION_FAMILY, REORDERING_FAMILY, SWAP_FAMILY, TemplateComplianceChecker
)
from src.explaining.neighborhood.templates.mapper import Mapper
from src.explaining.questioning.question import ContrastiveQuestion
from src.explaining.questioning.questions_templates_bank import (
    QUESTIONS_TEMPLATES, WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)
from tests.explaining.neighborhood.helpers import build_solution_with_task_performances
from tests.modeling.helpers import build_instance

# Global variables
_EXPECTED_FAMILY_BY_TEMPLATE_ID = {
    WHY_NOT_INS_1: INSERTION_FAMILY,
    WHY_NOT_INS_2A: INSERTION_FAMILY,
    WHY_NOT_INS_2B: INSERTION_FAMILY,
    WHY_NOT_INS_2C: INSERTION_FAMILY,
    WHY_NOT_INS_3: INSERTION_FAMILY,
    WHY_NOT_SWP_1: SWAP_FAMILY,
    WHY_NOT_SWP_2A: SWAP_FAMILY,
    WHY_NOT_SWP_2B: SWAP_FAMILY,
    WHY_NOT_SWP_2C: SWAP_FAMILY,
    WHY_NOT_SWP_3: SWAP_FAMILY,
    WHY_NOT_ORD_LAT_1: REORDERING_FAMILY,
    WHY_NOT_ORD_EAR_1: REORDERING_FAMILY,
    WHY_NOT_ORD_LAT_2: REORDERING_FAMILY,
    WHY_NOT_ORD_EAR_2: REORDERING_FAMILY,
    WHY_NOT_ORD_2: REORDERING_FAMILY,
    WHY_NOT_ORD_3: REORDERING_FAMILY,
}
_MAX_SAMPLES_PER_TEMPLATE = 6


@pytest.fixture(scope="module")
def instance():
    return build_instance()


@pytest.fixture(scope="module")
def solution(instance):
    # Valentin performs T1, T2, T3, T4 in order; Ambre performs T6, T7 in order;
    # T5, T8-T14 are left non-performed.
    return build_solution_with_task_performances(instance, "solution", {
        "T1": ("Valentin", 480), "T2": ("Valentin", 560), "T3": ("Valentin", 640), "T4": ("Valentin", 720),
        "T6": ("Ambre", 480), "T7": ("Ambre", 560),
    })


def build_mapped_neighborhoods(solution, template_id: str, max_samples: int = _MAX_SAMPLES_PER_TEMPLATE):
    """
    Build the neighborhoods Mapper induces for the given template, over up to max_samples of its valid
    field-value combinations.

    Args:
        solution: The solution the questions are asked about.
        template_id: The identifier of the question template to map.
        max_samples: The maximum number of field-value combinations to map.

    Returns:
        The mapped neighborhoods, which may be fewer than max_samples: a combination whose neighborhood
        cannot be built at all (an impossible transformation, or one NeighborhoodModel does not support) is
        skipped, since Mapper never returns one for it.
    """
    solution.compute_kpis()
    all_fields_values = QUESTIONS_TEMPLATES[template_id].compute_all_fields_valid_values(solution)
    neighborhoods = []
    for fields_values in all_fields_values[:max_samples]:
        try:
            neighborhoods.append(Mapper.map(ContrastiveQuestion(solution, template_id, fields_values)))
        except (ImpossibleTransformationException, NeighborhoodError):
            continue
    return neighborhoods


##############################################
# Every neighborhood Mapper builds is matched #
##############################################

@pytest.mark.parametrize("template_id", list(_EXPECTED_FAMILY_BY_TEMPLATE_ID))
def test_every_mapped_neighborhood_matches_its_own_family(solution, template_id):
    """
    Every neighborhood Mapper induces for a template is matched, and matched as that template's own family.

    This is what makes "the shapes the checker accepts are the shapes the tailored pipeline produces" an
    executable claim rather than a comment: it fails the day either Mapper or the checker drifts.
    """
    neighborhoods = build_mapped_neighborhoods(solution, template_id)
    assert len(neighborhoods) > 0, f"No neighborhood could be built for template {template_id}"

    for neighborhood in neighborhoods:
        assert TemplateComplianceChecker.match(neighborhood) == _EXPECTED_FAMILY_BY_TEMPLATE_ID[template_id]
        assert TemplateComplianceChecker.is_compliant(neighborhood)


###########################################################
# Shapes NeighborhoodModel accepts but no template produces #
###########################################################

def test_deletion_paired_with_repositioning_is_not_template_compliant(solution, instance):
    """
    A TaskDeletion paired with a TaskRepositioning is solvable but not template-shaped: only the (Swp,*)
    family pairs a deletion, and only ever with a TaskInsertion.
    """
    employee = instance.get_employee_by_name("Valentin")
    repositioned_task = instance.get_task_by_name("T1")
    deleted_task = instance.get_task_by_name("T2")
    neighborhood = Neighborhood(
        solution,
        [TaskRepositioning(employee, repositioned_task),
         TaskDeletion(frozenset({employee}), frozenset({deleted_task}))],
        [PrecedenceChain([instance.get_task_by_name("T3"), instance.get_task_by_name("T4")]),
         ImmediatePrecedence(instance.get_task_by_name("T3"), repositioned_task)]
    )

    NeighborhoodModel(neighborhood)

    assert TemplateComplianceChecker.match(neighborhood) is None


def test_insertion_open_on_both_sides_is_not_template_compliant(solution, instance):
    """
    A TaskInsertion with several candidate employees and several candidate tasks is solvable but not
    template-shaped: every template names one side of the pairing and leaves only the other open.
    """
    neighborhood = Neighborhood(
        solution,
        [TaskInsertion(frozenset(instance.employees),
                       frozenset({instance.get_task_by_name("T5"), instance.get_task_by_name("T8")}))],
        []
    )

    NeighborhoodModel(neighborhood)

    assert TemplateComplianceChecker.match(neighborhood) is None


###################################
# Shapes that are simply malformed #
###################################

def test_repositioning_whose_precedence_chain_still_pins_its_target_task_is_rejected(solution, instance):
    """
    The repositioned task must be left out of the chain keeping the rest of the sequence in place, or the
    restriction pins the very task the operator is meant to move.
    """
    employee = instance.get_employee_by_name("Valentin")
    target_task = instance.get_task_by_name("T1")
    employee_tasks = [instance.get_task_by_name(name) for name in ("T1", "T2", "T3", "T4")]
    neighborhood = Neighborhood(
        solution,
        [TaskRepositioning(employee, target_task)],
        [PrecedenceChain(employee_tasks), ImmediatePrecedence(instance.get_task_by_name("T3"), target_task)]
    )

    assert TemplateComplianceChecker.match(neighborhood) is None


def test_repositioning_without_anything_forcing_a_move_is_rejected(solution, instance):
    """
    A lone PrecedenceChain leaves the solver free to answer with the given sequence unchanged, so no
    template ever produces a TaskRepositioning without a restriction pinning a new position.
    """
    employee = instance.get_employee_by_name("Valentin")
    target_task = instance.get_task_by_name("T1")
    neighborhood = Neighborhood(
        solution,
        [TaskRepositioning(employee, target_task)],
        [PrecedenceChain([instance.get_task_by_name(name) for name in ("T2", "T3", "T4")])]
    )

    assert TemplateComplianceChecker.match(neighborhood) is None


def test_reordering_without_a_forbidden_sequence_is_rejected(solution, instance):
    """
    (Ord,3) always forbids the employee's own original sequence, otherwise the solver may answer with it
    unchanged.
    """
    neighborhood = Neighborhood(
        solution, [SequenceReordering(instance.get_employee_by_name("Valentin"))], [Precedence(
            instance.get_task_by_name("T1"), instance.get_task_by_name("T2"))]
    )

    assert TemplateComplianceChecker.match(neighborhood) is None


def test_reordering_forbidding_another_employees_sequence_is_rejected(solution, instance):
    """The forbidden sequence must be the reordered employee's own, not somebody else's."""
    neighborhood = Neighborhood(
        solution,
        [SequenceReordering(instance.get_employee_by_name("Valentin"))],
        [ForbiddenSequence(instance.get_employee_by_name("Ambre"),
                           [instance.get_task_by_name("T6"), instance.get_task_by_name("T7")])]
    )

    assert TemplateComplianceChecker.match(neighborhood) is None


def test_insertion_whose_immediate_precedence_ignores_the_inserted_task_is_rejected(solution, instance):
    """
    (Ins,1)'s ImmediatePrecedence pins where the inserted task goes, so its successor is that task; one
    pinning two other activities instead constrains something the operator never touches.
    """
    employee = instance.get_employee_by_name("Valentin")
    neighborhood = Neighborhood(
        solution,
        [TaskInsertion(frozenset({employee}), frozenset({instance.get_task_by_name("T5")}))],
        [PrecedenceChain([instance.get_task_by_name(name) for name in ("T1", "T2", "T3", "T4")]),
         ImmediatePrecedence(instance.get_task_by_name("T1"), instance.get_task_by_name("T2"))]
    )

    assert TemplateComplianceChecker.match(neighborhood) is None


def test_swap_deleting_and_inserting_for_different_employees_is_rejected(solution, instance):
    """
    A (Swp,*) neighborhood removes a task from and adds one to the same employees; freeing one employee's
    task while offering the incoming one to another is a relocation, which no template produces.
    """
    neighborhood = Neighborhood(
        solution,
        [TaskDeletion(frozenset({instance.get_employee_by_name("Valentin")}),
                      frozenset({instance.get_task_by_name("T1")})),
         TaskInsertion(frozenset({instance.get_employee_by_name("Ambre")}),
                       frozenset({instance.get_task_by_name("T5")}))],
        []
    )

    assert TemplateComplianceChecker.match(neighborhood) is None


def test_swap_fixing_the_order_twice_over_is_rejected(solution, instance):
    """
    A (Swp,*) neighborhood keeps the surviving tasks in order with a PrecedenceChain (when the outgoing task
    is named) or with a ForbiddenBackwardSubsequence (when it isn't), never with both at once.
    """
    employee = instance.get_employee_by_name("Valentin")
    employee_tasks = [instance.get_task_by_name(name) for name in ("T1", "T2", "T3", "T4")]
    neighborhood = Neighborhood(
        solution,
        [TaskDeletion(frozenset({employee}), frozenset({instance.get_task_by_name("T1")})),
         TaskInsertion(frozenset({employee}), frozenset({instance.get_task_by_name("T5")}))],
        [PrecedenceChain(employee_tasks[1:]), ForbiddenBackwardSubsequence(employee, employee_tasks)]
    )

    assert TemplateComplianceChecker.match(neighborhood) is None
