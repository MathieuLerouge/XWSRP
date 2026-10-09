# Standard library
import os

# Provider prefixes (of a "provider/model-name" string) that need an API key,
# mapped to the environment variable that must carry it
# - checked eagerly when an LLM-backed tool is built, so a missing key fails clearly right there,
# rather than surfacing a confusing error from deep inside instructor/the provider SDK on the first call.
PROVIDER_API_KEY_ENV_VARS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}

# Providers serving small local models, which follow a system prompt less reliably once the prompt carries JSON.
PROVIDERS_WITHOUT_JSON_CONTEXT_BY_DEFAULT = {"ollama"}


def get_provider(model: str) -> str:
    """
    Returns the provider prefix of an instructor model string.

    Args:
        model: The instructor model string ("provider/model-name").

    Returns:
        The part before the first "/".
    """
    return model.split("/", 1)[0]


def check_required_api_key_is_set(model: str):
    """
    Checks the environment carries the API key the given model's provider needs, if it needs one.

    Args:
        model: The instructor model string ("provider/model-name").

    Raises:
        RuntimeError: If model's provider requires an API key and the corresponding environment variable isn't set.
    """
    env_var_name = PROVIDER_API_KEY_ENV_VARS.get(get_provider(model))
    if env_var_name is not None and env_var_name not in os.environ:
        raise RuntimeError(f"Using model {model!r} requires the {env_var_name} environment variable to be set.")


def is_json_context_enabled_by_default(model: str) -> bool:
    """
    Returns whether a prompt sent to the given model describes the instance and the solution as JSON by default.

    Args:
        model: The instructor model string ("provider/model-name").

    Returns:
        False for the local providers of PROVIDERS_WITHOUT_JSON_CONTEXT_BY_DEFAULT, True otherwise.
    """
    return get_provider(model) not in PROVIDERS_WITHOUT_JSON_CONTEXT_BY_DEFAULT
