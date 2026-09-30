# Standard library
from enum import Enum


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
