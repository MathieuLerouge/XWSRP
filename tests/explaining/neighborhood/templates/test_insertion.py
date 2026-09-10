# Local libraries
from src.explaining.neighborhood.constraint import SequenceOrderFixed
from src.explaining.neighborhood.operator import POSITION_SIDE_AFTER, TaskInsertion
from src.explaining.neighborhood.templates import insertion
from src.explaining.questioning.question import ContrastiveQuestion
from src.explaining.questioning.questions_templates_bank import (
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3
)
from tests.explaining.neighborhood.helpers import build_solution_with_task_performances
from tests.modeling.helpers import build_instance


def _build_solution_with_valentin_performing_t1_and_t2():
    # Valentin performs T1 then T2 (feasible order: T1 ends at 540, 62min travel to T2, T2 starts at
    # 602, well within its [540,720] window). T4 (skill 1, capable by both employees) is left
    # non-performed and used as the insertion target across these tests.
    instance = build_instance()
    solution = build_solution_with_task_performances(
        instance, "solution", {"T1": ("Valentin", 480), "T2": ("Valentin", 602)}
    )
    return instance, solution


############
# (Ins,1) #
############

def test_map_ins_1_anchors_the_target_task_right_after_the_named_activity():
    instance, solution = _build_solution_with_valentin_performing_t1_and_t2()
    employee = instance.get_employee_by_name("Valentin")
    target_task = instance.get_task_by_name("T4")
    anchor = instance.get_task_by_name("T1")
    question = ContrastiveQuestion(solution, WHY_NOT_INS_1, ["Valentin", "T4", "T1"])
    neighborhood = insertion.map_ins_1(question)
    assert neighborhood.solution == solution
    assert neighborhood.employees == frozenset({employee})
    assert len(neighborhood.operators) == 1
    operator = neighborhood.operators[0]
    assert isinstance(operator, TaskInsertion)
    assert operator.candidate_employees == frozenset({employee})
    assert operator.candidate_tasks == frozenset({target_task})
    assert operator.anchor_activity == anchor
    assert operator.anchor_side == POSITION_SIDE_AFTER
    assert len(neighborhood.constraints) == 1
    assert isinstance(neighborhood.constraints[0], SequenceOrderFixed)
    assert neighborhood.constraints[0].employee == employee


#############
# (Ins,2a) #
#############

def test_map_ins_2a_targets_the_named_task_with_no_anchor():
    instance, solution = _build_solution_with_valentin_performing_t1_and_t2()
    employee = instance.get_employee_by_name("Valentin")
    target_task = instance.get_task_by_name("T4")
    question = ContrastiveQuestion(solution, WHY_NOT_INS_2A, ["Valentin", "T4"])
    neighborhood = insertion.map_ins_2a(question)
    operator = neighborhood.operators[0]
    assert operator.candidate_employees == frozenset({employee})
    assert operator.candidate_tasks == frozenset({target_task})
    assert operator.anchor_activity is None
    assert len(neighborhood.constraints) == 1
    assert isinstance(neighborhood.constraints[0], SequenceOrderFixed)


#############
# (Ins,2b) #
#############

def test_map_ins_2b_targets_every_non_performed_task_regardless_of_skill():
    instance, solution = _build_solution_with_valentin_performing_t1_and_t2()
    employee = instance.get_employee_by_name("Valentin")
    t1 = instance.get_task_by_name("T1")
    t2 = instance.get_task_by_name("T2")
    expected_candidates = frozenset(instance.tasks) - {t1, t2}
    question = ContrastiveQuestion(solution, WHY_NOT_INS_2B, ["Valentin"])
    neighborhood = insertion.map_ins_2b(question)
    operator = neighborhood.operators[0]
    assert operator.candidate_employees == frozenset({employee})
    assert operator.candidate_tasks == expected_candidates


#############
# (Ins,2c) #
#############

def test_map_ins_2c_targets_every_employee_regardless_of_skill():
    instance, solution = _build_solution_with_valentin_performing_t1_and_t2()
    target_task = instance.get_task_by_name("T4")
    all_employees = frozenset(instance.employees)
    question = ContrastiveQuestion(solution, WHY_NOT_INS_2C, ["T4"])
    neighborhood = insertion.map_ins_2c(question)
    operator = neighborhood.operators[0]
    assert operator.candidate_employees == all_employees
    assert operator.candidate_tasks == frozenset({target_task})
    assert neighborhood.employees == all_employees
    assert {constraint.employee for constraint in neighborhood.constraints} == all_employees
    assert all(isinstance(constraint, SequenceOrderFixed) for constraint in neighborhood.constraints)


############
# (Ins,3) #
############

def test_map_ins_3_leaves_the_order_free():
    instance, solution = _build_solution_with_valentin_performing_t1_and_t2()
    employee = instance.get_employee_by_name("Valentin")
    target_task = instance.get_task_by_name("T4")
    question = ContrastiveQuestion(solution, WHY_NOT_INS_3, ["Valentin", "T4"])
    neighborhood = insertion.map_ins_3(question)
    operator = neighborhood.operators[0]
    assert operator.candidate_employees == frozenset({employee})
    assert operator.candidate_tasks == frozenset({target_task})
    assert neighborhood.constraints == []
