from src.evaluation.routine import prepare_explainer_UI

explainer_UI = prepare_explainer_UI()
server = explainer_UI.application.server
explainer_UI.launch()
