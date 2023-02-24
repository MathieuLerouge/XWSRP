# Local libraries
from src.evaluation.constants import ACTIVATED_QUESTIONS_TEMPLATES_IDS_FOR_EVALUATION, EVALUATION_EXPERIMENTS_PARAMETERS
from src.evaluation.prepared_data_extraction import get_solution_for_evaluation, \
    get_explanations_for_evaluation_directory_path
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.explainer_web_UI import ExplainerWebGUI
from src.explaining.questioning.questions_templates_bank import LANGUAGE_FRENCH_KEY
from src.modeling.solution import Solution


#################################
# User interface for evaluation #
#################################


def prepare_explainer_GUI_for_evaluation_given_parameters(solution: Solution, enable_explanations: bool = True,
                                                          enable_explanations_representation: bool = True,
                                                          language: str = LANGUAGE_FRENCH_KEY):
    """
    Prepare the explainer GUI for evaluation.
    NB: the solution is assumed to be a solution prepared specifically for evaluation.

    :param solution: the solution to explain (Solution)
    :param enable_explanations: whether to enable explanations (bool)
    :param enable_explanations_representation: whether to enable explanations representation (bool)
    :param language: the language to use (str) (default language is French)
    :return: the explainer GUI (ExplainerWebGUI)
    """
    explainer = Explainer(solution)
    explainer.set_language(language)
    explainer.activate_only_questions_templates(ACTIVATED_QUESTIONS_TEMPLATES_IDS_FOR_EVALUATION)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.contrastive_explanations_inputs_directory_relative_path = get_explanations_for_evaluation_directory_path()
    explainer.enable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    if enable_explanations:
        title = "Visualize Plannings Plus"
        subtitle = "Outil de visualisation et d'explication des données de ComputePlannings"
    else:
        title = "Visualize Plannings"
        subtitle = "Outil de visualisation des données de ComputePlannings"
    explainer_GUI = ExplainerWebGUI(explainer, title, subtitle, enabling_explanations=enable_explanations)
    explainer_GUI.enable_tab_description_panels()
    if enable_explanations:
        explainer_GUI.enable_contrastive_statistics()
    if not enable_explanations_representation:
        explainer_GUI.disable_explanations_representation()
    return explainer_GUI


def prepare_explainer_GUI_for_evaluation_given_experiment_version(version: str):
    """
    Prepare the explainer GUI corresponding to the given evaluation experiment version.
    NB: the version is associated with parameters which defines the solution to explain,
    whether to enable explanations and whether to enable explanations representation.

    :param version: the evaluation experiment version (str)
    :return: the explainer GUI (ExplainerWebGUI)
    """
    parameters = EVALUATION_EXPERIMENTS_PARAMETERS[version]
    solution = get_solution_for_evaluation(parameters['instance_index'])
    enable_explanations = parameters['enable_explanations']
    enable_explanations_representation = parameters['enable_explanations_representation']
    return prepare_explainer_GUI_for_evaluation_given_parameters(solution, enable_explanations,
                                                                 enable_explanations_representation)


def launch_explainer_GUI_for_evaluation_given_experiment_version(version: str):
    """
    Launch the explainer GUI corresponding to the given evaluation experiment version.
    NB: the version is associated with parameters which defines the solution to explain,
    whether to enable explanations and whether to enable explanations representation.

    :param version: the evaluation experiment version (str)
    :return: None
    """
    explainer_GUI = prepare_explainer_GUI_for_evaluation_given_experiment_version(version)
    explainer_GUI.launch()
