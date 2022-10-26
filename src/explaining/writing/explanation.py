# Standard library
import json

# Local libraries
from src.explaining.answering.explanation import Explanation
from src.explaining.questioning.question import Question
from src.utils.constants import OUTPUTS_DIRECTORY_RELATIVE_PATH


def define_explanation_json_file_name(question: Question):
    return f"explanation_{question.solution.short_name}_{question.template.id}{question.fields_values}.json"


def export_explanation_to_json_file(explanation: Explanation, output_directory: str = None):
    file_name = define_explanation_json_file_name(explanation.question)
    if output_directory is None:
        output_directory = OUTPUTS_DIRECTORY_RELATIVE_PATH
    file_path = f"{output_directory}/{file_name}"
    with open(file_path, 'w') as file:
        json.dump(explanation.to_dict(), file, sort_keys=True, indent=4)


def define_explanations_json_file_name(explanations: list[Explanation]):
    explanation = explanations[0]
    return f"explanations_{explanation.question.solution.short_name}.json"


def export_explanations_to_json_file(explanations: list[Explanation], output_directory: str = None):
    file_name = define_explanations_json_file_name(explanations)
    if output_directory is None:
        output_directory = OUTPUTS_DIRECTORY_RELATIVE_PATH
    file_path = f"{output_directory}/{file_name}"
    explanations_dicts = []
    solution_name = explanations[0].question.solution.name
    for explanation in explanations:
        if explanation.question.solution.name != solution_name:
            raise ValueError(f"All the explanations must be related to the same solution {solution_name}"
                             f"but one is related to {explanation.question.solution.name}")
        explanations_dicts.append(explanation.to_dict())
    with open(file_path, 'w') as file:
        json.dump(explanations_dicts, file, sort_keys=True, indent=4)
