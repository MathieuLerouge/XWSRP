# Standard libraries
from typing import Union

# Local libraries
from src.explaining.questioning.question_template_field import *
from src.modeling.comeback import COMING_BACK_HOME_STRING
from src.modeling.departure import LEAVING_HOME_STRING
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY

# Global variable
TEMPLATE_FIELD_DEFAULT_VALUE = "_"
START_VALUE = LEAVING_HOME_STRING
RETURN_VALUE = COMING_BACK_HOME_STRING


# Class QuestionTemplate
class QuestionTemplate:

    def __init__(self, id: str, all_texts: dict[str, str], fields_assumptions: list[FieldAssumptions]):
        self._language = LANGUAGE_ENGLISH_KEY
        self._supported_languages = [LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY]
        self._id = id
        self._nb_fields = len(fields_assumptions)
        self._fields_assumptions = fields_assumptions
        self._all_texts = all_texts
        check_texts_and_assumptions_consistency(all_texts, fields_assumptions, raise_error=True)
        self._text = self._all_texts[self._language]
        self._update_fields_information()
        self._update_text_with_default_fields_values()

    def _update_fields_information(self):
        self._fields_information = []
        field_number = 0
        field_start_index_in_text, field_end_index_in_text = 0, 0
        while field_number < self._nb_fields:
            field_start_index_in_text = self._text.index('{', field_end_index_in_text)
            field_end_index_in_text = self._text.index('}', field_start_index_in_text)
            self._fields_information.append(
                dict(start_index_in_text=field_start_index_in_text, end_index_in_text=field_end_index_in_text,
                     key=self._text[field_start_index_in_text:field_end_index_in_text+1],
                     assumptions=self._fields_assumptions[field_number])
            )
            field_number += 1

    def _update_text_with_default_fields_values(self):
        self._text_with_default_fields_values = self.complete_text_with_fields_values(
            fields_values=[TEMPLATE_FIELD_DEFAULT_VALUE for _ in range(self._nb_fields)]
        )

    def __repr__(self):
        return self._text_with_default_fields_values

    @property
    def id(self):
        return self._id

    @property
    def nb_fields(self):
        return self._nb_fields

    @property
    def fields_keys(self):
        return [information['key'] for information in self._fields_information]

    @property
    def all_texts(self):
        current_language = self._language
        texts = dict()
        for language, text in self._all_texts.items():
            self.set_language(language)
            texts[language] = self._text
        self.set_language(current_language)
        return texts

    @property
    def text(self):
        return self._text_with_default_fields_values

    @property
    def supported_languages(self):
        return self._supported_languages

    def set_language(self, language_key: str):
        if language_key not in self.supported_languages:
            raise ValueError(f"The language {language_key} is not supported,"
                             f"supported languages are {self.supported_languages}")
        self._language = language_key
        self._text = self._all_texts[self._language]
        self._update_fields_information()
        self._update_text_with_default_fields_values()

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language_key: str):
        self.set_language(language_key)

    @property
    def language_is_english(self):
        return self._language == LANGUAGE_ENGLISH_KEY

    @property
    def language_is_french(self):
        return self._language == LANGUAGE_FRENCH_KEY

    def complete_text_with_fields_values(self, fields_values: Union[dict[int, str], list[str]]):
        if isinstance(fields_values, list):
            if len(fields_values) != self._nb_fields:
                raise ValueError(f"The list of fields values must contains {self._nb_fields} values")
        else:
            for field_number in fields_values.keys():
                if field_number < 0 or field_number > self._nb_fields:
                    raise ValueError(f"The field #{field_number} does not exist")
            fields_values = fields_values.copy()
            for field_number in range(self._nb_fields):
                if field_number not in fields_values.keys():
                    fields_values[field_number] = TEMPLATE_FIELD_DEFAULT_VALUE
        field_number = 0
        field_info = self._fields_information[field_number]
        complete_text = self._text[:field_info['start_index_in_text']] + fields_values[field_number]
        field_number += 1
        while field_number < self._nb_fields:
            previous_field_info, field_info = field_info, self._fields_information[field_number]
            complete_text += self._text[previous_field_info['end_index_in_text']+1:field_info['start_index_in_text']]
            complete_text += fields_values[field_number]
            field_number += 1
        complete_text += self._text[field_info['end_index_in_text']+1:]
        return complete_text

    def has_field_of_type(self, field_index: int, type_id: str):
        print("template.has_field_of_type() is deprecated")
        if (field_index < self.nb_fields) and (self._fields_information[field_index]['assumptions'].type_id == type_id):
            return True
        else:
            return False

    def compute_field_valid_values(self, solution: Solution, field_number: int,
                                   other_fields_values: dict[int, str] = None):
        if other_fields_values is not None:
            for other_field_number in other_fields_values.keys():
                if other_field_number < 0 or other_field_number > self._nb_fields:
                    raise ValueError(f"The field #{other_field_number} does not exist")
                if other_field_number == field_number:
                    raise ValueError(f"The field #{field_number} cannot be in the other fields values")
        else:
            other_fields_values = dict()
        instance = solution.instance
        field_assumptions = self._fields_information[field_number]['assumptions']
        # Case where the field must be an employee name
        if field_assumptions.must_refer_to_employee:
            # TODO change return depending on other_fields_values
            return instance.employees_names
        # Case where the field must be an task name
        elif field_assumptions.must_refer_to_task:
            possible_tasks = instance.tasks
            if field_assumptions.must_refer_to_performed_activity:
                possible_tasks = solution.performed_tasks
                if field_assumptions.must_refer_to_activity_performed_by_provided_employee:
                    employee_field_index = field_assumptions.field_index_of_employee_performing_this_field_activity
                    if employee_field_index in other_fields_values.keys():
                        employee = instance.get_employee_by_name(other_fields_values[employee_field_index])
                        possible_tasks = solution.get_tasks_performed_by(employee)
            elif field_assumptions.must_refer_to_not_performed_activity:
                possible_tasks = solution.non_performed_tasks
            if field_assumptions.must_refer_to_activity_not_performed_by_provided_employee:
                employee_field_index = field_assumptions.field_index_of_employee_not_performing_this_field_activity
                if employee_field_index in other_fields_values.keys():
                    employee = instance.get_employee_by_name(other_fields_values[employee_field_index])
                    possible_tasks = \
                        [task for task in possible_tasks if (not solution.get_task_performance_status(task)
                                                             or solution.get_task_assignee(task) != employee)]
            return [task.name for task in possible_tasks]
        # Case where the field must be an activity name
        elif field_assumptions.must_refer_to_activity:
            possible_activities_names = [START_VALUE] + solution.instance.tasks_names + [RETURN_VALUE]
            if field_assumptions.must_refer_to_performed_activity:
                possible_activities_names = [START_VALUE] + solution.performed_tasks_names + [RETURN_VALUE]
                if field_assumptions.must_refer_to_activity_performed_by_provided_employee:
                    employee_field_index = field_assumptions.field_index_of_employee_performing_this_field_activity
                    if employee_field_index in other_fields_values.keys():
                        employee = instance.get_employee_by_name(other_fields_values[employee_field_index])
                        possible_activities_names = \
                            [activity.name for activity in solution.get_sequence(employee).get_contained_activities()]
            elif field_assumptions.must_refer_to_not_performed_activity:
                possible_activities_names = solution.non_performed_tasks_names
            if field_assumptions.must_refer_to_activity_not_performed_by_provided_employee:
                employee_field_index = field_assumptions.field_index_of_employee_not_performing_this_field_activity
                if employee_field_index in other_fields_values.keys():
                    employee = instance.get_employee_by_name(other_fields_values[employee_field_index])
                    for task in solution.get_tasks_performed_by(employee):
                        if task.name in possible_activities_names:
                            possible_activities_names.remove(task.name)
            if field_assumptions.must_not_refer_to_start:
                if START_VALUE in possible_activities_names:
                    possible_activities_names.remove(START_VALUE)
            if field_assumptions.must_not_refer_to_return:
                if RETURN_VALUE in possible_activities_names:
                    possible_activities_names.remove(RETURN_VALUE)
            return possible_activities_names
        else:
            raise NotImplementedError(f"The field is either an employee, a task or an activity name")

    def compute_all_fields_valid_values(self, solution: Solution):
        def aux(first_fields_valid_values: list[dict[int, str]]):
            field_number = len(first_fields_valid_values[0])
            if field_number == self.nb_fields:
                return [list(fields_valid_values.values()) for fields_valid_values in first_fields_valid_values]
            else:
                next_first_fields_valid_values = []
                for fields_valid_values in first_fields_valid_values:
                    next_field_valid_values = \
                        self.compute_field_valid_values(solution, field_number, fields_valid_values)
                    for next_field_valid_value in next_field_valid_values:
                        fields_valid_values_with_next_field = fields_valid_values.copy()
                        fields_valid_values_with_next_field[field_number] = next_field_valid_value
                        next_first_fields_valid_values.append(fields_valid_values_with_next_field)
                return aux(next_first_fields_valid_values)
        return aux([dict()])

    def _check_field_value_type(self, instance: Instance, field_number: int, field_value: str):
        """
        Check that the value of the field #number corresponds to a name of the right type w.r.t. the instance

        :param instance:
        :param field_number:
        :param field_value:
        :return:
        """
        field_assumptions = self._fields_information[field_number]['assumptions']
        if field_assumptions.must_refer_to_employee:
            if field_value not in instance.employees_names:
                raise ValueError(f"The value {field_value} of the field #{field_number} "
                                 f"is not the name of an employee of the instance while it must be")
        elif field_assumptions.must_refer_to_task:
            if field_value not in instance.tasks_names:
                raise ValueError(f"The value {field_value} of the field #{field_number} "
                                 f"is not the name of a task of the instance while it must be")
        elif field_assumptions.must_refer_to_activity:
            if field_value not in (instance.tasks_names + [START_VALUE, RETURN_VALUE]):
                raise ValueError(f"The value {field_value} of the field #{field_number} "
                                 f"is not the name of an activity of the instance while it must be")
        else:
            raise NotImplementedError(f"The field is either an employee, a task or an activity name")
        return True

    def check_fields_values_validity(self, solution: Solution, fields_values: Union[dict[int, str], list[str]],
                                     raise_error: bool = False):
        """
        Check that the given values of the fields satisfy the assumptions about the fields w.r.t. the solution:

        - check that each value is a name of the right type;

        - check that each value corresponds to an element satisfying the expected field assumptions.

        :param solution:
        :param fields_values:
        :param raise_error:
        :return:
        """
        try:

            if isinstance(fields_values, list):
                if len(fields_values) != self._nb_fields:
                    raise ValueError(f"The list of fields values must contains {self._nb_fields} values")
                fields_values = dict(enumerate(fields_values))

            # Check that the name if the field is valid
            for field_number, field_value in fields_values.items():
                self._check_field_value_type(solution.instance, field_number, field_value)

            # Check other assumptions
            instance = solution.instance
            for field_number, field_value in fields_values.items():
                field_assumptions = self._fields_information[field_number]['assumptions']

                # Case where the field must refer to a task or
                # case where the field must refer to an activity and the given value is a task
                if (field_assumptions.must_refer_to_task or
                        (field_assumptions.must_refer_to_activity and field_value in instance.tasks_names)):
                    task_name = field_value
                    task = instance.get_task_by_name(task_name)
                    if field_assumptions.must_refer_to_performed_activity:
                        if not solution.get_task_performance_status(task):
                            raise ValueError(f"The task {field_value} of field #{field_number} is not performed "
                                             f"while it must be")
                        if field_assumptions.must_refer_to_activity_performed_by_provided_employee:
                            employee_field_index = \
                                field_assumptions.field_index_of_employee_performing_this_field_activity
                            if employee_field_index in fields_values.keys():
                                employee_name = fields_values[employee_field_index]
                                if employee_name != solution.get_task_assignee(task).name:
                                    raise ValueError(f"The task {field_value} of field #{field_number} is "
                                                     f"not performed by the employee {employee_name} "
                                                     f"of field #{employee_field_index} while it must be")
                    if field_assumptions.must_refer_to_not_performed_activity:
                        if solution.get_task_performance_status(task):
                            raise ValueError(f"The task {field_value} of field #{field_number} is performed "
                                             f"while it must not be")
                    if (field_assumptions.must_refer_to_activity_not_performed_by_provided_employee and
                            solution.get_task_performance_status(task)):
                        employee_field_index = \
                            field_assumptions.field_index_of_employee_not_performing_this_field_activity
                        if employee_field_index in fields_values.keys():
                            employee_name = fields_values[employee_field_index]
                            if employee_name == solution.get_task_assignee(task).name:
                                raise ValueError(f"The task {field_value} of field #{field_number} is performed "
                                                 f"by the employee {employee_name} of field #{employee_field_index} "
                                                 f"while it must not be")

                # Case where the field must refer to an activity (and is not a task)
                elif field_assumptions.must_refer_to_activity:
                    if field_value not in [START_VALUE, RETURN_VALUE]:
                        raise ValueError(f"The activity {field_value} of field #{field_number} is invalid")
                    if field_assumptions.must_refer_to_not_performed_activity:
                        raise ValueError(f"The activity {field_value} of field #{field_number} is performed "
                                         f"while it must not be")
                    if field_value == START_VALUE and field_assumptions.must_not_refer_to_start:
                        raise ValueError(f"The activity of field #{field_number} must not be {field_value}")
                    if field_value == RETURN_VALUE and field_assumptions.must_not_refer_to_return:
                        raise ValueError(f"The activity of field #{field_number} must not be {field_value}")

            return True

        # Catch any value error and raise it only if it is expected
        except ValueError as error:
            if raise_error:
                raise error
            else:
                return False
