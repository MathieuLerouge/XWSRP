# Class ExplanationTemplate
class ExplanationTemplate:

    def __init__(self, id: str, typical_expressions: dict[str, str]):
        self._id = id
        self._typical_expressions = typical_expressions

    @property
    def id(self):
        return self._id

    @property
    def typical_expressions(self):
        return self._typical_expressions
