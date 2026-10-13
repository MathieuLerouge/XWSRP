# Standard libraries
import os
import re
from typing import Callable, cast

# Third-party libraries
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

# Local libraries
from src.explaining.computing.neighborhood.model import NEIGHBORHOOD_CONSTRAINT_FAMILY_PREFIX
from src.explaining.explanation.explanation import Explanation, ExplanationComputationModes
from src.explaining.explanation.free.exceptions import ExplanationWritingError
from src.explaining.explanation.free.explanation import FreeTextExplanation
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.configuration import ExplainerConfiguration
from src.explaining.interacting.interface.cli.commands import *
from src.explaining.interacting.interface.cli.completer import ExplainerCLICompleter
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.neighborhood.neighborhood import Neighborhood, NeighborhoodExtractionModes
from src.explaining.question.predefined.bank import QUESTIONS_TEMPLATES
from src.feasibility.checker import FeasibilityChecker
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.optimization.milp.statistics import MilpStatistics
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY


################
# ExplainerCLI #
################

class ExplainerCLI:
    """
    REPL-style terminal interface for the Explainer class.

    Allows end-users to configure the explainer, ask questions about a solution, and manage stored solutions/instances.
    """

    def __init__(self, solution: Solution, explainer: Optional[Explainer] = None):
        """
        Initialize CLI with a solution and optionally a pre-configured Explainer.

        Args:
            solution: The solution to explain.
            explainer: Optional pre-configured Explainer instance.
                If provided, uses this explainer instead of creating a new one with default configuration.
        """
        if explainer is not None:
            self._explainer = explainer
            self._solution = solution
        else:
            configuration = ExplainerConfiguration(
                language=LANGUAGE_ENGLISH_KEY,
                history_enabled=True,
                neighborhood_llm_model=None,
                scenario_explanations_enabled=False,
                counterfactual_explanations_enabled=False,
                using_cached_contrastive_explanations_enabled=False,
                exporting_each_contrastive_explanation_automatically_enabled=False,
            )
            self._explainer = Explainer(solution, configuration)
            self._solution = solution
        # CLI-specific state
        self._running = True
        self._last_command: Optional[str] = None
        self._display_mode = DisplayModes.USER.value
        # Commands handlers registry
        self._commands: dict[str, Callable[[list[str]], str]] = {}
        # Register all commands
        self._register_commands()
        # Custom style for orange-yellow input text,
        # and gray template question previews with gray-yellow fields in the completion menu
        style = Style.from_dict({
            '': 'fg:#ffab40',
            'preview': 'fg:#767676',
            'preview.field': 'fg:#b39b6b',
            'completion-menu.meta.completion': 'bg:#262626 fg:#767676',
            'completion-menu.meta.completion.current': 'bg:#3a3a3a fg:#767676',
        })
        # Interactive prompt with tab-completion
        self._session: PromptSession = PromptSession(
            completer=ExplainerCLICompleter(self), complete_while_typing=True, style=style
        )

    @property
    def explainer(self) -> Explainer:
        """The Explainer this CLI drives."""
        return self._explainer

    def _register_commands(self) -> None:
        """Register all command handlers."""
        self._commands = {
            # Core
            Commands.ASK_TEMPLATE.name: self.handle_ask_template,
            Commands.ASK.name: self.handle_ask,
            Commands.SAVE_SOLUTION.name: self.handle_save_solution,
            Commands.LIST.name: self.handle_list,
            Commands.SWITCH.name: self.handle_switch,
            Commands.EXPORT.name: self.handle_export,
            # Configuration
            Commands.SET.name: self.handle_set,
            Commands.ENABLE.name: self.handle_enable,
            Commands.DISABLE.name: self.handle_disable,
            # Display
            Commands.SHOW.name: self.handle_show,
            Commands.HELP.name: self.handle_help,
            # Session
            Commands.CLEAR.name: self.handle_clear,
            Commands.QUIT.name: self.handle_quit,
        }

    def run(self) -> None:
        """Main REPL loop."""
        os.system('clear' if os.name != 'nt' else 'cls')
        print(f"{self._blue('XWSRP CLI')} - Interactive CLI for explaining WSRP solutions")
        print(f"Type {self._yellow(Commands.HELP.name)} for commands")
        print()
        print(self._gray(f"Loaded solution: {self._solution.name}"))
        print()
        while self._running:
            try:
                # Show prompt
                user_input = self._session.prompt("> ").strip()
                if not user_input:
                    continue
                # Store for potential multi-part commands
                self._last_command = user_input
                # Dispatch
                self.dispatch(user_input)
                print()
            except KeyboardInterrupt:
                print(f"\nUse {self._yellow(Commands.QUIT.name)} to exit.")
                print()
            except EOFError:
                print()
                self._stop()
            except Exception as e:
                print(f"Error: {e}")

    def _stop(self) -> None:
        """Cleanup and exit."""
        self._running = False
        print()
        print("Ciao ciao!")

    def dispatch(self, input_str: str) -> None:
        """Parse and route input to command handler."""
        # Skip empty input
        if not input_str:
            return
        # Parse command and args
        parts = input_str.split()
        if not parts:
            return
        command = parts[0].lower()
        args = parts[1:]
        # Check if it's a known command
        if command in self._commands:
            try:
                result = self._commands[command](args)
                if result:
                    print()
                    print(result)
            except Exception as e:
                print()
                print(f"Error executing {command}: {e}")
        else:
            print()
            print(f"Unknown command '{command}'. "
                  f"Type {self._yellow(Commands.HELP.name)} for available commands.")

    ##########################
    # Command Handlers - Ask #
    ##########################

    def handle_ask(self, args: list[str]) -> str:
        """Handle /ask <question> command."""
        if len(args) < 1:
            return f"Usage: {self._yellow(Commands.ASK.name)} <free-text-question>"
        if self._explainer.neighborhood_extraction_llm_model is None:
            set_llm_model_str = self._highlight_command(
                Commands.SET.name, SetTargets.LLM_MODEL.value, LLMModelTargets.NEIGHBORHOOD_EXTRACTION.value
            )
            return f"No LLM model configured. Use {set_llm_model_str} <provider/model> first."
        if (self._explainer.configuration.free_text_explanation_mode == FreeTextExplanationModes.WRITTEN.value
                and self._explainer.explanation_writing_llm_model is None):
            set_llm_model_str = self._highlight_command(
                Commands.SET.name, SetTargets.LLM_MODEL.value, LLMModelTargets.EXPLANATION_WRITING.value
            )
            set_writing_mode = self._highlight_command(
                Commands.SET.name, SetTargets.FREE_TEXT_EXPLANATION_WRITING_MODE.value
            )
            return (f"No writer LLM model configured. Use {set_llm_model_str} <provider/model> first, "
                    f"or {set_writing_mode} {FreeTextExplanationModes.TEMPLATED.value}.")
        question_text = " ".join(args)
        try:
            explanation = self._explainer.get_free_text_explanation(question_text)
            return self._format_explanation_output(explanation)
        except (NeighborhoodError, ExplanationWritingError, ValueError) as e:
            return f"Error: {e}"

    def handle_ask_template(self, args: list[str]) -> str:
        """Handle /ask-template <kind> <template_id> <value1> <value2> ... command."""
        activated_targets = self.get_activated_ask_template_targets()
        if len(args) < 1:
            return (f"Usage: {self._yellow(Commands.ASK_TEMPLATE.name)} <kind> <template_id> <value1> <value2> ... "
                    f"where kind is: {', '.join(activated_targets)}")
        target = args[0].lower()
        if target in AskTemplateTargets.values() and target not in activated_targets:
            return (f"{target.capitalize()} questions are not activated. "
                    f"Use {self._highlight_command(Commands.ENABLE.name, target)} first.")
        if target == AskTemplateTargets.CONTRASTIVE.value:
            return self._handle_ask_template_contrastive(args[1:])
        elif target == AskTemplateTargets.SCENARIO.value:
            return self._handle_ask_template_scenario(args[1:])
        elif target == AskTemplateTargets.COUNTERFACTUAL.value:
            return self._handle_ask_template_counterfactual(args[1:])
        else:
            return (f"Unknown target '{target}'. "
                    f"Valid targets: {', '.join(activated_targets)}")

    def get_activated_ask_template_targets(self) -> list[str]:
        """Return the kinds of template-based questions /ask-template can currently ask."""
        configuration = self._explainer.configuration
        targets = [AskTemplateTargets.CONTRASTIVE.value]
        if configuration.scenario_explanations_enabled:
            targets.append(AskTemplateTargets.SCENARIO.value)
        if configuration.counterfactual_explanations_enabled:
            targets.append(AskTemplateTargets.COUNTERFACTUAL.value)
        return targets

    def _handle_ask_template_contrastive(self, args: list[str]) -> str:
        """Handle /ask-template contrastive <template_id> <value1> <value2> ... command."""
        if len(args) < 1:
            ask_template_str = self._highlight_command(Commands.ASK_TEMPLATE.name, AskTemplateTargets.CONTRASTIVE.value)
            return f"Usage: {ask_template_str} <template_id> <value1> <value2> ..."
        template_id, field_values = args[0], args[1:]
        problem = self._check_template_question(template_id, field_values, list(QUESTIONS_TEMPLATES.keys()))
        if problem is not None:
            return problem
        try:
            explanation = self._explainer.get_contrastive_explanation(template_id, field_values)
            return self._format_explanation_output(explanation)
        except (ValueError, TypeError) as e:
            return f"Error: {e}"

    @staticmethod
    def _handle_ask_template_scenario(args: list[str]) -> str:
        """
        Handle /ask-template scenario command.

        WIP: A scenario question re-asks the last contrastive question on an altered instance,
        and the CLI has no way to describe instance alterations yet.
        """
        return "Scenario questions cannot be asked from the CLI yet."

    def _handle_ask_template_counterfactual(self, args: list[str]) -> str:
        """
        Handle /ask-template counterfactual [<template_id> <value1> <value2> ...] command.

        With no template, the last contrastive question is the one turned around.
        """
        if len(args) > 0:
            template_id, field_values = args[0], args[1:]
            valid_template_ids = self._explainer.configuration.activated_counterfactual_questions_templates_ids
            problem = self._check_template_question(template_id, field_values, valid_template_ids)
            if problem is not None:
                return problem
        else:
            template_id, field_values = None, None
        try:
            explanation = self._explainer.compute_counterfactual_explanation(template_id, field_values)
            return self._format_explanation_output(explanation)
        except (PermissionError, ValueError) as e:
            return f"Error: {e}"

    def _check_template_question(self, template_id: str, field_values: list[str],
                                 valid_template_ids: list[str]) -> Optional[str]:
        """
        Return why the given template id and field values cannot make a template-based question, if they cannot.

        Args:
            template_id: The template id typed.
            field_values: The field values typed after it.
            valid_template_ids: The template ids the kind of question asked accepts.

        Returns:
            The message reporting the first problem found, or None if there is none.
        """
        if template_id not in valid_template_ids:
            list_templates_str = self._highlight_command(
                Commands.LIST.name, ListTargets.TEMPLATE_QUESTIONS.value
            )
            return f"Unknown template ID '{template_id}'. Use {list_templates_str} to see available templates."
        nb_expected_fields = len(QUESTIONS_TEMPLATES[template_id].fields_keys)
        nb_provided_values = len(field_values)
        if nb_provided_values < nb_expected_fields:
            return (f"Template '{template_id}' requires {nb_expected_fields} values, "
                    f"but only {nb_provided_values} provided.")
        if nb_provided_values > nb_expected_fields:
            return (f"Template '{template_id}' requires {nb_expected_fields} values, "
                    f"but {nb_provided_values} provided.")
        return None

    def _format_explanation_output(self, explanation: Explanation) -> str:
        """Format an explanation for display."""
        question_text = explanation.question.text
        explanation_text = explanation.text
        feasibility = "feasible" if explanation.support_solution_is_feasible else "infeasible"
        lines = [
            f"Question:",
            f"{question_text}",
            f"",
            f"Explanation:",
            f"{explanation_text}"
        ]
        if self._display_mode == DisplayModes.DEVELOPER.value:
            lines.append("")
            lines.append(self._gray(f"Questioning mode: {explanation.question.mode}"))
            if explanation.mode is not None:
                lines.append(self._gray(f"Explanation computation mode: {explanation.mode}"))
                if explanation.mode == ExplanationComputationModes.NEIGHBORHOOD.value:
                    neighborhood = cast(Neighborhood, explanation.neighborhood)
                    lines.append(self._gray(f"Neighborhood extraction mode: {neighborhood.extraction_mode}"))
                    lines.append(self._gray(f"Neighborhood scope: {neighborhood.scope}"))
                    lines.append(self._gray(f"Neighborhood primitives: {neighborhood}"))
                    lines.append("")
                    lines.extend(
                        self._gray(line) for line in self._format_milp_statistics_lines(explanation.milp_statistics)
                    )
            if isinstance(explanation, FreeTextExplanation):
                lines.append("")
                writing_mode = FreeTextExplanationModes.WRITTEN.value
                lines.append(self._gray(f"Free-text explanation writing mode: {writing_mode}"))
                lines.append(self._gray(f"Explanation writing LLM model: {explanation.llm_model}"))
                lines.append(self._gray(f"Outcome: {explanation.facts.outcome.value}"))
            lines.append("")
            lines.append(self._gray(f"Support solution: {feasibility}"))
            if explanation.computation_time is not None:
                lines.append(self._gray(f"Computation time: {explanation.computation_time:.3f}s"))
        return "\n".join(lines)

    @staticmethod
    def _format_milp_statistics_lines(milp_statistics: Optional[MilpStatistics]) -> list[str]:
        """
        Format the statistics of the MILP solved to compute an explanation, one line per statistic.

        Args:
            milp_statistics: The statistics of the MILP solved,
                or None if none was (e.g. a skill conflict settled the question, or the explanation was imported).

        Returns:
            The lines describing the MILP's size, objectives, and build and solve times,
            with one indented line per neighborhood constraint family.
        """
        if milp_statistics is None:
            return ["MILP: none solved"]
        nb_neighborhood_constraints = milp_statistics.count_constraints_in_families_starting_with(
            NEIGHBORHOOD_CONSTRAINT_FAMILY_PREFIX
        )
        nb_base_constraints = milp_statistics.nb_constraints - nb_neighborhood_constraints
        lines = [
            f"MILP variables: {milp_statistics.nb_variables} "
            f"(binary: {milp_statistics.nb_binary_variables}, integer: {milp_statistics.nb_integer_variables}, "
            f"continuous: {milp_statistics.nb_continuous_variables}; fixed: {milp_statistics.nb_fixed_variables})",
            f"MILP constraints: {milp_statistics.nb_constraints} "
            f"(base: {nb_base_constraints}, neighborhood: {nb_neighborhood_constraints})"
        ]
        for family, nb_constraints in sorted(milp_statistics.nb_constraints_by_family.items()):
            if family.startswith(NEIGHBORHOOD_CONSTRAINT_FAMILY_PREFIX):
                lines.append(f"  {family}: {nb_constraints}")
        lines.append(f"MILP objectives: {milp_statistics.nb_objectives}")
        lines.append(f"MILP build time: {milp_statistics.build_time:.3f}s")
        if milp_statistics.solve_time is not None:
            lines.append(f"MILP solve time: {milp_statistics.solve_time:.3f}s")
        return lines

    ####################################
    # Command Handlers - Save solution #
    ####################################

    def handle_save_solution(self, args: list[str]) -> str:
        """Handle /save-solution command."""
        try:
            is_newly_saved = self._explainer.save_last_contrastive_support_solution()
            support_solution = self._explainer.last_contrastive_explanation.support_solution
            # NB: The stored solution, not the support solution itself,
            # whose name is not its history name when it was already stored under another one.
            stored_solution = self._explainer.find_stored_solution_with_same_content(support_solution)
            if not is_newly_saved:
                return f"Support solution already saved as {stored_solution.name}"
            return f"Support solution saved as {stored_solution.name}"
        except PermissionError as e:
            return f"Error: {e}"

    ###########################
    # Command Handlers - List #
    ###########################

    def handle_list(self, args: list[str]) -> str:
        """Handle /list <target> command."""
        if len(args) < 1:
            return (f"Usage: {self._yellow(Commands.LIST.name)} <target> "
                    f"where target is: {', '.join(ListTargets.values())}")
        target = args[0].lower()
        if target == ListTargets.TEMPLATE_QUESTIONS.value:
            return self._list_template_questions()
        elif target == ListTargets.INSTANCES.value:
            return self._list_instances()
        elif target == ListTargets.SOLUTIONS.value:
            return self._list_solutions()
        else:
            return (f"Unknown target '{target}'. "
                    f"Valid targets: {', '.join(ListTargets.values())}")

    def _list_template_questions(self) -> str:
        """Handle /list template-questions command."""
        templates = self._explainer.activated_question_templates
        if not templates:
            return "No templates available."
        lines = ["Available templates:"]
        for template in templates:
            language = self._explainer.language
            text = template.all_texts.get(language, template.all_texts[LANGUAGE_ENGLISH_KEY])
            lines.append(f"  • {self._yellow(template.id)}: {self._highlight_fields(text)}")
        return "\n".join(lines)

    def _list_instances(self) -> str:
        """Handle /list instances command."""
        instance_names = self._explainer.history.instances_names
        if not instance_names:
            return "No stored instances."
        lines = ["Stored instances:"]
        for name in instance_names:
            lines.append(f"  • {name}")
        return "\n".join(lines)

    def _list_solutions(self) -> str:
        """Handle /list solutions command."""
        solution_names = self._explainer.history.solutions_names
        if not solution_names:
            return "No stored solutions."
        lines = ["Stored solutions:"]
        for name in solution_names:
            lines.append(f"  • {name}")
        return "\n".join(lines)

    #############################
    # Command Handlers - Switch #
    #############################

    def handle_switch(self, args: list[str]) -> str:
        """Handle /switch <target> [name] command."""
        if len(args) < 1:
            return (f"Usage: {self._yellow(Commands.SWITCH.name)} <target> [name] "
                    f"where target is: {', '.join(SwitchTargets.values())}")
        target = args[0].lower()
        if target == SwitchTargets.INSTANCE.value:
            return self._switch_instance(args[1:])
        elif target == SwitchTargets.SOLUTION.value:
            return self._switch_solution(args[1:])
        elif target == SwitchTargets.LAST_SUPPORT_INSTANCE.value:
            return self._switch_last_support_instance()
        elif target == SwitchTargets.LAST_SUPPORT_SOLUTION.value:
            return self._switch_last_support_solution()
        else:
            return (f"Unknown target '{target}'. "
                    f"Valid targets: {', '.join(SwitchTargets.values())}")

    def _switch_instance(self, args: list[str]) -> str:
        """Handle /switch instance <instance_name> command, switching to that instance's first stored solution."""
        if len(args) < 1:
            return f"Usage: {self._yellow(Commands.SWITCH.name)} {SwitchTargets.INSTANCE.value} <instance_name>"
        instance_name = args[0]
        try:
            solutions = self._explainer.history.get_solutions_of_instance_by_name(instance_name)
            if solutions:
                solution = solutions[0]
                self._explainer.current_solution = solution
                return f"Switched to instance {instance_name} and solution {solution.name}"
            else:
                return f"Instance {instance_name} found but has no associated solutions."
        except KeyError:
            list_instances_str = self._highlight_command(Commands.LIST.name, ListTargets.INSTANCES.value)
            return f"Instance '{instance_name}' not found. Use {list_instances_str} to see available instances."

    def _switch_solution(self, args: list[str]) -> str:
        """Handle /switch solution <solution_name> command."""
        if len(args) < 1:
            return f"Usage: {self._yellow(Commands.SWITCH.name)} {SwitchTargets.SOLUTION.value} <solution_name>"
        solution_name = args[0]
        try:
            solution = self._explainer.history.get_solution_by_name(solution_name)
            self._explainer.current_solution = solution
            return f"Switched to solution {solution.name}"
        except KeyError:
            list_solutions_str = self._highlight_command(Commands.LIST.name, ListTargets.SOLUTIONS.value)
            return f"Solution '{solution_name}' not found. Use {list_solutions_str} to see available solutions."

    def _switch_last_support_instance(self) -> str:
        """Handle /switch last-support-instance command, switching to that instance's first stored solution."""
        try:
            last_explanation = self._explainer.last_contrastive_explanation
        except PermissionError:
            return "No explanation yet. Ask a question first."
        return self._switch_instance([last_explanation.support_solution.instance.name])

    def _switch_last_support_solution(self) -> str:
        """
        Handle /switch last-support-solution command.

        The support solution is saved to history first if no solution with the same content is there yet,
        as /save-solution does, so that it gets its history name.
        Switching is refused if it cannot be saved (e.g. it is infeasible).
        """
        try:
            last_explanation = self._explainer.last_contrastive_explanation
        except PermissionError:
            return "No explanation yet. Ask a question first."
        try:
            is_newly_saved = self._explainer.save_last_contrastive_support_solution()
        except PermissionError as e:
            return f"Error: {e}"
        # NB: Switching to the stored solution rather than to the support solution itself, which,
        # when already stored under another name, would get stored again under its own unsaved name.
        stored_solution = self._explainer.find_stored_solution_with_same_content(last_explanation.support_solution)
        self._explainer.current_solution = stored_solution
        result = f"Switched to last support solution {stored_solution.name}"
        if is_newly_saved:
            result += " (saved to history)"
        return result

    #############################
    # Command Handlers - Export #
    #############################

    def handle_export(self, args: list[str]) -> str:
        """Handle /export command."""
        try:
            self._explainer.export_last_contrastive_explanation()
            file_path = self._explainer.configuration.contrastive_explanation_output_directory_relative_path
            return f"Explanation exported to {file_path}"
        except PermissionError as e:
            return f"Error: {e}"

    ##########################
    # Command Handlers - Set #
    ##########################

    def handle_set(self, args: list[str]) -> str:
        """Handle /set <target> <option> [value] command."""
        if len(args) < 1:
            return (f"Usage: {self._yellow(Commands.SET.name)} <target> <option> [value] "
                    f"where target is: {', '.join(SetTargets.values())}")
        target = args[0].lower()
        if target == SetTargets.LLM_MODEL.value:
            return self._set_llm_model(args[1:])
        elif target == SetTargets.PIPELINE.value:
            return self._set_pipeline(args[1:])
        elif target == SetTargets.TEMPLATE_COMPUTATION_MODE.value:
            return self._set_template_computation_mode(args[1:])
        elif target == SetTargets.NEIGHBORHOOD_EXTRACTION_MODE.value:
            return self._set_neighborhood_extraction_mode(args[1:])
        elif target == SetTargets.FREE_TEXT_EXPLANATION_WRITING_MODE.value:
            return self._set_free_text_explanation_writing_mode(args[1:])
        elif target == SetTargets.SOLVING_TIME_LIMIT.value:
            return self._set_solving_time_limit(args[1:])
        elif target == SetTargets.LANGUAGE.value:
            return self._set_language(args[1:])
        elif target == SetTargets.DISPLAY_MODE.value:
            return self._set_display_mode(args[1:])
        else:
            return (f"Unknown target '{target}'. "
                    f"Valid targets: {', '.join(SetTargets.values())}")

    def _set_llm_model(self, args: list[str]) -> str:
        """Handle /set llm-model <neighborhood-extraction|explanation-writing> <provider/model> command."""
        if len(args) < 1:
            return (f"Usage: {self._highlight_command(Commands.SET.name, SetTargets.LLM_MODEL.value)} "
                    f"<{'|'.join(LLMModelTargets.values())}> <provider/model>")
        target = args[0].lower()
        if target not in LLMModelTargets.values():
            return (f"Unknown target '{target}'. "
                    f"Valid targets: {', '.join(LLMModelTargets.values())}")
        if len(args) < 2:
            set_llm_model_str = self._highlight_command(Commands.SET.name, SetTargets.LLM_MODEL.value, target)
            return f"Usage: {set_llm_model_str} <provider/model> (e.g. {', '.join(LLMModels.values())})"
        model = args[1]
        # Basic validation: should contain a slash
        if "/" not in model:
            return f"Invalid model format '{model}'. Expected format: 'provider/model'"
        if target == LLMModelTargets.NEIGHBORHOOD_EXTRACTION.value:
            return self._set_neighborhood_extraction_llm_model(model)
        else:
            return self._set_explanation_writing_llm_model(model)

    def _set_neighborhood_extraction_llm_model(self, model: str) -> str:
        """
        Handle /set llm-model neighborhood-extraction <provider/model> command.

        In llm neighborhood extraction mode, the extractor is set up right away,
        so that a misconfigured LLM backend is reported now rather than on the next question.
        """
        self._explainer.neighborhood_extraction_llm_model = model
        if self._explainer.configuration.neighborhood_extraction_mode == NeighborhoodExtractionModes.LLM.value:
            try:
                self._explainer.prepare_extractor()
            except (ValueError, RuntimeError, ImportError) as e:
                return f"Neighborhood extraction LLM model set to {model}, but its extractor could not be set up: {e}"
        return f"Neighborhood extraction LLM model set to {model}"

    def _set_explanation_writing_llm_model(self, model: str) -> str:
        """
        Handle /set llm-model explanation-writing <provider/model> command.

        In written free-text explanation mode, the writer is set up right away,
        so that a misconfigured LLM backend is reported now rather than on the next question.
        """
        self._explainer.explanation_writing_llm_model = model
        if self._explainer.configuration.free_text_explanation_mode == FreeTextExplanationModes.WRITTEN.value:
            try:
                self._explainer.prepare_writer()
            except (ValueError, RuntimeError, ImportError) as e:
                return f"Explanation writing LLM model set to {model}, but its writer could not be set up: {e}"
        return f"Explanation writing LLM model set to {model}"

    def _set_pipeline(self, args: list[str]) -> str:
        """
        Handle /set pipeline <tailored|llm> [provider/model] command.

        Every setting the pipeline needs is set at once, and left as it was if the llm pipeline's LLM backend
        cannot be set up (see Explainer.set_pipeline).
        """
        usage = (f"Usage: {self._highlight_command(Commands.SET.name, SetTargets.PIPELINE.value)} "
                 f"<{'|'.join(Pipelines.values())}> [provider/model]")
        if len(args) < 1:
            return usage
        pipeline = args[0].lower()
        if pipeline not in Pipelines.values():
            return usage
        llm_model = args[1] if len(args) > 1 else None
        if llm_model is not None and "/" not in llm_model:
            return f"Invalid model format '{llm_model}'. Expected format: 'provider/model'"
        try:
            self._explainer.set_pipeline(pipeline, llm_model)
        except (ValueError, RuntimeError, ImportError) as e:
            return f"Error: {e}"
        configuration = self._explainer.configuration
        lines = [
            f"Pipeline set to {pipeline}:",
            f"  Template computation mode: {configuration.template_computation_mode}",
            f"  Neighborhood extraction mode: {configuration.neighborhood_extraction_mode}",
            f"  Free-text explanation writing mode: {configuration.free_text_explanation_mode}",
        ]
        if pipeline == Pipelines.LLM.value:
            lines += [
                f"  Neighborhood extraction LLM model: {configuration.neighborhood_extraction_llm_model}",
                f"  Explanation writing LLM model: {configuration.explanation_writing_llm_model}",
            ]
        return "\n".join(lines)

    def _set_template_computation_mode(self, args: list[str]) -> str:
        """Handle /set template-computation-mode <tailored|neighborhood> command."""
        set_template_computation_mode_str = self._highlight_command(
            Commands.SET.name, SetTargets.TEMPLATE_COMPUTATION_MODE.value
        )
        usage = f"Usage: {set_template_computation_mode_str} <{'|'.join(TemplateComputationModes.values())}>"
        if len(args) < 1:
            return usage
        mode = args[0].lower()
        if mode not in TemplateComputationModes.values():
            return usage
        self._explainer.configuration.template_computation_mode = mode
        return f"Template computation mode set to {mode}"

    def _set_neighborhood_extraction_mode(self, args: list[str]) -> str:
        """
        Handle /set neighborhood-extraction-mode <llm|tailored> command.

        Switching to llm sets up the LLM extractor right away, so that a misconfigured LLM backend is reported now
        rather than on the next question. The mode is left unchanged if no LLM model is set or the setup fails.
        """
        usage = (f"Usage: {self._highlight_command(Commands.SET.name, SetTargets.NEIGHBORHOOD_EXTRACTION_MODE.value)} "
                 f"<{'|'.join(NeighborhoodExtractionModes.values())}>")
        if len(args) < 1:
            return usage
        mode = args[0].lower()
        if mode not in NeighborhoodExtractionModes.values():
            return usage
        if mode == NeighborhoodExtractionModes.LLM.value:
            if self._explainer.neighborhood_extraction_llm_model is None:
                set_llm_model_str = self._highlight_command(
                    Commands.SET.name, SetTargets.LLM_MODEL.value, LLMModelTargets.NEIGHBORHOOD_EXTRACTION.value
                )
                return f"No LLM model configured. Use {set_llm_model_str} <provider/model> first."
            try:
                self._explainer.prepare_extractor()
            except (ValueError, RuntimeError, ImportError) as e:
                return f"Error: {e}"
        self._explainer.configuration.neighborhood_extraction_mode = mode
        result = f"Neighborhood extraction mode set to {mode}"
        if self._explainer.configuration.template_computation_mode == TemplateComputationModes.TAILORED.value:
            result += "\n" + self._gray(
                f"NB: It only applies in {TemplateComputationModes.NEIGHBORHOOD.value} template computation mode "
                f"(see {Commands.SET.name} {SetTargets.TEMPLATE_COMPUTATION_MODE.value})."
            )
        return result

    def _set_free_text_explanation_writing_mode(self, args: list[str]) -> str:
        """
        Handle /set free-text-explanation-writing-mode <written|templated> command.

        Switching to written sets up the writer right away, so that a misconfigured LLM backend is reported now
        rather than on the next question. The mode is left unchanged if no writer LLM model is set or the setup fails.
        """
        set_writing_mode_str = self._highlight_command(
            Commands.SET.name, SetTargets.FREE_TEXT_EXPLANATION_WRITING_MODE.value
        )
        usage = f"Usage: {set_writing_mode_str} <{'|'.join(FreeTextExplanationModes.values())}>"
        if len(args) < 1:
            return usage
        mode = args[0].lower()
        if mode not in FreeTextExplanationModes.values():
            return usage
        if mode == FreeTextExplanationModes.WRITTEN.value:
            if self._explainer.explanation_writing_llm_model is None:
                set_llm_model_str = self._highlight_command(
                    Commands.SET.name, SetTargets.LLM_MODEL.value, LLMModelTargets.EXPLANATION_WRITING.value
                )
                return f"No writer LLM model configured. Use {set_llm_model_str} <provider/model> first."
            try:
                self._explainer.prepare_writer()
            except (ValueError, RuntimeError, ImportError) as e:
                return f"Error: {e}"
        self._explainer.configuration.free_text_explanation_mode = mode
        return f"Free-text explanation writing mode set to {mode}"

    def _set_solving_time_limit(self, args: list[str]) -> str:
        """Handle /set solving-time-limit <contrastive|counterfactual> <seconds> command."""
        command_tokens = (Commands.SET.name, SetTargets.SOLVING_TIME_LIMIT.value)
        if len(args) < 1:
            return (f"Usage: {self._highlight_command(*command_tokens)} "
                    f"<{'|'.join(SolvingTimeLimitTargets.values())}> <seconds>")
        target = args[0].lower()
        if target not in SolvingTimeLimitTargets.values():
            return (f"Unknown target '{target}'. "
                    f"Valid targets: {', '.join(SolvingTimeLimitTargets.values())}")
        if len(args) < 2:
            return f"Usage: {self._highlight_command(*command_tokens, target)} <seconds>"
        try:
            seconds = int(args[1])
        except ValueError:
            return "Time limit must be an integer."
        if seconds < 0:
            return "Time limit must be a non-negative integer."
        if target == SolvingTimeLimitTargets.CONTRASTIVE.value:
            self._explainer.configuration.time_limit_for_contrastive_explanation_milp_computation = seconds
            return f"Contrastive MILP time limit set to {seconds} seconds"
        else:
            self._explainer.configuration.time_limit_for_counterfactual_explanation_milp_computation = seconds
            return f"Counterfactual MILP time limit set to {seconds} seconds"

    def _set_language(self, args: list[str]) -> str:
        """Handle /set language <en|fr> command."""
        usage = (f"Usage: {self._highlight_command(Commands.SET.name, SetTargets.LANGUAGE.value)} "
                 f"<{'|'.join(Languages.values())}>")
        if len(args) < 1:
            return usage
        lang = args[0].lower()
        if lang not in Languages.values():
            return usage
        if lang == Languages.EN.value:
            lang = LANGUAGE_ENGLISH_KEY
        elif lang == Languages.FR.value:
            lang = LANGUAGE_FRENCH_KEY
        self._explainer.language = lang
        return f"Language set to {lang}"

    def _set_display_mode(self, args: list[str]) -> str:
        """Handle /set display-mode <user|developer> command."""
        usage = (f"Usage: {self._highlight_command(Commands.SET.name, SetTargets.DISPLAY_MODE.value)} "
                 f"<{'|'.join(DisplayModes.values())}>")
        if len(args) < 1:
            return usage
        mode = args[0].lower()
        if mode not in DisplayModes.values():
            return usage
        self._display_mode = mode
        return f"Display mode set to {mode}"

    def handle_enable(self, args: list[str]) -> str:
        """Handle /enable <feature> command."""
        if len(args) < 1:
            return f"Usage: {self._yellow(Commands.ENABLE.name)} <feature>"
        feature = args[0].lower()
        enable_targets = EnableTargets.values()
        if feature not in enable_targets:
            return f"Unknown feature. Valid features: {', '.join(enable_targets)}"
        if feature == "history":
            # History cannot be enabled after construction
            return "Error: history cannot be enabled/disabled after Explainer construction"
        elif feature == "scenario":
            self._explainer.configuration.scenario_explanations_enabled = True
        elif feature == "counterfactual":
            self._explainer.configuration.counterfactual_explanations_enabled = True
        elif feature == "auto-export":
            self._explainer.configuration.exporting_each_contrastive_explanation_automatically_enabled = True
        return f"{feature} enabled"

    def handle_disable(self, args: list[str]) -> str:
        """Handle /disable <feature> command."""
        if len(args) < 1:
            return f"Usage: {self._yellow(Commands.DISABLE.name)} <feature>"
        feature = args[0].lower()
        enable_targets = EnableTargets.values()
        if feature not in enable_targets:
            return f"Unknown feature. Valid features: {', '.join(enable_targets)}"
        if feature == "history":
            # History cannot be disabled after construction
            return "Error: history cannot be enabled/disabled after Explainer construction"
        elif feature == "scenario":
            self._explainer.configuration.scenario_explanations_enabled = False
        elif feature == "counterfactual":
            self._explainer.configuration.counterfactual_explanations_enabled = False
        elif feature == "auto-export":
            self._explainer.configuration.exporting_each_contrastive_explanation_automatically_enabled = False
        return f"{feature} disabled"

    ###########################
    # Command Handlers - Show #
    ###########################

    def handle_show(self, args: list[str]) -> str:
        """Handle /show <resource> [name] command."""
        if len(args) < 1:
            return (f"Usage: {self._yellow(Commands.SHOW.name)} <resource> [name] "
                    f"where resource is: {', '.join(ShowTargets.values())}")
        resource = args[0].lower()
        if resource == ShowTargets.SOLUTION.value:
            return self._show_solution(args[1:])
        elif resource == ShowTargets.INSTANCE.value:
            return self._show_instance(args[1:])
        elif resource == ShowTargets.CURRENT_SOLUTION.value:
            return self._show_current_solution()
        elif resource == ShowTargets.CURRENT_INSTANCE.value:
            return self._show_current_instance()
        elif resource == ShowTargets.EXPLANATION.value:
            return self._show_last_explanation()
        elif resource == ShowTargets.HISTORY.value:
            return self._show_history()
        elif resource == ShowTargets.CONFIG.value:
            return self._show_config()
        else:
            return (f"Unknown resource '{resource}'. "
                    f"Valid resources: {', '.join(ShowTargets.values())}")

    def _show_instance(self, args: list[str]) -> str:
        """Handle /show instance <instance_name> command."""
        if len(args) < 1:
            return f"Usage: {self._yellow(Commands.SHOW.name)} {ShowTargets.INSTANCE.value} <instance_name>"
        instance_name = args[0]
        try:
            instance = self._explainer.history.get_instance_by_name(instance_name)
            return self._format_instance_output(instance)
        except KeyError:
            return f"Instance '{instance_name}' not found."

    def _show_current_instance(self) -> str:
        """Format current instance details."""
        instance = self._explainer.current_instance
        return self._format_instance_output(instance)

    @staticmethod
    def _format_instance_output(instance: Instance) -> str:
        """Format an instance for display."""
        lines = [
            f"Instance: {instance.name}",
            f"Nb employees: {len(instance.employees)}",
            f"Nb tasks: {len(instance.tasks)}",
            ""
        ]
        # Employees
        lines.append("Employees:")
        for employee in instance.employees:
            lines.append(employee.__repr__())
        lines.append("")
        # Tasks
        lines.append("Tasks:")
        for task in instance.tasks:
            lines.append(task.__repr__())
        return "\n".join(lines)

    def _show_solution(self, args: list[str]) -> str:
        """Handle /show solution <solution_name> command."""
        if len(args) < 1:
            return f"Usage: {self._yellow(Commands.SHOW.name)} {ShowTargets.SOLUTION.value} <solution_name>"
        solution_name = args[0]
        try:
            solution = self._explainer.history.get_solution_by_name(solution_name)
            return self._format_solution_output(solution)
        except KeyError:
            return f"Solution '{solution_name}' not found."

    def _show_current_solution(self) -> str:
        """Format current solution details."""
        solution = self._explainer.current_solution
        return self._format_solution_output(solution)

    @staticmethod
    def _format_solution_output(solution: Solution) -> str:
        """Format a solution for display."""
        instance = solution.instance
        lines = [
            f"Solution: {solution.name}",
            f"Instance: {instance.name}",
            f"Feasible: {FeasibilityChecker(solution).is_feasible()}",
            ""
        ]
        # Sequences
        lines.append("Sequences:")
        for employee in instance.employees:
            sequence = solution.get_sequence(employee)
            lines.append(f"{employee.name}: {sequence.__repr__()}")
        lines.append("")
        # KPIs
        if not solution.has_kpis:
            solution.compute_kpis()
        lines.append("KPIs:")
        for kpi_name, kpi_value in solution.kpis.to_dict().items():
            lines.append(f"{kpi_name}: {kpi_value}")
        return "\n".join(lines)


    def _show_last_explanation(self) -> str:
        """Format last explanation for display."""
        try:
            explanation = self._explainer.last_contrastive_explanation
            return self._format_explanation_output(explanation)
        except PermissionError:
            return "No explanation to show. Ask a question first."

    def _show_history(self) -> str:
        """Format history for display."""
        history = self._explainer.history
        lines = ["History:"]
        for instance_name in history.instances_names:
            lines.append(f"\nInstance: {instance_name}")
            solutions = history.get_solutions_names_of_instance_by_name(instance_name)
            for solution_name in solutions:
                lines.append(f"  - Solution: {solution_name}")
        return "\n".join(lines)

    def _show_config(self) -> str:
        """Format configuration for display."""
        config = self._explainer.configuration
        lines = [
            "Configuration:",
            f"  Display Mode: {self._display_mode}",
            f"  Language: {config.language}",
            f"  History Enabled: {'Yes' if config.history_enabled else 'No'}",
            f"  Scenario Enabled: {'Yes' if config.scenario_explanations_enabled else 'No'}",
            f"  Counterfactual Enabled: {'Yes' if config.counterfactual_explanations_enabled else 'No'}",
            f"  Contrastive Time Limit: {config.time_limit_for_contrastive_explanation_milp_computation or 'None'}",
            f"  Counterfactual Time Limit: {config.time_limit_for_counterfactual_explanation_milp_computation or 'None'}",
            f"  Neighborhood Extraction LLM Model: {config.neighborhood_extraction_llm_model or 'None'}",
            f"  Explanation Writing LLM Model: {config.explanation_writing_llm_model or 'None'}",
            f"  Pipeline: {config.pipeline or 'custom'}",
            f"  Template Computation Mode: {config.template_computation_mode}",
            f"  Neighborhood Extraction Mode: {config.neighborhood_extraction_mode}",
            f"  Free-Text Explanation Writing Mode: {config.free_text_explanation_mode}",
            f"  Reuse Cached Explanations: {'Yes' if config.using_cached_contrastive_explanations_enabled else 'No'}",
            f"  Auto-Export Enabled: {'Yes' if config.exporting_each_contrastive_explanation_automatically_enabled else 'No'}",
        ]
        return "\n".join(lines)

    ###########################
    # Command Handlers - Help #
    ###########################

    def handle_help(self, args: list[str]) -> str:
        """Handle /help command, listing only the kinds of template-based questions currently activated."""
        return Commands.list_string(self.get_activated_ask_template_targets())

    ############################
    # Command Handlers - Clear #
    ############################

    def handle_clear(self, args: list[str]) -> str:
        """Handle /clear <target> command."""
        usage = f"Usage: {self._yellow(Commands.CLEAR.name)} <{'|'.join(ClearTargets.values())}>"
        if len(args) < 1:
            return usage
        target = args[0].lower()
        if target == ClearTargets.SCREEN.value:
            os.system('clear' if os.name != 'nt' else 'cls')
            return ""
        if target == ClearTargets.CACHED_EXPLANATIONS.value:
            if not self._explainer.configuration.using_cached_contrastive_explanations_enabled:
                return "Using cached contrastive explanations is disabled: nothing to clear."
            nb_cleared_explanations = self._explainer.clear_cached_contrastive_explanations()
            return f"Cleared {nb_cleared_explanations} cached contrastive explanation(s)"
        return usage

    ###########################
    # Command Handlers - Quit #
    ###########################

    def handle_quit(self, args: list[str]) -> str:
        """Handle /quit command."""
        self._stop()
        return ""

    #########################
    # Helper Methods - Text #
    #########################

    @staticmethod
    def _yellow(text: str) -> str:
        """Return text formatted in color #ffab40 (orange-yellow) using 24-bit ANSI codes."""
        return f"\033[38;2;255;171;64m{text}\033[0m"

    @staticmethod
    def _blue(text: str) -> str:
        """Return text formatted in color #4285f4 (blue) using 24-bit ANSI codes."""
        return f"\033[38;2;66;133;244m{text}\033[0m"

    @staticmethod
    def _gray(text: str) -> str:
        """Return text formatted in color #767676 (gray) using 24-bit ANSI codes."""
        return f"\033[38;2;118;118;118m{text}\033[0m"

    @staticmethod
    def _highlight_command(*tokens: str) -> str:
        """
        Return the command made of the given tokens (e.g. /set and one of its targets), highlighted,
        as it is named in usages and hints.

        Args:
            tokens: The command name, then the targets or options typed after it.

        Returns:
            The tokens joined by spaces, in yellow.
        """
        return ExplainerCLI._yellow(" ".join(tokens))

    @staticmethod
    def _highlight_fields(text: str) -> str:
        """Highlight field patterns like {Employee}, {Task}, ... in yellow."""
        def replace_field(match):
            return ExplainerCLI._yellow(match.group(0))
        return re.sub(r'\{[^}]+}', replace_field, text)
