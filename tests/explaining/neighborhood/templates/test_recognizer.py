# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.assembler import Assembler
from src.explaining.neighborhood.operator import TaskInsertion
from src.explaining.neighborhood.restriction import PrecedenceChain
from src.explaining.neighborhood.templates.mapper import Mapper
from src.explaining.neighborhood.templates.recognizer import Recognizer
from src.explaining.question.question import ContrastiveQuestion
from src.explaining.question.questions_templates_bank import (
    QUESTIONS_TEMPLATES, WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)
from src.modeling.solution import Solution
from tests.importing.helpers import build_solution


###########
# Helpers #
###########


@pytest.fixture(scope="module")
def get_text_solution() -> Solution:
    """The tests' data directory's reference solution, with its KPIs computed."""
    reference_solution = build_solution()
    reference_solution.compute_kpis()
    return reference_solution


def assert_every_mapped_neighborhood_is_recognized(solution: Solution, template_id: str):
    """
    Check that Recognizer recovers the very question Mapper mapped, over every valid field-value
    combination of the given template.

    Args:
        solution: The solution the questions are asked about.
        template_id: The identifier of the question template to enumerate, map and recognize back.

    Raises:
        AssertionError: if the template has no valid field-value combination at all for solution,
            or if any mapped neighborhood is recognized as another question, or not recognized at all.
    """
    all_fields_values = QUESTIONS_TEMPLATES[template_id].compute_all_fields_valid_values(solution)
    assert len(all_fields_values) > 0, f"No valid field-value combination found for template {template_id}"
    for fields_values in all_fields_values:
        neighborhood = Mapper.map(ContrastiveQuestion(solution, template_id, fields_values))
        question = Recognizer.recognize(neighborhood)
        assert question is not None, f"Template {template_id} maps {fields_values} to an unrecognized neighborhood"
        assert question.template.id == template_id, (
            f"Template {template_id} maps {fields_values} to a neighborhood recognized as {question.template.id}"
        )
        assert question.fields_values == fields_values, (
            f"Template {template_id} maps {fields_values} to a neighborhood recognized with "
            f"{question.fields_values} instead"
        )


#########
# Tests #
#########


def test_ins_1_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Ins,1): why is {Employee} not performing {Task} just after {Activity}?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_INS_1)


def test_ins_2a_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Ins,2a): why is {Employee} not performing {Task} between two consecutive activities of their route?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_INS_2A)


def test_ins_2b_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Ins,2b): why is {Employee} not performing any non-performed task between two consecutive activities?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_INS_2B)


def test_ins_2c_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Ins,2c): why is any employee not performing {Task} between two consecutive activities of their route?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_INS_2C)


def test_ins_3_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Ins,3): why is {Employee} not performing {Task} in addition to their already-performed activities?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_INS_3)


def test_swp_1_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Swp,1): why is {Employee} not performing {Task1} rather than {Task2}?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_SWP_1)


def test_swp_2a_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Swp,2a): why is {Employee} not performing {Task} rather than any of their already-performed tasks?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_SWP_2A)


def test_swp_2b_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Swp,2b): why is {Employee} not performing any non-performed task rather than an already-performed one?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_SWP_2B)


def test_swp_2c_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Swp,2c): why is any employee not performing {Task} rather than any of their already-performed tasks?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_SWP_2C)


def test_swp_3_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Swp,3): why is {Employee} not performing {Task} rather than any of their tasks, order left free?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_SWP_3)


def test_ord_1a_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Ord,1a): why is {Employee} not performing {Task1} later in their planning, just after {Task2}?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_ORD_LAT_1)


def test_ord_1b_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Ord,1b): why is {Employee} not performing {Task1} earlier in their planning, just before {Task2}?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_ORD_EAR_1)


def test_ord_2a_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Ord,2a): why is {Employee} not performing {Task} at a later stage of their planning?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_ORD_LAT_2)


def test_ord_2b_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Ord,2b): why is {Employee} not performing {Task} at an earlier stage of their planning?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_ORD_EAR_2)


def test_ord_2c_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Ord,2c): why is {Employee} not performing {Task} at any another stage in their planning?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_ORD_2)


def test_ord_3_round_trip_over_all_valid_fields_values(get_text_solution):
    """(Ord,3): why is {Employee} not performing the activities of their route in another order?"""
    assert_every_mapped_neighborhood_is_recognized(get_text_solution, WHY_NOT_ORD_3)


##################################################
# Boundary between the (Ins,2a)/(Ins,2b) shapes  #
##################################################


def _build_insertion_neighborhood(solution: Solution, employee_name: str, candidate_tasks_names: list[str]):
    """
    Assemble the (Ins,2*) neighborhood shape by hand, with an arbitrary set of candidate tasks.

    Args:
        solution: The solution the neighborhood is built around.
        employee_name: The name of the employee the tasks may be inserted into the sequence of.
        candidate_tasks_names: The names of the tasks offered as candidates.

    Returns:
        The neighborhood a TaskInsertion of those candidates, over that employee's order-preserved
        sequence, makes up.
    """
    instance = solution.instance
    employee = instance.get_employee_by_name(employee_name)
    candidate_tasks = frozenset(instance.get_task_by_name(name) for name in candidate_tasks_names)
    operator = TaskInsertion(frozenset({employee}), candidate_tasks)
    employee_tasks = list(solution.get_sequence(employee).get_contained_tasks())
    return Assembler.assemble([operator], [PrecedenceChain(employee_tasks)], solution)


def test_every_non_performed_task_offered_is_read_as_ins_2b(get_text_solution):
    """Offering exactly the solution's non-performed tasks is the (Ins,2b) shape, whatever their number."""
    neighborhood = _build_insertion_neighborhood(
        get_text_solution, "Ellen", get_text_solution.non_performed_tasks_names
    )
    question = Recognizer.recognize(neighborhood)
    assert question.template.id == WHY_NOT_INS_2B
    assert question.fields_values == ["Ellen"]


def test_one_named_task_offered_is_read_as_ins_2a(get_text_solution):
    """Offering a single task is the (Ins,2a) shape, even when that task is one of the non-performed ones."""
    neighborhood = _build_insertion_neighborhood(get_text_solution, "Ellen", ["T27"])
    question = Recognizer.recognize(neighborhood)
    assert question.template.id == WHY_NOT_INS_2A
    assert question.fields_values == ["Ellen", "T27"]


def test_some_but_not_all_non_performed_tasks_offered_is_recognized_as_nothing(get_text_solution):
    """
    Offering several tasks without offering every non-performed one is no template's shape.

    It is a neighborhood NeighborhoodModel can still solve - it is just not one the question catalogue
    induces, so there is no explanation template to phrase an answer from.
    """
    some_non_performed_tasks_names = get_text_solution.non_performed_tasks_names[:2]
    assert len(some_non_performed_tasks_names) == 2, "The reference solution should leave several tasks unperformed"
    neighborhood = _build_insertion_neighborhood(get_text_solution, "Ellen", some_non_performed_tasks_names)
    assert Recognizer.recognize(neighborhood) is None
