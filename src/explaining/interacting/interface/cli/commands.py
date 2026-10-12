# Standard libraries
from enum import Enum
from typing import Optional

# Local libraries
from src.explaining.interacting.configuration import FreeTextExplanationModes, Pipelines, TemplateComputationModes
from src.explaining.neighborhood.neighborhood import NeighborhoodExtractionModes


############
# Commands #
############

class Commands(Enum):
    """Enum of all CLI commands with their metadata."""
    
    # Core Commands
    ASK = ("/ask", "Ask a free-text question")
    ASK_TEMPLATE = ("/ask-template", "Ask a template-based question")
    SAVE_SOLUTION = ("/save-solution", "Save current support solution")
    LIST = ("/list", "List available or stored items")
    SWITCH = ("/switch", "Change current instance or solution")
    EXPORT = ("/export", "Export last explanation")
    
    # Configuration Commands
    SET = ("/set", "Set the pipeline, the language, a mode, a MILP solving time limit or an LLM model")
    ENABLE = ("/enable", "Enable a feature")
    DISABLE = ("/disable", "Disable a feature")
    
    # Display Commands
    SHOW = ("/show", "Show details")
    HELP = ("/help", "Show this help message")
    
    # Session Commands
    CLEAR = ("/clear", "Clear the terminal screen or the cached contrastive explanations")
    QUIT = ("/quit", "Exit the CLI")
    
    @property
    def name(self) -> str:
        """Return the command name (e.g., '/set')."""
        return self.value[0]
    
    @property
    def description(self) -> str:
        """Return the command description."""
        return self.value[1]

    @classmethod
    def list_string(cls, ask_template_targets: Optional[list[str]] = None) -> str:
        """
        Generate the list string for all commands.

        Args:
            ask_template_targets: The kinds of template-based questions to list for /ask-template
                (typically the activated ones), or None to list every kind.
        """
        if ask_template_targets is None:
            ask_template_targets = AskTemplateTargets.list_values()
        lines = [
            "Explainer CLI - Available Commands",
            "",
            "Core Commands:",
            f"  {cls.ASK.name} <question>                      {cls.ASK.description}",
            f"  {cls.ASK_TEMPLATE.name} <kind> <id> <vals>     {cls.ASK_TEMPLATE.description} "
            f"({', '.join(ask_template_targets)})",
            f"  {cls.SAVE_SOLUTION.name}                       {cls.SAVE_SOLUTION.description}",
            f"  {cls.LIST.name} <target>                       {cls.LIST.description} "
            f"({', '.join(ListTargets.list_values())})",
            f"  {cls.SWITCH.name} <target> [name]              {cls.SWITCH.description} "
            f"({', '.join(SwitchTargets.list_values())})",
            f"  {cls.EXPORT.name}                              {cls.EXPORT.description}",
            "",
            "Configuration Commands:",
            f"  {cls.SET.name} <target> <option> [value]    {cls.SET.description}:",
            f"    {SetTargets.PIPELINE.value} <{'|'.join(Pipelines.list_values())}> [provider/model]",
            f"    {SetTargets.LANGUAGE.value} <{'|'.join(Languages.list_values())}>",
            f"    {SetTargets.DISPLAY_MODE.value} <{'|'.join(DisplayModes.list_values())}>",
            f"    {SetTargets.TEMPLATE_COMPUTATION_MODE.value} <{'|'.join(TemplateComputationModes.list_values())}>",
            f"    {SetTargets.NEIGHBORHOOD_EXTRACTION_MODE.value} "
            f"<{'|'.join(NeighborhoodExtractionModes.list_values())}>",
            f"    {SetTargets.FREE_TEXT_EXPLANATION_WRITING_MODE.value} "
            f"<{'|'.join(FreeTextExplanationModes.list_values())}>",
            f"    {SetTargets.SOLVING_TIME_LIMIT.value} <{'|'.join(SolvingTimeLimitTargets.list_values())}> <seconds>",
            f"    {SetTargets.LLM_MODEL.value} <{'|'.join(LLMModelTargets.list_values())}> <provider/model>",
            f"  {cls.ENABLE.name} <feature>                 {cls.ENABLE.description}",
            f"  {cls.DISABLE.name} <feature>                {cls.DISABLE.description}",
            "",
            "Display Commands:",
            f"  {cls.SHOW.name} <resource> [name]    {cls.SHOW.description} ({', '.join(ShowTargets.list_values())})",
            f"  {cls.HELP.name}                      {cls.HELP.description}",
            "",
            "Session Commands:",
            f"  {cls.CLEAR.name} <target>    {cls.CLEAR.description} ({', '.join(ClearTargets.list_values())})",
            f"  {cls.QUIT.name}              {cls.QUIT.description}",
        ]
        return "\n".join(lines)


#############
# Languages #
#############

