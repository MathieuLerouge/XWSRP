# Global variables
from explanation.constants import *


# Class TemplateQuestion
class TemplateQuestion:

    def __init__(self, key: str):
        self._key = key
        self._text = QUESTIONS_TEMPLATES[key]

    def __repr__(self):
        return self._text

    @property
    def key(self):
        return self._key

    @property
    def text(self):
        return self._text

    @property
    def nb_fields(self):
        return self._text.count('{')

    def fill(self, fields: list[str]):
        text = self._text
        for i, field in enumerate(fields):
            text = text.replace(f'{i}', field)
        return text
