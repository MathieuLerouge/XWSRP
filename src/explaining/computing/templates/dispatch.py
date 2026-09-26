# Standard library
from typing import Callable, Optional

# Local libraries
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.computing.templates.contrastive_and_scenario.insertion import InsertionApplier
from src.explaining.computing.templates.contrastive_and_scenario.reordering import ReorderingApplier
from src.explaining.computing.templates.contrastive_and_scenario.swap import SwapApplier
from src.explaining.computing.templates.counterfactual.insertion import InsertionWithAlterationsApplier
from src.explaining.computing.templates.counterfactual.reordering import ReorderingWithAlterationsApplier
from src.explaining.computing.templates.counterfactual.swap import SwapWithAlterationsApplier
from src.explaining.modeling.solution import EditableSolution
from src.explaining.questioning.question import ContrastiveQuestion, CounterfactualQuestion, Question, ScenarioQuestion
from src.explaining.questioning.questions_templates_bank import \
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3, \
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3, \
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3

# Global variables
POLYNOMIAL_CONTRASTIVE_TRANSFORMATIONS: dict[str, Callable[..., TransformationResult]] = {
    WHY_NOT_INS_1: InsertionApplier.apply_1,
    WHY_NOT_INS_2A: InsertionApplier.apply_2a,
    WHY_NOT_INS_2B: InsertionApplier.apply_2b,
    WHY_NOT_INS_2C: InsertionApplier.apply_2c,
    WHY_NOT_SWP_1: SwapApplier.apply_1,
    WHY_NOT_SWP_2A: SwapApplier.apply_2a,
    WHY_NOT_SWP_2B: SwapApplier.apply_2b,
    WHY_NOT_SWP_2C: SwapApplier.apply_2c,
    WHY_NOT_ORD_LAT_1: ReorderingApplier.apply_1a,
    WHY_NOT_ORD_EAR_1: ReorderingApplier.apply_1b,
    WHY_NOT_ORD_LAT_2: ReorderingApplier.apply_2a,
    WHY_NOT_ORD_EAR_2: ReorderingApplier.apply_2b,
    WHY_NOT_ORD_2: ReorderingApplier.apply_2c,
}
MILP_CONTRASTIVE_TRANSFORMATIONS: dict[str, Callable[..., TransformationResult]] = {
    WHY_NOT_INS_3: InsertionApplier.apply_3,
    WHY_NOT_SWP_3: SwapApplier.apply_3,
    WHY_NOT_ORD_3: ReorderingApplier.apply_3,
}
# Every counterfactual transformation goes through a MILP model, so they all share one signature.
# NB: (Ins,2c) and (Swp,2c) are missing on purpose: they ask about any employee rather than a named one,
# which the counterfactual transformations do not handle.
COUNTERFACTUAL_TRANSFORMATIONS: dict[str, Callable[..., TransformationResult]] = {
    WHY_NOT_INS_1: InsertionWithAlterationsApplier.apply_1,
    WHY_NOT_INS_2A: InsertionWithAlterationsApplier.apply_2a,
    WHY_NOT_INS_2B: InsertionWithAlterationsApplier.apply_2b,
    WHY_NOT_INS_3: InsertionWithAlterationsApplier.apply_3,
    WHY_NOT_SWP_1: SwapWithAlterationsApplier.apply_1,
    WHY_NOT_SWP_2A: SwapWithAlterationsApplier.apply_2a,
    WHY_NOT_SWP_2B: SwapWithAlterationsApplier.apply_2b,
    WHY_NOT_SWP_3: SwapWithAlterationsApplier.apply_3,
    WHY_NOT_ORD_LAT_1: ReorderingWithAlterationsApplier.apply_1a,
    WHY_NOT_ORD_EAR_1: ReorderingWithAlterationsApplier.apply_1b,
    WHY_NOT_ORD_LAT_2: ReorderingWithAlterationsApplier.apply_2a,
    WHY_NOT_ORD_EAR_2: ReorderingWithAlterationsApplier.apply_2b,
    WHY_NOT_ORD_2: ReorderingWithAlterationsApplier.apply_2c,
    WHY_NOT_ORD_3: ReorderingWithAlterationsApplier.apply_3,
}


############################
# TransformationDispatcher #
############################

class TransformationDispatcher:
    """
    Hands a question to the transformation its template calls for.
    """

    @staticmethod
    def handle_contrastive_or_scenario_question(
            solution: EditableSolution, question: Question,
            milp_solving_time_limit: Optional[int] = None
    ) -> TransformationResult:
        """
        Apply the transformation the given contrastive or scenario question induces.

        Args:
            solution: The solution to explain.
            question: The question that induces the transformation.
            milp_solving_time_limit: The solving time limit in seconds, for the templates computed
                through a MILP model. The others ignore it, being computed in polynomial time.

        Returns:
            The result of the applied transformation.

        Raises:
            TypeError: if the question is neither a contrastive nor a scenario question.
            NotImplementedError: if no transformation is registered for the question's template.
        """
        if not isinstance(question, (ContrastiveQuestion, ScenarioQuestion)):
            raise TypeError(f"Question {question} is not a contrastive or scenario question")
        question_template_id = question.template.id
        fields_values = question.fields_values
        if question_template_id in POLYNOMIAL_CONTRASTIVE_TRANSFORMATIONS:
            return POLYNOMIAL_CONTRASTIVE_TRANSFORMATIONS[question_template_id](solution, *fields_values)
        if question_template_id in MILP_CONTRASTIVE_TRANSFORMATIONS:
            transformation = MILP_CONTRASTIVE_TRANSFORMATIONS[question_template_id]
            return transformation(solution, *fields_values, milp_solving_time_limit)
        raise NotImplementedError(f"Transformation induced by the template {question_template_id} is not handled")

    @staticmethod
    def handle_counterfactual_question(
            solution: EditableSolution, question: CounterfactualQuestion,
            milp_solving_time_limit: Optional[int] = None
    ) -> TransformationResult:
        """
        Apply the transformation the given counterfactual question induces.

        Args:
            solution: The solution to explain.
            question: The question to answer.
            milp_solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.

        Raises:
            NotImplementedError: if no transformation is registered for the question's template.
        """
        question_template_id = question.template.id
        if question_template_id not in COUNTERFACTUAL_TRANSFORMATIONS:
            raise NotImplementedError(f"The transformation induced by the template {question_template_id} "
                                      f"is not handled for counterfactual questions")
        transformation = COUNTERFACTUAL_TRANSFORMATIONS[question_template_id]
        return transformation(solution, *question.fields_values,
                              question.instance_parameter_alteration_bounds, milp_solving_time_limit)
