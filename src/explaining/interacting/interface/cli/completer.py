# Standard libraries
import re
from typing import Iterable, TYPE_CHECKING

# Third-party libraries
from prompt_toolkit.completion import Completer, Completion, CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText

# Local libraries
from src.explaining.interacting.interface.cli.commands import *
from src.explaining.neighborhood.neighborhood import NeighborhoodExtractionModes
from src.explaining.question.predefined.bank import QUESTIONS_TEMPLATES
from src.explaining.question.predefined.template import QuestionTemplate

# Library for type checking only (to avoid circular imports)
if TYPE_CHECKING:
    from src.explaining.interacting.interface.cli.cli import ExplainerCLI

# Global variables
PREVIEW_STYLE = "class:preview"
PREVIEW_FIELD_STYLE = "class:preview.field"
FIELD_PATTERN = re.compile(r"(\{[^}]+})")
# The kinds of /ask-template questions that are asked from a template id and field values, and so get previews.
_TEMPLATE_QUESTION_TARGETS = (AskTemplateTargets.CONTRASTIVE.value, AskTemplateTargets.COUNTERFACTUAL.value)


#########################
# ExplainerCLICompleter #
#########################

class ExplainerCLICompleter(Completer):
    """
    Tab-completion for ExplainerCLI's REPL input.

    Completes command names, and command-specific arguments,
    reusing the same candidate sources the command handlers themselves validate against.
    """

    def __init__(self, cli: "ExplainerCLI"):
        """
        Initialize the completer with the CLI instance it completes input for.

        Args:
            cli: The ExplainerCLI whose current state (explainer, history) drives completion candidates.
        """
        self._cli = cli

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        """
        Yield completions for the command or argument the user's cursor is currently on.

        Args:
            document: The current input text buffer and user's cursor position.
            complete_event: Unused; required by prompt_toolkit's Completer interface.
        """
        try:
            prior_tokens, partial_token = self._split_text_before_cursor(document)
            completions = [
                (text, self._compute_display_meta(prior_tokens, text)) for text in self._compute_completions(document)
            ]
        except Exception:
            # NB: A completer must never crash the REPL's typing loop; degrade to "no suggestions".
            return
        for text, display_meta in completions:
            yield Completion(text, start_position=-len(partial_token), display_meta=display_meta)

    @staticmethod
    def _split_text_before_cursor(document: Document) -> tuple[list[str], str]:
        """
        Split the text before the user's cursor into fully-typed tokens and the partial token under the cursor.

        Args:
            document: The current input buffer and user's cursor position.

        Returns:
            A tuple of (prior_tokens, partial_token):
            prior_tokens are the whitespace-separated tokens fully typed before the token under the user's cursor
            (prior_tokens[0] is the command token, if any);
            partial_token is the (possibly empty) run of non-whitespace characters immediately before the user's
            cursor, i.e. the text a produced Completion's start_position must replace.
        """
        text_before_cursor = document.text_before_cursor
        # NB: \S*$ matches the last run of non-whitespace characters before the cursor,
        # or "" if the cursor is at whitespace.
        partial_token_match = re.search(r"\S*$", text_before_cursor)
        partial_token = partial_token_match.group() if partial_token_match else ""
        prior_text = text_before_cursor[:len(text_before_cursor) - len(partial_token)]
        prior_tokens = prior_text.split()
        return prior_tokens, partial_token

    def _compute_completions(self, document: Document) -> list[str]:
        """Return the candidate completion texts for the token the cursor is currently on."""
        prior_tokens, partial_token = self._split_text_before_cursor(document)
        token_index = len(prior_tokens)
        if token_index == 0:
            return self._matching(partial_token, [command.name for command in Commands])
        command_name = prior_tokens[0].lower()
        args = prior_tokens[1:]
        if command_name == Commands.ASK_TEMPLATE.name and token_index >= 1:
            return self._complete_ask_template(args, partial_token)
        if command_name == Commands.SET.name and token_index >= 1:
            return self._complete_set(args, partial_token)
        if command_name == Commands.LIST.name and token_index == 1:
            return self._matching(partial_token, ListTargets.values())
        if command_name in (Commands.ENABLE.name, Commands.DISABLE.name) and token_index == 1:
            return self._matching(partial_token, EnableTargets.values())
        if command_name == Commands.SHOW.name and token_index == 1:
            return self._matching(partial_token, ShowTargets.values())
        if command_name == Commands.SHOW.name and token_index == 2 and args[0].lower() == ShowTargets.INSTANCE.value:
            return self._complete_history_names(lambda history: history.instances_names, partial_token)
        if command_name == Commands.SHOW.name and token_index == 2 and args[0].lower() == ShowTargets.SOLUTION.value:
            return self._complete_history_names(lambda history: history.solutions_names, partial_token)
        if command_name == Commands.CLEAR.name and token_index == 1:
            return self._matching(partial_token, ClearTargets.values())
        if command_name == Commands.SWITCH.name and token_index == 1:
            return self._matching(partial_token, SwitchTargets.values())
        if (command_name == Commands.SWITCH.name and token_index == 2
                and args[0].lower() == SwitchTargets.INSTANCE.value):
            return self._complete_history_names(lambda history: history.instances_names, partial_token)
        if (command_name == Commands.SWITCH.name and token_index == 2
                and args[0].lower() == SwitchTargets.SOLUTION.value):
            return self._complete_history_names(lambda history: history.solutions_names, partial_token)
        return []

    @staticmethod
    def _matching(partial_token: str, candidate_tokens: Iterable[str]) -> list[str]:
        """Return the candidate tokens whose text starts with partial_token, matched case-insensitively."""
        lowered_partial_token = partial_token.lower()
        return [candidate for candidate in candidate_tokens if candidate.lower().startswith(lowered_partial_token)]

    @staticmethod
    def _compute_display_meta(prior_tokens: list[str], candidate: str) -> Optional[FormattedText]:
        """
        Return the text shown next to a completion candidate in the menu, if any.

        Only the template ids and field values of /ask-template contrastive|counterfactual get one:
        the question they lead to, as a preview.
        A template id candidate previews its own question, with every field left as a placeholder.
        A field value candidate previews the question with the values already typed and itself filled in,
        the later fields being left as placeholders.

        Args:
            prior_tokens: The tokens fully typed before the one being completed, the command token first.
            candidate: The completion candidate to compute the text for.

        Returns:
            The question preview, or None if the candidate gets no text next to it.
        """
        if (len(prior_tokens) < 2 or prior_tokens[0].lower() != Commands.ASK_TEMPLATE.name
                or prior_tokens[1].lower() not in _TEMPLATE_QUESTION_TARGETS):
            return None
        if len(prior_tokens) == 2:
            return ExplainerCLICompleter._build_template_question_preview(QUESTIONS_TEMPLATES[candidate], [])
        template = QUESTIONS_TEMPLATES[prior_tokens[2]]
        return ExplainerCLICompleter._build_template_question_preview(template, prior_tokens[3:] + [candidate])

    @staticmethod
    def _build_template_question_preview(template: QuestionTemplate, fields_values: list[str]) -> FormattedText:
        """
        Return the template's question, in its current language, with its first fields filled with the given values.

        Args:
            template: The question template to preview.
            fields_values: The values of the template's first fields, in order; the others stay as placeholders.

        Returns:
            The question, with values and placeholders styled apart from the rest of it.
        """
        # NB: The raw text is read rather than template.text, which substitutes a default value for every field.
        raw_text = template.all_texts[template.language]
        fragments = []
        field_index = 0
        for part in FIELD_PATTERN.split(raw_text):
            if FIELD_PATTERN.fullmatch(part):
                value = fields_values[field_index] if field_index < len(fields_values) else part
                fragments.append((PREVIEW_FIELD_STYLE, value))
                field_index += 1
            elif part:
                fragments.append((PREVIEW_STYLE, part))
        return FormattedText(fragments)

    def _complete_set(self, args: list[str], partial_token: str) -> list[str]:
        """
        Return the candidate completion texts for the token after /set and the args already typed after it.

        Args:
            args: The tokens already typed after /set.
            partial_token: The token the cursor is currently on.

        Returns:
            The set targets first, then the options (modes, languages, ...) of the target typed,
            then the suggested LLM models after /set llm-model <target> and /set pipeline llm.
        """
        if len(args) == 0:
            return self._matching(partial_token, SetTargets.values())
        target = args[0].lower()
        if len(args) == 1:
            if target == SetTargets.PIPELINE.value:
                return self._matching(partial_token, Pipelines.values())
            if target == SetTargets.LANGUAGE.value:
                return self._matching(partial_token, Languages.values())
            if target == SetTargets.DISPLAY_MODE.value:
                return self._matching(partial_token, DisplayModes.values())
            if target == SetTargets.TEMPLATE_COMPUTATION_MODE.value:
                return self._matching(partial_token, TemplateComputationModes.values())
            if target == SetTargets.NEIGHBORHOOD_EXTRACTION_MODE.value:
                return self._matching(partial_token, NeighborhoodExtractionModes.values())
            if target == SetTargets.FREE_TEXT_EXPLANATION_WRITING_MODE.value:
                return self._matching(partial_token, FreeTextExplanationModes.values())
            if target == SetTargets.SOLVING_TIME_LIMIT.value:
                return self._matching(partial_token, SolvingTimeLimitTargets.values())
            if target == SetTargets.LLM_MODEL.value:
                return self._matching(partial_token, LLMModelTargets.values())
        if len(args) == 2 and target == SetTargets.LLM_MODEL.value and args[1].lower() in LLMModelTargets.values():
            return self._matching(partial_token, LLMModels.values())
        if len(args) == 2 and target == SetTargets.PIPELINE.value and args[1].lower() == Pipelines.LLM.value:
            return self._matching(partial_token, LLMModels.values())
        return []

    def _complete_ask_template(self, args: list[str], partial_token: str) -> list[str]:
        """
        Return the candidate completion texts for the token after /ask-template and the args already typed after it.

        Args:
            args: The tokens already typed after /ask-template.
            partial_token: The token the cursor is currently on.

        Returns:
            The activated kinds of questions first, then the template ids that kind accepts,
            then the valid values of the template's field the cursor is on.
            Nothing for a scenario question, which takes no template from the CLI yet.
        """
        if len(args) == 0:
            return self._matching(partial_token, self._cli.get_activated_ask_template_targets())
        target = args[0].lower()
        if target == AskTemplateTargets.CONTRASTIVE.value:
            template_ids = list(QUESTIONS_TEMPLATES.keys())
        elif target == AskTemplateTargets.COUNTERFACTUAL.value:
            template_ids = self._cli.explainer.configuration.activated_counterfactual_questions_templates_ids
        else:
            return []
        if target not in self._cli.get_activated_ask_template_targets():
            return []
        if len(args) == 1:
            return self._matching(partial_token, template_ids)
        if args[1] not in template_ids:
            return []
        return self._complete_template_question_field(args[1:], partial_token)

    def _complete_template_question_field(self, args: list[str], partial_token: str) -> list[str]:
        """Return valid values for the template field the cursor is currently on, narrowed by prior fields."""
        if not args:
            return []
        template_id = args[0]
        if template_id not in QUESTIONS_TEMPLATES:
            # Partial/invalid template id typed so far - nothing to offer, not an error.
            return []
        template = QUESTIONS_TEMPLATES[template_id]
        field_values_already_typed = args[1:]
        focused_field_index = len(field_values_already_typed)
        if focused_field_index >= template.nb_fields:
            return []
        other_fields_with_fixed_values = dict(enumerate(field_values_already_typed))
        try:
            solution = self._cli.explainer.current_solution
            valid_values = template.compute_field_valid_values(
                solution, focused_field_index, other_fields_with_fixed_values
            )
        except Exception:
            # NB: compute_field_valid_values can raise NotImplementedError for an unrecognized assumption type;
            # a completer must degrade to "no suggestions" rather than crash the REPL.
            return []
        return self._matching(partial_token, valid_values)

    def _complete_history_names(self, get_names_function, partial_token: str) -> list[str]:
        """Return history-stored instance/solution names matching partial_token."""
        return self._matching(partial_token, get_names_function(self._cli.explainer.history))
