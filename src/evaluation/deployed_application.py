#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from src.evaluation.configuration import EVALUATION_EXPERIMENT_VERSION
from src.evaluation.user_interface_with_prepared_data import \
    prepare_explainer_GUI_for_evaluation_given_experiment_version


# Define server variable of explainer GUI
explainer_GUI = prepare_explainer_GUI_for_evaluation_given_experiment_version(EVALUATION_EXPERIMENT_VERSION)
server = explainer_GUI.application.server
