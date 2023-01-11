#! /usr/bin/env python3
# coding: utf-8


# Local library
from src.evaluation.routine import prepare_explainer_UI_on_evaluation_solution


explainer_UI = prepare_explainer_UI_on_evaluation_solution(instance_index=1)
# explainer_UI.disable_explanations_representation()
server = explainer_UI.application.server
