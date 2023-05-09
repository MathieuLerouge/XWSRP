# Global variables
# - Type
EMPLOYEE_TYPE_ID = 'Employee'
TASK_TYPE_ID = 'Task'
ACTIVITY_TYPE_ID = 'Activity'
EMPLOYEE = "<must refer to employee>"
TASK = "<must refer to task>"
ACTIVITY = "<must refer to activity>"
# - Performing employee
PERFORMING_EMPLOYEE = "<must refer to a performing employee>"
PERFORMING_MORE_THAN_ONE_TASK_EMPLOYEE = "<must refer to a employee performing more than one task>"
# - Performed task
PERFORMED = "<must refer to performed activity>"
NOT_PERFORMED = "<must refer to non performed activity>"
# - Performed task by
PERFORMED_BY_0 = "<must refer to activity performed by 0>"
PERFORMED_BY_1 = "<must refer to activity performed by 1>"
PERFORMED_BY_2 = "<must refer to activity performed by 2>"
PERFORMED_BY_S = [PERFORMED_BY_0, PERFORMED_BY_1, PERFORMED_BY_2]
NOT_PERFORMED_BY_0 = "<must refer to activity not performed by 0>"
NOT_PERFORMED_BY_1 = "<must refer to activity not performed by 1>"
NOT_PERFORMED_BY_2 = "<must refer to activity not performed by 2>"
NOT_PERFORMED_BY_S = [NOT_PERFORMED_BY_0, NOT_PERFORMED_BY_1, NOT_PERFORMED_BY_2]
# - First or last activity
EXCLUDING_FIRST_TASK = "<must refer to a different task than the first one>"
EXCLUDING_LAST_TASK = "<must refer to a different task than the last one>"
# - Start and return
EXCLUDING_START = "<must not refer to start>"
EXCLUDING_RETURN = "<must not refer to return>"
# - Order
BEFORE_1 = "<must refer to activity before 1>"
AFTER_1 = "<must refer to activity after 2>"
# Note: if an assumption is added, then FieldAssumptions.__init__() must be updated as well as
# QuestionTemplate.compute_field_valid_values() and QuestionTemplate.check_fields_values_validity()


