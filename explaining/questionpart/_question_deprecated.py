# Standard Library
from typing import Union

# Local libraries
from explaining._constants_deprecated import *
from model.activity import Activity
from model.employee import Employee
from model.task import Task

# Global variable
TEMPLATE_FIELD_DEFAULT_VALUE = "_"


# Class TemplateField
class TemplateField:

    def __init__(self, type_key: str, start_index: int, end_index: int,
                 value: str = TEMPLATE_FIELD_DEFAULT_VALUE, obj: Union[Employee, Activity] = None):
        self._type_key = type_key
        self._type = None
        if type_key == EMPLOYEE_FIELD_KEY:
            self._type = Employee
        elif type_key == TASK_FIELD_KEY:
            self._type = Task
        elif type_key == ACTIVITY_FIELD_KEY:
            self._type = Activity
        else:
            raise ValueError(f"The type key {type_key} cannot be handled")
        self._start_index = start_index
        self._end_index = end_index
        self._value = value
        if obj is not None:
            if not isinstance(obj, self._type):
                raise TypeError(f"The type of the given value parameter {obj} and "
                                f"the field type parameter {self._type} do not match")
        self._obj = obj

    def __repr__(self):
        return self._value

    @property
    def type_key(self):
        return self._type_key

    @property
    def type(self):
        return self._type

    @property
    def start_index(self):
        return self._start_index

    @property
    def end_index(self):
        return self._end_index

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value: str):
        self._value = value

    @property
    def obj(self):
        return self._obj

    @obj.setter
    def obj(self, obj: Union[Employee, Activity]):
        if not isinstance(obj, self._type):
            raise TypeError(f"The type of the obj parameter {obj} and "
                            f"the type {self._type} of the template field do not match")
        self._obj = obj
        if isinstance(obj, Employee):
            self._value = obj.name
        elif isinstance(obj, Activity):
            self._value = obj.name

    def reset_value(self):
        self._value = TEMPLATE_FIELD_DEFAULT_VALUE


# Class TemplateQuestion
class TemplateQuestionDeprecated:

    def __init__(self, key: str):
        self._key = key
        self._template_text = QUESTIONS_TEMPLATES_DEPRECATED[key]
        self._nb_fields = self._template_text.count('{')
        self._fields = []
        start_index = self._template_text.index('{')
        end_index = self._template_text.index('}')
        type_key = self._template_text[start_index:end_index + 1]
        self._fields.append(TemplateField(type_key=type_key, start_index=start_index, end_index=end_index))
        field_number = 1
        while field_number < self.nb_fields:
            start_index = self._template_text.index('{', end_index)
            end_index = self._template_text.index('}', start_index)
            type_key = self._template_text[start_index:end_index + 1]
            self._fields.append(TemplateField(type_key=type_key, start_index=start_index, end_index=end_index))
            field_number += 1
        self._text = ""
        self._update_question_text_with_fields_names()
        self._template_text_with_default_values = self._text

    def _update_question_text_with_fields_names(self):
        field_number = 0
        field = self._fields[field_number]
        question_text = self._template_text[:field.start_index] + field.value
        field_number = 1
        while field_number < self._nb_fields:
            previous_field, field = field, self._fields[field_number]
            question_text += self._template_text[previous_field.end_index + 1:field.start_index]
            question_text += self._fields[field_number].value
            field_number += 1
        question_text += self._template_text[field.end_index + 1:]
        self._text = question_text

    def __repr__(self):
        return self._text

    @property
    def key(self):
        return self._key

    @property
    def template_text(self):
        return self._template_text

    @property
    def template_text_with_default_values(self):
        return self._template_text_with_default_values

    @property
    def text(self):
        self._update_question_text_with_fields_names()
        return self._text

    @property
    def nb_fields(self):
        return self._nb_fields

    @property
    def fields(self):
        return self._fields

    def has_field_of_type(self, field_index: int, type_key: str):
        if (field_index < self.nb_fields) and (self.fields[field_index].type_key == type_key):
            return True
        else:
            return False
