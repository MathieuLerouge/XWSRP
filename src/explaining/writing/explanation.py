# Standard library
import json

# Local libraries
from src.explaining.answering.explanation import Explanation
from src.explaining.questioning.question import ContrastiveQuestion
from src.modeling.solution import Solution
from src.utils.constants import OUTPUTS_DIRECTORY_RELATIVE_PATH
from src.utils.files import make_absolute_path


def define_single_contrastive_explanation_json_file_name(question: ContrastiveQuestion):
    return f"explanation_{question.solution.short_name}_{question.template.id}{question.fields_values}.json"


def export_single_contrastive_explanation_to_json_file(explanation: Explanation,
                                                       outputs_directory_relative_path: str = None):
    file_name = define_single_contrastive_explanation_json_file_name(explanation.question)
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = OUTPUTS_DIRECTORY_RELATIVE_PATH
    file_path = make_absolute_path(f"{outputs_directory_relative_path}/{file_name}")
    with open(file_path, 'w') as file:
        json.dump(explanation.to_dict(), file, sort_keys=True, indent=4)


def define_multiple_contrastive_explanations_json_file_name(solution: Solution):
    return f"explanations_{solution.short_name}.json"


def export_multiple_contrastive_explanations_to_json_file(explanations: list[Explanation],
                                                          outputs_directory_relative_path: str = None):
    solution = explanations[0].question.solution
    file_name = define_multiple_contrastive_explanations_json_file_name(solution)
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = OUTPUTS_DIRECTORY_RELATIVE_PATH
    file_path = make_absolute_path(f"{outputs_directory_relative_path}/{file_name}")
    explanations_dicts = []
    for explanation in explanations:
        if not explanation.is_contrastive:
            raise ValueError(f"All the explanations must be contrastive")
        if explanation.question.solution.name != solution.name:
            raise ValueError(f"All the explanations must be related to the same solution {solution.name}"
                             f"but one is related to {explanation.question.solution.name}")
        explanations_dicts.append(explanation.to_dict())
    with open(file_path, 'w') as file:
        json.dump(explanations_dicts, file, sort_keys=True, indent=4)
