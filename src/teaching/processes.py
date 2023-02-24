# Local libraries
from src.checking.feasibility import check_feasibility, create_multiple_solution_feasibility_checks_file_path
from src.drawing.figuresmanager import FiguresManager
from src.teaching.optimization.programming.model import WSRPIPModelForTeaching
from src.teaching.reading.instance import extract_teaching_instance_from_file
from src.teaching.reading.solution import extract_solution_for_teaching_from_file
from src.utils.constants import LINE_BREAK_STRING
from src.utils.display import print_title_frame, create_title_frame
from src.utils.files import get_paths_of_instances_files_in_given_directory, \
    get_paths_of_solutions_files_in_given_directory
from src.writing.analysis import write_solution_analysis
from src.writing.common import write_text_to_file
from src.writing.solution import write_solution


###################
# IP Optimization #
###################


def run_IP_optimization_on_teaching_instances(solving_process_time_limit_in_seconds: int = 3600,
                                              mute_solving_process: bool = True):
    """
    Solve all the instances located in the default inputs directory.
    Solution files as well as solution analysis files are generated in the default outputs directory.
    Besides, figures about the solution are displayed and saved in the default outputs directory.

    :param solving_process_time_limit_in_seconds: the time limit for solving each instance (int)
    :param mute_solving_process: mute the solving process (bool)
    :return: None
    """

    instances_files_paths = get_paths_of_instances_files_in_given_directory()

    if len(instances_files_paths) == 0:
        print("No instance file found in the default inputs directory")

    for instance_file_path in instances_files_paths:
        print("")

        # Instance extraction
        print_title_frame(f"Instance extraction")
        print("")
        print(f"Instance file path: {instance_file_path}")
        instance = extract_teaching_instance_from_file(instance_file_path)
        print(f"Instance name: {instance.name}")
        print(f"Instance name with version: {instance.name_with_version}")
        print(f"Instance name without version: {instance.name_without_version}")
        print(f"Instance version: {instance.version}")
        print(f"Instance has employee unavailabilities: {instance.has_employee_unavailabilities}")
        print(f"Instance has task unavailabilities: {instance.has_task_unavailabilities}")
        print(f"Instance has lunch breaks: {instance.has_lunch_break}")
        print("Extraction: done")
        print("")

        # Optimization
        print_title_frame(f"IP optimization of {instance.name}")
        print("")
        model = WSRPIPModelForTeaching(instance)
        model.update()
        model.solving_time_limit = solving_process_time_limit_in_seconds
        print(f"IP model name: {model.name}")
        print(f"IP model version: {model.version}")
        model.optimize(mute_solving_process)
        print("Optimization: done")
        print("")

        # Building solution and checking feasibility
        print_title_frame(f"Building solution and checking feasibility")
        print("")
        solution = model.solution
        if check_feasibility(solution, covering=(model.version == 1))[0]:
            raise Exception("The solution given by the optimization is not feasible")
        print("Solution feasible: True")
        print(f"Solution name: {solution.name}")
        print(f"Solution name with solving method: {solution.name_with_solving_method}")
        print(f"Solution name without solving method: {solution.name_without_solving_method}")
        print("")

        # Solution writing
        print_title_frame("Solution writing")
        print("")
        solution.compute_KPIs()
        # solution.tighten_times()
        write_solution(solution)
        write_solution_analysis(solution)
        print("Writing: done")
        print("")

        # Solution representation
        print_title_frame(f"Solution representation")
        print("")
        figures_manager = FiguresManager(solution)
        figures_manager.show_figures(solution)
        figures_manager.save_figures()
        print("Representation: done")
        print("")


##############################
# Solution feasibility check #
##############################


def run_feasibility_check_on_provided_solutions(save_solutions_feasibility_check_as_file: bool,
                                                save_solutions_analysis_as_files: bool,
                                                show_solutions_figures: bool, save_solutions_figures: bool,
                                                tolerance_in_minutes: int = 0):
    """
    Check the feasibility of all the solutions located in the default inputs directory.

    :param save_solutions_feasibility_check_as_file: save the feasibility check as a file (bool)
    :param save_solutions_analysis_as_files: save the solutions analysis as files (bool)
    :param show_solutions_figures: show the figures of the solutions (bool)
    :param save_solutions_figures: save the figures of the solutions (bool)
    :param tolerance_in_minutes: tolerance in minutes to consider when checking time constraints (int)
    :return: None
    """
    solutions_files_paths = get_paths_of_solutions_files_in_given_directory()
    if len(solutions_files_paths) == 0:
        print("No solution file found in the default inputs directory")
    solutions_checking_text = ""
    for solution_file_path in solutions_files_paths:
        solution = extract_solution_for_teaching_from_file(solution_file_path)
        solution.compute_KPIs()
        feasible, checking_text = check_feasibility(solution, tolerance_in_minutes=tolerance_in_minutes)
        title_frame = create_title_frame(f"Checking of {solution.name}")
        checking_text = (title_frame + LINE_BREAK_STRING + LINE_BREAK_STRING +
                         checking_text + LINE_BREAK_STRING + LINE_BREAK_STRING)
        if feasible and save_solutions_analysis_as_files:
            write_solution_analysis(solution)
        if show_solutions_figures or save_solutions_figures:
            figures_manager = FiguresManager(solution)
            if show_solutions_figures:
                print(checking_text.removesuffix(LINE_BREAK_STRING))
                figures_manager.show_figures()
            if save_solutions_figures:
                figures_manager.save_figures()
        solutions_checking_text += checking_text
        print(solution)
        print("")
    solutions_checking_text = solutions_checking_text.removesuffix(LINE_BREAK_STRING)
    if save_solutions_feasibility_check_as_file:
        write_text_to_file(solutions_checking_text, create_multiple_solution_feasibility_checks_file_path())
    if not show_solutions_figures:
        print("")
        print(solutions_checking_text)
