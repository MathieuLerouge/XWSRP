# Standard library
from typing import Optional

# Third-party library
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Local library
from src.explaining.neighborhood.llm.extracted_neighborhood import ExtractedNeighborhood


#####################
# ExtractionOutcome #
#####################

class ExtractionOutcome(BaseModel):
    """
    The actual top-level object an LLM extraction returns:
    either a coverable question's ExtractedNeighborhood,
    or an explicit admission that the question can't be expressed with the available primitives,
    together with a short reason.
    """

    model_config = ConfigDict(extra="forbid")

    coverable: bool = Field(
        description="Whether the question can be expressed with the available primitives - one "
                    "feasibility-shortfall operator, an optional paired task deletion, and any "
                    "number of restrictions. False for anything needing more than that (e.g. "
                    "relocating a task between two employees, or more than one operator)."
    )
    neighborhood: Optional[ExtractedNeighborhood] = Field(
        default=None,
        description="The extracted Neighborhood. Required when coverable is True, omitted otherwise."
    )
    reason: Optional[str] = Field(
        default=None,
        description="A short, one-sentence explanation of why the question isn't coverable. "
                    "Required when coverable is False, omitted otherwise."
    )

    @model_validator(mode="after")
    def _check_neighborhood_and_reason_match_coverable(self) -> "ExtractionOutcome":
        """
        Returns:
            ExtractionOutcome: This instance, unchanged, once the cross-field check passes.

        Raises:
            ValueError: If coverable is True but neighborhood is missing, or coverable is False
                but reason is missing.
        """
        if self.coverable and self.neighborhood is None:
            raise ValueError("neighborhood is required when coverable is True")
        if not self.coverable and self.reason is None:
            raise ValueError("reason is required when coverable is False")
        return self
