# Standard library
from typing import Optional

# Local libraries
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.templates.recognizer import Recognizer
from src.explaining.questioning.questions_templates_bank import (
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)

# Global variables
INSERTION_FAMILY = "(Ins,*)"
SWAP_FAMILY = "(Swp,*)"
REORDERING_FAMILY = "(Ord,*)"

# The family each question template belongs to.
FAMILY_BY_TEMPLATE_ID: dict[str, str] = {
    WHY_NOT_INS_1: INSERTION_FAMILY,
    WHY_NOT_INS_2A: INSERTION_FAMILY,
    WHY_NOT_INS_2B: INSERTION_FAMILY,
    WHY_NOT_INS_2C: INSERTION_FAMILY,
    WHY_NOT_INS_3: INSERTION_FAMILY,
    WHY_NOT_SWP_1: SWAP_FAMILY,
    WHY_NOT_SWP_2A: SWAP_FAMILY,
    WHY_NOT_SWP_2B: SWAP_FAMILY,
    WHY_NOT_SWP_2C: SWAP_FAMILY,
    WHY_NOT_SWP_3: SWAP_FAMILY,
    WHY_NOT_ORD_LAT_1: REORDERING_FAMILY,
    WHY_NOT_ORD_EAR_1: REORDERING_FAMILY,
    WHY_NOT_ORD_LAT_2: REORDERING_FAMILY,
    WHY_NOT_ORD_EAR_2: REORDERING_FAMILY,
    WHY_NOT_ORD_2: REORDERING_FAMILY,
    WHY_NOT_ORD_3: REORDERING_FAMILY,
}


#############################
# TemplateComplianceChecker #
#############################

class TemplateComplianceChecker:
    """
    Stateless collection of static methods telling whether a Neighborhood is one of the shapes that
    the tailored per-template pipeline (src/explaining/computing/templates) handles
    - that is, whether it is in the image of Mapper.map over the question catalogue.

    The shapes themselves are Recognizer's to know; this class only reports the family of whatever
    template it recognized. Answers are given by family rather than by template id because that is the
    granularity callers grading an LLM extraction want: a question asked in free text is a question of a
    kind, and which of (Swp,2a)/(Swp,2b) its neighborhood happens to match turns on how many tasks the
    solution leaves unperformed rather than on anything the asker said.

    NB: This predicate is strictly narrower than "a Neighborhood NeighborhoodModel can solve".
    """

    @staticmethod
    def match(neighborhood: Neighborhood) -> Optional[str]:
        """
        Return the question family whose shape the given neighborhood has, or None if it has none of them.

        Args:
            neighborhood: The neighborhood to match.

        Returns:
            INSERTION_FAMILY, SWAP_FAMILY or REORDERING_FAMILY,
            or None if the neighborhood is not one the tailored pipeline's question catalogue produces.
        """
        recognition = Recognizer.recognize_template(neighborhood)
        if recognition is None:
            return None
        template_id, _ = recognition
        return FAMILY_BY_TEMPLATE_ID[template_id]

    @staticmethod
    def is_compliant(neighborhood: Neighborhood) -> bool:
        """
        Return whether the given neighborhood is one the tailored pipeline's question catalogue produces.

        Args:
            neighborhood: The neighborhood to check.

        Returns:
            Whether it has the shape of one of the catalogue's question families.
        """
        return TemplateComplianceChecker.match(neighborhood) is not None
