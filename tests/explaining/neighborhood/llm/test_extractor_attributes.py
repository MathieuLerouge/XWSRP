# Standard library
import os

# Third-party libraries
import pytest
from instructor import Mode

# Local libraries
from src.explaining.neighborhood.llm.extractor import Extractor
from src.explaining.neighborhood.operator import TaskInsertion, TaskRepositioning
from src.explaining.question.free.question import FreeTextQuestion
from tests.explaining.neighborhood.helpers import build_solution_with_task_performances
from tests.modeling.helpers import build_instance

# Real-model checks that a question referring to tasks/employees by attribute rather than by name is grounded
# to the right names, which only the JSON context (see build_user_prompt) makes possible.
# Each question below has a single right answer in build_instance's data.
# Same backend selection as test_extractor_compliance.py, e.g.
# XWSRP_EXTRACTOR_TEST_MODEL=mistral/mistral-medium-latest pytest -m llm
_MODEL = os.environ.get("XWSRP_EXTRACTOR_TEST_MODEL", "ollama/qwen2.5:7b")
_MODE = Mode.MD_JSON if _MODEL.startswith("ollama/") else None


@pytest.fixture(scope="module")
def instance():
    return build_instance()


@pytest.fixture(scope="module")
def solution(instance):
    # Valentin (skill level 2) performs T1, T2, T3, T4 in order; Ambre (skill level 1) performs T6, T7 in order;
    # T5, T8-T14 are left non-performed.
    return build_solution_with_task_performances(instance, "solution", {
        "T1": ("Valentin", 480), "T2": ("Valentin", 560), "T3": ("Valentin", 640), "T4": ("Valentin", 720),
        "T6": ("Ambre", 480), "T7": ("Ambre", 560),
    })


@pytest.fixture
def ask(solution):
    """Asks a JSON-context extractor a free-text question about the test solution, and returns the neighborhood."""
    extractor = Extractor(solution, _MODEL, mode=_MODE, with_json_context=True)

    def ask_question(question_text: str):
        return extractor.extract(FreeTextQuestion(solution, question_text))
    return ask_question


def _get_operator(neighborhood, operator_type):
    return next(operator for operator in neighborhood.operators if isinstance(operator, operator_type))


@pytest.mark.llm
def test_employee_referred_to_by_skill_level(ask, instance):
    neighborhood = ask("Why isn't the more skilled of the two employees doing T8 at some point in their day?")
    task_insertion = _get_operator(neighborhood, TaskInsertion)
    assert task_insertion.candidate_employees == frozenset({instance.get_employee_by_name("Valentin")})
    assert instance.get_task_by_name("T8") in task_insertion.candidate_tasks


@pytest.mark.llm
def test_task_referred_to_by_duration(ask, instance):
    neighborhood = ask("Why doesn't Ambre take on the shortest of the unassigned tasks?")
    task_insertion = _get_operator(neighborhood, TaskInsertion)
    assert task_insertion.candidate_tasks == frozenset({instance.get_task_by_name("T14")})


@pytest.mark.llm
def test_performed_task_referred_to_by_duration(ask, instance):
    neighborhood = ask("Why doesn't Valentin do his longest task later in his day?")
    task_repositioning = _get_operator(neighborhood, TaskRepositioning)
    assert task_repositioning.target_task == instance.get_task_by_name("T2")


@pytest.mark.llm
def test_task_referred_to_by_time_window(ask, instance):
    neighborhood = ask("Why isn't the unassigned task that can only start from 2pm given to Valentin?")
    task_insertion = _get_operator(neighborhood, TaskInsertion)
    assert task_insertion.candidate_tasks == frozenset({instance.get_task_by_name("T13")})
