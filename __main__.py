#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from checking.routine import apply_checking_routine
from explanation.routine import apply_explanation_routine
from optimization.routine import apply_optimization_routine


# Global variables
CHECKING_ROUTINE_KEY = 'checking'
OPTIMIZING_ROUTINE_KEY = 'optimizing'
EXPLAINING_ROUTINE_KEY = 'explaining'

# Variables to set
# - Choose which routine to run
# ROUTINE_KEY = CHECKING_ROUTINE_KEY
# ROUTINE_KEY = CHECKING_ROUTINE_KEY
ROUTINE_KEY = EXPLAINING_ROUTINE_KEY
# - Toggle model assumptions
IGNORE_EMPLOYEES_UNAVAILABILITIES = False
IGNORE_TASKS_UNAVAILABILITIES = True
IGNORE_LUNCH_BREAKS = True
# - Toggle behaviours
SAVING_CHECKING = True
SAVING_ANALYSIS = True
SHOWING_FIGURES = False
SAVING_FIGURES = True
SOLVING_TIME_LIMIT_IN_SECONDS = 3*60


# Main function
def main():
    if ROUTINE_KEY == CHECKING_ROUTINE_KEY:
        apply_checking_routine(SAVING_CHECKING, SAVING_ANALYSIS, SHOWING_FIGURES, SAVING_FIGURES)
    elif ROUTINE_KEY == OPTIMIZING_ROUTINE_KEY:
        apply_optimization_routine(SOLVING_TIME_LIMIT_IN_SECONDS)
    elif ROUTINE_KEY == EXPLAINING_ROUTINE_KEY:
        apply_explanation_routine(IGNORE_EMPLOYEES_UNAVAILABILITIES, IGNORE_TASKS_UNAVAILABILITIES, IGNORE_LUNCH_BREAKS)
    else:
        raise ValueError(f"The routine {ROUTINE_KEY} does not exist")


if __name__ == '__main__':
    main()
