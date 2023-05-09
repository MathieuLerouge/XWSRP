# Standard library
import json

# Local libraries
from src.explaining.answering.explanation import Explanation
from src.explaining.questioning.question import ContrastiveQuestion
from src.modeling.solution import Solution
from src.utils.constants import DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
from src.utils.files import make_absolute_path_from_relative_one


################
# Explanations #
################


def define_single_contrastive_explanation_json_file_name(question: ContrastiveQuestion):
    return f"explanation_{question.solution.core_name}_{question.template.id}{question.fields_values}.json"


def export_single_contrastive_explanation_to_json_file(explanation: Explanation,
                                                       outputs_directory_relative_path: str = None):
    file_name = define_single_contrastive_explanation_json_file_name(explanation.question)
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
    file_path = make_absolute_path_from_relative_one(f"{outputs_directory_relative_path}/{file_name}")
    with open(file_path, 'w') as file:
        json.dump(explanation.to_dict(), file, sort_keys=True, indent=4)


def define_multiple_contrastive_explanations_json_file_name(solution: Solution):
    return f"explanations_{solution.core_name}.json"


def export_multiple_contrastive_explanations_to_json_file(explanations: list[Explanation],
                                                          outputs_directory_relative_path: str = None):
    solution = explanations[0].question.solution
    file_name = define_multiple_contrastive_explanations_json_file_name(solution)
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
    file_path = make_absolute_path_from_relative_one(f"{outputs_directory_relative_path}/{file_name}")
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


#########################
# Explanations analysis #
#########################


def define_contrastive_explanations_analysis_json_file_name(solution: Solution):
    """
    Define the name (with extension) of the file of the contrastive explanations
    :param solution: the solution to which the explanations are related (Solution)
    :return: the name (with extension) of the file of analysis of contrastive explanations (str)
    """
    return f"{solution.name}_explanations_analysis.json"


def export_contrastive_explanations_analysis_to_json_file(solution: Solution, explanations_analysis: dict,
                                                          outputs_directory_relative_path: str = None):
    """
    Export the contrastive explanations analysis to a json file
    :param solution: the solution to which the explanations are related (Solution)
    :param explanations_analysis: the analysis of contrastive explanations (dict)
    :param outputs_directory_relative_path: the relative path of the directory where the file will be saved (str)
    :return: None
    """
    file_name = define_contrastive_explanations_analysis_json_file_name(solution)
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
    file_path = make_absolute_path_from_relative_one(f"{outputs_directory_relative_path}/{file_name}")
    with open(file_path, 'w') as file:
        json.dump(explanations_analysis, file, sort_keys=True, indent=4)
