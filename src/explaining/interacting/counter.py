# Standard library
from enum import Enum

# Local library
from src.explaining.question.predefined.question import (
    ContrastiveQuestion, CounterfactualQuestion, ScenarioQuestion, PredefinedQuestion
)


################
# QuestionType #
################

class QuestionType(Enum):
    """Enum for the different types of predefined questions that can be counted."""
    CONTRASTIVE = "contrastive"
    SCENARIO = "scenario"
    COUNTERFACTUAL = "counterfactual"


######################
# ExplanationCounter #
######################

class ExplanationCounter:
    """
    Tracks how many times each question template has been asked, for each question type.
    
    This class centralizes the counting functionality for predefined questions,
    reducing the size of the Explainer class.
    """

    def __init__(self, template_ids: list[str]):
        """
        Initialize counters for all template IDs across all question types.
        
        Args:
            template_ids: List of template IDs to initialize counters for.
        """
        self._counters: dict[QuestionType, dict[str, int]] = {}
        for qtype in QuestionType:
            self._counters[qtype] = {template_id: 0 for template_id in template_ids}

    def increase(self, question_type: QuestionType, template_id: str):
        """
        Increment the counter for a specific question type and template ID.
        
        Args:
            question_type: The type of question being asked.
            template_id: The ID of the template being asked.
        """
        if template_id not in self._counters[question_type]:
            self._counters[question_type][template_id] = 0
        self._counters[question_type][template_id] += 1

    def get_count(self, question_type: QuestionType, template_id: str) -> int:
        """
        Get the count for a specific question type and template ID.
        
        Args:
            question_type: The type of question to get the count for.
            template_id: The ID of the template to get the count for.
            
        Returns:
            The number of times this template has been asked for this question type.
        """
        return self._counters[question_type].get(template_id, 0)

    def reset(self):
        """Reset all counters for all question types to zero."""
        for qtype in self._counters:
            for template_id in self._counters[qtype]:
                self._counters[qtype][template_id] = 0

    def reset_for_type(self, question_type: QuestionType):
        """
        Reset counters for a specific question type to zero.
        
        Args:
            question_type: The question type to reset counters for.
        """
        for template_id in self._counters[question_type]:
            self._counters[question_type][template_id] = 0

    def increase_question_count(self, question: PredefinedQuestion):
        """
        Increases by one the asked count of the given question's template.
        
        Args:
            question: The predefined question that was just asked.
        
        Raises:
            ValueError: if the question is of a kind this counter does not track.
        """
        if isinstance(question, ContrastiveQuestion):
            self.increase(QuestionType.CONTRASTIVE, question.template.id)
        elif isinstance(question, ScenarioQuestion):
            self.increase(QuestionType.SCENARIO, question.template.id)
        elif isinstance(question, CounterfactualQuestion):
            self.increase(QuestionType.COUNTERFACTUAL, question.template.id)
        else:
            raise ValueError(f"Unknown question type: {type(question)}")
