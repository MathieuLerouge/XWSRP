# Standard library
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
from src.explaining.neighborhood.neighborhood import Neighborhood, NeighborhoodExtractionModes
from src.explaining.question.free.question import FreeTextQuestion
from src.modeling.solution import Solution
from src.utils.llm import check_required_api_key_is_set, is_json_context_enabled_by_default


#############
# Extractor #
#############

class Extractor:
    """
    Converts a free-text contrastive question into the Neighborhood it induces,
    using a model-agnostic LLM (via instructor.from_provider) to identify the corresponding primitives.
    """

    def __init__(self, solution: Solution, model: str, mode: Optional[Mode] = None,
                 with_json_context: Optional[bool] = None):
        """
        Args:
            solution: The solution every question asked through this Extractor is about.
            model: The instructor model string ("provider/model-name", e.g. "anthropic/claude-...", "ollama/llama3.2").
            mode: Override for instructor's response-parsing mode.
                Left as None (instructor's own per-provider default, typically its TOOLS mode)
                unless the provider needs something else - e.g. Ollama's tool-calling support isn't reliable enough
                for the default mode and needs Mode.MD_JSON instead.
            with_json_context: Whether the prompt describes the instance and the solution as JSON.
                Left as None, it is enabled for every provider except the local ones of
                src.utils.llm.PROVIDERS_WITHOUT_JSON_CONTEXT_BY_DEFAULT.

        Raises:
            RuntimeError: If model's provider requires an API key and the corresponding environment variable isn't set.
        """
        check_required_api_key_is_set(model)
        self._solution = solution
        self._client = instructor.from_provider(model, mode=mode)
        if with_json_context is None:
            with_json_context = is_json_context_enabled_by_default(model)
        self._with_json_context = with_json_context

    def extract(self, question: FreeTextQuestion) -> Neighborhood:
        """
        Args:
            question: A free-text contrastive question, asked about this Extractor's own solution.

        Returns:
            Neighborhood: The induced Neighborhood.

        Raises:
            ValueError: If question is asked about another solution than the one this Extractor grounds against.
            NeighborhoodExtractionError: If the question cannot be turned into a Neighborhood
                that NeighborhoodModel can solve:
                the LLM exhausted its retries without producing schema-valid output;
                it explicitly reported the question as not coverable;
                it named an entity unresolvable against solution;
                or it named a primitive combination NeighborhoodModel doesn't support yet.
        """
        if question.solution is not self._solution:
            raise ValueError("The question must be asked about the solution this Extractor was built for")
        user_prompt = build_user_prompt(self._solution, question.text, with_json_context=self._with_json_context)
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
            neighborhood = Assembler.assemble(operators, restrictions, self._solution)
        except NeighborhoodError as error:
            raise NeighborhoodExtractionError() from error
        neighborhood.extraction_mode = NeighborhoodExtractionModes.LLM.value
        return neighborhood
