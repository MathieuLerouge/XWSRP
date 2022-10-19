# Global variables - Template questions fields keys
EMPLOYEE_FIELD_KEY = '{Employee}'
TASK_FIELD_KEY = '{Task}'
ACTIVITY_FIELD_KEY = '{Activity}'

# Global variables - Contrastive questions - Inserting
#
WHY_NOT_PERFORMING_JUST_AFTER_KEY = 'why_not_performing_just_after'
WHY_NOT_PERFORMING_JUST_AFTER_TEXT = "Why is the employee {Employee} not performing the task {Task} just after the activity {Activity}?"
#
WHY_NOT_PERFORMING_BETWEEN_KEY = 'why_not_performing_between'
WHY_NOT_PERFORMING_BETWEEN_TEXT = \
    "Why is the employee {Employee} not performing the task {Task} between two consecutive activities?"
#
WHY_NOT_PERFORMING_IN_ADDITION_KEY = 'why_not_performing_in_addition'
WHY_NOT_PERFORMING_IN_ADDITION_TEXT = "Why is the employee {Employee} not performing the task {Task} in addition to their tasks?"

# Global variables - Contrastive questions - Swapping
#
WHY_REALIZING_INSTEAD_OF_KEY = 'why_performing_instead_of'
WHY_REALIZING_INSTEAD_OF_TEXT = "Why is the employee {Employee} performing the task {Task} instead of the task {Task}?"
#
WHY_NOT_REALIZING_INSTEAD_OF_KEY = 'why_not_performing_instead_of'
WHY_NOT_REALIZING_INSTEAD_OF_TEXT = "Why is the employee {Employee} not performing the task {Task} instead of the task {Task}?"

# Global variables - Contrastive questions - Reordering
#
WHY_NOT_REALIZING_AT_ANOTHER_TIME_KEY = 'why_not_performing_at_another_time'
WHY_NOT_REALIZING_AT_ANOTHER_TIME_TEXT = \
    "Why is the employee {Employee} not performing the task {Task} at another time in their planning (KSOE)?"
#
WHY_NOT_REALIZED_KEY = 'why_not_performed'
WHY_NOT_REALIZED_TEXT = "Why is the task {Task} not performed in addition to the other tasks (KSOE)?"


# Global variables - Model-counterfactual questions
#
WHAT_IF_INSERTING_KEY = 'what_if_inserting'
WHAT_IF_INSERTING_TEXT = "What if the employee {Employee} tries to perform the task {Task} in addition to their tasks?"
#
WHAT_IF_REALIZING_KEY = 'what_if_performing'
WHAT_IF_REALIZING_TEXT = "What if the employee {Employee} is constrained to perform the task {Task}?"
#
WHAT_IF_REORDERING_KEY = 'what_if_reordering'
WHAT_IF_REORDERING_TEXT = "What if the tasks of the employee {Employee} are in another order?"


# Global variables - Instance-counterfactual questions
#
HOW_REALIZING_IN_ADDITION_KEY = 'how_performing_in_addition'
HOW_REALIZING_IN_ADDITION_TEXT = \
    "What can be done so that the employee {Employee} performs the task {Task} in addition to their tasks?"


# Global variables - all pairs (key, text) of questions
QUESTIONS_TEMPLATES_DEPRECATED = {
    WHY_NOT_PERFORMING_JUST_AFTER_KEY: WHY_NOT_PERFORMING_JUST_AFTER_TEXT,
    WHY_NOT_PERFORMING_BETWEEN_KEY: WHY_NOT_PERFORMING_BETWEEN_TEXT,
    WHY_NOT_PERFORMING_IN_ADDITION_KEY: WHY_NOT_PERFORMING_IN_ADDITION_TEXT,
    WHY_REALIZING_INSTEAD_OF_KEY: WHY_REALIZING_INSTEAD_OF_TEXT,
    WHY_NOT_REALIZING_INSTEAD_OF_KEY: WHY_NOT_REALIZING_INSTEAD_OF_TEXT,
    WHY_NOT_REALIZING_AT_ANOTHER_TIME_KEY: WHY_NOT_REALIZING_AT_ANOTHER_TIME_TEXT,
    WHY_NOT_REALIZED_KEY: WHY_NOT_REALIZED_TEXT,
    WHAT_IF_INSERTING_KEY: WHAT_IF_INSERTING_TEXT,
    WHAT_IF_REALIZING_KEY: WHAT_IF_REALIZING_TEXT,
    WHAT_IF_REORDERING_KEY: WHAT_IF_REORDERING_TEXT,
    HOW_REALIZING_IN_ADDITION_KEY: HOW_REALIZING_IN_ADDITION_TEXT
}
QUESTIONS_TEMPLATES_KEYS = list(QUESTIONS_TEMPLATES_DEPRECATED.values())
