# Standard library
from typing import Optional

# Third-party library
from pydantic import BaseModel, ConfigDict, Field

# Local library
from src.explaining.neighborhood.llm.operator import (
    ExtractedFeasibilityShortfallOperator, ExtractedTaskDeletion
)
from src.explaining.neighborhood.llm.restriction import ExtractedRestriction


#########################
# ExtractedNeighborhood #
#########################

class ExtractedNeighborhood(BaseModel):
    """
    The top-level result an LLM extraction must return: the Neighborhood it induces,
    expressed with raw solution/instance names rather than domain objects,
    bounded to exactly the shape NeighborhoodModel supports today.

    Exactly one feasibility-shortfall operator is required;
    an ExtractedTaskDeletion may optionally be paired alongside it
    (needed for the (Swp,*)-style "remove one task, insert another" questions);
    any number of restrictions may narrow how either may transform the in-scope sequences.
    """

    model_config = ConfigDict(extra="forbid")

    operator: ExtractedFeasibilityShortfallOperator = Field(
        description="The feasibility-shortfall operator (task insertion, task repositioning or "
                    "sequence reordering) the question is asking about."
    )
    deletion: Optional[ExtractedTaskDeletion] = Field(
        default=None,
        description="The task deletion paired alongside the operator, if the question also implies "
                    "removing an already-performed task to make room (e.g. a 'rather than' question)."
    )
    restrictions: list[ExtractedRestriction] = Field(
        default_factory=list,
        description="The scope restrictions narrowing how the operator/deletion may transform the "
                    "in-scope sequences, e.g. to keep the rest of an employee's route unchanged."
    )
