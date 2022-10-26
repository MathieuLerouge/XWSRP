# Standard library
from os import path
import json

# Local libraries
from src.explaining.answering.explanation import create_explanation_from_dict
from src.modeling.solution import Solution
from src.utils.constants import INPUTS_DIRECTORY_RELATIVE_PATH


def create_explanation_json_file_path(file_name: str, input_directory: str = None):
    if input_directory is None:
        input_directory = INPUTS_DIRECTORY_RELATIVE_PATH
    file_path = f"{input_directory}/{file_name}"
    return file_path


def check_explanation_json_file_existence(file_name: str, input_directory: str = None):
    return path.exists(create_explanation_json_file_path(file_name, input_directory))


def import_explanation_from_json_file(file_name: str, solution: Solution, input_directory: str = None):
    if not check_explanation_json_file_existence(file_name, input_directory):
        raise FileNotFoundError(f"The given explanation json file {file_name} in {input_directory} "
                                f"directory does not exists")
    file_path = create_explanation_json_file_path(file_name, input_directory)
    with open(file_path) as json_file:
        explanation_dictionary = json.load(json_file)
        explanation = create_explanation_from_dict(explanation_dictionary, solution)
    return explanation


def import_explanations_from_json_file(file_name: str, solution: Solution, input_directory: str = None):
    if not check_explanation_json_file_existence(file_name, input_directory):
        raise FileNotFoundError(f"The given explanation json file {file_name} in {input_directory} "
                                f"directory does not exists")
    file_path = create_explanation_json_file_path(file_name, input_directory)
    with open(file_path) as json_file:
        explanations_dictionaries = json.load(json_file)
        explanations = dict()
        for explanation_dictionary in explanations_dictionaries:
            explanation = create_explanation_from_dict(explanation_dictionary, solution)
            template_id = explanation.question.template.id
            if template_id not in explanations:
                explanations[template_id] = dict()
            explanations[template_id][str(explanation.question.fields_values)] = explanation
    return explanations
