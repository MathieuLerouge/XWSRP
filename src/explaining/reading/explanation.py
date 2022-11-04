# Standard library
import json

# Local libraries
from src.explaining.answering.explanation import create_explanation_from_dict
from src.modeling.solution import Solution
from src.utils.files import create_inputs_file_path, check_inputs_file_existence


def import_single_explanation_from_json_file(file_name_with_extension: str, solution: Solution,
                                             input_directory: str = None):
    if ".json" not in file_name_with_extension:
        raise FileNotFoundError(f"The given file name {file_name_with_extension} does not have a json extension")
    if not check_inputs_file_existence(file_name_with_extension, input_directory):
        raise FileNotFoundError(f"The given explanation json file {file_name_with_extension} in {input_directory} "
                                f"directory does not exists")
    file_path = create_inputs_file_path(file_name_with_extension, input_directory)
    with open(file_path) as json_file:
        explanation_dictionary = json.load(json_file)
        explanation = create_explanation_from_dict(explanation_dictionary, solution)
    return explanation


def import_multiple_explanations_from_json_file(file_name_with_extension: str, solution: Solution,
                                                input_directory: str = None):
    if ".json" not in file_name_with_extension:
        raise FileNotFoundError(f"The given file name {file_name_with_extension} does not have a json extension")
    if not check_inputs_file_existence(file_name_with_extension, input_directory):
        raise FileNotFoundError(f"The given explanation json file {file_name_with_extension} in {input_directory} "
                                f"directory does not exists")
    file_path = create_inputs_file_path(file_name_with_extension, input_directory)
    with open(file_path) as json_file:
        explanations_dictionaries = json.load(json_file)
        # explanations = dict()
        # for explanation_dictionary in explanations_dictionaries:
        #     explanation = create_explanation_from_dict(explanation_dictionary, solution)
        #     template_id = explanation.question.template.id
        #     if template_id not in explanations:
        #         explanations[template_id] = dict()
        #     explanations[template_id][str(explanation.question.fields_values)] = explanation
        explanations = list()
        for explanation_dictionary in explanations_dictionaries:
            explanations.append(create_explanation_from_dict(explanation_dictionary, solution))
    return explanations
