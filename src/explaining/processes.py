# Standard libraries
import random
import time

# Third-party libraries
import numpy as np

# Local libraries
from main_configuration import EXPLANATIONS_ANALYSIS_TIME_LIMIT_FOR_COMPUTING_EACH_EXPLANATION, \
    EXPLANATION_COMPUTATION_TIME_BETWEEN_MESSAGES
from src.checking.feasibility import check_feasibility
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.explainer_web_UI import ExplainerWebGUI
from src.explaining.questioning.question import ContrastiveQuestion, CounterfactualQuestion
from src.explaining.questioning.questions_templates_bank import *
from src.explaining.transforming.exceptions import ImpossibleTransformationException
from src.explaining.writing.explanation import export_multiple_contrastive_explanations_to_json_file
from src.modeling.solution import Solution
from src.optimization.milp.solver.exceptions import TimeLimitReachedWithSolutionException, \
    TimeLimitReachedWithoutSolutionException
from src.reading.solution import extract_solution_from_file
from src.utils.constants import DEFAULT_INPUTS_DIRECTORY_RELATIVE_PATH
from src.utils.files import get_project_directory_path, get_paths_of_solutions_files_in_given_directory


##############################
# Explainer on demo solution #
##############################


def get_demo_solution_path():
    """
    Returns the path of the solution for demo.

    :return: the path of the solution for demo (str)
    """
    return f"{get_project_directory_path()}/data/demo/solutions/solution_demo.txt"


def get_demo_solution():
    """
    Returns the solution for demo.

    :return: the solution for demo (Solution)
    """
    solution = extract_solution_from_file(get_demo_solution_path(), True, True, True)
    if not check_feasibility(solution)[0]:
        raise ValueError(f"The solution {solution.name} is not feasible")
    return solution


def compute_contrastive_explanations_about_demo_solution_in_separate_files(questions_templates_ids: list[str] = None):
    """
    Compute contrastive explanations in separate .json files.

    :param questions_templates_ids: the IDs of the questions templates to use (list of str),
    if None, all activated questions templates are computed
    :return: None
    """
    solution = get_demo_solution()
    explainer = Explainer(solution)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    if questions_templates_ids is None:
        questions_templates_ids = explainer.activated_questions_templates_ids
    explanations = []
    for question_template_id in questions_templates_ids:
        question_template = QUESTIONS_TEMPLATES[question_template_id]
        if question_template in explainer.activated_questions_templates:
            print("Computing explanations related to:", question_template.id)
            all_fields_valid_values = question_template.compute_all_fields_valid_values(solution)
            for fields_values in all_fields_valid_values:
                explanations.append(explainer.get_contrastive_explanation(question_template.id, fields_values))
    export_multiple_contrastive_explanations_to_json_file(explanations)


def compute_contrastive_explanations_about_demo_solution_in_one_file(questions_templates_ids: list[str] = None):
    """
    Compute contrastive explanations in one .json file.

    :param questions_templates_ids: the IDs of the questions templates to use (list of str),
    if None, all activated questions templates are computed
    :return: None
    """
    solution = get_demo_solution()
    explainer = Explainer(solution)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.enable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    if questions_templates_ids is None:
        questions_templates_ids = explainer.activated_questions_templates_ids
    for question_template_id in questions_templates_ids:
        question_template = QUESTIONS_TEMPLATES[question_template_id]
        if question_template in explainer.activated_questions_templates:
            print("Computing explanations related to:", question_template.id)
            all_fields_valid_values = question_template.compute_all_fields_valid_values(solution)
            for fields_values in all_fields_valid_values:
                explainer.get_contrastive_explanation(question_template.id, fields_values)
    explainer.export_all_already_computed_contrastive_explanations()


