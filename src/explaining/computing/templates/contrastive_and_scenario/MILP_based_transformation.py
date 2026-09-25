# Local libraries
from src.explaining.modeling.solution import EditableSolution
from src.explaining.computing.templates.common.description import TransformationDescriptionBuilder
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.computing.templates.contrastive_and_scenario.MILP_model.reordering3 import MILPModelForReordering3
from src.explaining.computing.templates.common.runner import MILPTransformationRunner
from src.explaining.computing.templates.contrastive_and_scenario.extraction import \
    extract_support_sequence_and_conflict


#############################
# Reordering transformation #
#############################

def apply_ord_3(solution: EditableSolution, employee_name: str, time_limit: int = None):
    """
    Apply induced transformation and get explanation content for answering (Ord,3) contrastive question:
    "Why is employee {Employee} not performing the activities of their route in another order?"

    :param solution: the solution to explain (EditableSolution)
    :param employee_name: the name of the employee mentioned in the question (str)
    :param time_limit: the time limit in seconds for computing the transformation (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    employee = solution.instance.get_employee_by_name(employee_name)
    sequence = solution.get_sequence(employee)
    model = MILPModelForReordering3(sequence)
    if time_limit is not None:
        model.solving_time_limit = time_limit
    MILPTransformationRunner.solve_or_raise(model)
    pivot_task = model.pivot_task
    support_solution, conflict, description_of_support_sequence = \
        extract_support_sequence_and_conflict(solution, employee, pivot_task, model)
    descriptions = TransformationDescriptionBuilder.for_reordering_route(employee, description_of_support_sequence)
    return TransformationResult(support_solution, conflict, descriptions)
