# Local libraries
from main_configuration import MAIN_PROCESS, TEACHING_INSTANCE_OPTIMIZATION_PROCESS, TEACHING_FEASIBILITY_CHECK_PROCESS
from src.teaching.configuration import *
from src.teaching.processes import run_IP_optimization_on_teaching_instances, \
    run_feasibility_check_on_provided_solutions


########
# Main #
########


def teaching_main():
    """
    Main function of the teaching-relative part of the project.
    There are two main processes:
    - optimizing teaching instances located in the default inputs directory
    - checking the feasibility of provided solutions.

    :return: None
    """
    if MAIN_PROCESS == TEACHING_INSTANCE_OPTIMIZATION_PROCESS:
        run_IP_optimization_on_teaching_instances(SOLVING_PROCESS_TIME_LIMIT_IN_SECONDS, MUTE_SOLVING_PROCESS)
    elif MAIN_PROCESS == TEACHING_FEASIBILITY_CHECK_PROCESS:
        run_feasibility_check_on_provided_solutions(SAVE_SOLUTIONS_FEASIBILITY_CHECK_AS_FILE,
                                                    SAVE_SOLUTIONS_ANALYSIS_AS_FILES,
                                                    SHOW_FIGURES_IN_FEASIBILITY_CHECK,
                                                    SAVE_FIGURES_IN_FEASIBILITY_CHECK,
                                                    TOLERANCE_IN_MINUTES_IN_TIME_CONSTRAINTS_CHECK)
    else:
        raise ValueError(f"The process {MAIN_PROCESS} is not a teaching process")


if __name__ == '__main__':
    teaching_main()
