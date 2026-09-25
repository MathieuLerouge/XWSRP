"""
Characterization tests pinning down what every question template's transformation produces today.

These tests assert nothing about what the transformations *should* do: they compare their output
against a baseline snapshot recorded from the current implementation. Their purpose is to make the
refactoring of src.explaining.computing.templates verifiable, in particular for the counterfactual
transformations, which no other test exercises.

Regenerate the baseline (only when a behaviour change is intended and reviewed) with:
    PYTHONPATH=. python tests/explaining/computing/test_transformation_characterization.py
"""

# Standard libraries
import json
import os
from typing import Any, Optional

# Third-party library
import pytest

# Local libraries
from src.explaining.computing.templates.transformation import \
    apply_transformation_induced_by_contrastive_or_scenario_question, \
    apply_transformation_induced_by_counterfactual_question
from src.explaining.computing.conflict.conflict import Conflict
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.solution import EditableSolution
from src.explaining.questioning.question import ContrastiveQuestion, CounterfactualQuestion
from src.explaining.questioning.questions_templates_bank import \
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3, \
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3, \
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
from src.modeling.solution import Solution
from tests.importing.helpers import build_solution

# Global variables
# NB: Path is relative to the project's root directory, which is where pytest is run from.
BASELINE_FILE_PATH = "tests/data/transformation_characterization.json"
# The field values are the ones the parity tests use, so that a case which is interesting there
# (a real conflict, a real alteration) stays interesting here.
CONTRASTIVE_CASES = [
    ("ins_1", WHY_NOT_INS_1, ["Ellen", "T27", "T17"]),
    ("ins_2a", WHY_NOT_INS_2A, ["Ellen", "T27"]),
    ("ins_2b", WHY_NOT_INS_2B, ["Ellen"]),
    ("ins_2c", WHY_NOT_INS_2C, ["T27"]),
    ("ins_3", WHY_NOT_INS_3, ["Ellen", "T27"]),
    ("swp_1", WHY_NOT_SWP_1, ["Ellen", "T27", "T17"]),
    ("swp_2a", WHY_NOT_SWP_2A, ["Ellen", "T27"]),
    ("swp_2b", WHY_NOT_SWP_2B, ["Ellen"]),
    ("swp_2c", WHY_NOT_SWP_2C, ["T27"]),
    ("swp_3", WHY_NOT_SWP_3, ["Ellen", "T27"]),
    ("ord_lat_1", WHY_NOT_ORD_LAT_1, ["Ellen", "T30", "T26"]),
    ("ord_ear_1", WHY_NOT_ORD_EAR_1, ["Ellen", "T26", "T7"]),
    ("ord_lat_2", WHY_NOT_ORD_LAT_2, ["Ellen", "T3"]),
    ("ord_ear_2", WHY_NOT_ORD_EAR_2, ["Ellen", "T3"]),
    ("ord_2", WHY_NOT_ORD_2, ["Ellen", "T1"]),
    ("ord_3", WHY_NOT_ORD_3, ["Carlotta"]),
]
# (Ins,2c) and (Swp,2c) ask about *any* employee rather than a named one,
# which the counterfactual transformations do not handle.
TEMPLATES_IDS_WITHOUT_COUNTERFACTUAL_TRANSFORMATION = [WHY_NOT_INS_2C, WHY_NOT_SWP_2C]
COUNTERFACTUAL_CASES = [case for case in CONTRASTIVE_CASES
                        if case[1] not in TEMPLATES_IDS_WITHOUT_COUNTERFACTUAL_TRANSFORMATION]
CONFLICT_KEY = "conflict"
DESCRIPTIONS_KEY = "descriptions"
ROUTES_KEY = "routes"
KPIS_KEY = "kpis"
ALTERATIONS_KEY = "alterations"


def build_snapshot(support_solution: EditableSolution, conflict: Optional[Conflict],
                   descriptions: dict[str, str],
                   instance_alterations: Optional[InstanceChanges] = None) -> dict[str, Any]:
    """
    Turn what a transformation returned into a JSON-serializable snapshot.

    Args:
        support_solution: The transformed solution the transformation produced.
        conflict: The conflict the transformation ran into, or None when it is feasible.
        descriptions: The texts describing the applied transformation, keyed by language.
        instance_alterations: The instance parameter changes, for counterfactual transformations only.

    Returns:
        A dictionary holding the conflict, the descriptions, each employee's route, the solution's
        KPIs and the instance alterations.
    """
    routes = {employee.name: [step.activity.name for step in support_solution.get_sequence(employee)]
              for employee in support_solution.instance.employees}
    return {
        CONFLICT_KEY: None if conflict is None else conflict.to_dict(),
        DESCRIPTIONS_KEY: descriptions,
        ROUTES_KEY: routes,
        KPIS_KEY: support_solution.kpis.to_dict() if support_solution.has_kpis else None,
        ALTERATIONS_KEY: None if instance_alterations is None else instance_alterations.as_list_of_strings(),
    }


