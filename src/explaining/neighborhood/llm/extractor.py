# Standard library
import os
from typing import Optional, cast

# Third-party libraries
import instructor
from instructor import Mode
from instructor.core import InstructorRetryException
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

# Local libraries
from src.explaining.neighborhood.assembler import Assembler
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.neighborhood.llm.exceptions import NeighborhoodExtractionError
from src.explaining.neighborhood.llm.extraction_outcome import ExtractionOutcome
from src.explaining.neighborhood.llm.grounder import Grounder
from src.explaining.neighborhood.llm.neighborhood import ExtractedNeighborhood
from src.explaining.neighborhood.llm.prompt import SYSTEM_PROMPT, build_user_prompt
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.modeling.solution import Solution


# Provider prefixes (of a "provider/model-name" string) that need an API key,
# mapped to the environment variable that must carry it
# - checked eagerly at Extractor construction time so a missing key fails clearly right here,
# rather than surfacing a confusing error from deep inside instructor/the provider SDK on the first extract() call.
_PROVIDER_API_KEY_ENV_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
}


def _check_required_api_key_is_set(model: str):
    """
    Raises:
        RuntimeError: If model's provider requires an API key and the corresponding environment variable isn't set.
    """
    provider = model.split("/", 1)[0]
    env_var_name = _PROVIDER_API_KEY_ENV_VARS.get(provider)
    if env_var_name is not None and env_var_name not in os.environ:
        raise RuntimeError(f"Using model {model!r} requires the {env_var_name} environment variable to be set.")


#############
# Extractor #
#############

class Extractor:
    """
    Converts a free-text contrastive question into the Neighborhood it induces,
    using a model-agnostic LLM (via instructor.from_provider) to identify the corresponding primitives.
    """

    def __init__(self, solution: Solution, model: str, mode: Optional[Mode] = None):
        """
        Args:
            solution: The solution every question asked through this Extractor is about.
            model: The instructor model string ("provider/model-name", e.g. "anthropic/claude-...", "ollama/llama3.2").
            mode: Override for instructor's response-parsing mode.
                Left as None (instructor's own per-provider default, typically its TOOLS mode)
                unless the provider needs something else - e.g. Ollama's tool-calling support isn't reliable enough
                for the default mode and needs Mode.MD_JSON instead.

        Raises:
            RuntimeError: If model's provider requires an API key and the corresponding environment variable isn't set.
        """
        _check_required_api_key_is_set(model)
        self._solution = solution
        self._client = instructor.from_provider(model, mode=mode)

    def extract(self, question_text: str) -> Neighborhood:
        """
        Args:
            question_text: A free-text contrastive question.

        Returns:
            Neighborhood: The induced Neighborhood.

        Raises:
            NeighborhoodExtractionError: If question_text cannot be turned into a Neighborhood
                that NeighborhoodModel can solve:
                the LLM exhausted its retries without producing schema-valid output;
                it explicitly reported the question as not coverable;
                it named an entity unresolvable against solution;
                or it named a primitive combination NeighborhoodModel doesn't support yet.
        """
        user_prompt = build_user_prompt(self._solution, question_text)
        messages = [
            ChatCompletionSystemMessageParam(role="system", content=SYSTEM_PROMPT),
            ChatCompletionUserMessageParam(role="user", content=user_prompt),
        ]
        try:
            outcome = self._client.chat.completions.create(
                messages=messages,
                response_model=ExtractionOutcome,
            )
        except InstructorRetryException as error:
            raise NeighborhoodExtractionError() from error
        if not outcome.coverable:
            raise NeighborhoodExtractionError()
        # NB: ExtractionOutcome's own validator guarantees neighborhood is set whenever coverable is True.
        extracted_neighborhood = cast(ExtractedNeighborhood, outcome.neighborhood)
        operators, restrictions = Grounder.ground(extracted_neighborhood, self._solution)
        try:
            return Assembler.assemble(operators, restrictions, self._solution)
        except NeighborhoodError as error:
            raise NeighborhoodExtractionError() from error
