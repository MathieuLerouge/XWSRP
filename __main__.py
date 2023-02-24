#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from main_configuration import MAIN_PROCESS
from src.explaining.__main__ import explaining_main
from src.teaching.__main__ import teaching_main
from src.utils.constants import *


########
# Main #
########


def main():
    if MAIN_PROCESS in [TEACHING_FEASIBILITY_CHECK_PROCESS, TEACHING_INSTANCE_OPTIMIZATION_PROCESS]:
        teaching_main()
    elif MAIN_PROCESS in [EXPLAINER_ON_DEMO_SOLUTION_PROCESS, EXPLAINER_ON_SOLUTION_IN_DEFAULT_INPUTS_PROCESS]:
        explaining_main()
    elif MAIN_PROCESS == EVALUATION_PROCESS:
        print("Go to src/evaluation/processes.py to run the evaluation routine.")
    else:
        raise ValueError(f"The routine {MAIN_PROCESS} does not exist")


if __name__ == '__main__':
    main()
