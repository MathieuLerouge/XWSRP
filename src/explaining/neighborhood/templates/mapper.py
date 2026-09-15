# Local libraries
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.templates import insertion, reordering, swap
from src.explaining.questioning.question import ContrastiveQuestion, Question
from src.explaining.questioning.questions_templates_bank import (
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)


##########
# Mapper #
##########

class Mapper:
    """
    Maps a contrastive question to the Neighborhood it induces,
    using each question template's hand-wired mapping to elementary operators and scope restrictions.
    """

    @staticmethod
    def map(question: Question) -> Neighborhood:
        """
        Return the Neighborhood induced by the given question.

        Args:
            question: The contrastive question to map.

        Returns:
            The Neighborhood induced by the question.

        Raises:
            TypeError: If question is not a ContrastiveQuestion.
            NotImplementedError: If the question's template is not yet handled by this mapper.
        """
        if not isinstance(question, ContrastiveQuestion):
            raise TypeError(f"Question {question} is not a contrastive question")
        template_id = question.template.id
        if template_id == WHY_NOT_INS_1:
            return insertion.map_ins_1(question)
        elif template_id == WHY_NOT_INS_2A:
            return insertion.map_ins_2a(question)
        elif template_id == WHY_NOT_INS_2B:
            return insertion.map_ins_2b(question)
        elif template_id == WHY_NOT_INS_2C:
            return insertion.map_ins_2c(question)
        elif template_id == WHY_NOT_INS_3:
            return insertion.map_ins_3(question)
        elif template_id == WHY_NOT_SWP_1:
            return swap.map_swp_1(question)
        elif template_id == WHY_NOT_SWP_2A:
            return swap.map_swp_2a(question)
        elif template_id == WHY_NOT_SWP_2B:
            return swap.map_swp_2b(question)
        elif template_id == WHY_NOT_SWP_2C:
            return swap.map_swp_2c(question)
        elif template_id == WHY_NOT_SWP_3:
            return swap.map_swp_3(question)
        elif template_id == WHY_NOT_ORD_LAT_1:
            return reordering.map_ord_1a(question)
        elif template_id == WHY_NOT_ORD_EAR_1:
            return reordering.map_ord_1b(question)
        elif template_id == WHY_NOT_ORD_LAT_2:
            return reordering.map_ord_2a(question)
        elif template_id == WHY_NOT_ORD_EAR_2:
            return reordering.map_ord_2b(question)
        elif template_id == WHY_NOT_ORD_2:
            return reordering.map_ord_2c(question)
        elif template_id == WHY_NOT_ORD_3:
            return reordering.map_ord_3(question)
        else:
            raise NotImplementedError(f"The neighborhood mapping for template {template_id} is not yet handled")
