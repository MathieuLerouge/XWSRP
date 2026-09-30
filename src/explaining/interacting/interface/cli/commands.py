# Standard library
from enum import Enum


############
# Commands #
############

class Commands(Enum):
    """Enum of all CLI commands with their metadata."""
    
    # Core Commands
    LLM_MODEL = ("/llm-model", "Set LLM model for free-text extraction")
    TEMPLATE_MODE = ("/template-mode", "Switch template pipeline (tailored/neighborhood)")
    ASK = ("/ask", "Ask a free-text contrastive question")
    CONTRASTIVE = ("/contrastive", "Ask a template-based contrastive question")
    SAVE_SOLUTION = ("/save-solution", "Save current support solution")
    LIST_TEMPLATES = ("/list-templates", "Show available question templates")
    LIST_INSTANCES = ("/list-instances", "List stored instances")
    LIST_SOLUTIONS = ("/list-solutions", "List stored solutions")
    SWITCH_INSTANCE = ("/switch-instance", "Change current instance")
    SWITCH_SOLUTION = ("/switch-solution", "Change current solution")
    LANGUAGE = ("/language", "Switch language")
    EXPORT = ("/export", "Export last explanation")
    
    # Configuration Commands
    TIME_LIMIT_CONTRASTIVE = ("/time-limit-contrastive", "Set MILP time limit for contrastive")
    TIME_LIMIT_COUNTERFACTUAL = ("/time-limit-counterfactual", "Set MILP time limit for counterfactual")
    ENABLE = ("/enable", "Enable a feature")
    DISABLE = ("/disable", "Disable a feature")
    
    # Display Commands
    SHOW = ("/show", "Show details")
    SHOW_INSTANCE = ("/show-instance", "Show instance details")
    SHOW_SOLUTION = ("/show-solution", "Show solution details")
    HELP = ("/help", "Show this help message")
    
    # Session Commands
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
            f"  {cls.LLM_MODEL.name} <model>          {cls.LLM_MODEL.description}",
            f"  {cls.TEMPLATE_MODE.name} <mode>       {cls.TEMPLATE_MODE.description}",
            f"  {cls.ASK.name} <question>             {cls.ASK.description}",
            f"  {cls.CONTRASTIVE.name} <id> <vals>    {cls.CONTRASTIVE.description}",
            f"  {cls.SAVE_SOLUTION.name}              {cls.SAVE_SOLUTION.description}",
            f"  {cls.LIST_TEMPLATES.name}             {cls.LIST_TEMPLATES.description}",
            f"  {cls.LIST_INSTANCES.name}             {cls.LIST_INSTANCES.description}",
            f"  {cls.LIST_SOLUTIONS.name}             {cls.LIST_SOLUTIONS.description}",
            f"  {cls.SWITCH_INSTANCE.name} <name>     {cls.SWITCH_INSTANCE.description}",
            f"  {cls.SWITCH_SOLUTION.name} <name>     {cls.SWITCH_SOLUTION.description}",
            f"  {cls.LANGUAGE.name} <en|fr>           {cls.LANGUAGE.description}",
            f"  {cls.EXPORT.name}                     {cls.EXPORT.description}",
            "",
            "Configuration Commands:",
            f"  {cls.TIME_LIMIT_CONTRASTIVE.name} <s>       {cls.TIME_LIMIT_CONTRASTIVE.description}",
            f"  {cls.TIME_LIMIT_COUNTERFACTUAL.name} <s>    {cls.TIME_LIMIT_COUNTERFACTUAL.description}",
            f"  {cls.ENABLE.name} <feature>                 {cls.ENABLE.description}",
            f"  {cls.DISABLE.name} <feature>                {cls.DISABLE.description}",
            "",
            "Display Commands:",
            f"  {cls.SHOW.name} <resource>           {cls.SHOW.description} ({', '.join(Content.list_values())})",
            f"  {cls.SHOW_INSTANCE.name} <name>      {cls.SHOW_INSTANCE.description}",
            f"  {cls.SHOW_SOLUTION.name} <name>      {cls.SHOW_SOLUTION.description}",
            f"  {cls.HELP.name}                      {cls.HELP.description}",
            "",
            "Session Commands:",
            f"  {cls.QUIT.name}                      {cls.QUIT.description}",
        ]
        return "\n".join(lines)


###########################
# TemplateComputationMode #
###########################

class TemplateComputationMode(Enum):
    """Enum for template computation mode options."""
    TAILORED = "tailored"
    NEIGHBORHOOD = "neighborhood"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid template computation mode values."""
        return [member.value for member in cls]


############
# Language #
############

class Language(Enum):
    """Enum for language options (lowercase, as entered by user)."""
    EN = "en"
    FR = "fr"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid language values."""
        return [member.value for member in cls]


###########
# Feature #
###########

class Feature(Enum):
    """Enum for feature names that can be enabled/disabled."""
    HISTORY = "history"
    SCENARIO = "scenario"
    COUNTERFACTUAL = "counterfactual"
    AUTO_EXPORT = "auto-export"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid feature name values."""
        return [member.value for member in cls]


###########
# Content #
###########

class Content(Enum):
    """Enum for contents that can be shown."""
    SOLUTION = "solution"
    INSTANCE = "instance"
    EXPLANATION = "explanation"
    HISTORY = "history"
    CONFIG = "config"

    @classmethod
    def list_values(cls) -> list[str]:
        """Return list of all valid content values."""
        return [member.value for member in cls]
