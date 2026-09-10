# Local libraries
from src.explaining.questioning.questions_templates_bank import (
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3
)
from tests.explaining.computing.helpers import (
    assert_same_kpis, build_austria_solution, get_neighborhood_computation_pipeline_gap_and_solution,
    get_tailored_computation_pipeline_gap_and_solution
)


def test_ins_1_parity():
    """(Ins,1): why is Ellen not performing T27 just after T17?"""
    solution = build_austria_solution()
    fields_values = ["Ellen", "T27", "T17"]

    tailored_gap, tailored_solution = get_tailored_computation_pipeline_gap_and_solution(
        solution, WHY_NOT_INS_1, fields_values
    )
    neighborhood_gap, neighborhood_solution = get_neighborhood_computation_pipeline_gap_and_solution(
        solution, WHY_NOT_INS_1, fields_values
    )

    assert tailored_gap == neighborhood_gap
    if tailored_gap == 0:
        assert_same_kpis(tailored_solution, neighborhood_solution)


def test_ins_2a_parity():
    """(Ins,2a): why is Ellen not performing T27 between two consecutive activities of her route?"""
    solution = build_austria_solution()
    fields_values = ["Ellen", "T27"]

    tailored_gap, tailored_solution = get_tailored_computation_pipeline_gap_and_solution(
        solution, WHY_NOT_INS_2A, fields_values
    )
    neighborhood_gap, neighborhood_solution = get_neighborhood_computation_pipeline_gap_and_solution(
        solution, WHY_NOT_INS_2A, fields_values
    )

    assert tailored_gap == neighborhood_gap
    if tailored_gap == 0:
        assert_same_kpis(tailored_solution, neighborhood_solution)


def test_ins_2b_parity():
    """(Ins,2b): why is Ellen not performing any non-performed task between two consecutive activities
    of her route?"""
    solution = build_austria_solution()
    fields_values = ["Ellen"]

    tailored_gap, tailored_solution = get_tailored_computation_pipeline_gap_and_solution(
        solution, WHY_NOT_INS_2B, fields_values
    )
    neighborhood_gap, neighborhood_solution = get_neighborhood_computation_pipeline_gap_and_solution(
        solution, WHY_NOT_INS_2B, fields_values
    )

    assert tailored_gap == neighborhood_gap
    if tailored_gap == 0:
        assert_same_kpis(tailored_solution, neighborhood_solution)


def test_ins_2c_parity():
    """(Ins,2c): why is any employee not performing T27 between two consecutive activities of their
    route?"""
    solution = build_austria_solution()
    fields_values = ["T27"]

    tailored_gap, tailored_solution = get_tailored_computation_pipeline_gap_and_solution(
        solution, WHY_NOT_INS_2C, fields_values
    )
    neighborhood_gap, neighborhood_solution = get_neighborhood_computation_pipeline_gap_and_solution(
        solution, WHY_NOT_INS_2C, fields_values
    )

    assert tailored_gap == neighborhood_gap
    if tailored_gap == 0:
        assert_same_kpis(tailored_solution, neighborhood_solution)


def test_ins_3_parity():
    """
    (Ins,3): why is Ellen not performing T27 in addition to her already-performed activities (even if
    it means changing their order)?
    """
    solution = build_austria_solution()
    fields_values = ["Ellen", "T27"]

    tailored_gap, tailored_solution = get_tailored_computation_pipeline_gap_and_solution(
        solution, WHY_NOT_INS_3, fields_values
    )
    neighborhood_gap, neighborhood_solution = get_neighborhood_computation_pipeline_gap_and_solution(
        solution, WHY_NOT_INS_3, fields_values
    )

    assert tailored_gap == neighborhood_gap
    if tailored_gap == 0:
        assert_same_kpis(tailored_solution, neighborhood_solution)