class Languages(Enum):
    """Enum for language options (lowercase, as entered by user)."""
    EN = "en"
    FR = "fr"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid language values."""
        return [member.value for member in cls]


#################
# EnableTargets #
#################

class EnableTargets(Enum):
    """Enum for what /enable and /disable can enable or disable."""
    HISTORY = "history"
    SCENARIO = "scenario"
    COUNTERFACTUAL = "counterfactual"
    AUTO_EXPORT = "auto-export"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid enable target values."""
        return [member.value for member in cls]


##############
# SetTargets #
##############

class SetTargets(Enum):
    """Enum for what /set can set."""
    LLM_MODEL = "llm-model"
    PIPELINE = "pipeline"
    TEMPLATE_COMPUTATION_MODE = "template-computation-mode"
    NEIGHBORHOOD_EXTRACTION_MODE = "neighborhood-extraction-mode"
    FREE_TEXT_EXPLANATION_WRITING_MODE = "free-text-explanation-writing-mode"
    SOLVING_TIME_LIMIT = "solving-time-limit"
    LANGUAGE = "language"
    DISPLAY_MODE = "display-mode"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid set target values."""
        return [member.value for member in cls]


###########################
# SolvingTimeLimitTargets #
###########################

class SolvingTimeLimitTargets(Enum):
    """Enum for which MILP solving time limit /set solving-time-limit can set."""
    CONTRASTIVE = "contrastive"
    COUNTERFACTUAL = "counterfactual"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid solving time limit target values."""
        return [member.value for member in cls]


###################
# LLMModelTargets #
###################

class LLMModelTargets(Enum):
    """Enum for which LLM model /set llm-model can set (extracting neighborhoods, or writing explanations)."""
    NEIGHBORHOOD_EXTRACTION = "neighborhood-extraction"
    EXPLANATION_WRITING = "explanation-writing"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid LLM model target values."""
        return [member.value for member in cls]


######################
# AskTemplateTargets #
######################

class AskTemplateTargets(Enum):
    """
    Enum for the kinds of template-based questions /ask-template can ask.

    Only contrastive questions can always be asked: scenario and counterfactual ones need to be activated first.
    """
    CONTRASTIVE = "contrastive"
    SCENARIO = "scenario"
    COUNTERFACTUAL = "counterfactual"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid ask-template target values."""
        return [member.value for member in cls]


###############
# ListTargets #
###############

class ListTargets(Enum):
    """Enum for what /list can list."""
    TEMPLATE_QUESTIONS = "template-questions"
    INSTANCES = "instances"
    SOLUTIONS = "solutions"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid list target values."""
        return [member.value for member in cls]


###############
# ShowTargets #
###############

class ShowTargets(Enum):
    """Enum for what /show can show."""
    CURRENT_SOLUTION = "current-solution"
    CURRENT_INSTANCE = "current-instance"
    SOLUTION = "solution"
    INSTANCE = "instance"
    EXPLANATION = "explanation"
    HISTORY = "history"
    CONFIG = "config"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid show target values."""
        return [member.value for member in cls]


#################
# SwitchTargets #
#################

class SwitchTargets(Enum):
    """Enum for what /switch can switch to."""
    INSTANCE = "instance"
    SOLUTION = "solution"
    LAST_SUPPORT_INSTANCE = "last-support-instance"
    LAST_SUPPORT_SOLUTION = "last-support-solution"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid switch target values."""
        return [member.value for member in cls]


################
# ClearTargets #
################

class ClearTargets(Enum):
    """Enum for what /clear can clear."""
    SCREEN = "screen"
    CACHED_EXPLANATIONS = "cached-explanations"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid clear target values."""
        return [member.value for member in cls]


################
# DisplayModes #
################

class DisplayModes(Enum):
    """Enum for display mode options (lowercase, as entered by user)."""
    USER = "user"
    DEVELOPER = "developer"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid display mode values."""
        return [member.value for member in cls]

    def __contains__(self, value):
        """Check if a value is a valid display mode."""
        return value in self.list_values()


#############
# LLMModels #
#############

class LLMModels(Enum):
    """
    Enum for the LLM models suggested by /set llm-model's completion, as instructor model strings ("provider/model").

    These are suggestions only: any "provider/model" string instructor accepts can be set as well.
    """
    OLLAMA_LLAMA_3_2 = "ollama/llama3.2"
    OLLAMA_QWEN_2_5_7B = "ollama/qwen2.5:7b"
    ANTHROPIC_CLAUDE_SONNET_5 = "anthropic/claude-sonnet-5"
    MISTRAL_SMALL_LATEST = "mistral/mistral-small-latest"
    MISTRAL_MEDIUM_LATEST = "mistral/mistral-medium-latest"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all suggested LLM model values."""
        return [member.value for member in cls]
