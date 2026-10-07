# Standard libraries
import os
import re
from typing import Callable, Optional, cast

# Third-party libraries
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

# Local libraries
from src.explaining.explanation.explanation import Explanation, ExplanationComputationModes
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.configuration import ExplainerConfiguration, TemplateComputationModes
from src.explaining.interacting.interface.cli.commands import (
    Commands, ClearTargets, ShowTargets, SwitchTargets, Features, Languages, DisplayModes, LLMModels,
)
from src.explaining.interacting.interface.cli.completer import ExplainerCLICompleter
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.neighborhood.neighborhood import Neighborhood, NeighborhoodExtractionModes
from src.explaining.question.predefined.bank import QUESTIONS_TEMPLATES
from src.feasibility.checker import FeasibilityChecker
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY


################
# ExplainerCLI #
################

class ExplainerCLI:
    """
    REPL-style terminal interface for the Explainer class.

    Allows end-users to interactively ask questions about a solution,
    configure the explainer, and manage stored solutions/instances.
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
                using_already_computed_contrastive_explanations_enabled=False,
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
            Commands.LLM_MODEL.name: self.handle_llm_model,
            Commands.TEMPLATE_COMPUTATION_MODE.name: self.handle_template_mode,
            Commands.NEIGHBORHOOD_EXTRACTION_MODE.name: self.handle_neighborhood_extraction_mode,
            Commands.CONTRASTIVE.name: self.handle_contrastive,
            Commands.ASK.name: self.handle_ask,
            Commands.SAVE_SOLUTION.name: self.handle_save_solution,
            Commands.LIST_TEMPLATES.name: self.handle_list_templates,
            Commands.LIST_INSTANCES.name: self.handle_list_instances,
            Commands.LIST_SOLUTIONS.name: self.handle_list_solutions,
            Commands.SWITCH.name: self.handle_switch,
            Commands.LANGUAGE.name: self.handle_language,
            Commands.EXPORT.name: self.handle_export,
            # Configuration
            Commands.TIME_LIMIT_CONTRASTIVE.name: self.handle_time_limit_contrastive,
            Commands.TIME_LIMIT_COUNTERFACTUAL.name: self.handle_time_limit_counterfactual,
            Commands.ENABLE.name: self.handle_enable,
            Commands.DISABLE.name: self.handle_disable,
            # Display
            Commands.SHOW.name: self.handle_show,
            Commands.DISPLAY_MODE.name: self.handle_display_mode,
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

    ####################
    # Command Handlers #
    ####################

    def handle_llm_model(self, args: list[str]) -> str:
        """Handle /llm-model <model> command."""
        if len(args) < 1:
            return (f"Usage: {self._yellow(Commands.LLM_MODEL.name)} <provider/model> "
                    f"(e.g. {', '.join(LLMModels.list_values())})")
        model = args[0]
        # Basic validation: should contain a slash
        if "/" not in model:
            return f"Invalid model format '{model}'. Expected format: 'provider/model'"
        self._explainer.neighborhood_extraction_llm_model = model
        if self._explainer.configuration.neighborhood_extraction_mode == NeighborhoodExtractionModes.LLM.value:
            try:
                self._explainer.prepare_extractor()
            except (ValueError, RuntimeError, ImportError) as e:
                return f"LLM model set to {model}, but its extractor could not be set up: {e}"
        return f"LLM model set to {model}"

    def handle_template_mode(self, args: list[str]) -> str:
        """Handle /template-computation-mode <mode> command."""
        if len(args) < 1:
            return (f"Usage: {self._yellow(Commands.TEMPLATE_COMPUTATION_MODE.name)} "
                    f"<{'|'.join(TemplateComputationModes.list_values())}>")
        mode = args[0].lower()
        if mode not in TemplateComputationModes.list_values():
            return (f"Usage: {self._yellow(Commands.TEMPLATE_COMPUTATION_MODE.name)} "
                    f"<{'|'.join(TemplateComputationModes.list_values())}>")
        self._explainer.configuration.template_computation_mode = mode
        return f"Template computation mode set to {mode}"

    def handle_neighborhood_extraction_mode(self, args: list[str]) -> str:
        """
        Handle /neighborhood-extraction-mode <mode> command.

        Switching to llm sets up the LLM extractor right away, so that a misconfigured LLM backend is reported now
        rather than on the next question. The mode is left unchanged if no LLM model is set or the setup fails.
        """
        usage = (f"Usage: {self._yellow(Commands.NEIGHBORHOOD_EXTRACTION_MODE.name)} "
                 f"<{'|'.join(NeighborhoodExtractionModes.list_values())}>")
        if len(args) < 1:
            return usage
        mode = args[0].lower()
        if mode not in NeighborhoodExtractionModes.list_values():
            return usage
        if mode == NeighborhoodExtractionModes.LLM.value:
            if self._explainer.neighborhood_extraction_llm_model is None:
                return (f"No LLM model configured. "
                        f"Use {self._yellow(Commands.LLM_MODEL.name)} <provider/model> first.")
            try:
                self._explainer.prepare_extractor()
            except (ValueError, RuntimeError, ImportError) as e:
                return f"Error: {e}"
        self._explainer.configuration.neighborhood_extraction_mode = mode
        result = f"Neighborhood extraction mode set to {mode}"
        if self._explainer.configuration.template_computation_mode == TemplateComputationModes.TAILORED.value:
            result += "\n" + self._gray(
                f"NB: It only applies in {TemplateComputationModes.NEIGHBORHOOD.value} template computation mode "
                f"(see {Commands.TEMPLATE_COMPUTATION_MODE.name})."
            )
        return result

    def handle_ask(self, args: list[str]) -> str:
        """Handle /ask <question> command."""
        if len(args) < 1:
            return f"Usage: {self._yellow(Commands.ASK.name)} <free-text-question>"
        if self._explainer.neighborhood_extraction_llm_model is None:
            return (f"No LLM model configured. "
                    f"Use {self._yellow(Commands.LLM_MODEL.name)} <provider/model> first.")
        question_text = " ".join(args)
        try:
            explanation = self._explainer.get_free_text_explanation(question_text)
            return self._format_explanation_output(explanation)
        except (NeighborhoodError, ValueError) as e:
            return f"Error: {e}"

    def handle_contrastive(self, args: list[str]) -> str:
        """Handle /contrastive <template_id> <value1> <value2> ... command."""
        if len(args) < 1:
            return f"Usage: {self._yellow(Commands.CONTRASTIVE.name)} <template_id> <value1> <value2> ..."
        template_id = args[0]
        field_values = args[1:]
        # Validate template ID
        if template_id not in QUESTIONS_TEMPLATES:
            return (f"Unknown template ID '{template_id}'. "
                    f"Use {self._yellow(Commands.LIST_TEMPLATES.name)} to see available templates.")
        # Get template to check number of fields
        template = QUESTIONS_TEMPLATES[template_id]
        nb_expected_fields = len(template.fields_keys)
        nb_provided_values = len(field_values)
        if nb_provided_values < nb_expected_fields:
            return (f"Template '{template_id}' requires {nb_expected_fields} values, "
                    f"but only {nb_provided_values} provided.")
        if nb_provided_values > nb_expected_fields:
            return (f"Template '{template_id}' requires {nb_expected_fields} values, "
                    f"but {nb_provided_values} provided.")
        try:
            explanation = self._explainer.get_contrastive_explanation(template_id, field_values)
            return self._format_explanation_output(explanation)
        except (ValueError, TypeError) as e:
            return f"Error: {e}"

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

    def handle_list_templates(self, args: list[str]) -> str:
        """Handle /list-templates command."""
        templates = self._explainer.activated_question_templates
        if not templates:
            return "No templates available."
        lines = ["Available templates:"]
        for template in templates:
            language = self._explainer.language
            text = template.all_texts.get(language, template.all_texts[LANGUAGE_ENGLISH_KEY])
            lines.append(f"  • {self._yellow(template.id)}: {self._highlight_fields(text)}")
        return "\n".join(lines)

    def handle_list_instances(self, args: list[str]) -> str:
        """Handle /list-instances command."""
        instance_names = self._explainer.history.instances_names
        if not instance_names:
            return "No stored instances."
        lines = ["Stored instances:"]
        for name in instance_names:
            lines.append(f"  • {name}")
        return "\n".join(lines)

    def handle_list_solutions(self, args: list[str]) -> str:
        """Handle /list-solutions command."""
        solution_names = self._explainer.history.solutions_names
        if not solution_names:
            return "No stored solutions."
        lines = ["Stored solutions:"]
        for name in solution_names:
            lines.append(f"  • {name}")
        return "\n".join(lines)

    def handle_switch(self, args: list[str]) -> str:
        """Handle /switch <target> [name] command."""
        if len(args) < 1:
            return (f"Usage: {self._yellow(Commands.SWITCH.name)} <target> [name] "
                    f"where target is: {', '.join(SwitchTargets.list_values())}")
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
                    f"Valid targets: {', '.join(SwitchTargets.list_values())}")

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
            return (f"Instance '{instance_name}' not found. "
                    f"Use {self._yellow(Commands.LIST_INSTANCES.name)} to see available instances.")

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
            return (f"Solution '{solution_name}' not found. "
                    f"Use {self._yellow(Commands.LIST_SOLUTIONS.name)} to see available solutions.")

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

    def handle_language(self, args: list[str]) -> str:
        """Handle /language <en|fr> command."""
        if len(args) < 1:
            return f"Usage: {self._yellow(Commands.LANGUAGE.name)} <{'|'.join(Languages.list_values())}>"
        lang = args[0].lower()
        if lang not in Languages.list_values():
            return f"Usage: {self._yellow(Commands.LANGUAGE.name)} <{'|'.join(Languages.list_values())}>"
        if lang == "en":
            lang = LANGUAGE_ENGLISH_KEY
        elif lang == "fr":
            lang = LANGUAGE_FRENCH_KEY
        self._explainer.language = lang
        return f"Language set to {lang}"

    def handle_export(self, args: list[str]) -> str:
        """Handle /export command."""
        try:
            self._explainer.export_last_contrastive_explanation()
            file_path = self._explainer.configuration.contrastive_explanation_output_directory_relative_path
            return f"Explanation exported to {file_path}"
        except PermissionError as e:
            return f"Error: {e}"

    def handle_time_limit_contrastive(self, args: list[str]) -> str:
        """Handle /time-limit-contrastive <seconds> command."""
        if len(args) < 1:
            return f"Usage: {self._yellow(Commands.TIME_LIMIT_CONTRASTIVE.name)} <seconds>"
        try:
            seconds = int(args[0])
            if seconds < 0:
                return "Time limit must be a non-negative integer."
            self._explainer.configuration.time_limit_for_contrastive_explanation_milp_computation = seconds
            return f"Contrastive MILP time limit set to {seconds} seconds"
        except ValueError:
            return "Time limit must be an integer."

    def handle_time_limit_counterfactual(self, args: list[str]) -> str:
        """Handle /time-limit-counterfactual <seconds> command."""
        if len(args) < 1:
            return f"Usage: {Commands.TIME_LIMIT_COUNTERFACTUAL.name} <seconds>"
        try:
            seconds = int(args[0])
            if seconds < 0:
                return "Time limit must be a non-negative integer."
            self._explainer.configuration.time_limit_for_counterfactual_explanation_milp_computation = seconds
            return f"Counterfactual MILP time limit set to {seconds} seconds"
        except ValueError:
            return "Time limit must be an integer."

    def handle_enable(self, args: list[str]) -> str:
        """Handle /enable <feature> command."""
        if len(args) < 1:
            return f"Usage: {self._yellow(Commands.ENABLE.name)} <feature>"
        feature = args[0].lower()
        valid_features = Features.list_values()
        if feature not in valid_features:
            return f"Unknown feature. Valid features: {', '.join(valid_features)}"
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
        valid_features = Features.list_values()
        if feature not in valid_features:
            return f"Unknown feature. Valid features: {', '.join(valid_features)}"
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

    def handle_show(self, args: list[str]) -> str:
        """Handle /show <resource> [name] command."""
        if len(args) < 1:
            return (f"Usage: {self._yellow(Commands.SHOW.name)} <resource> [name] "
                    f"where resource is: {', '.join(ShowTargets.list_values())}")
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
                    f"Valid resources: {', '.join(ShowTargets.list_values())}")

    def handle_display_mode(self, args: list[str]) -> str:
        """Handle /display-mode <user|developer> command."""
        if len(args) < 1:
            return f"Usage: {Commands.DISPLAY_MODE.name} <{'|'.join(DisplayModes.list_values())}>"
        mode = args[0].lower()
        if mode not in DisplayModes:
            return f"Usage: {Commands.DISPLAY_MODE.name} <{'|'.join(DisplayModes.list_values())}>"
        self._display_mode = mode
        return f"Display mode set to {mode}"

    @staticmethod
    def handle_help(args: list[str]) -> str:
        """Handle /help command."""
        return Commands.list_string()

    def handle_clear(self, args: list[str]) -> str:
        """Handle /clear <target> command."""
        usage = f"Usage: {self._yellow(Commands.CLEAR.name)} <{'|'.join(ClearTargets.list_values())}>"
        if len(args) < 1:
            return usage
        target = args[0].lower()
        if target == ClearTargets.SCREEN.value:
            os.system('clear' if os.name != 'nt' else 'cls')
            return ""
        if target == ClearTargets.CACHED_EXPLANATIONS.value:
            if not self._explainer.configuration.using_already_computed_contrastive_explanations_enabled:
                return "Using already computed contrastive explanations is disabled: nothing to clear."
            nb_cleared_explanations = self._explainer.clear_already_computed_contrastive_explanations()
            return f"Cleared {nb_cleared_explanations} cached contrastive explanation(s)"
        return usage

    def handle_quit(self, args: list[str]) -> str:
        """Handle /quit command."""
        self._stop()
        return ""

    ##################
    # Helper Methods #
    ##################

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
    def _highlight_fields(text: str) -> str:
        """Highlight field patterns like {Employee}, {Task}, ... in yellow."""
        def replace_field(match):
            return ExplainerCLI._yellow(match.group(0))
        return re.sub(r'\{[^}]+}', replace_field, text)

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
            if explanation.computation_time is not None:
                lines.append(self._gray(f"Computation time: {explanation.computation_time:.3f}s"))
            lines.append(self._gray(f"Support solution: {feasibility}"))
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
            f"  LLM Model: {config.neighborhood_extraction_llm_model or 'None'}",
            f"  Template Computation Mode: {config.template_computation_mode}",
            f"  Neighborhood Extraction Mode: {config.neighborhood_extraction_mode}",
            f"  Scenario Enabled: {'Yes' if config.scenario_explanations_enabled else 'No'}",
            f"  Counterfactual Enabled: {'Yes' if config.counterfactual_explanations_enabled else 'No'}",
            f"  Reuse Computed Explanations: "
            f"{'Yes' if config.using_already_computed_contrastive_explanations_enabled else 'No'}",
            f"  Contrastive Time Limit: {config.time_limit_for_contrastive_explanation_milp_computation or 'None'}",
            f"  Counterfactual Time Limit: {config.time_limit_for_counterfactual_explanation_milp_computation or 'None'}",
            f"  Auto-Export Enabled: {'Yes' if config.exporting_each_contrastive_explanation_automatically_enabled else 'No'}",
        ]
        return "\n".join(lines)