def launch_explainer_UI_on_demo_solution(language: str = LANGUAGE_ENGLISH_KEY, enable_history: bool = True,
                                         enable_scenario_explanations: bool = True,
                                         enable_counterfactual_explanations: bool = True,
                                         enable_using_already_computed_contrastive_explanations: bool = True):
    """
    Launch the explainer UI on the demo solution.

    :param language: the language to use (str)
    :param enable_history: whether to enable the history (bool)
    :param enable_scenario_explanations: whether to enable the scenario explanations (bool)
    :param enable_counterfactual_explanations: whether to enable the counterfactual explanations (bool)
    :param enable_using_already_computed_contrastive_explanations:
    whether to enable using already computed contrastive explanations (bool)
    :return: None
    """
    explainer = Explainer(get_demo_solution())
    explainer.set_language(language)
    if enable_history:
        explainer.enable_history()
    if enable_scenario_explanations:
        explainer.enable_scenario_explanations()
    if enable_counterfactual_explanations:
        explainer.enable_counterfactual_explanations()
    if enable_using_already_computed_contrastive_explanations:
        explainer.contrastive_explanations_inputs_directory_relative_path = "data/demo/explanations"
        explainer.enable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    explainer_UI = ExplainerWebGUI(explainer)
    explainer_UI.launch()


#################################
# Explainer on default solution #
#################################

def get_default_solution():
    """
    Returns the solution in the default inputs directory.
    If several solutions are found in the default inputs directory, the first one is returned.

    :return: the solution in the default inputs directory (Solution)
    """
    try:
        solution_file_path = get_paths_of_solutions_files_in_given_directory()[0]
    except IndexError:
        raise FileNotFoundError(f"There are no solutions files found in directory "
                                f"{DEFAULT_INPUTS_DIRECTORY_RELATIVE_PATH}")
    solution = extract_solution_from_file(solution_file_path, True, True, True)
    if not check_feasibility(solution)[0]:
        raise ValueError(f"The solution {solution.name} is not feasible")
    return solution


def launch_explainer_UI_on_default_solution(language: str, enable_history: bool = True,
                                            enable_scenario_explanations: bool = True,
                                            enable_counterfactual_explanations: bool = True):
    """
    Launch the explainer UI on the default solution.

    :param language: the language to use (str)
    :param enable_history: whether to enable the history (bool)
    :param enable_scenario_explanations: whether to enable the scenario explanations (bool)
    :param enable_counterfactual_explanations: whether to enable the counterfactual explanations (bool)
    :return: None
    """
    explainer = Explainer(get_demo_solution())
    explainer.set_language(language)
    if enable_history:
        explainer.enable_history()
    if enable_scenario_explanations:
        explainer.enable_scenario_explanations()
    if enable_counterfactual_explanations:
        explainer.enable_counterfactual_explanations()
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    explainer_UI = ExplainerWebGUI(explainer)
    explainer_UI.launch()


##########################################
# Explanations computation time analysis #
##########################################

