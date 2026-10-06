# Standard library
from enum import Enum


############
# Commands #
############

class Commands(Enum):
    """Enum of all CLI commands with their metadata."""
    
    # Core Commands
    LLM_MODEL = ("/llm-model", "Set LLM model for free-text extraction")
    TEMPLATE_COMPUTATION_MODE = ("/template-computation-mode", "Switch template pipeline (tailored/neighborhood)")
    NEIGHBORHOOD_EXTRACTION_MODE = ("/neighborhood-extraction-mode", "Switch neighborhood extraction (llm/tailored)")
    ASK = ("/ask", "Ask a free-text contrastive question")
    CONTRASTIVE = ("/contrastive", "Ask a template-based contrastive question")
    SAVE_SOLUTION = ("/save-solution", "Save current support solution")
    LIST_TEMPLATES = ("/list-templates", "Show available question templates")
    LIST_INSTANCES = ("/list-instances", "List stored instances")
    LIST_SOLUTIONS = ("/list-solutions", "List stored solutions")
    SWITCH = ("/switch", "Change current instance or solution")
    LANGUAGE = ("/language", "Switch language")
    EXPORT = ("/export", "Export last explanation")
    
    # Configuration Commands
    TIME_LIMIT_CONTRASTIVE = ("/time-limit-contrastive", "Set MILP time limit for contrastive")
    TIME_LIMIT_COUNTERFACTUAL = ("/time-limit-counterfactual", "Set MILP time limit for counterfactual")
    ENABLE = ("/enable", "Enable a feature")
    DISABLE = ("/disable", "Disable a feature")
    
    # Display Commands
    SHOW = ("/show", "Show details")
    DISPLAY_MODE = ("/display-mode", "Set the CLI display mode (user/developer)")
    HELP = ("/help", "Show this help message")
    
    # Session Commands
    CLEAR = ("/clear", "Clear the terminal screen or the cached contrastive explanations")
    QUIT = ("/quit", "Exit the CLI")
    
    @property
    def name(self) -> str:
        """Return the command name (e.g., '/llm-model')."""
        return self.value[0]
    
    @property
    def description(self) -> str:
        """Return the command description."""
        return self.value[1]

    @classmethod
    def list_string(cls) -> str:
        """Generate the list string for all commands."""
        lines = [
            "Explainer CLI - Available Commands",
            "",
            "Core Commands:",
            f"  {cls.LLM_MODEL.name} <model>                   {cls.LLM_MODEL.description}",
            f"  {cls.TEMPLATE_COMPUTATION_MODE.name} <mode>    {cls.TEMPLATE_COMPUTATION_MODE.description}",
            f"  {cls.NEIGHBORHOOD_EXTRACTION_MODE.name} <mode> {cls.NEIGHBORHOOD_EXTRACTION_MODE.description}",
            f"  {cls.ASK.name} <question>                      {cls.ASK.description}",
            f"  {cls.CONTRASTIVE.name} <id> <vals>             {cls.CONTRASTIVE.description}",
            f"  {cls.SAVE_SOLUTION.name}                       {cls.SAVE_SOLUTION.description}",
            f"  {cls.LIST_TEMPLATES.name}                      {cls.LIST_TEMPLATES.description}",
            f"  {cls.LIST_INSTANCES.name}                      {cls.LIST_INSTANCES.description}",
            f"  {cls.LIST_SOLUTIONS.name}                      {cls.LIST_SOLUTIONS.description}",
            f"  {cls.SWITCH.name} <target> [name]              {cls.SWITCH.description} "
            f"({', '.join(SwitchTargets.list_values())})",
            f"  {cls.LANGUAGE.name} <en|fr>                    {cls.LANGUAGE.description}",
            f"  {cls.EXPORT.name}                              {cls.EXPORT.description}",
            "",
            "Configuration Commands:",
            f"  {cls.TIME_LIMIT_CONTRASTIVE.name} <s>       {cls.TIME_LIMIT_CONTRASTIVE.description}",
            f"  {cls.TIME_LIMIT_COUNTERFACTUAL.name} <s>    {cls.TIME_LIMIT_COUNTERFACTUAL.description}",
            f"  {cls.ENABLE.name} <feature>                 {cls.ENABLE.description}",
            f"  {cls.DISABLE.name} <feature>                {cls.DISABLE.description}",
            "",
            "Display Commands:",
            f"  {cls.SHOW.name} <resource> [name]           {cls.SHOW.description} ({', '.join(ShowTargets.list_values())})",
            f"  {cls.DISPLAY_MODE.name} <user|developer>    {cls.DISPLAY_MODE.description}",
            f"  {cls.HELP.name}                             {cls.HELP.description}",
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


############
# Features #
############

class Features(Enum):
    """Enum for feature names that can be enabled/disabled."""
    HISTORY = "history"
    SCENARIO = "scenario"
    COUNTERFACTUAL = "counterfactual"
    AUTO_EXPORT = "auto-export"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid feature name values."""
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
    Enum for the LLM models suggested by /llm-model's completion, as instructor model strings ("provider/model").

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
