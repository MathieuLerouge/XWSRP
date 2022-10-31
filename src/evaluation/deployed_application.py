#! /usr/bin/env python3
# coding: utf-8


# Local library
from src.evaluation.routine import prepare_explainer_UI


explainer_UI = prepare_explainer_UI()
# explainer_UI.disable_explanations_representation()
server = explainer_UI.application.server
