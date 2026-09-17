# Local libraries
from src.feasibility.violation.skill import SkillViolation
from tests.feasibility.helpers import build_employee, build_task


def test_skill_violation_text_reports_both_skill_levels():
    task = build_task(skill_level=3)
    employee = build_employee(skill_level=1)
    violation = SkillViolation(task, employee)
    assert violation.text == (
        f"{employee.name} is supposed to perform task "
        f"{task.name}, which has a skill level equal to {task.skill_level}, "
        f"while he/she has a skill level which is equal to {employee.skill_level}."
    )


def test_skill_violation_properties_return_constructor_arguments():
    task = build_task()
    employee = build_employee()
    violation = SkillViolation(task, employee)
    assert violation.task is task
    assert violation.employee is employee