def compute_computation_time_analysis_of_explanations(
        solution: Solution, questions_templates_ids: list[str] = None,
        maximum_number_of_explanations_per_template: int = 50, question_type=None):
    """
    Compute the computation time analysis of the contrastive explanations about the given solution.

    :param solution: the solution (Solution)
    :param questions_templates_ids: the IDs of the questions templates to use (list of str),
    if None, all activated questions templates are computed
    :param maximum_number_of_explanations_per_template: the maximum number of explanations per template (int)
    :param question_type: the type of question/explanation to analyze (either contrastive of counterfactual)
    :return: the analysis of explanations (ExplanationsAnalysis)
    """
    if question_type is None or question_type == ContrastiveQuestion:
        explanations_are_contrastive = True
    else:
        explanations_are_contrastive = False

    # Prepare explainer
    explainer = Explainer(solution)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    if explanations_are_contrastive:
        explainer.disable_counterfactual_explanations()
        explainer.time_limit_for_contrastive_explanation_ILP_computation = \
            EXPLANATIONS_ANALYSIS_TIME_LIMIT_FOR_COMPUTING_EACH_EXPLANATION
    else:
        explainer.enable_counterfactual_explanations()
        explainer.time_limit_for_counterfactual_explanation_ILP_computation = \
            EXPLANATIONS_ANALYSIS_TIME_LIMIT_FOR_COMPUTING_EACH_EXPLANATION
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()

    # Define question templates to analyze
    if questions_templates_ids is None:
        if explanations_are_contrastive:
            questions_templates_ids = explainer.activated_questions_templates_ids
        else:
            questions_templates_ids = explainer.activated_counterfactual_questions_templates_ids

    # Run analysis
    analysis = dict()
    for question_template_id in questions_templates_ids:
        question_template = QUESTIONS_TEMPLATES[question_template_id]
        if question_template in explainer.activated_questions_templates:

            # Prepare fields values
            all_fields_valid_values = question_template.compute_all_fields_valid_values(solution)
            nb_possible_questions = len(all_fields_valid_values)
            random.seed(42)
            random.shuffle(all_fields_valid_values)

            computation_times = []
            nb_executed_computations = 0
            nb_interrupted_computations, nb_interruptions_with_solution, nb_interruptions_without_solution = 0, 0, 0
            nb_completed_computations, nb_positive_explanations, nb_negative_explanations = 0, 0, 0
            nb_rejected_computations = 0
            messages_counter = 0

            print("Computing explanations related to:", question_template.id)

            explanations_computation_start_time = time.time()
            while ((nb_executed_computations < maximum_number_of_explanations_per_template) and
                   len(all_fields_valid_values) > 0):

                # Select fields values
                fields_values = all_fields_valid_values.pop()

                # Compute the explanation associated with the given question template and the given fields
                # and save information about the explanation
                start_time = time.time()
                try:
                    if explanations_are_contrastive:
                        explanation = explainer.get_contrastive_explanation(question_template.id, fields_values)
                    else:
                        explanation = explainer.compute_counterfactual_explanation(question_template.id, fields_values)
                    nb_completed_computations += 1
                    if explanation.is_positive():
                        nb_positive_explanations += 1
                    else:
                        nb_negative_explanations += 1
                    computation_times.append(np.round(time.time() - start_time, 3))
                except TimeLimitReachedWithSolutionException:
                    nb_interrupted_computations += 1
                    nb_interruptions_with_solution += 1
                except TimeLimitReachedWithoutSolutionException:
                    nb_interrupted_computations += 1
                    nb_interruptions_without_solution += 1
                except ImpossibleTransformationException:
                    nb_rejected_computations += 1
                except Exception as e:
                    question = ContrastiveQuestion(solution, question_template_id, fields_values)
                    if not explanations_are_contrastive:
                        question = CounterfactualQuestion(question)
                    if 'Ins' in question.template.id or 'Swp' in question.template.id:
                        if fields_values[0] in solution.instance.employees_names:
                            employee = solution.instance.get_employee_by_name(fields_values[0])
                            sequence = solution.get_sequence(employee)
                            if len(fields_values) > 1 and fields_values[1] in solution.instance.tasks_names:
                                task_1 = solution.instance.get_task_by_name(fields_values[1])
                                travel_time = solution.instance.compute_traveling_duration(sequence[0].activity, task_1)
                                if travel_time > 12*60:
                                    nb_completed_computations += 1
                                    nb_negative_explanations += 1
                                    computation_times.append(np.round(time.time() - start_time, 3))
                                else:
                                    print("Question:", question.text)
                                    print("Sequence:", sequence)
                                    print("Travel time between home and inserted task:", travel_time)
                                    raise e
                            else:
                                if 'Ins-2b' in question.template.id:
                                    print("Non performed tasks:", solution.non_performed_tasks)
                                    print("Nb possible questions:", nb_possible_questions)
                                print("Question:", question.text)
                                print("Sequence:", sequence)
                                raise e
                        else:
                            print("Question:", question.text)
                            raise e
                    else:
                        print("Question:", question.text)
                        raise e
                nb_executed_computations += 1

                # Display messages about the analysis computation at regular intervals
                # (to make sure every thing is working properly)
                explanations_computation_time = time.time() - explanations_computation_start_time
                n = explanations_computation_time // EXPLANATION_COMPUTATION_TIME_BETWEEN_MESSAGES
                if n > messages_counter:
                    messages_counter = n
                    nb_computations_left = min(len(all_fields_valid_values),
                                               maximum_number_of_explanations_per_template - nb_executed_computations)
                    print(f"{nb_executed_computations} explanation computation run, "
                          f"{nb_computations_left} explanation computation left")

            # Save analysis results related to the question template within a dictionary
            analysis[question_template_id] = dict(
                nb_possible_questions=nb_possible_questions,
                nb_explanation_computations=nb_executed_computations,
                nb_interrupted_computations=nb_interrupted_computations,
                nb_interruptions_with_solution=nb_interruptions_with_solution,
                nb_interruptions_without_solution=nb_interruptions_without_solution,
                nb_completed_computations=nb_completed_computations,
                nb_positive_explanations=nb_positive_explanations,
                nb_negative_explanations=nb_negative_explanations,
                minimum_computation_time=np.round(min(computation_times), 3) if computation_times else None,
                maximum_computation_time=np.round(max(computation_times), 3) if computation_times else None,
                average_computation_time=np.round(np.mean(computation_times), 3) if computation_times else None,
                standard_deviation_computation_time=(np.round(np.std(computation_times), 3) if computation_times
                                                     else None),
                median_computation_time=np.round(np.median(computation_times), 3) if computation_times else None,
                first_quartile_computation_time=(np.round(np.percentile(computation_times, 25), 3) if computation_times
                                                 else None),
                third_quartile_computation_time=(np.round(np.percentile(computation_times, 75), 3) if computation_times
                                                 else None),
                computation_times=computation_times
            )

            # Display analysis results related to the question template
            template_analysis = analysis[question_template_id]
            print(f"Explanations related to {question_template.id} computed")
            print(f"Nb of possible questions: {nb_possible_questions}")
            if nb_rejected_computations > 0:
                print(f"Nb of rejected computations: {nb_rejected_computations}")
            print(f"Nb of executed computations: {nb_executed_computations}")
            if nb_interrupted_computations > 0:
                print(f"Nb of interrupted computations: {nb_interrupted_computations}")
                print(f"Nb of inter. comput. w. solution : {nb_interruptions_with_solution}")
                print(f"Nb of inter. comput. wo. solution : {nb_interruptions_without_solution}")
            print(f"Nb of completed computations: {nb_completed_computations}")
            positive_rate = \
                nb_positive_explanations / nb_completed_computations if nb_completed_computations > 0 else 0
            print(f"Nb of positive explanations: {nb_positive_explanations} ({round(positive_rate * 100, 2)}%)")
            negative_rate = \
                nb_negative_explanations / nb_completed_computations if nb_completed_computations > 0 else 0
            print(f"Nb of negative explanations: {nb_negative_explanations} ({round(negative_rate * 100, 2)}%)")
            print(f"Minimum computation time: {template_analysis['minimum_computation_time']}s")
            print(f"Maximum computation time: {template_analysis['maximum_computation_time']}s")
            print(f"Average computation time: {template_analysis['average_computation_time']}s")
            print(f"Standard deviation computation time: "
                  f"{template_analysis['standard_deviation_computation_time']}s")
            print(f"Median computation time: {template_analysis['median_computation_time']}s")
            print(f"First quartile computation time: {template_analysis['first_quartile_computation_time']}s")
            print(f"Third quartile computation time: {template_analysis['third_quartile_computation_time']}s")
            print("")

    return analysis


########
# Main #
########


if __name__ == '__main__':
    # compute_contrastive_explanations_about_demo_solution_in_one_file()
    launch_explainer_UI_on_demo_solution()
    # launch_explainer_UI_on_default_solution()
