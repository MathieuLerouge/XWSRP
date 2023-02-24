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
    Check if the given language key is English.

    :param language_key: language key (str)
    :return: True if the language key is English, False otherwise (bool)
    """
    return language_key == LANGUAGE_ENGLISH_KEY


def check_if_language_is_french(language_key: str):
    """
    Check if the given language key is French.

    :param language_key: language key (str)
    :return: True if the language key is French, False otherwise (bool)
    """
    return language_key == LANGUAGE_FRENCH_KEY
