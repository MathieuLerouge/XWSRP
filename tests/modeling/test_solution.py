# Local libraries
from src.modeling.sequence import Sequence
from src.modeling.solution import Solution
from tests.modeling.helpers import build_employee, build_instance, build_sequence, build_solution, build_task


###########
# __eq__  #
###########

def test_solution_eq_with_identical_sequences_returns_true():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    overrides = {employee.name: build_sequence(instance, employee, [(task, 500)])}
    solution_1 = build_solution(instance, "solution_1", overrides)
    solution_2 = build_solution(instance, "solution_2", overrides)
    assert solution_1 == solution_2


def test_solution_eq_with_different_sequence_for_one_employee_returns_false():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    solution_1 = build_solution(
        instance, "solution_1", {employee.name: build_sequence(instance, employee, [(task, 500)])}
    )
    solution_2 = build_solution(
        instance, "solution_2", {employee.name: build_sequence(instance, employee, [(task, 600)])}
    )
    assert solution_1 != solution_2


def test_solution_eq_with_missing_employee_returns_false():
    instance = build_instance()
    solution_1 = build_solution(instance, "solution_1", {})
    sequences_2 = {employee.name: Sequence(instance, employee) for employee in instance.employees}
    del sequences_2[build_employee(instance).name]
    solution_2 = Solution(instance, name="solution_2", sequences=sequences_2)
    assert solution_1 != solution_2


def test_solution_eq_with_non_solution_returns_false():
    instance = build_instance()
    solution = build_solution(instance, "solution", {})
    assert solution != "not a solution"
