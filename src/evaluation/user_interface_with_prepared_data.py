# Local libraries
from src.evaluation.constants import ACTIVATED_QUESTIONS_TEMPLATES_IDS_FOR_EVALUATION
from src.evaluation.reading import get_solution_for_evaluation
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.interface.explainer_web_UI import ExplainerWebGUI
from src.explaining.questioning.questions_templates_bank import LANGUAGE_FRENCH_KEY
from src.modeling.solution import Solution


#################################
# User interface for evaluation #
#################################


def prepare_explainer_UI_for_evaluation(solution: Solution, language: str = LANGUAGE_FRENCH_KEY):
    explainer = Explainer(solution)
    explainer.set_language(language)
    explainer.activate_only_questions_templates(ACTIVATED_QUESTIONS_TEMPLATES_IDS_FOR_EVALUATION)
    explainer.disable_history()
    explainer.disable_scenario_explanations()
    explainer.disable_counterfactual_explanations()
    explainer.disable_using_already_computed_contrastive_explanations()
    explainer.disable_exporting_automatically_single_contrastive_explanations()
    return ExplainerWebGUI(explainer)


def prepare_explainer_UI_on_evaluation_solution(instance_index: int = 0):
    return prepare_explainer_UI_for_evaluation(get_solution_for_evaluation(instance_index))


def launch_explainer_UI_on_evaluation_solution():
    explainer_UI = prepare_explainer_UI_on_evaluation_solution()
    explainer_UI.launch()
