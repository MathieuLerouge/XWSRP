# Local libraries
from main_configuration import *
from src.teaching.processes import run_IP_optimization_on_teaching_instances, \
    run_feasibility_check_on_provided_solutions


########
# Main #
########

def teaching_main():
    """
    Main function of the teaching-relative part of the project.
    There are two main processes:
    - solving teaching instances (provided in the default inputs directory) thanks to IP optimization;
    - checking the feasibility of teaching solutions (provided in the default inputs directory).
    :return: None
    """
    if MAIN_PROCESS == TEACHING_PROCESS:
        if MAIN_PROCESS_AMONG_TEACHING_ONES == TEACHING_INSTANCE_IP_SOLVING_PROCESS:
            run_IP_optimization_on_teaching_instances(SOLVING_TIME_LIMIT_IN_SECONDS, MUTE_SOLVING_PROCESS)
        elif MAIN_PROCESS_AMONG_TEACHING_ONES == TEACHING_SOLUTION_FEASIBILITY_CHECK_PROCESS:
            run_feasibility_check_on_provided_solutions(WRITE_TEACHING_SOLUTIONS_FEASIBILITY_CHECKS_INTO_A_FILE,
                                                        WRITE_TEACHING_SOLUTIONS_ANALYSIS_INTO_FILES,
                                                        SHOW_TEACHING_SOLUTIONS_FIGURES_WHILE_CHECKING_FEASIBILITY,
                                                        SAVE_TEACHING_SOLUTIONS_FIGURES_WHILE_CHECKING_FEASIBILITY,
                                                        TOLERANCE_IN_MINUTES_IN_TIME_CONSTRAINTS_CHECK)
        else:
            raise ValueError(f"The process {MAIN_PROCESS_AMONG_TEACHING_ONES} is not a teaching process")
    else:
        raise ValueError(f"The process {MAIN_PROCESS} is not a teaching process")


if __name__ == '__main__':
    teaching_main()
