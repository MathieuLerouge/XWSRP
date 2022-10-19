#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from checking.feasibility import check_feasibility
from drawing.figuresmanager import FiguresManager
from extraction.solution import extract_solution_from_file
from utils.constants import LINE_BREAK_STRING, OUTPUTS_DIRECTORY
from utils.display import create_title_frame
from utils.files import get_solutions_files_names
from writing.common import write_text_to_file
from writing.analysis import write_solution_analysis


from optimization.localsearch.solution import SolutionLS


# Checking routine function
def apply_checking_routine(ignore_employees_unavailabilities: bool = False,
                           ignore_tasks_unavailabilities: bool = False, ignore_lunch_breaks: bool = False,
                           ignore_solving_method: bool = False, ignore_instance_version: bool = False,
                           save_checking_as_file: bool = True, save_analysis: bool = True,
                           show_figures: bool = True, save_figures: bool = False):
    solutions_files_names = get_solutions_files_names()
    solutions_checking_text = ""
    for solution_filename in solutions_files_names:
        solution = extract_solution_from_file(
            solution_filename, ignore_employees_unavailabilities, ignore_tasks_unavailabilities, ignore_lunch_breaks,
            ignore_instance_version, ignore_solving_method
        )
        solution.compute_KPIs()
        feasible, checking_text = check_feasibility(solution)
        title_frame = create_title_frame("Checking of " + solution.name)
        checking_text = (title_frame + LINE_BREAK_STRING + LINE_BREAK_STRING +
                         checking_text + LINE_BREAK_STRING + LINE_BREAK_STRING)
        if feasible and save_analysis:
            write_solution_analysis(solution)
        if show_figures or save_figures:
            figures_manager = FiguresManager(solution)
            if show_figures:
                print(checking_text)
                figures_manager.show_figures()
            if save_figures:
                figures_manager.save_figures()
        solutions_checking_text += checking_text
        solution = SolutionLS.from_Solution(solution)
        print(solution)
    solutions_checking_text = solutions_checking_text.removesuffix(LINE_BREAK_STRING)
    if save_checking_as_file:
        write_text_to_file(solutions_checking_text, OUTPUTS_DIRECTORY + "/SolutionsChecks.txt")
    if not show_figures:
        print("")
        print(solutions_checking_text)


# Main function
def main():
    apply_checking_routine(
        ignore_employees_unavailabilities=False, ignore_tasks_unavailabilities=False, ignore_lunch_breaks=False,
        ignore_solving_method=False, ignore_instance_version=False,
        save_checking_as_file=False, save_analysis=False, show_figures=False, save_figures=False
    )


if __name__ == '__main__':
    main()
