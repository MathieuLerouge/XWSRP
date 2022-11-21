# Local libraries
from src.utils.constants import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY


# Class ExplanationTemplate
class ExplanationTemplate:

    def __init__(self, id: str, all_typical_expressions: dict[str, dict[str, str]]):
        self._id = id
        self._language_key = LANGUAGE_ENGLISH_KEY
        self._all_typical_expressions = all_typical_expressions

    @property
    def id(self):
        return self._id

    def set_language(self, language_key: str):
        self._language_key = language_key

    @property
    def language(self):
        return self._language_key

    @language.setter
    def language(self, language_key: str):
        self.set_language(language_key)

    @property
    def typical_expressions(self):
        return self._all_typical_expressions[self._language_key]
