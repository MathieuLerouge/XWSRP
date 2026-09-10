# Local libraries
from src.modeling.comeback import ComeBack
from src.modeling.step import Step
from tests.modeling.helpers import build_employee, build_instance


###########
# __eq__  #
###########

def test_step_eq_with_same_activity_and_times_returns_true():
    employee = build_employee(build_instance())
    step_1 = Step(ComeBack(employee), start_time=500, end_time=500)
    step_2 = Step(ComeBack(employee), start_time=500, end_time=500)
    assert step_1 == step_2


def test_step_eq_with_different_start_time_returns_false():
    employee = build_employee(build_instance())
    step_1 = Step(ComeBack(employee), start_time=500, end_time=500)
    step_2 = Step(ComeBack(employee), start_time=510, end_time=510)
    assert step_1 != step_2
