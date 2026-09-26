# Local libraries
from src.explaining.modeling.solution import EditableSolution
from src.explaining.questioning.question import Question, CounterfactualQuestion, ContrastiveQuestion, ScenarioQuestion
from src.explaining.questioning.questions_templates_bank import *
from src.explaining.computing.templates.contrastive_and_scenario.insertion import InsertionApplier
from src.explaining.computing.templates.contrastive_and_scenario.reordering import ReorderingApplier
from src.explaining.computing.templates.contrastive_and_scenario.swap import SwapApplier
from src.explaining.computing.templates.counterfactual.insertion import InsertionWithAlterationsApplier
from src.explaining.computing.templates.counterfactual.swap import SwapWithAlterationsApplier
from src.explaining.computing.templates.counterfactual.MILP_based_transformation import \
    apply_ctf_ord_1a, apply_ctf_ord_1b, apply_ctf_ord_2a, apply_ctf_ord_2b, apply_ctf_ord_2c, apply_ctf_ord_3


#####################################
# Contrastive and scenario question #
#####################################

def apply_transformation_induced_by_contrastive_or_scenario_question(solution: EditableSolution, question: Question,
                                                                     milp_solving_time_limit: int = None):
    """
    Apply the transformation induced by the (contrastive or scenario) question to the solution
    NB: a time limit can be set for transformations that require MILP computation

    :param solution: the solution to explain (EditableSolution)
    :param question: the question that induces the transformation (Question)
    :param milp_solving_time_limit: the time limit in seconds for MILP computation (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    if isinstance(question, ContrastiveQuestion) or isinstance(question, ScenarioQuestion):
        question_template_id = question.template.id
        fields_values = question.fields_values
        if question_template_id == WHY_NOT_INS_1:
            return InsertionApplier.apply_1(solution, fields_values[0], fields_values[1], fields_values[2])
        elif question_template_id == WHY_NOT_INS_2A:
            return InsertionApplier.apply_2a(solution, fields_values[0], fields_values[1])
        elif question_template_id == WHY_NOT_INS_2B:
            return InsertionApplier.apply_2b(solution, fields_values[0])
        elif question_template_id == WHY_NOT_INS_2C:
            return InsertionApplier.apply_2c(solution, fields_values[0])
        elif question_template_id == WHY_NOT_INS_3:
            return InsertionApplier.apply_3(solution, fields_values[0], fields_values[1], milp_solving_time_limit)
        elif question_template_id == WHY_NOT_SWP_1:
            return SwapApplier.apply_1(solution, fields_values[0], fields_values[1], fields_values[2])
        elif question_template_id == WHY_NOT_SWP_2A:
            return SwapApplier.apply_2a(solution, fields_values[0], fields_values[1])
        elif question_template_id == WHY_NOT_SWP_2B:
            return SwapApplier.apply_2b(solution, fields_values[0])
        elif question_template_id == WHY_NOT_SWP_2C:
            return SwapApplier.apply_2c(solution, fields_values[0])
        elif question_template_id == WHY_NOT_SWP_3:
            return SwapApplier.apply_3(solution, fields_values[0], fields_values[1], milp_solving_time_limit)
        elif question_template_id == WHY_NOT_ORD_LAT_1:
            return ReorderingApplier.apply_1a(solution, fields_values[0], fields_values[1], fields_values[2])
        elif question_template_id == WHY_NOT_ORD_EAR_1:
            return ReorderingApplier.apply_1b(solution, fields_values[0], fields_values[1], fields_values[2])
        elif question_template_id == WHY_NOT_ORD_LAT_2:
            return ReorderingApplier.apply_2a(solution, fields_values[0], fields_values[1])
        elif question_template_id == WHY_NOT_ORD_EAR_2:
            return ReorderingApplier.apply_2b(solution, fields_values[0], fields_values[1])
        elif question_template_id == WHY_NOT_ORD_2:
            return ReorderingApplier.apply_2c(solution, fields_values[0], fields_values[1])
        elif question_template_id == WHY_NOT_ORD_3:
            return ReorderingApplier.apply_3(solution, fields_values[0], milp_solving_time_limit)
        else:
            raise NotImplementedError(f"Transformation induced by the template {question_template_id} is not handled")
    else:
        raise TypeError(f"Question {question} is not a contrastive or scenario question")


###########################
# Counterfactual question #
###########################

def apply_transformation_induced_by_counterfactual_question(solution: EditableSolution,
                                                            question: CounterfactualQuestion,
                                                            milp_solving_time_limit: int = None):
    """
    Apply the transformation induced by the counterfactual question to the solution

    :param solution: the solution to explain (EditableSolution)
    :param question: the question to answer (Question)
    :param milp_solving_time_limit: the time limit in seconds for MILP computation (int)
    :return: the result of the applied transformation (TransformationResult)
    """
    question_template_id = question.template.id
    fields_values = question.fields_values
    if question_template_id == WHY_NOT_INS_1:
        return InsertionWithAlterationsApplier.apply_1(
            solution, fields_values[0], fields_values[1], fields_values[2],
            question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_INS_2A:
        return InsertionWithAlterationsApplier.apply_2a(
            solution, fields_values[0], fields_values[1],
            question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_INS_2B:
        return InsertionWithAlterationsApplier.apply_2b(
            solution, fields_values[0],
            question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_INS_3:
        return InsertionWithAlterationsApplier.apply_3(
            solution, fields_values[0], fields_values[1],
            question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_SWP_1:
        return SwapWithAlterationsApplier.apply_1(
            solution, fields_values[0], fields_values[1], fields_values[2],
            question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_SWP_2A:
        return SwapWithAlterationsApplier.apply_2a(
            solution, fields_values[0], fields_values[1],
            question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_SWP_2B:
        return SwapWithAlterationsApplier.apply_2b(
            solution, fields_values[0],
            question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_SWP_3:
        return SwapWithAlterationsApplier.apply_3(
            solution, fields_values[0], fields_values[1],
            question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_ORD_LAT_1:
        return apply_ctf_ord_1a(solution, fields_values[0], fields_values[1], fields_values[2],
                                question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_ORD_EAR_1:
        return apply_ctf_ord_1b(solution, fields_values[0], fields_values[1], fields_values[2],
                                question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_ORD_LAT_2:
        return apply_ctf_ord_2a(solution, fields_values[0], fields_values[1],
                                question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_ORD_EAR_2:
        return apply_ctf_ord_2b(solution, fields_values[0], fields_values[1],
                                question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_ORD_2:
        return apply_ctf_ord_2c(solution, fields_values[0], fields_values[1],
                                question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    elif question_template_id == WHY_NOT_ORD_3:
        return apply_ctf_ord_3(solution, fields_values[0],
                               question.instance_parameter_alteration_bounds, milp_solving_time_limit)
    else:
        raise NotImplementedError(f"The transformation induced by the template {question_template_id} is not handled "
                                  f"for counterfactual questions")
