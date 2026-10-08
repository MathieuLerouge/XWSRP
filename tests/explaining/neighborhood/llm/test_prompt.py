# Standard library
import json

# Local libraries
from src.explaining.neighborhood.llm.prompt import build_user_prompt
from tests.explaining.neighborhood.helpers import build_solution_with_task_performances
from tests.modeling.helpers import build_instance


def _build_solution():
    instance = build_instance()
    return build_solution_with_task_performances(instance, "solution", {
        "T1": ("Valentin", 480), "T2": ("Valentin", 560), "T6": ("Ambre", 480),
    })


def test_prompt_without_json_context_lists_sequences_only():
    prompt = build_user_prompt(_build_solution(), "Why not?")
    assert "- Valentin performs, in order: T1, T2" in prompt
    assert "- Ambre performs, in order: T6" in prompt
    assert "(JSON" not in prompt
    assert prompt.endswith("Non-performed tasks: T3, T4, T5, T7, T8, T9, T10, T11, T12, T13, T14")


def test_prompt_with_json_context_gives_instance_and_solution_separately():
    prompt = build_user_prompt(_build_solution(), "Why not?", with_json_context=True)
    instance_start = prompt.index("Instance (JSON):\n") + len("Instance (JSON):\n")
    solution_header_start = prompt.index("Current solution (JSON")
    solution_start = prompt.index("\n", solution_header_start) + 1
    non_performed_start = prompt.index("Non-performed tasks:")
    instance_dictionary = json.loads(prompt[instance_start:solution_header_start])
    solution_dictionary = json.loads(prompt[solution_start:non_performed_start])
    assert instance_dictionary["tasks"]["T5"]["skill level"] == 2
    assert solution_dictionary["sequences"] == {"Valentin": ["T1", "T2"], "Ambre": ["T6"]}
    assert "instance" not in solution_dictionary
    assert "kpis" not in solution_dictionary
