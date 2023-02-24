# Local libraries
from main_configuration import MAIN_PROCESS
from src.explaining.configuration import *
from src.explaining.processes import launch_explainer_UI_on_demo_solution, launch_explainer_UI_on_default_solution
from src.utils.constants import EXPLAINER_ON_DEMO_SOLUTION_PROCESS, EXPLAINER_ON_SOLUTION_IN_DEFAULT_INPUTS_PROCESS


########
# Main #
########


def explaining_main():
    """
    Main function of the explaining module
    There are two main processes:
    - launching the explainer UI on the demo solution
    - launching the explainer UI on the solution in the default inputs directory

    :return: None
    """
    if MAIN_PROCESS == EXPLAINER_ON_DEMO_SOLUTION_PROCESS:
        launch_explainer_UI_on_demo_solution(
            EXPLAINER_DEMO_SOLUTION_LANGUAGE, EXPLAINER_DEMO_SOLUTION_ENABLE_HISTORY,
            EXPLAINER_DEMO_SOLUTION_ENABLE_SCENARIO, EXPLAINER_DEMO_SOLUTION_ENABLE_COUNTERFACTUAL,
            EXPLAINER_DEMO_SOLUTION_ENABLE_USING_ALREADY_COMPUTED_CONTRASTIVE_EXPLANATIONS
        )
    elif MAIN_PROCESS == EXPLAINER_ON_SOLUTION_IN_DEFAULT_INPUTS_PROCESS:
        launch_explainer_UI_on_default_solution(
            EXPLAINER_DEFAULT_SOLUTION_LANGUAGE, EXPLAINER_DEFAULT_SOLUTION_ENABLE_HISTORY,
            EXPLAINER_DEFAULT_SOLUTION_ENABLE_SCENARIO, EXPLAINER_DEFAULT_SOLUTION_ENABLE_COUNTERFACTUAL
        )
    else:
        raise ValueError(f"The process {MAIN_PROCESS} is not an explainer process")


if __name__ == '__main__':
    explaining_main()
