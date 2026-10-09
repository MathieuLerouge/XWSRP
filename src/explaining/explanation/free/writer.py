# Standard library
import json
from typing import Any, Optional

# Third-party libraries
import instructor
from instructor import Mode
from instructor.core import InstructorRetryException
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

# Local libraries
from src.explaining.computing.neighborhood.facts import ExplanationFacts
from src.explaining.explanation.free.exceptions import ExplanationWritingError
from src.explaining.explanation.free.explanation import FreeTextExplanation
from src.explaining.explanation.free.grounding import find_names, find_times
from src.explaining.explanation.free.prompt import SYSTEM_PROMPT, build_facts_document, build_user_prompt
from src.explaining.explanation.free.written_explanation import (
    ALLOWED_NAMES_KEY, ALLOWED_TIMES_KEY, KNOWN_NAMES_KEY, REQUIRED_NAMES_KEY, WrittenExplanation
)
from src.explaining.question.free.question import FreeTextQuestion
from src.modeling.solution import Solution
from src.utils.llm import check_required_api_key_is_set, is_json_context_enabled_by_default


#####################
# ExplanationWriter #
#####################

class ExplanationWriter:
    """
    Words the ExplanationFacts into the FreeTextExplanation answering a free-text question, using an LLM.

    The LLM only words: what the explanation states is fixed by the facts, which it is told to state and nothing else,
    and its text is checked to mention no time and no name the facts do not hold (see WrittenExplanation),
    instructor sending it back for another attempt otherwise.
    """

    def __init__(self, model: str, mode: Optional[Mode] = None, with_json_context: Optional[bool] = None,
                 max_retries: int = 2, client: Optional[Any] = None):
        """
        Args:
            model: The instructor model string ("provider/model-name", e.g. "anthropic/claude-...", "ollama/llama3.2").
            mode: Override for instructor's response-parsing mode.
                Left as None (instructor's own per-provider default) unless the provider needs something else
                - e.g. Ollama needs Mode.MD_JSON (see Extractor).
            with_json_context: Whether the prompt also describes the instance and the current solution as JSON.
                Left as None, it is enabled for every provider except the local ones of
                src.utils.llm.PROVIDERS_WITHOUT_JSON_CONTEXT_BY_DEFAULT.
            max_retries: How many times instructor asks the LLM again after an invalid or ungrounded answer.
            client: The instructor client to word explanations with, in place of the one built for model
                - e.g. a fake one in tests.

        Raises:
            RuntimeError: If no client is given, and model's provider requires an API key
                whose environment variable isn't set.
        """
        if client is None:
            check_required_api_key_is_set(model)
            client = instructor.from_provider(model, mode=mode)
        self._model = model
        self._client = client
        if with_json_context is None:
            with_json_context = is_json_context_enabled_by_default(model)
        self._with_json_context = with_json_context
        self._max_retries = max_retries

    @property
    def model(self) -> str:
        """The instructor model string explanations are worded with."""
        return self._model

    @property
    def with_json_context(self) -> bool:
        """Whether the prompt also describes the instance and the current solution as JSON."""
        return self._with_json_context

    def write(self, question: FreeTextQuestion, facts: ExplanationFacts, support_solution: Solution,
              computation_mode: Optional[str] = None,
              computation_time: Optional[float] = None) -> FreeTextExplanation:
        """
        Words the given facts into the explanation answering the given question.

        Args:
            question: The free-text question to answer.
            facts: The facts of the neighborhood the question induced, once solved (see ExplanationFactsBuilder).
            support_solution: The solution found while answering it (see ExplanationFactsBuilder.get_support_solution).
            computation_mode: The mode in which the explanation is computed, or None if not available.
            computation_time: The computation time in seconds, or None if not available.

        Returns:
            The explanation.

        Raises:
            ValueError: If the facts were not read off this very question, or are in another language than it.
            ExplanationWritingError: If the LLM exhausted its retries without producing a valid, grounded text.
        """
        if facts.question != question.text or facts.language != question.language:
            raise ValueError("The facts must be read off the very question to answer, in its language")
        facts_document = build_facts_document(facts)
        user_prompt = build_user_prompt(facts_document, question.solution, with_json_context=self._with_json_context)
        messages = [
            ChatCompletionSystemMessageParam(role="system", content=SYSTEM_PROMPT),
            ChatCompletionUserMessageParam(role="user", content=user_prompt),
        ]
        try:
            written_explanation = self._client.chat.completions.create(
                messages=messages,
                response_model=WrittenExplanation,
                context=self._build_validation_context(facts_document, question),
                max_retries=self._max_retries,
            )
        except InstructorRetryException as error:
            raise ExplanationWritingError() from error
        return FreeTextExplanation(question, support_solution, facts, written_explanation.text, self._model,
                                   computation_mode, computation_time)

    @staticmethod
    def _build_validation_context(facts_document: dict[str, Any], question: FreeTextQuestion) -> dict[str, set]:
        """
        Returns the context WrittenExplanation checks the worded text against:
        the times and the names the facts document states, out of every employee and task name of the instance,
        and the names the question states, which the text is to state as well.

        NB: Read off the document as serialized, so that what is allowed is exactly what the LLM was shown,
        spelled the way it was shown.
        """
        serialized_facts_document = json.dumps(facts_document, ensure_ascii=False)
        instance = question.solution.instance
        known_names = {employee.name for employee in instance.employees} | {task.name for task in instance.tasks}
        allowed_times: set[int] = set()
        for candidates in find_times(serialized_facts_document):
            allowed_times |= candidates
        return {
            ALLOWED_TIMES_KEY: allowed_times,
            ALLOWED_NAMES_KEY: find_names(serialized_facts_document, known_names),
            KNOWN_NAMES_KEY: known_names,
            REQUIRED_NAMES_KEY: find_names(question.text, known_names),
        }