# Class FieldAssumptions
class FieldAssumptions:

    def __init__(self, assumptions: str = ""):
        self._type_id = None
        self._must_refer_to_employee = False
        self._must_refer_to_a_performing_employee = False
        self._must_refer_to_an_employee_performing_more_than_one_task = False
        self._must_refer_to_task = False
        self._must_refer_to_activity = False
        self._must_refer_to_performed_activity = False
        self._must_refer_to_not_performed_activity = False
        self._must_refer_to_activity_performed_by_provided_employee = False
        self._field_index_of_employee_performing_this_field_activity = None
        self._must_refer_to_activity_not_performed_by_provided_employee = False
        self._field_index_of_employee_not_performing_this_field_activity = None
        self._must_not_refer_to_first_task = False
        self._must_not_refer_to_last_task = False
        self._must_not_refer_to_start = False
        self._must_not_refer_to_return = False
        self._must_refer_to_task_before_mentioned_task = False
        self._must_refer_to_task_after_mentioned_task = False
        self._field_index_of_mentioned_task = None
        if EMPLOYEE in assumptions:
            self._set_type_id(EMPLOYEE_TYPE_ID)
            self._must_refer_to_employee = True
        if TASK in assumptions:
            self._set_type_id(TASK_TYPE_ID)
            self._must_refer_to_task = True
        if ACTIVITY in assumptions:
            self._set_type_id(ACTIVITY_TYPE_ID)
            self._must_refer_to_activity = True
        if PERFORMING_EMPLOYEE in assumptions:
            if self._type_id != EMPLOYEE_TYPE_ID:
                raise ValueError(f"{PERFORMING_EMPLOYEE} can only be used with {EMPLOYEE}")
            self._must_refer_to_a_performing_employee = True
        if PERFORMING_MORE_THAN_ONE_TASK_EMPLOYEE in assumptions:
            if self._type_id != EMPLOYEE_TYPE_ID:
                raise ValueError(f"{PERFORMING_MORE_THAN_ONE_TASK_EMPLOYEE} can only be used with {EMPLOYEE}")
            self._must_refer_to_an_employee_performing_more_than_one_task = True
        if PERFORMED in assumptions:
            if self._type_id not in [TASK_TYPE_ID, ACTIVITY_TYPE_ID]:
                raise ValueError(f"The field cannot satisfy both {PERFORMED} and not {TASK_TYPE_ID, ACTIVITY_TYPE_ID}")
            self._must_refer_to_performed_activity = True
        if NOT_PERFORMED in assumptions:
            if self._type_id not in [TASK_TYPE_ID, ACTIVITY_TYPE_ID]:
                raise ValueError(f"The field cannot satisfy both {NOT_PERFORMED} and "
                                 f"not {TASK_TYPE_ID, ACTIVITY_TYPE_ID}")
            if self._must_refer_to_performed_activity:
                raise ValueError(f"The field cannot satisfy both {PERFORMED} and {NOT_PERFORMED}")
            self._must_refer_to_not_performed_activity = True
        for index, assumption in enumerate(PERFORMED_BY_S):
            if assumption in assumptions:
                if self._type_id not in [TASK_TYPE_ID, ACTIVITY_TYPE_ID]:
                    raise ValueError(f"The field cannot satisfy both {assumption} and "
                                     f"not {TASK_TYPE_ID, ACTIVITY_TYPE_ID}")
                if self._must_refer_to_not_performed_activity:
                    raise ValueError(f"The field cannot satisfy both {assumption} and {NOT_PERFORMED}")
                self._must_refer_to_performed_activity = True
                self._must_refer_to_activity_performed_by_provided_employee = True
                self._field_index_of_employee_performing_this_field_activity = index
        for index, assumption in enumerate(NOT_PERFORMED_BY_S):
            if assumption in assumptions:
                if self._type_id not in [TASK_TYPE_ID, ACTIVITY_TYPE_ID]:
                    raise ValueError(f"The field cannot satisfy both {assumption} and "
                                     f"not {TASK_TYPE_ID, ACTIVITY_TYPE_ID}")
                if PERFORMED_BY_S[index] in assumptions:
                    raise ValueError(f"The field cannot satisfy both {assumption} and {PERFORMED_BY_S[index]}")
                self._must_refer_to_activity_not_performed_by_provided_employee = True
                self._field_index_of_employee_not_performing_this_field_activity = index
        if EXCLUDING_FIRST_TASK in assumptions:
            if self._type_id not in [TASK_TYPE_ID, ACTIVITY_TYPE_ID]:
                raise ValueError(f"The field cannot satisfy both {EXCLUDING_FIRST_TASK} and "
                                 f"not {TASK_TYPE_ID, ACTIVITY_TYPE_ID}")
            self._must_not_refer_to_first_task = True
        if EXCLUDING_LAST_TASK in assumptions:
            if self._type_id not in [TASK_TYPE_ID, ACTIVITY_TYPE_ID]:
                raise ValueError(f"The field cannot satisfy both {EXCLUDING_LAST_TASK} and "
                                 f"not {TASK_TYPE_ID, ACTIVITY_TYPE_ID}")
            self._must_not_refer_to_last_task = True
        if EXCLUDING_START in assumptions:
            if self._type_id != ACTIVITY_TYPE_ID:
                raise ValueError(f"The field cannot satisfy both {EXCLUDING_START} and not {ACTIVITY_TYPE_ID}")
            self._must_not_refer_to_start = True
        if EXCLUDING_RETURN in assumptions:
            if self._type_id != ACTIVITY_TYPE_ID:
                raise ValueError(f"The field cannot satisfy both {EXCLUDING_RETURN} and not {ACTIVITY_TYPE_ID}")
            self._must_not_refer_to_return = True
        if BEFORE_1 in assumptions:
            if self._type_id != TASK_TYPE_ID:
                raise ValueError(f"The field cannot satisfy both {BEFORE_1} and not {TASK_TYPE_ID}")
            self._must_refer_to_task_before_mentioned_task = True
            self._field_index_of_mentioned_task = 1
        if AFTER_1 in assumptions:
            if self._type_id != TASK_TYPE_ID:
                raise ValueError(f"The field cannot satisfy both {AFTER_1} and not {TASK_TYPE_ID}")
            if BEFORE_1 in assumptions:
                raise ValueError(f"The field cannot satisfy both {BEFORE_1} and {AFTER_1}")
            self._must_refer_to_task_after_mentioned_task = True
            self._field_index_of_mentioned_task = 1

    def _set_type_id(self, type_id: str):
        if self._type_id is not None and self._type_id != type_id:
            raise ValueError(f"The field cannot be both {self._type_id} and {type_id}")
        self._type_id = type_id

    @property
    def type_id(self):
        return self._type_id

    @property
    def this_field_must_refer_to_an_employee(self):
        return self._must_refer_to_employee

    @property
    def this_field_must_refer_to_a_performing_employee(self):
        return self._must_refer_to_a_performing_employee

    @property
    def this_field_must_refer_to_an_employee_performing_more_than_one_task(self):
        return self._must_refer_to_an_employee_performing_more_than_one_task

    @property
    def this_field_must_refer_to_a_task(self):
        return self._must_refer_to_task

    @property
    def this_field_must_refer_to_an_activity(self):
        return self._must_refer_to_activity

    @property
    def this_field_must_refer_to_non_performed_activity(self):
        return self._must_refer_to_not_performed_activity

    @property
    def this_field_must_refer_to_a_performed_activity(self):
        return self._must_refer_to_performed_activity

    @property
    def this_field_must_refer_to_an_activity_performed_by_a_selected_employee(self):
        return self._must_refer_to_activity_performed_by_provided_employee

    @property
    def field_index_mentioning_employee_performing_activity_of_this_field(self):
        return self._field_index_of_employee_performing_this_field_activity

    @property
    def this_field_must_refer_to_activity_not_performed_by_selected_employee(self):
        return self._must_refer_to_activity_not_performed_by_provided_employee

    @property
    def field_index_mentioning_the_employee_not_performing_the_activity_of_this_field(self):
        return self._field_index_of_employee_not_performing_this_field_activity

    @property
    def this_field_must_not_refer_to_first_task(self):
        return self._must_not_refer_to_first_task

    @property
    def this_field_must_not_refer_to_last_task(self):
        return self._must_not_refer_to_last_task

    @property
    def this_field_must_not_refer_to_start(self):
        return self._must_not_refer_to_start

    @property
    def this_field_must_not_refer_to_return(self):
        return self._must_not_refer_to_return

    @property
    def this_field_must_refer_to_any_task_before_task_selected_in_other_field(self):
        return self._must_refer_to_task_before_mentioned_task

    @property
    def this_field_must_refer_to_any_task_after_task_selected_in_other_field(self):
        return self._must_refer_to_task_after_mentioned_task

    @property
    def field_index_mentioning_other_task(self):
        return self._field_index_of_mentioned_task


def check_text_and_assumptions_consistency(text: str, fields_assumptions: list[FieldAssumptions], raise_error=False):
    try:
        if text.count('{') != text.count('}'):
            raise ValueError(f"There is not the number of {'{'} symbols as {'}'} in {text}")
        if text.count('{') != len(fields_assumptions):
            raise ValueError(f"There are not as many fields assumptions ({len(fields_assumptions)}) "
                             f"as fields ({text.count('{')}) in {text}")
        return True
    except ValueError as error:
        if raise_error:
            raise error
        else:
            return False


def check_texts_and_assumptions_consistency(texts: dict[str, str], fields_assumptions: list[FieldAssumptions],
                                            raise_error=False):
    for text in texts.values():
        if not check_text_and_assumptions_consistency(text, fields_assumptions, raise_error):
            return False
    return True
