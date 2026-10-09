# Third-party library
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

# Local library
from src.explaining.explanation.free.grounding import find_ungrounded_mentions

# Keys of the validation context WrittenExplanation checks its text against (see ExplanationWriter).
ALLOWED_TIMES_KEY = "allowed_times"
ALLOWED_NAMES_KEY = "allowed_names"
KNOWN_NAMES_KEY = "known_names"
REQUIRED_NAMES_KEY = "required_names"


######################
# WrittenExplanation #
######################

class WrittenExplanation(BaseModel):
    """
    The top-level object an LLM wording an explanation returns.

    When validated with a context (see ExplanationWriter), its text is checked to state no time and no name
    the facts it was worded from do not hold, and to state the names the question does,
    so that instructor sends it back for another attempt otherwise.
    """

    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        description="The explanation, in plain text, in the requested language, stating only what the FACTS say."
    )

    @field_validator("text")
    @classmethod
    def _check_text_is_grounded(cls, text: str, info: ValidationInfo) -> str:
        """
        Returns:
            The text, unchanged, once it is checked to be grounded in the facts.

        Raises:
            ValueError: If the text is empty, states a time or a name the validation context does not allow,
                or misses a name it requires.
        """
        if text.strip() == "":
            raise ValueError("The explanation text must not be empty")
        context = info.context
        if context is None:
            return text
        ungrounded_mentions = find_ungrounded_mentions(
            text, context[ALLOWED_TIMES_KEY], context[ALLOWED_NAMES_KEY], context[KNOWN_NAMES_KEY],
            context.get(REQUIRED_NAMES_KEY)
        )
        if len(ungrounded_mentions) > 0:
            raise ValueError(
                "The explanation does not stick to the FACTS: " + ", ".join(ungrounded_mentions)
                + ". Restate it using only the times and names written in the FACTS, spelled exactly as there."
            )
        return text
