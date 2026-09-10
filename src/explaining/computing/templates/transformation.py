# Local libraries
from src.explaining.modeling.solution import EditableSolution
from src.explaining.questioning.question import Question, CounterfactualQuestion, ContrastiveQuestion, ScenarioQuestion
from src.explaining.questioning.questions_templates_bank import *
from src.explaining.computing.templates.contrastive_and_scenario.LS_based_transformation import \
    apply_ins_1, apply_ins_2a, apply_ins_2b, apply_ins_2c, \
    apply_swp_1, apply_swp_2a, apply_swp_2b, apply_swp_2c, \
    apply_ord_1a, apply_ord_1b, apply_ord_2a, apply_ord_2b, apply_ord_2c
from src.explaining.computing.templates.contrastive_and_scenario.ILP_based_transformation import \
    apply_ins_3, apply_swp_3, apply_ord_3
from src.explaining.computing.templates.counterfactual.ILP_based_transformation import \
    apply_ctf_ins_1, apply_ctf_ins_2a, apply_ctf_ins_2b, apply_ctf_ins_3, \
    apply_ctf_swp_1, apply_ctf_swp_2a, apply_ctf_swp_3, \
    apply_ctf_ord_1a, apply_ctf_ord_1b, apply_ctf_ord_2a, apply_ctf_ord_2b, apply_ctf_ord_2c, apply_ctf_ord_3, \
    apply_ctf_swp_2b


#####################################
# Contrastive and scenario question #
#####################################

def apply_transformation_induced_by_contrastive_or_scenario_question(solution: EditableSolution, question: Question,
                                                                     time_limit_for_ILP_computation: int = None):
    """
    Apply the transformation induced by the (contrastive or scenario) question to the solution
    NB: a time limit can be set for transformations that require ILP computation

    :param solution: the solution to explain (EditableSolution)
    :param question: the question that induces the transformation (Question)
    :param time_limit_for_ILP_computation: the time limit in seconds for ILP computation (int)
    :return: a tuple containing the transformed solution (EditableSolution), the infeasibility (Infeasibility if any 
    and the text describing the transformation in various languages (dict)
    """
    if isinstance(question, ContrastiveQuestion) or isinstance(question, ScenarioQuestion):
        question_template_id = question.template.id
        fields_values = question.fields_values
        if question_template_id == WHY_NOT_INS_1:
            return apply_ins_1(solution, fields_values[0], fields_values[1], fields_values[2])
        elif question_template_id == WHY_NOT_INS_2A:
            return apply_ins_2a(solution, fields_values[0], fields_values[1])
        elif question_template_id == WHY_NOT_INS_2B:
            return apply_ins_2b(solution, fields_values[0])
        elif question_template_id == WHY_NOT_INS_2C:
            return apply_ins_2c(solution, fields_values[0])
        elif question_template_id == WHY_NOT_INS_3:
            return apply_ins_3(solution, fields_values[0], fields_values[1], time_limit_for_ILP_computation)
        elif question_template_id == WHY_NOT_SWP_1:
            return apply_swp_1(solution, fields_values[0], fields_values[1], fields_values[2])
        elif question_template_id == WHY_NOT_SWP_2A:
            return apply_swp_2a(solution, fields_values[0], fields_values[1])
        elif question_template_id == WHY_NOT_SWP_2B:
            return apply_swp_2b(solution, fields_values[0])
        elif question_template_id == WHY_NOT_SWP_2C:
            return apply_swp_2c(solution, fields_values[0])
        elif question_template_id == WHY_NOT_SWP_3:
            return apply_swp_3(solution, fields_values[0], fields_values[1], time_limit_for_ILP_computation)
        elif question_template_id == WHY_NOT_ORD_LAT_1:
            return apply_ord_1a(solution, fields_values[0], fields_values[1], fields_values[2])
        elif question_template_id == WHY_NOT_ORD_EAR_1:
            return apply_ord_1b(solution, fields_values[0], fields_values[1], fields_values[2])
        elif question_template_id == WHY_NOT_ORD_LAT_2:
            return apply_ord_2a(solution, fields_values[0], fields_values[1])
        elif question_template_id == WHY_NOT_ORD_EAR_2:
            return apply_ord_2b(solution, fields_values[0], fields_values[1])
        elif question_template_id == WHY_NOT_ORD_2:
            return apply_ord_2c(solution, fields_values[0], fields_values[1])
        elif question_template_id == WHY_NOT_ORD_3:
            return apply_ord_3(solution, fields_values[0], time_limit_for_ILP_computation)
        else:
            raise NotImplementedError(f"Transformation induced by the template {question_template_id} is not handled")
    else:
        raise TypeError(f"Question {question} is not a contrastive or scenario question")


###########################
# Counterfactual question #
###########################

def apply_transformation_induced_by_counterfactual_question(solution: EditableSolution,
                                                            question: CounterfactualQuestion,
                                                            time_limit_for_ILP_computation: int = None):
    """
    Apply the transformation induced by the counterfactual question to the solution

    :param solution: the solution to explain (EditableSolution)
    :param question: the question to answer (Question)
    :param time_limit_for_ILP_computation: the time limit in seconds for ILP computation (int)
    :return: a tuple containing the transformed solution (EditableSolution), the infeasibility (Infeasibility) if any,
    the texts describing the transformation in various languages (dict) and the instance changes (InstanceChanges)
    """
    question_template_id = question.template.id
    fields_values = question.fields_values
    if question_template_id == WHY_NOT_INS_1:
        return apply_ctf_ins_1(solution, fields_values[0], fields_values[1], fields_values[2],
                               question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_INS_2A:
        return apply_ctf_ins_2a(solution, fields_values[0], fields_values[1],
                                question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_INS_2B:
        return apply_ctf_ins_2b(solution, fields_values[0],
                                question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_INS_3:
        return apply_ctf_ins_3(solution, fields_values[0], fields_values[1],
                               question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_SWP_1:
        return apply_ctf_swp_1(solution, fields_values[0], fields_values[1], fields_values[2],
                               question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_SWP_2A:
        return apply_ctf_swp_2a(solution, fields_values[0], fields_values[1],
                                question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_SWP_2B:
        return apply_ctf_swp_2b(solution, fields_values[0],
                                question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_SWP_3:
        return apply_ctf_swp_3(solution, fields_values[0], fields_values[1],
                               question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_ORD_LAT_1:
        return apply_ctf_ord_1a(solution, fields_values[0], fields_values[1], fields_values[2],
                                question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_ORD_EAR_1:
        return apply_ctf_ord_1b(solution, fields_values[0], fields_values[1], fields_values[2],
                                question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_ORD_LAT_2:
        return apply_ctf_ord_2a(solution, fields_values[0], fields_values[1],
                                question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_ORD_EAR_2:
        return apply_ctf_ord_2b(solution, fields_values[0], fields_values[1],
                                question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_ORD_2:
        return apply_ctf_ord_2c(solution, fields_values[0], fields_values[1],
                                question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    elif question_template_id == WHY_NOT_ORD_3:
        return apply_ctf_ord_3(solution, fields_values[0],
                               question.instance_parameter_alteration_bounds, time_limit_for_ILP_computation)
    else:
        raise NotImplementedError(f"The transformation induced by the template {question_template_id} is not handled "
                                  f"for counterfactual questions")
