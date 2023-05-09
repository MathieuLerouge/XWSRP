#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from main_configuration import MAIN_PROCESS
from src.checking.__main__ import analysis_main
from src.explaining.__main__ import explaining_main
from src.optimization.__main__ import optimization_main
from src.teaching.__main__ import teaching_main
from src.utils.constants import *


########
# Main #
########


def main():
    """
    Main process of the project
    NB: configuration parameters about main process can be set in main_configuration.py
    """
    if MAIN_PROCESS == EXPLANATION_PROCESS:
        explaining_main()
    elif MAIN_PROCESS == EVALUATION_PROCESS:
        print("Go to src/evaluation/processes.py to run the evaluation process.")
    elif MAIN_PROCESS in [OPTIMIZATION_PROCESS, REOPTIMIZATION_PROCESS]:
        optimization_main()
    elif MAIN_PROCESS == ANALYSIS_PROCESS:
        analysis_main()
    elif MAIN_PROCESS == TEACHING_PROCESS:
        teaching_main()
    else:
        raise ValueError(f"The process {MAIN_PROCESS} does not exist")


if __name__ == '__main__':
    main()
