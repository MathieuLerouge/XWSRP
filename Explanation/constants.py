REALIZING_INSTEAD_OF_KEY = "realizing_instead_of"
REALIZING_INSTEAD_OF_TEXT = "Why employee {0} does not realize task {1} instead of the task {2}?"

REALIZING_JUST_AFTER_KEY = "RealizingJustAfter"
REALIZING_JUST_AFTER_TEXT = "Why employee {0} does not realize task {1} just after the activity {2}?"

REALIZING_IN_ADDITION_KEY = "RealizingInAddition"
REALIZING_IN_ADDITION_TEXT = "Why employee {0} does not realize task {1} in addition to his/her tasks?"

REALIZING_AT_ANOTHER_TIME_KEY = "RealizingAtAnotherTime"
REALIZING_AT_ANOTHER_TIME_TEXT = "Why employee {0} does not realize task {1} at another time in his/her planning?"

NOT_REALIZED_KEY = "NotRealized"
NOT_REALIZED_TEXT = "Why task {1} is not realized in addition to the other tasks?"

REALIZING_AT_ALL_COSTS_KEY = "RealizingAtAllCosts"
REALIZING_AT_ALL_COSTS_TEXT = "What if employee {0} realizes task {1}?"

QUESTIONS_TEMPLATES = {
    REALIZING_INSTEAD_OF_KEY: REALIZING_INSTEAD_OF_TEXT,
    REALIZING_JUST_AFTER_KEY: REALIZING_JUST_AFTER_TEXT,
    REALIZING_IN_ADDITION_KEY: REALIZING_IN_ADDITION_TEXT,
    REALIZING_AT_ANOTHER_TIME_KEY: REALIZING_AT_ANOTHER_TIME_TEXT,
    NOT_REALIZED_KEY: NOT_REALIZED_TEXT,
    REALIZING_AT_ALL_COSTS_KEY: REALIZING_AT_ALL_COSTS_TEXT
}
QUESTIONS_TEMPLATES_KEYS = list(QUESTIONS_TEMPLATES.values())

# self._add_template("Realizing", "Why employee {0} does realize task {1}?")
# self._add_template("NotRealized", "Why task {1} is not realized?")
# self._add_template("Tightening", "Can you tighten the plannings please?")
