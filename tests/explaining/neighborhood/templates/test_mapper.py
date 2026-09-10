# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.templates.mapper import Mapper
from src.explaining.questioning.question import ContrastiveQuestion, CounterfactualQuestion, ScenarioQuestion
from src.explaining.questioning.questions_templates_bank import WHY_NOT_INS_2A
from tests.explaining.neighborhood.helpers import build_solution_with_task_performances
from tests.modeling.helpers import build_instance


def test_map_rejects_a_scenario_question():
    instance = build_instance()
    solution = build_solution_with_task_performances(instance, "solution", {"T1": ("Valentin", 480)})
    contrastive_question = ContrastiveQuestion(solution, WHY_NOT_INS_2A, ["Valentin", "T4"])
    question = ScenarioQuestion(contrastive_question, instance)
    with pytest.raises(TypeError):
        Mapper.map(question)


def test_map_rejects_a_counterfactual_question():
    instance = build_instance()
    solution = build_solution_with_task_performances(instance, "solution", {"T1": ("Valentin", 480)})
    contrastive_question = ContrastiveQuestion(solution, WHY_NOT_INS_2A, ["Valentin", "T4"])
    question = CounterfactualQuestion(contrastive_question)
    with pytest.raises(TypeError):
        Mapper.map(question)


def test_map_routes_ins_2a_to_the_neighborhood_targeting_the_named_task():
    instance = build_instance()
    solution = build_solution_with_task_performances(instance, "solution", {"T1": ("Valentin", 480)})
    question = ContrastiveQuestion(solution, WHY_NOT_INS_2A, ["Valentin", "T4"])
    neighborhood = Mapper.map(question)
    assert neighborhood.target_tasks == frozenset({instance.get_task_by_name("T4")})
    assert neighborhood.employees == frozenset({instance.get_employee_by_name("Valentin")})
