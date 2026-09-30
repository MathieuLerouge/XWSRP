# Standard libraries
import argparse
from typing import Callable, Optional

# Local libraries
from src.explaining.interacting.explainer import Explainer
from src.explaining.interacting.configuration import ExplainerConfiguration
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.question.predefined.bank import QUESTIONS_TEMPLATES
from src.modeling.solution import Solution
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY


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
                extractor_model=None,  # Set via /llm-model
                language=LANGUAGE_ENGLISH_KEY,
                history_enabled=True,
                scenario_explanations_enabled=False,  # TODO: Not yet implemented
                counterfactual_explanations_enabled=False,  # TODO: Not yet implemented
                using_already_computed_contrastive_explanations_enabled=False,
                exporting_each_contrastive_explanation_automatically_enabled=False,
            )
            self._explainer = Explainer(solution, configuration)
            self._solution = solution

        # CLI-specific state
        self._running = True
        self._last_command: Optional[str] = None
        self._template_mode: str = "tailored"  # or "neighborhood"

        # Command handlers registry
        self._commands: dict[str, Callable[[list[str]], str]] = {}

        # Register all commands
        self._register_commands()

    def _register_commands(self) -> None:
        """Register all command handlers."""
        self._commands = {
            # Core
            "/llm-model": self.handle_llm_model,
            "/template-mode": self.handle_template_mode,
            "/ask": self.handle_ask,
            "/contrastive": self.handle_contrastive,
            "/save-solution": self.handle_save_solution,
            "/list-templates": self.handle_list_templates,
            "/list-instances": self.handle_list_instances,
            "/list-solutions": self.handle_list_solutions,
            "/switch-instance": self.handle_switch_instance,
            "/switch-solution": self.handle_switch_solution,
            "/language": self.handle_language,
            "/export": self.handle_export,

            # Configuration
            "/time-limit-contrastive": self.handle_time_limit_contrastive,
            "/time-limit-counterfactual": self.handle_time_limit_counterfactual,
            "/enable": self.handle_enable,
            "/disable": self.handle_disable,

            # Display
            "/show": self.handle_show,
            "/show-instance": self.handle_show_instance,
            "/show-solution": self.handle_show_solution,
            "/help": self.handle_help,

            # Session
            "/quit": self.handle_quit,
        }

    def run(self) -> None:
        """Main REPL loop."""
        print("Explainer CLI - Type /help for commands, /quit to exit")
        print(f"Loaded solution: {self._solution.name}")

        while self._running:
            try:
                # Show prompt
                user_input = input("> ").strip()

                if not user_input:
                    continue

                # Store for potential multi-part commands
                self._last_command = user_input

                # Dispatch
                self.dispatch(user_input)

            except KeyboardInterrupt:
                print("\nUse /quit to exit.")
            except EOFError:
                print()
                self._stop()
            except Exception as e:
                print(f"Error: {e}")

    def _stop(self) -> None:
        """Cleanup and exit."""
        self._running = False
        print("Goodbye!")

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
                    print(result)
            except Exception as e:
                print(f"Error executing {command}: {e}")
        else:
            print(f"Unknown command '{command}'. Type /help for available commands.")

    ####################
    # Command Handlers #
    ####################

    def handle_llm_model(self, args: list[str]) -> str:
        """Handle /llm-model <model> command."""
        if len(args) < 1:
            return "Usage: /llm-model <provider/model>"

        model = args[0]
        # Basic validation: should contain a slash
        if "/" not in model:
            return f"Invalid model format '{model}'. Expected format: 'provider/model'"

        self._explainer.extractor_model = model
        return f"LLM model set to {model}"

    def handle_template_mode(self, args: list[str]) -> str:
        """Handle /template-mode <mode> command."""
        if len(args) < 1:
            return "Usage: /template-mode <tailored|neighborhood>"

        mode = args[0].lower()
        if mode not in ["tailored", "neighborhood"]:
            return "Usage: /template-mode <tailored|neighborhood>"

        if mode == "neighborhood":
            return "NotImplementedError: Tailored-neighborhood pipeline for template questions is not yet implemented."

        self._template_mode = mode
        return f"Template mode set to {mode}"

    def handle_ask(self, args: list[str]) -> str:
        """Handle /ask <question> command."""
        if len(args) < 1:
            return "Usage: /ask <free-text-question>"

        if self._explainer.extractor_model is None:
            return "No LLM model configured. Use /llm-model <provider/model> first."

        question_text = " ".join(args)
        try:
            explanation = self._explainer.get_free_text_explanation(question_text)
            return self._format_explanation_output(explanation)
        except (NeighborhoodError, ValueError) as e:
            return f"Error: {e}"

    def handle_contrastive(self, args: list[str]) -> str:
        """Handle /contrastive <template_id> <value1> <value2> ... command."""
        if len(args) < 1:
            return "Usage: /contrastive <template_id> <value1> <value2> ..."

        template_id = args[0]
        field_values = args[1:]

        # Validate template ID
        if template_id not in QUESTIONS_TEMPLATES:
            return f"Unknown template ID '{template_id}'. Use /list-templates to see available templates."

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
            self._explainer.save_last_contrastive_support_solution()
            last_explanation = self._explainer.last_contrastive_explanation
            solution_name = last_explanation.support_solution.name
            return f"Support solution saved as {solution_name}"
        except PermissionError as e:
            return f"Error: {e}"

    def handle_list_templates(self, args: list[str]) -> str:
        """Handle /list-templates command."""
        templates = self._explainer.activated_question_templates
        if not templates:
            return "No templates available."

        lines = ["Available templates:"]
        for template in templates:
            lang = self._explainer.language
            text = template.all_texts.get(lang, template.all_texts[LANGUAGE_ENGLISH_KEY])
            lines.append(f"  - {template.id}: {text}")

        return "\n".join(lines)

    def handle_list_instances(self, args: list[str]) -> str:
        """Handle /list-instances command."""
        instance_names = self._explainer.history.instances_names
        if not instance_names:
            return "No stored instances."

        lines = ["Stored instances:"]
        for name in instance_names:
            lines.append(f"  - {name}")

        return "\n".join(lines)

    def handle_list_solutions(self, args: list[str]) -> str:
        """Handle /list-solutions command."""
        solution_names = self._explainer.history.solutions_names
        if not solution_names:
            return "No stored solutions."

        lines = ["Stored solutions:"]
        for name in solution_names:
            lines.append(f"  - {name}")

        return "\n".join(lines)

    def handle_switch_instance(self, args: list[str]) -> str:
        """Handle /switch-instance <instance_name> command."""
        if len(args) < 1:
            return "Usage: /switch-instance <instance_name>"

        instance_name = args[0]
        try:
            instance = self._explainer.history.get_instance_by_name(instance_name)
            # Find a solution associated with this instance
            solutions = self._explainer.history.get_solutions_of_instance_by_name(instance_name)
            if solutions:
                solution = solutions[0]
                self._explainer.current_solution = solution
                return f"Switched to instance {instance_name} and solution {solution.name}"
            else:
                return f"Instance {instance_name} found but has no associated solutions."
        except KeyError:
            return f"Instance '{instance_name}' not found. Use /list-instances to see available instances."

    def handle_switch_solution(self, args: list[str]) -> str:
        """Handle /switch-solution <solution_name> command."""
        if len(args) < 1:
            return "Usage: /switch-solution <solution_name>"

        solution_name = args[0]
        try:
            solution = self._explainer.history.get_solution_by_name(solution_name)
            self._explainer.current_solution = solution
            return f"Switched to solution {solution.name}"
        except KeyError:
            return f"Solution '{solution_name}' not found. Use /list-solutions to see available solutions."

    def handle_language(self, args: list[str]) -> str:
        """Handle /language <en|fr> command."""
        if len(args) < 1:
            return "Usage: /language <en|fr>"

        lang = args[0].lower()
        if lang not in ["en", "fr", LANGUAGE_ENGLISH_KEY.lower(), LANGUAGE_FRENCH_KEY.lower()]:
            return "Usage: /language <en|fr>"

        # Normalize to uppercase
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
            last_explanation = self._explainer.last_contrastive_explanation
            file_path = self._explainer.configuration.contrastive_explanation_output_directory_relative_path
            return f"Explanation exported to {file_path}"
        except PermissionError as e:
            return f"Error: {e}"

    def handle_time_limit_contrastive(self, args: list[str]) -> str:
        """Handle /time-limit-contrastive <seconds> command."""
        if len(args) < 1:
            return "Usage: /time-limit-contrastive <seconds>"

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
            return "Usage: /time-limit-counterfactual <seconds>"

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
            return "Usage: /enable <feature>"

        feature = args[0].lower()
        valid_features = ["history", "scenario", "counterfactual", "auto-export"]

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
            return "Usage: /disable <feature>"

        feature = args[0].lower()
        valid_features = ["history", "scenario", "counterfactual", "auto-export"]

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
        """Handle /show <resource> command."""
        if len(args) < 1:
            return "Usage: /show <resource> where resource is: solution, instance, explanation, history, config"

        resource = args[0].lower()

        if resource == "solution":
            return self._show_current_solution()
        elif resource == "instance":
            return self._show_current_instance()
        elif resource == "explanation":
            return self._show_last_explanation()
        elif resource == "history":
            return self._show_history()
        elif resource == "config":
            return self._show_config()
        else:
            return f"Unknown resource '{resource}'. Valid resources: solution, instance, explanation, history, config"

    def handle_show_instance(self, args: list[str]) -> str:
        """Handle /show-instance <instance_name> command."""
        if len(args) < 1:
            return "Usage: /show-instance <instance_name>"

        instance_name = args[0]
        try:
            instance = self._explainer.history.get_instance_by_name(instance_name)
            return self._format_instance_output(instance)
        except KeyError:
            return f"Instance '{instance_name}' not found."

    def handle_show_solution(self, args: list[str]) -> str:
        """Handle /show-solution <solution_name> command."""
        if len(args) < 1:
            return "Usage: /show-solution <solution_name>"

        solution_name = args[0]
        try:
            solution = self._explainer.history.get_solution_by_name(solution_name)
            return self._format_solution_output(solution)
        except KeyError:
            return f"Solution '{solution_name}' not found."

    def handle_help(self, args: list[str]) -> str:
        """Handle /help command."""
        return """Explainer CLI - Available Commands

Core Commands:
  /llm-model <model>          Set LLM model for free-text extraction
  /template-mode <mode>       Switch template pipeline (tailored/neighborhood)
  /ask <question>             Ask a free-text contrastive question
  /contrastive <id> <vals>    Ask a template-based contrastive question
  /save-solution              Save current support solution
  /list-templates             Show available question templates
  /list-instances             List stored instances
  /list-solutions             List stored solutions
  /switch-instance <name>     Change current instance
  /switch-solution <name>    Change current solution
  /language <en|fr>           Switch language
  /export                     Export last explanation

Configuration Commands:
  /time-limit-contrastive <s>    Set MILP time limit for contrastive
  /time-limit-counterfactual <s> Set MILP time limit for counterfactual
  /enable <feature>              Enable a feature (history, scenario, counterfactual, auto-export)
  /disable <feature>             Disable a feature

Display Commands:
  /show <resource>            Show details (solution, instance, explanation, history, config)
  /show-instance <name>      Show instance details
  /show-solution <name>     Show solution details
  /help                      Show this help message

Session Commands:
  /quit                      Exit the CLI"""

    def handle_quit(self, args: list[str]) -> str:
        """Handle /quit command."""
        self._stop()
        return ""

    ##################
    # Helper Methods #
    ##################

    def _format_explanation_output(self, explanation) -> str:
        """Format an explanation for display."""
        question_text = explanation.question.text
        explanation_text = explanation.text
        support_feasible = "Yes" if explanation.support_solution_is_feasible else "No"
        support_name = explanation.support_solution.name

        return f"""Question: {question_text}

Explanation:
{explanation_text}

Support Solution Feasible: {support_feasible}
Support Solution Name: {support_name}"""

    def _show_current_solution(self) -> str:
        """Format current solution details."""
        solution = self._explainer.current_solution
        instance_name = solution.instance.name
        feasible = "Yes" if solution.has_kpis else "Unknown"

        try:
            nb_employees = len(solution.instance.employees)
            nb_tasks = len(solution.instance.tasks)
        except AttributeError:
            nb_employees = 0
            nb_tasks = 0

        # Get route summary
        routes_summary = []
        for employee in solution.instance.employees:
            try:
                seq = solution.get_sequence(employee)
                tasks = [str(step.activity) for step in seq.get_steps() if hasattr(step.activity, 'name')]
                routes_summary.append(f"{employee.name}: {' -> '.join(tasks)}")
            except Exception:
                pass

        return f"""Solution: {solution.name}
Instance: {instance_name}
Feasible: {feasible}

Employees: {nb_employees}
Tasks: {nb_tasks}
Routes: {len(routes_summary)}"""

    def _show_current_instance(self) -> str:
        """Format current instance details."""
        instance = self._explainer.current_instance
        return self._format_instance_output(instance)

    def _format_instance_output(self, instance) -> str:
        """Format an instance for display."""
        lines = [f"Instance: {instance.name}", "", "Employees:"]

        for employee in instance.employees:
            lines.append(f"  - {employee.name}: skill={employee.skill_level}, "
                        f"location={employee.location.name if hasattr(employee.location, 'name') else employee.location}")

        lines.append("")
        lines.append("Tasks:")

        for task in instance.tasks:
            lines.append(f"  - {task.name}: duration={task.duration}, "
                        f"location={task.location.name if hasattr(task.location, 'name') else task.location}")

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
        lines = ["Configuration:"]
        lines.append(f"  LLM Model: {config.extractor_model or 'None'}")
        lines.append(f"  Template Mode: {self._template_mode}")
        lines.append(f"  Language: {config.language}")
        lines.append(f"  History Enabled: {'Yes' if config.history_enabled else 'No'}")
        lines.append(f"  Scenario Enabled: {'Yes' if config.scenario_explanations_enabled else 'No'}")
        lines.append(f"  Counterfactual Enabled: {'Yes' if config.counterfactual_explanations_enabled else 'No'}")
        lines.append(f"  Auto-Export Enabled: {'Yes' if config.exporting_each_contrastive_explanation_automatically_enabled else 'No'}")
        lines.append(f"  Contrastive Time Limit: {config.time_limit_for_contrastive_explanation_milp_computation or 'None'}")
        lines.append(f"  Counterfactual Time Limit: {config.time_limit_for_counterfactual_explanation_milp_computation or 'None'}")
        return "\n".join(lines)


def main():
    """Entry point for CLI usage."""
    parser = argparse.ArgumentParser(description="Explainer CLI")
    parser.add_argument("solution", help="Path to solution file (JSON or TXT)")
    args = parser.parse_args()

    # Load solution
    from src.importing.solution import import_solution_from_json_file, import_solution_from_txt_file
    
    solution_file_path = args.solution
    if solution_file_path.endswith('.json'):
        solution = import_solution_from_json_file(solution_file_path)
    elif solution_file_path.endswith('.txt'):
        solution = import_solution_from_txt_file(solution_file_path)
    else:
        # Try JSON first, then TXT
        try:
            solution = import_solution_from_json_file(solution_file_path)
        except Exception:
            solution = import_solution_from_txt_file(solution_file_path)

    # Start CLI
    cli = ExplainerCLI(solution)
    cli.run()


if __name__ == "__main__":
    main()