def compute_contrastive_snapshot(solution: Solution, template_id: str, fields_values: list[str]) -> dict[str, Any]:
    """Return the snapshot of the transformation the given contrastive question induces."""
    editable_solution = EditableSolution.from_solution(solution)
    question = ContrastiveQuestion(editable_solution, template_id, fields_values)
    support_solution, conflict, descriptions = \
        apply_transformation_induced_by_contrastive_or_scenario_question(editable_solution, question)
    return build_snapshot(support_solution, conflict, descriptions)


def compute_counterfactual_snapshot(solution: Solution, template_id: str, fields_values: list[str]) -> dict[str, Any]:
    """Return the snapshot of the transformation the given counterfactual question induces."""
    editable_solution = EditableSolution.from_solution(solution)
    contrastive_question = ContrastiveQuestion(editable_solution, template_id, fields_values)
    question = CounterfactualQuestion(contrastive_question)
    support_solution, conflict, descriptions, instance_alterations = \
        apply_transformation_induced_by_counterfactual_question(editable_solution, question)
    return build_snapshot(support_solution, conflict, descriptions, instance_alterations)


def build_reference_solution() -> Solution:
    """Return the tests' reference solution, with its KPIs computed."""
    solution = build_solution()
    solution.compute_kpis()
    return solution


def read_baseline() -> dict[str, dict[str, Any]]:
    """
    Return the recorded baseline snapshots, keyed by question kind and then by case id.

    Raises:
        AssertionError: if the baseline file is missing, which means it has yet to be generated.
    """
    assert os.path.isfile(BASELINE_FILE_PATH), (
        f"Missing baseline file {BASELINE_FILE_PATH}. Generate it by running this module as a script."
    )
    with open(BASELINE_FILE_PATH, encoding="utf-8") as baseline_file:
        return json.load(baseline_file)


def assert_same_snapshot(snapshot: dict[str, Any], expected_snapshot: dict[str, Any]):
    """Assert the two snapshots match, one field at a time so that a failure names the field that moved."""
    assert snapshot[CONFLICT_KEY] == expected_snapshot[CONFLICT_KEY], "The conflict changed"
    assert snapshot[DESCRIPTIONS_KEY] == expected_snapshot[DESCRIPTIONS_KEY], "The transformation texts changed"
    assert snapshot[ROUTES_KEY] == expected_snapshot[ROUTES_KEY], "The support solution's routes changed"
    assert snapshot[KPIS_KEY] == expected_snapshot[KPIS_KEY], "The support solution's KPIs changed"
    assert snapshot[ALTERATIONS_KEY] == expected_snapshot[ALTERATIONS_KEY], "The instance alterations changed"


@pytest.mark.parametrize("case_id, template_id, fields_values", CONTRASTIVE_CASES,
                         ids=[case[0] for case in CONTRASTIVE_CASES])
def test_contrastive_transformation_is_unchanged(case_id: str, template_id: str, fields_values: list[str]):
    """The transformation induced by each contrastive question still produces its recorded result."""
    snapshot = compute_contrastive_snapshot(build_reference_solution(), template_id, fields_values)
    assert_same_snapshot(snapshot, read_baseline()["contrastive"][case_id])


@pytest.mark.parametrize("case_id, template_id, fields_values", COUNTERFACTUAL_CASES,
                         ids=[case[0] for case in COUNTERFACTUAL_CASES])
def test_counterfactual_transformation_is_unchanged(case_id: str, template_id: str, fields_values: list[str]):
    """The transformation induced by each counterfactual question still produces its recorded result."""
    snapshot = compute_counterfactual_snapshot(build_reference_solution(), template_id, fields_values)
    assert_same_snapshot(snapshot, read_baseline()["counterfactual"][case_id])


def write_baseline():
    """Record the current output of every transformation into the baseline file."""
    solution = build_reference_solution()
    baseline = {
        "contrastive": {case_id: compute_contrastive_snapshot(solution, template_id, fields_values)
                        for case_id, template_id, fields_values in CONTRASTIVE_CASES},
        "counterfactual": {case_id: compute_counterfactual_snapshot(solution, template_id, fields_values)
                           for case_id, template_id, fields_values in COUNTERFACTUAL_CASES},
    }
    with open(BASELINE_FILE_PATH, "w", encoding="utf-8") as baseline_file:
        json.dump(baseline, baseline_file, indent=2, ensure_ascii=False)
        baseline_file.write("\n")
    print(f"Wrote {len(CONTRASTIVE_CASES)} contrastive and {len(COUNTERFACTUAL_CASES)} counterfactual "
          f"snapshots to {BASELINE_FILE_PATH}")


if __name__ == "__main__":
    write_baseline()
