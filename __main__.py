#! /usr/bin/env python3
# coding: utf-8


# Local libraries
# from src.checking.routine import apply_checking_routine
from src.evaluation.routine import prepare_explainer_UI
# from src.explaining.routine import apply_explanation_routine
# from src.optimization.routine import apply_optimization_routine


# # Global variables
# CHECKING_ROUTINE_KEY = 'checking'
# OPTIMIZING_ROUTINE_KEY = 'optimizing'
# EXPLAINING_ROUTINE_KEY = 'explaining'
# EVALUATION_ROUTINE_KEY = 'evaluation'
#
# # Choose which routine to run (Variables to set)
# # ROUTINE_KEY = CHECKING_ROUTINE_KEY
# # ROUTINE_KEY = OPTIMIZING_ROUTINE_KEY
# # ROUTINE_KEY = EXPLAINING_ROUTINE_KEY
# ROUTINE_KEY = EVALUATION_ROUTINE_KEY
#
#
# # Main function
# def main():
#
#     if ROUTINE_KEY == CHECKING_ROUTINE_KEY:
#         # Toggle (Variables to set)
#         ignore_employees_unavailabilities = False
#         ignore_tasks_unavailabilities = False
#         ignore_lunch_breaks = False
#         ignore_solving_method = False
#         ignore_instance_version = False
#         saving_checking = False
#         saving_analysis = False
#         showing_figures = True
#         saving_figures = False
#         # Apply the routine
#         apply_checking_routine(
#             ignore_employees_unavailabilities, ignore_tasks_unavailabilities, ignore_lunch_breaks,
#             ignore_solving_method, ignore_instance_version,
#             saving_checking, saving_analysis, showing_figures, saving_figures
#         )
#
#     elif ROUTINE_KEY == OPTIMIZING_ROUTINE_KEY:
#         # Toggle (Variables to set)
#         solving_time_limit_in_seconds = 3 * 60
#         # Apply the routine
#         apply_optimization_routine(solving_time_limit_in_seconds)
#
#     elif ROUTINE_KEY == EXPLAINING_ROUTINE_KEY:
#         # Apply the routine
#         apply_explanation_routine()
#
#     elif ROUTINE_KEY == EVALUATION_ROUTINE_KEY:
#         explainer_UI = prepare_explainer_UI()
#         server = explainer_UI.application.server
#
#     else:
#         raise ValueError(f"The routine {ROUTINE_KEY} does not exist")

explainer_UI = prepare_explainer_UI()
server = explainer_UI.application.server
explainer_UI.launch()

if __name__ == '__main__':
    explainer_UI = prepare_explainer_UI()
    server = explainer_UI.application.server
    explainer_UI.launch()
