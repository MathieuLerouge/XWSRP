####################
# Global variables #
####################

LANGUAGE_ENGLISH_KEY = 'EN'
LANGUAGE_FRENCH_KEY = 'FR'


####################
# Global functions #
####################

def check_if_language_is_english(language_key: str):
    """
    Returns whether the given language key is English.

    Args:
        language_key: Language key to check.

    Returns:
        True if language_key is English, False otherwise.
    """
    return language_key == LANGUAGE_ENGLISH_KEY


def check_if_language_is_french(language_key: str):
    """
    Returns whether the given language key is French.

    Args:
        language_key: Language key to check.

    Returns:
        True if language_key is French, False otherwise.
    """
    return language_key == LANGUAGE_FRENCH_KEY
