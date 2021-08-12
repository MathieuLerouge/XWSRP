#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from checking.feasibility import check_feasibility
from explanation.explainer import Explainer
from explanation.explainer_UI import ExplainerUI
from extraction.solution import extract_solution_from_file
from utils.constants import INPUTS_DIRECTORY
from utils.display import print_title_frame
from utils.files import get_solutions_files_names


def apply_explanation_routine(ignore_employees_unavailabilities: bool = False,
                              ignore_tasks_unavailabilities: bool = True,
                              ignore_lunch_breaks: bool = True):
    try:
        solution_file_name = get_solutions_files_names()[0]
    except IndexError:
        raise FileNotFoundError(f"There are no solutions files found in directory {INPUTS_DIRECTORY}")
    ignore_instance_version = True
    ignore_solving_method = True
    solution = extract_solution_from_file(
        solution_file_name, ignore_employees_unavailabilities, ignore_tasks_unavailabilities, ignore_lunch_breaks,
        ignore_instance_version, ignore_solving_method
    )
    if not check_feasibility(solution)[0]:
        raise ValueError(f"The solution {solution.name} is not feasible")
    print("")
    print_title_frame(f"Explaining {solution.name}")
    print("")
    explainer = Explainer(solution)
    explainerUI = ExplainerUI(explainer)
    explainerUI.display()


if __name__ == '__main__':
    apply_explanation_routine()
