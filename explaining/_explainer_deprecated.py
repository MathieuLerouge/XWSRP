# Standard library
import re

# Local libraries
from explaining._constants_deprecated import *
from explaining.explanationpart._examination_deprecated import (
    examine_placing_at, examine_insertion_at, examine_best_insertion, examine_insertion_in_addition,
    examine_best_insertion_when_isolated
)
from explaining.explanationpart._explanation_deprecated import ExplanationDeprecated
from explaining.questionpart.question import Question
from explaining.questionpart.questions_templates_bank import *
from explaining.questionpart._question_deprecated import TemplateQuestionDeprecated
from model.comeback import ComeBack
from model.solution import Solution, compare_solutions
from optimization.IP.sequence.alteringmodel import IPModelForAlteringSequence
from optimization.localsearch.solution import SolutionLS
from utils.constants import LINE_BREAK_STRING


# Class ExplainerDeprecated
class ExplainerDeprecated:

    _selected_questions_keys = [
        WHY_NOT_PERFORMING_JUST_AFTER_KEY, WHY_NOT_PERFORMING_BETWEEN_KEY, WHY_NOT_PERFORMING_IN_ADDITION_KEY,
        WHY_REALIZING_INSTEAD_OF_KEY, WHY_NOT_REALIZING_INSTEAD_OF_KEY,
        WHY_NOT_REALIZING_AT_ANOTHER_TIME_KEY, WHY_NOT_REALIZED_KEY,
        WHAT_IF_INSERTING_KEY, WHAT_IF_REALIZING_KEY, WHAT_IF_REORDERING_KEY, HOW_REALIZING_IN_ADDITION_KEY
    ]

    def __init__(self, solution: Solution = None):
        self._current_solution = None
        self._last_explanation_feasible_solution = None
        self._solutions_history = dict()
        if solution is not None:
            if not isinstance(solution, SolutionLS):
                solution_copy = SolutionLS.from_Solution(solution)
            else:
                solution_copy = solution.copy_deprecated(True)
            # TODO Not sure about managing _0 here
            solution_copy.name = solution.name.removesuffix("ByLS") + "_0"
            # solution_copy.tighten_times(False)
            solution_copy.compute_KPIs()
            self._current_solution = solution_copy
            self._solutions_history[self._current_solution.name] = self._current_solution
        self._questions = dict([(key, TemplateQuestionDeprecated(key)) for key in self._selected_questions_keys])

    @property
    def current_solution(self):
        return self._current_solution

    @current_solution.setter
    def current_solution(self, solution: Solution):
        if not (solution.name in self._solutions_history.values()):
            if not isinstance(solution, SolutionLS):
                solution = SolutionLS.from_Solution(solution)
            self._solutions_history[solution.name] = solution
        self._current_solution = solution

    @property
    def last_explanation_feasible_solution(self):
        return self._last_explanation_feasible_solution

    @property
    def nb_solutions(self):
        return len(self._solutions_history)

    @property
    def questions(self):
        return self._questions.values()

    @property
    def questions_keys(self):
        return self._questions.keys()

    #############
    # Solutions #
    #############

    def get_solution_by_name(self, solution_name: str):
        try:
            return self._solutions_history[solution_name]
        except KeyError:
            raise ValueError(f"There is not any stored solution named {solution_name}")

    def set_current_solution_by_name(self, solution_name: str):
        self._current_solution = self.get_solution_by_name(solution_name)

    def store_last_explanation_feasible_solution(self):
        if self._last_explanation_feasible_solution is None:
            raise AttributeError("There is not any feasible solution from the last explanation")
        else:
            solution = self._last_explanation_feasible_solution
            solution.name = re.sub(r"_.+", f"_{self.nb_solutions}", solution.name)
            self._solutions_history[solution.name] = solution

    def _copy_current_solution_for_new_solution(self):
        new_solution = self._current_solution.copy_deprecated(True)
        new_solution.name = re.sub(r"_.+", "_New", new_solution.name)
        return new_solution

    def _copy_current_solution_for_new_feasible_solution(self):
        new_solution = self._current_solution.copy_deprecated(True)
        new_solution.name = re.sub(r"_.+", "_NewFeasible", new_solution.name)
        return new_solution

    def _copy_current_solution_for_infeasible_solution(self):
        infeasible_solution = self._current_solution.copy_deprecated(True)
        infeasible_solution.name = re.sub(r"_.+", "_Infeasible", self._current_solution.name)
        return infeasible_solution

    ######################
    # Template questions #
    ######################

    def get_question(self, question_key: str):
        try:
            return self._questions[question_key]
        except KeyError:
            raise ValueError(f"There is not any template questioning associated to the given key {question_key},"
                             f"the questions' keys are {self._selected_questions_keys}")

    #####################################
    # Explanation computation - General #
    #####################################

    def compute_explanation(self, question: Question):
        template_id = question.template.id
        map_new_question_template_id_to_deprecated_one = dict([
            (WHY_NOT_INS_1, WHY_NOT_PERFORMING_JUST_AFTER_KEY),
            (WHY_NOT_INS_2A, WHY_NOT_PERFORMING_BETWEEN_KEY),
            (WHY_NOT_INS_3, WHY_NOT_PERFORMING_IN_ADDITION_KEY),
            (WHY_NOT_SWP_1, WHY_NOT_REALIZING_INSTEAD_OF_KEY)
        ])
        question_key_deprecated = map_new_question_template_id_to_deprecated_one[template_id]
        fields_values = dict(enumerate(question.fields_values))
        return self.compute_explanation_deprecated(question_key_deprecated, fields_values)

    def compute_explanation_deprecated(self, question_key: str, fields_values: dict[int, str]):
        # template_question = self.get_question(question_key)
        # if template_question.nb_fields != len(fields_values):
        #     raise ValueError(f"The given number of fields {len(fields_values)} in the dictionary {fields_values} "
        #                 f"does not match the number of fields expected by the given questioning {template_question}")
        if question_key in self._selected_questions_keys:
            if question_key == WHY_NOT_REALIZING_INSTEAD_OF_KEY:
                employee_name = fields_values[0]
                replacing_task_name = fields_values[1]
                leaving_task_name = fields_values[2]
                explanation = self.answer_question_about_why_not_realizing_instead_of(
                    employee_name, replacing_task_name, leaving_task_name
                )
            elif question_key == WHY_NOT_PERFORMING_JUST_AFTER_KEY:
                employee_name = fields_values[0]
                task_name = fields_values[1]
                activity_name = fields_values[2]
                explanation = self.answer_question_about_performing_after(employee_name, task_name, activity_name)
            elif question_key == WHY_NOT_PERFORMING_BETWEEN_KEY:
                employee_name = fields_values[0]
                task_name = fields_values[1]
                explanation = self.answer_question_about_performing_in_between(employee_name, task_name)
            elif question_key == WHY_NOT_REALIZING_AT_ANOTHER_TIME_KEY:
                employee_name = fields_values[0]
                task_name = fields_values[1]
                explanation = self.answer_question_about_why_not_realizing_at_another_time(employee_name, task_name)
            elif question_key == WHY_NOT_REALIZED_KEY:
                task_name = fields_values[1]
                explanation = self.answer_question_about_why_task_is_not_realized(task_name)
            elif question_key in WHY_NOT_PERFORMING_IN_ADDITION_KEY:
                employee_name = fields_values[0]
                task_name = fields_values[1]
                explanation = self.answer_question_about_performing_in_addition(employee_name, task_name)
            elif question_key in WHAT_IF_INSERTING_KEY:
                employee_name = fields_values[0]
                task_name = fields_values[1]
                explanation = self.answer_question_about_performing_in_addition_former(employee_name, task_name)
            elif question_key == WHAT_IF_REALIZING_KEY:
                employee_name = fields_values[0]
                task_name = fields_values[1]
                explanation = self.answer_question_what_if_realizing(employee_name, task_name)
            elif question_key == WHAT_IF_REORDERING_KEY:
                employee_name = fields_values[0]
                explanation = self.answer_question_what_if_reordering(employee_name)
            elif question_key == HOW_REALIZING_IN_ADDITION_KEY:
                employee_name = fields_values[0]
                task_name = fields_values[1]
                explanation = self.answer_question_how_realizing_in_addition(employee_name, task_name)
            # elif question_key == "Tightening":
            #     explanation = self.answer_question_about_tightening()
            else:
                raise Exception("There is something wrong with selected questioning keys and explanation computation")
        else:
            explanation = ExplanationDeprecated("Not yet coded but thank you for your interest ;)")
        return explanation

    ###################################################
    # Explanation computation - Contrastive questions #
    ###################################################

    def answer_question_about_why_realizing_instead_of(self, employee_name: str,
                                                       leaving_task_name: str, entering_task_name: str):
        """
        Compute the explanation about why is the given employee performing the given leaving task
        instead of the given entering task.


        The leaving task must be performed by the employee, otherwise a ValueError is raised.
        The entering task must not be performed by the employee, otherwise a ValueError is raised.

        :param employee_name: the name (str) of the employee who is figured to performed the given entering task
        :param leaving_task_name: the name (str) of the given leaving task
        :param entering_task_name: the name (str) of the given entering task
        :return: an explanation (Explanation)
        """

        # Get employee, sequence, entering task and leaving task
        employee = self._current_solution.instance.get_employee_by_name(employee_name)
        sequence = self._current_solution.get_sequence(employee)
        entering_task = self._current_solution.instance.get_task_by_name(entering_task_name)
        if sequence.contains(entering_task):
            raise ValueError(f"The entering task {entering_task_name} is performed by the employee {employee_name}")
        leaving_task = self._current_solution.instance.get_task_by_name(leaving_task_name)
        leaving_task_index = sequence.get_step_index_of(leaving_task)

        # Check the employee capacity to perform the entering task
        if not employee.is_capable_of_performing(entering_task):
            explanation_text = (
                f"{employee_name} does not have enough skills to do {entering_task_name}, {LINE_BREAK_STRING}"
                f"therefore {employee_name} can not do {entering_task_name} instead of {leaving_task_name}."
            )
            return ExplanationDeprecated(explanation_text)

        # Examine the placement of the entering task instead of the leaving task
        step_before_placement_index = leaving_task_index - 1
        step_after_placement_index = leaving_task_index + 1
        examination = examine_placing_at(
            self._current_solution, employee, entering_task, step_before_placement_index, step_after_placement_index
        )

        # If the placement is not feasible,
        if not examination['is_feasible']:

            # Create the infeasible solution
            infeasible_solution = self._copy_current_solution_for_infeasible_solution()
            infeasible_solution.replace_task_by_another(
                leaving_task, entering_task, examination['earliest_start_time_for_upstream'],
                examination['earliest_start_time_for_upstream'], examination['latest_start_time_for_downstream'],
                False, False
            )

            # Create the explanation text
            explanation_text = (
                f"Let assume that {entering_task_name} is put in {employee_name}'s planning "
                f"instead of {leaving_task_name}. {LINE_BREAK_STRING}"
                f"{examination['comment']} {LINE_BREAK_STRING}"
                f"Therefore {employee_name} can not do {entering_task_name} instead of {leaving_task_name}."
            )

            # Save the infeasibility reason
            # TODO make a class of it?
            infeasibility = {
                'employee_name': employee_name,
                'task_name': entering_task_name
            }
            critical_bounds = None
            # TODO Why only if upstream feasible?
            if examination['is_upstream_feasible']:
                critical_LB_index = (
                    infeasible_solution.get_sequence(
                        employee
                    ).find_first_critical_step_index_backward_from(step_before_placement_index)
                )
                critical_UB_index = (
                    infeasible_solution.get_sequence(
                        employee
                    ).find_first_critical_step_index_forward_from(step_after_placement_index)
                )
                critical_bounds = {
                    employee_name: {
                        infeasible_solution.get_sequence(employee)[critical_LB_index].activity.name: "LB",
                        infeasible_solution.get_sequence(employee)[critical_UB_index].activity.name: "UB"
                    }
                }

            # Return the explanation
            return ExplanationDeprecated(explanation_text, infeasible_solution, False, infeasibility, critical_bounds)

        # If the insertion is feasible,
        else:

            # Create the new feasible solution
            new_solution = self._copy_current_solution_for_new_feasible_solution()
            new_solution.replace_task_by_another(
                leaving_task, entering_task, examination['start_time'],
                tighten_times=True, update_KPIs=True
            )
            # new_solution.compute_KPIs()
            self._last_explanation_feasible_solution = new_solution

            # Create the explanation text
            explanation_text = (
                f"{employee_name} can actually do {entering_task_name} "
                f"instead of {leaving_task_name}. {LINE_BREAK_STRING}"
            )
            comparison_text = compare_solutions(self._current_solution, new_solution)
            explanation_text += comparison_text.replace(
                self._current_solution.name, "the former solution"
            ).replace(new_solution.name, "the new solution")

            # Return the explanation
            return ExplanationDeprecated(explanation_text, new_solution, True)

    def answer_question_about_why_not_realizing_instead_of(self, employee_name: str,
                                                           entering_task_name: str, leaving_task_name: str):
        """
        Compute the explanation about why-not having the given employee performing the given entering task
        instead of the given leaving task.

        The entering task must not be performed by the employee, otherwise a ValueError is raised.
        The leaving task must be performed by the employee, otherwise a ValueError is raised.

        :param employee_name: the name (str) of the employee who is figured to performed the given entering task
        :param entering_task_name: the name (str) of the given entering task
        :param leaving_task_name: the name (str) of the given leaving task
        :return: an explanation (Explanation)
        """

        return self.answer_question_about_why_realizing_instead_of(
            employee_name, leaving_task_name, entering_task_name
        )

    def answer_question_about_performing_after(self, employee_name: str,
                                               entering_task_name: str, activity_before_insertion_name: str):
        """
        Compute the explanation about why-not having the given employee
        performing the given entering task just after the given activity.

        The entering task must not be performed by the employee, otherwise a ValueError is raised.
        The entering task may be performed by another employee however.
        The activity must not be the employee's comeback, otherwise a ValueError is raised.

        :param employee_name: the name (str) of the employee who is figured to performed the given entering task
        :param entering_task_name: the name (str) of the given entering task
        :param activity_before_insertion_name: the name (str) of the given activity
        :return: an explanation (Explanation)
        """

        # Get employee, sequence, entering task and activity before
        employee = self._current_solution.instance.get_employee_by_name(employee_name)
        sequence = self._current_solution.get_sequence(employee)
        entering_task = self._current_solution.instance.get_task_by_name(entering_task_name)
        if sequence.contains(entering_task):
            raise ValueError(f"The entering task {entering_task_name} is performed by the employee {employee_name}")
        activity_before_insertion = self._current_solution.instance.get_hypothetical_activity_by_names(
            activity_before_insertion_name, employee_name
        )
        if isinstance(activity_before_insertion, ComeBack):
            raise ValueError(f"The entering task {entering_task_name} can not be inserted "
                             f"after the employee's comeback {activity_before_insertion.name}")
        before_insertion_activity_index = sequence.get_step_index_of(activity_before_insertion)

        # Check the employee capacity to perform the entering task
        if not employee.is_capable_of_performing(entering_task):
            explanation_text = (
                f"{employee_name} does not have enough skills to do {entering_task_name}, {LINE_BREAK_STRING}"
                f"therefore {employee_name} can not do {entering_task_name} after {activity_before_insertion_name}."
            )
            return ExplanationDeprecated(explanation_text)

        # Examine the insertion of the entering task
        examination = examine_insertion_at(
            self._current_solution, employee, entering_task, before_insertion_activity_index + 1
        )

        # If the insertion is not feasible,
        if not examination['is_feasible']:

            # Create the infeasible solution
            infeasible_solution = self._copy_current_solution_for_infeasible_solution()
            infeasible_solution.insert_task_after_activity(
                entering_task, activity_before_insertion, examination['earliest_start_time_for_upstream'],
                examination['earliest_start_time_for_upstream'], examination['latest_start_time_for_downstream'],
                False, False
            )

            # Create the explanation text
            explanation_text = (
                f"Let assume that {entering_task_name} is put in {employee_name}'s planning "
                f"just after {activity_before_insertion.name}. {LINE_BREAK_STRING}"
                f"{examination['comment']} {LINE_BREAK_STRING}"
                f"Therefore {employee_name} can not do {entering_task_name} "
                f"just after {activity_before_insertion.name}"
            )

            # Save the infeasibility reason
            infeasibility = {
                'employee_name': employee_name,
                'task_name': entering_task_name
            }
            critical_bounds = None
            if examination['is_upstream_feasible']:
                critical_LB_index = (
                    infeasible_solution.get_sequence(
                        employee
                    ).find_first_critical_step_index_backward_from(before_insertion_activity_index)
                )
                critical_UB_index = (
                    infeasible_solution.get_sequence(
                        employee
                    ).find_first_critical_step_index_forward_from(before_insertion_activity_index + 2)
                )
                critical_bounds = {
                    employee_name: {
                        infeasible_solution.get_sequence(employee)[critical_LB_index].activity.name: "LB",
                        infeasible_solution.get_sequence(employee)[critical_UB_index].activity.name: "UB"}
                }

            # Return the explanation
            return ExplanationDeprecated(explanation_text, infeasible_solution, False, infeasibility, critical_bounds)

        # If the insertion is feasible,
        else:

            # Create the new feasible solution
            new_solution = self._copy_current_solution_for_new_feasible_solution()
            new_solution.insert_task_after_activity(
                entering_task, activity_before_insertion, examination['start_time'],
                tighten_times=True, update_KPIs=True
            )
            # new_solution.compute_KPIs()
            self._last_explanation_feasible_solution = new_solution

            # Create the explanation text
            explanation_text = (
                f"{employee_name} can actually do {entering_task_name} "
                f"just after {activity_before_insertion_name}. {LINE_BREAK_STRING}"
            )
            comparison_text = compare_solutions(self._current_solution, new_solution)
            explanation_text += comparison_text.replace(
                self._current_solution.name, "the former solution"
            ).replace(new_solution.name, "the new solution")

            # Return the explanation
            return ExplanationDeprecated(explanation_text, new_solution, True)

    def answer_question_about_performing_in_between(self, employee_name: str, entering_task_name: str):
        """
        Compute the explanation about why-not having the given employee performing the given entering task
        in addition to the tasks already performed by him/her.

        The entering task must not be performed by the employee, otherwise a ValueError is raised.
        The entering task may be performed by another employee however.

        :param employee_name: the name (str) of the employee who is figured to performed the given entering task
        :param entering_task_name: the name (str) of the given entering task
        :return: an explanation (Explanation)
        """

        # Get employee, sequence and entering task
        employee = self._current_solution.instance.get_employee_by_name(employee_name)
        sequence = self._current_solution.get_sequence(employee)
        entering_task = self._current_solution.instance.get_task_by_name(entering_task_name)
        if sequence.contains(entering_task):
            raise ValueError(f"The entering task {entering_task_name} is performed by the employee {employee_name}")

        # Check the employee capacity to perform the entering task
        if not employee.is_capable_of_performing(entering_task):
            explanation_text = (
                f"{employee_name} does not have enough skills to do {entering_task_name}, {LINE_BREAK_STRING}"
                f"therefore {employee_name} can not do {entering_task.name} "
                f"in addition to the tasks of their planning."
            )
            return ExplanationDeprecated(explanation_text)

        # Examine the best insertion of the entering task
        examination = examine_best_insertion(self._current_solution, entering_task, employee)
        insertion_index = examination['step_index_for_insertion']
        step_before_insertion = sequence[insertion_index - 1]

        # If the insertion is not feasible,
        if not examination['is_feasible']:

            # Create the infeasible solution
            infeasible_solution = self._copy_current_solution_for_infeasible_solution()
            infeasible_solution.insert_task_after_activity(
                entering_task, step_before_insertion.activity, examination['earliest_start_time_for_upstream'],
                examination['earliest_start_time_for_upstream'], examination['latest_start_time_for_downstream'],
                False, False
            )

            # Create the explanation text
            if not examination['is_upstream_feasible']:
                explanation_text = (
                    f"Let assume that {entering_task.name} is inserted in {employee_name}'s planning"
                    f"just after {step_before_insertion.activity.name}. {LINE_BREAK_STRING}"
                    f"{examination['comment']} {LINE_BREAK_STRING}"
                    f"Inserting {entering_task.name} later in {employee_name}'s planning "
                    f"can only lead to a later ending time. {LINE_BREAK_STRING}"
                    f"Therefore {employee_name} can not do {entering_task.name} "
                    f"just after {step_before_insertion.activity.name}"
                )
            else:
                explanation_text = (
                    f"All insertions of {entering_task.name} in {employee_name}'s planning have been tested "
                    f"and none of them are feasible. {LINE_BREAK_STRING}"
                    f"For instance, one of the nearest solutions to feasibility is obtained "
                    f"by inserting {entering_task.name} in {employee_name}'s planning "
                    f"just after {step_before_insertion.activity.name}. {LINE_BREAK_STRING}"
                    f"Let assume that {entering_task.name} is inserted this way. {examination['comment']} "
                    f"Therefore {employee_name} can not do {entering_task.name} "
                    f"just after {step_before_insertion.activity.name}. {LINE_BREAK_STRING}"
                    f"More generally, {employee_name} can not do {entering_task.name} "
                    f"in addition to the tasks of their planning."
                )

            # Save the infeasibility reason
            infeasibility = {
                'employee_name': employee_name,
                'task_name': entering_task_name
            }
            critical_bounds = None
            if examination['is_upstream_feasible']:
                critical_LB_index = infeasible_solution.get_sequence(
                    employee
                ).find_first_critical_step_index_backward_from(insertion_index - 1)
                critical_UB_index = infeasible_solution.get_sequence(
                    employee
                ).find_first_critical_step_index_forward_from(insertion_index + 1)
                critical_bounds = {
                    employee_name: {
                        infeasible_solution.get_sequence(employee)[critical_LB_index].activity.name: "LB",
                        infeasible_solution.get_sequence(employee)[critical_UB_index].activity.name: "UB"
                    }
                }

            # Return the explanation
            return ExplanationDeprecated(explanation_text, infeasible_solution, False, infeasibility, critical_bounds)

        # If the insertion is feasible,
        else:

            # Create the new feasible solution
            new_solution = self._copy_current_solution_for_new_feasible_solution()
            new_solution.insert_task_after_activity(
                entering_task, step_before_insertion.activity, examination['start_time'],
                tighten_times=True, update_KPIs=True
            )
            self._last_explanation_feasible_solution = new_solution

            # Create the explanation text
            explanation_text = (
                    f"{employee.name} can actually do {entering_task_name} "
                    f"in addition to the tasks of their planning by inserting it "
                    f"after {step_before_insertion.activity.name}. {LINE_BREAK_STRING}"
            )
            comparison_text = compare_solutions(self._current_solution, new_solution)
            explanation_text += comparison_text.replace(
                self._current_solution.name, "the former solution"
            ).replace(new_solution.name, "the new solution")

            # Return the explanation
            return ExplanationDeprecated(explanation_text, new_solution, True)

    def answer_question_about_performing_in_addition(self, employee_name: str, entering_task_name: str):
        """
        Compute the explanation to the questioning "why is the given employee not performing the given entering task
        in addition to the activities of their planning?"

        The entering task must not be performed by the employee, otherwise a ValueError is raised.
        The entering task may be performed by another employee however.

        :param employee_name: the name (str) of the employee who is figured to performed the given entering task
        :param entering_task_name: the name (str) of the given entering task
        :return: an explanation (Explanation)
        """

        # Get employee, sequence and entering task
        employee = self._current_solution.instance.get_employee_by_name(employee_name)
        sequence = self._current_solution.get_sequence(employee)
        entering_task = self._current_solution.instance.get_task_by_name(entering_task_name)
        if sequence.contains(entering_task):
            raise ValueError(f"The entering task {entering_task_name} is performed by the employee {employee_name}")

        # Check the employee capacity to perform the entering task
        if not employee.is_capable_of_performing(entering_task):
            explanation_text = (
                f"{employee_name} does not have enough skills to do {entering_task_name}, {LINE_BREAK_STRING}"
                f"therefore {employee_name} can not perform {entering_task.name}."
            )
            return ExplanationDeprecated(explanation_text)

        # Examine if the task can be affected to employee as their only task
        examination = examine_best_insertion_when_isolated(self._current_solution, employee, entering_task)

        # If the task can not be affected to employee even if it is their only task
        if not examination['is_feasible']:

            # Get the infeasible solution
            infeasible_solution = examination['solution']
            infeasible_solution.name = re.sub(r"_.+", "_Infeasible", infeasible_solution.name)
            infeasible_sequence = infeasible_solution.get_sequence(employee)
            insertion_index = examination['step_index_for_insertion']
            step_before_insertion = infeasible_sequence[insertion_index - 1]
            step_after_insertion = infeasible_sequence[insertion_index + 1]

            # Create the explanation text
            explanation_text = (
                f"{employee.name} can not perform {entering_task_name} in addition to their activities."
                f"{LINE_BREAK_STRING}"
                f"Consider that {entering_task_name} is the only task to be performed by {employee.name} "
                f"and that it is inserted between {step_before_insertion.activity.name} "
                f"and {step_after_insertion.activity.name}. {LINE_BREAK_STRING}"
                f"{examination['comment']} {LINE_BREAK_STRING}"
                f"Therefore, as {employee_name} can not perform {entering_task_name} as their only task, "
                f"{employee.name} can not perform {entering_task_name} in addition to their activities."
            )

            # Save the infeasibility reason
            infeasibility = {'employee_name': employee_name, 'task_name': entering_task_name}

            # Return the explanation
            return ExplanationDeprecated(explanation_text, infeasible_solution, False, infeasibility)

        # If the task can be affected to employee as their only task
        else:

            # Examine the best insertion of the entering task in addition to the other activities
            examination = examine_insertion_in_addition(self._current_solution, employee, entering_task)

            # If the insertion is not feasible,
            if not examination['is_feasible']:

                # Get the infeasible solution
                infeasible_solution = examination['solution']
                infeasible_solution.name = re.sub(r"_.+", "_Infeasible", infeasible_solution.name)
                infeasible_sequence = infeasible_solution.get_sequence(employee)
                insertion_index = examination['step_index_for_insertion']
                step_before_insertion = infeasible_sequence[insertion_index - 1]
                step_after_insertion = infeasible_sequence[insertion_index + 1]

                # Create the explanation text
                explanation_text = (
                    f"{employee.name} can not perform {entering_task_name} in addition to their activities."
                    f"{LINE_BREAK_STRING}"
                    f"All the ways to order {employee_name}'s planning have been tested "
                    f"and none of them allows to add {entering_task_name} in a feasible way. {LINE_BREAK_STRING}"
                    f"The solution in which {entering_task_name} is added to {employee_name}'s planning "
                    f"that is the nearest to feasibility is provided here, "
                    f"where {entering_task_name} is inserted between {step_before_insertion.activity.name} and "
                    f"{step_after_insertion.activity.name}. {LINE_BREAK_STRING}"
                    f"{examination['comment']} {LINE_BREAK_STRING}"
                    f"More generally, any solution in which {entering_task_name} is added to {employee_name}'s "
                    f"planning is infeasible."
                )

                # Save the infeasibility reason
                infeasibility = {
                    'employee_name': employee_name,
                    'task_name': entering_task_name
                }
                critical_bounds = None
                if examination['is_upstream_feasible']:
                    critical_LB_index = infeasible_solution.get_sequence(
                        employee
                    ).find_first_critical_step_index_backward_from(insertion_index - 1)
                    critical_UB_index = infeasible_solution.get_sequence(
                        employee
                    ).find_first_critical_step_index_forward_from(insertion_index + 1)
                    critical_bounds = {
                        employee_name: {
                            infeasible_solution.get_sequence(employee)[critical_LB_index].activity.name: "LB",
                            infeasible_solution.get_sequence(employee)[critical_UB_index].activity.name: "UB"
                        }
                    }

                # Return the explanation
                return ExplanationDeprecated(explanation_text, infeasible_solution, False, infeasibility, critical_bounds)

            else:

                # Create the new feasible solution
                new_solution = examination['solution']
                new_solution.name = re.sub(r"_.+", "_NewFeasible", new_solution.name)
                new_solution.compute_KPIs()
                self._last_explanation_feasible_solution = new_solution

                # Create the explanation text
                explanation_text = (
                    f"It is possible to add {entering_task_name} in {employee.name}'s planning "
                    f"in addition to their activities. {LINE_BREAK_STRING}"
                )
                comparison_text = compare_solutions(self._current_solution, new_solution)
                explanation_text += comparison_text.replace(
                    self._current_solution.name, "the former solution"
                ).replace(new_solution.name, "the new solution")

                # Return the explanation
                return ExplanationDeprecated(explanation_text, new_solution, True)

    def answer_question_about_why_not_realizing_at_another_time(self, employee_name: str, task_name: str):
        """
        Compute the explanation about why-not having the given employee performing the given task
        at another time in their planning.

        The given task must be performed by the employee, otherwise a ValueError is raised.

        :param employee_name: the name (str) of the employee who is figured to performed the given entering task
        :param task_name: the name (str) of the given task to move
        :return: an explanation (Explanation)
        """

        # Get employee, task and its corresponding step index
        employee = self._current_solution.instance.get_employee_by_name(employee_name)
        task = self._current_solution.instance.get_task_by_name(task_name)
        step_index = self._current_solution.get_sequence(employee).get_step_index_of(task)

        # Create new solution and remove task
        new_solution = self._copy_current_solution_for_new_solution()
        new_solution.remove_task(task, False, True)
        new_sequence = new_solution.get_sequence(employee)

        # Examine the best insertion of the task while preventing the insertion at the same step index
        examination = examine_best_insertion(new_solution, task, employee, [step_index])
        insertion_index = examination['step_index_for_insertion']
        step_before_insertion = new_sequence[insertion_index - 1]

        # If insertion is infeasible
        if not examination['is_feasible']:

            # Create the infeasible solution
            infeasible_solution = new_solution
            infeasible_solution.insert_task_after_activity(
                task, step_before_insertion.activity, examination['earliest_start_time_for_upstream'],
                examination['earliest_start_time_for_upstream'], examination['latest_start_time_for_downstream'],
                False, False
            )

            # Create the explanation text
            explanation_text = (
                f"All insertions of {task_name} in {employee_name}'s planning have been tested "
                f"and none of them are feasible. {LINE_BREAK_STRING}"
                f"For instance, one of the nearest solutions to feasibility is obtained by inserting {task_name} "
                f"in {employee_name}'s just after {step_before_insertion.activity.name}. {LINE_BREAK_STRING}"
                f"Let assume that {task_name} is inserted this way. {examination['comment']} "
                f"Therefore {employee_name} can not do {task_name} "
                f"just after {step_before_insertion.activity.name}. {LINE_BREAK_STRING}"
                f"More generally, {employee_name} can not do {task_name} at another time in their planning."
            )

            # Save the infeasibility reason
            infeasibility = {
                'employee_name': employee_name,
                'task_name': task_name
            }

            # Return the explanation
            return ExplanationDeprecated(explanation_text, infeasible_solution, False, infeasibility)

        # If the insertion is feasible,
        else:

            # Create the new feasible solution
            new_solution.insert_task_after_activity(
                task, step_before_insertion.activity, examination['start_time'],
                tighten_times=True, update_KPIs=True
            )
            self._last_explanation_feasible_solution = new_solution

            # Create the explanation text
            explanation_text = (
                f"{employee.name} can actually do {task.name} " 
                f"at another time in their planning by inserting it "
                f"after {step_before_insertion.activity.name}. {LINE_BREAK_STRING}"
            )
            comparison_text = compare_solutions(self._current_solution, new_solution)
            explanation_text += comparison_text.replace(
                self._current_solution.name, "the former solution"
            ).replace(new_solution.name, "the new solution")

            # Return the explanation
            return ExplanationDeprecated(explanation_text, new_solution, True)

    def answer_question_about_why_task_is_not_realized(self, task_name: str):

        # Get the task
        task = self._current_solution.instance.get_task_by_name(task_name)

        # Examine the best insertion of the task
        examination = examine_best_insertion(self._current_solution, task)
        employee = examination['employee']

        # If the insertion is not feasible,
        if not examination['is_feasible']:

            # If none of the employees is capable of performing the task
            if employee is None:
                explanation_text = (
                    f"None of the employees is capable of performing the task {task_name}. {LINE_BREAK_STRING}"
                    f"Therefore, {task_name} can not be performed."
                )
                return ExplanationDeprecated(explanation_text)

            # If some employees are capable of performing the task
            else:

                # Get step before the insertion
                insertion_index = examination['step_index_for_insertion']
                step_before_insertion = self._current_solution.get_sequence(employee)[insertion_index - 1]

                # Create the infeasible solution
                infeasible_solution = self._copy_current_solution_for_infeasible_solution()
                infeasible_solution.insert_task_after_activity(
                    task, step_before_insertion.activity, examination['earliest_start_time_for_upstream'],
                    examination['earliest_start_time_for_upstream'], examination['latest_start_time_for_downstream'],
                    False, False
                )

                # Create the explanation text
                explanation_text = (
                    f"All insertions of {task_name} in all employees' plannings have been tested "
                    f"and none of them are feasible. {LINE_BREAK_STRING}"
                    f"For instance, one of the nearest solutions to feasibility is obtained "
                    f"by inserting {task_name} in {employee.name}'s planning "
                    f"just after {step_before_insertion.activity.name}. {LINE_BREAK_STRING}"
                    f"Let assume that {task_name} is inserted this way. {examination['comment']} "
                    f"Therefore {employee.name} can not perform {task_name} "
                    f"just after {step_before_insertion.activity.name}. {LINE_BREAK_STRING}"
                    f"More generally, no employee can perform {task_name} in their planning."
                )

                # Save the infeasibility reason
                infeasibility = {
                    'employee_name': employee.name,
                    'task_name': task_name
                }

                # Return the explanation
                return ExplanationDeprecated(explanation_text, infeasible_solution, False, infeasibility)

        # If the insertion is feasible
        else:

            # Get step before the insertion
            insertion_index = examination['step_index_for_insertion']
            step_before_insertion = self._current_solution.get_sequence(employee)[insertion_index - 1]

            # Create the new feasible solution
            new_solution = self._copy_current_solution_for_new_feasible_solution()
            new_solution.insert_task_after_activity(
                task, step_before_insertion.activity, examination['start_time'],
                tighten_times=True, update_KPIs=True
            )
            self._last_explanation_feasible_solution = new_solution

            # Create the explanation text
            explanation_text = (
                f"{task.name} can be performed by {employee.name} "
                f"in addition to the tasks of their planning by inserting it "
                f"after {step_before_insertion.activity.name}. {LINE_BREAK_STRING}"
            )
            comparison_text = compare_solutions(self._current_solution, new_solution)
            explanation_text += comparison_text.replace(
                self._current_solution.name, "the former solution"
            ).replace(new_solution.name, "the new solution")

            # Return the explanation
            return ExplanationDeprecated(explanation_text, new_solution, True)

    ######################################################
    # Explanation computation - Counterfactual questions #
    ######################################################

    def answer_question_about_performing_in_addition_former(self, employee_name: str, entering_task_name: str):

        # Get employee, sequence and entering task
        employee = self._current_solution.instance.get_employee_by_name(employee_name)
        sequence = self._current_solution.get_sequence(employee)
        entering_task = self._current_solution.instance.get_task_by_name(entering_task_name)

        # Check the employee capacity to perform the entering task
        if not employee.is_capable_of_performing(entering_task):
            explanation_text = (
                f"{employee_name} does not have enough skills to do {entering_task_name}, {LINE_BREAK_STRING}"
                f"therefore {employee_name} can not perform {entering_task.name}."
            )
            return ExplanationDeprecated(explanation_text)

        # Examine if the task can be affected to employee as their only task
        examination = examine_best_insertion_when_isolated(self._current_solution, employee, entering_task)
        insertion_index = examination['step_index_for_insertion']

        # If the task can not be affected to employee even if it is their only task
        if not examination['is_feasible']:

            # Get the infeasible solution
            infeasible_solution = examination['solution']
            infeasible_solution.name = re.sub(r"_.+", "_Infeasible", infeasible_solution.name)
            infeasible_sequence = infeasible_solution.get_sequence(employee)
            step_before_insertion = infeasible_sequence[insertion_index - 1]
            step_after_insertion = sequence[insertion_index + 1]

            # Create the explanation text
            explanation_text = (
                f"{employee.name} can not perform {entering_task_name}. {LINE_BREAK_STRING}"
                f"Indeed, let assume that {entering_task_name} is the only task to be in {employee.name}'s planning "
                f"and that it is inserted between {step_before_insertion.activity.name} "
                f"and {step_after_insertion.activity.name}. {LINE_BREAK_STRING}"
                f"{examination['comment']} {LINE_BREAK_STRING}"
                f"Therefore {employee_name} can not perform {entering_task_name} "
                f"whatever is done about the other tasks."
            )

            # Save  the infeasibility reason
            infeasibility = {'employee_name': employee_name, 'task_name': entering_task_name}

            # Return the explanation
            return ExplanationDeprecated(explanation_text, infeasible_solution, False, infeasibility)

        # If the task can be affected to employee as their only task
        else:

            # Create the new feasible solution
            new_solution = self._copy_current_solution_for_new_feasible_solution()
            new_solution.try_inserting(employee, entering_task, True, True)
            self._last_explanation_feasible_solution = new_solution

            # Create the explanation text
            explanation_text = ""
            if not (entering_task in new_solution.get_sequence(employee).get_contained_tasks()):
                explanation_text += (
                    f"It is not possible to insert {entering_task_name} in {employee.name}'s planning "
                    f"while keeping all other tasks performed even if their order changes."
                )
            else:
                explanation_text += (
                    f"It is possible to insert {entering_task_name} in {employee.name}'s planning. "
                    f"{LINE_BREAK_STRING}"
                )
                comparison_text = compare_solutions(self._current_solution, new_solution)
                explanation_text += comparison_text.replace(
                    self._current_solution.name, "the former solution"
                ).replace(new_solution.name, "the new solution")

            # Return the explanation
            return ExplanationDeprecated(explanation_text, new_solution, True)

    def answer_question_what_if_realizing(self, employee_name: str, entering_task_name: str):

        # Get employee, sequence and entering task
        employee = self._current_solution.instance.get_employee_by_name(employee_name)
        sequence = self._current_solution.get_sequence(employee)
        entering_task = self._current_solution.instance.get_task_by_name(entering_task_name)

        # Check the employee capacity to perform the entering task
        if not employee.is_capable_of_performing(entering_task):
            explanation_text = (
                f"{employee_name} does not have enough skills to do {entering_task_name}, {LINE_BREAK_STRING}"
                f"therefore {employee_name} can not perform {entering_task.name}."
            )
            return ExplanationDeprecated(explanation_text)

        # Examine if the task can be affected to employee as their only task
        examination = examine_best_insertion_when_isolated(self._current_solution, employee, entering_task)
        insertion_index = examination['step_index_for_insertion']

        # If the task can not be affected to employee even if it is their only task
        if not examination['is_feasible']:

            # Get the infeasible solution
            infeasible_solution = examination['solution']
            infeasible_solution.name = re.sub(r"_.+", "_Infeasible", infeasible_solution.name)
            infeasible_sequence = infeasible_solution.get_sequence(employee)
            step_before_insertion = infeasible_sequence[insertion_index - 1]
            step_after_insertion = sequence[insertion_index + 1]

            # Create the explanation text
            explanation_text = (
                f"{employee.name} can not perform {entering_task_name}. {LINE_BREAK_STRING}"
                f"Indeed, let assume that {entering_task_name} is the only task to be in {employee.name}'s planning "
                f"and that it is inserted between {step_before_insertion.activity.name} "
                f"and {step_after_insertion.activity.name}. {LINE_BREAK_STRING}"
                f"{examination['comment']} {LINE_BREAK_STRING}"
                f"Therefore {employee_name} can not perform {entering_task_name} "
                f"whatever is done about the other tasks."
            )

            # Save  the infeasibility reason
            infeasibility = {
                'employee_name': employee_name,
                'task_name': entering_task_name
            }

            # Return the explanation
            return ExplanationDeprecated(explanation_text, infeasible_solution, False, infeasibility)

        # If the task can be affected to employee as their only task
        else:

            # Create the new feasible solution
            new_solution = self._copy_current_solution_for_new_feasible_solution()
            new_solution.insert_task_at_all_costs(employee, entering_task, True, True)
            removed_tasks = set(sequence.get_contained_tasks()).difference(
                new_solution.get_sequence(employee).get_contained_tasks())
            self._last_explanation_feasible_solution = new_solution

            # Create the explanation text
            explanation_text = ""
            if not bool(removed_tasks):
                explanation_text += (
                    f"It is possible to insert {entering_task_name} in {employee.name}'s planning " 
                    f"while keeping all other tasks performed. {LINE_BREAK_STRING}"
                )
            else:
                explanation_text += (
                    f"If {entering_task_name} is inserted in {employee.name}'s planning, "
                    f"then one or several tasks must be removed. {LINE_BREAK_STRING}"
                    f"The solution maximizing the total working duration is obtained "
                    f"by removing the task{'s' if len(removed_tasks) > 1 else ''}: "
                )
                for task in removed_tasks:
                    explanation_text += f"{task.name}, "
                explanation_text = explanation_text.removesuffix(", ")
                explanation_text += "." + LINE_BREAK_STRING
            comparison_text = compare_solutions(self._current_solution, new_solution)
            explanation_text += comparison_text.replace(
                self._current_solution.name, "the former solution"
            ).replace(new_solution.name, "the new solution")

            # Return the explanation
            return ExplanationDeprecated(explanation_text, new_solution, True)

    def answer_question_what_if_reordering(self, employee_name: str):

        # Get employee, sequence and entering task
        employee = self._current_solution.instance.get_employee_by_name(employee_name)
        sequence = self._current_solution.get_sequence(employee)

        # Create the new feasible solution
        new_solution = self._copy_current_solution_for_new_feasible_solution()
        new_solution.reorder(employee, True, True)
        removed_tasks = set(sequence.get_contained_tasks()).difference(
            new_solution.get_sequence(employee).get_contained_tasks())
        self._last_explanation_feasible_solution = new_solution

        # Create the explanation text
        explanation_text = ""
        if not bool(removed_tasks):
            explanation_text += (
                f"It is possible to change the order of the activities in {employee.name}'s planning "
                f"while keeping all tasks performed."
            )
        else:
            explanation_text += (
                f"If the order of the activities in {employee.name}'s planning is changed "
                f"then one or several tasks must be removed. {LINE_BREAK_STRING}"
                f"The solution maximizing the total working duration is obtained "
                f"by removing the task{'s' if len(removed_tasks) > 1 else ''}: "
            )
            for task in removed_tasks:
                explanation_text += f"{task.name}, "
            explanation_text = explanation_text.removesuffix(", ")
            explanation_text += "."
        explanation_text += LINE_BREAK_STRING
        comparison_text = compare_solutions(self._current_solution, new_solution)
        explanation_text += comparison_text.replace(
            self._current_solution.name, "the former solution"
        ).replace(new_solution.name, "the new solution")

        # Return the explanation
        return ExplanationDeprecated(explanation_text, new_solution, True)

    def answer_question_how_realizing_in_addition(self, employee_name: str, task_name: str):

        # Get the employee, the sequence and the entering task
        employee = self._current_solution.instance.get_employee_by_name(employee_name)
        sequence = self._current_solution.get_sequence(employee)
        entering_task = self._current_solution.instance.get_task_by_name(task_name)

        # Check the employee capacity to perform the entering task
        if not employee.is_capable_of_performing(entering_task):
            explanation_text = (
                f"{employee_name} does not have enough skills to do {task_name}, {LINE_BREAK_STRING}"
                f"therefore {employee_name} can not perform {task_name}."
            )
            return ExplanationDeprecated(explanation_text)

        # Create and run the IP model for sequence reordering optimization
        model = IPModelForAlteringSequence(sequence, entering_task)
        model.optimize(mute=True)

        # Get the alterations
        alterations = model.alterations

        # Create new solution
        new_sequence = model.solution_sequence
        infeasible_solution = self._copy_current_solution_for_infeasible_solution()
        if infeasible_solution.get_task_realization(entering_task):
            infeasible_solution.remove_task(entering_task, False, False)
        infeasible_solution._replace_sequence_by_another(employee, new_sequence, False)

        # Create the explanation text
        nb_alterations = alterations.nb
        explanation_text = (
            f"In order to perform the task {task_name}, the inputs must be changed. {LINE_BREAK_STRING}"
            f"At least {nb_alterations} alteration{'s' if nb_alterations > 1 else ''} must be applied to the inputs. "
        )
        if nb_alterations == 1:
            explanation_text += (
                f"One sufficient alteration is to {alterations.enumerate()[0]}. "
            )
        else:
            explanation_text += "Sufficient alterations are:"
            for alteration_text in alterations.enumerate():
                explanation_text += f"{LINE_BREAK_STRING} - {alteration_text};"
            explanation_text = explanation_text.removesuffix(";") + "."

        # Save the infeasibility reason
        infeasibility = {
            'employee_name': employee_name,
            'task_name': task_name
        }

        # Return the explanation
        return ExplanationDeprecated(explanation_text, infeasible_solution, False, infeasibility)

    #####################################
    # Explanation computation - Request #
    #####################################

    def answer_question_about_tightening(self):
        new_solution = self._copy_current_solution_for_new_feasible_solution()
        new_solution.tighten_times()
        explanation_text = "All plannings are now tightened."
        return ExplanationDeprecated(explanation_text, new_solution, True)

    ####################################
    # Explanation computation - Moving #
    ####################################

    def answerQuestionAboutIntraMovingAfter(self, employeeName, movingTaskName, beforeInsertionActivityName):

        # Define variables
        employee = self._current_solution.instance.get_employee_by_name(employeeName)
        sequence = self._current_solution.get_sequence(employee)
        movingTask = self._current_solution.instance.get_task_by_name(movingTaskName)

        #
        print("To be completed")
        newSolution = self._current_solution.copy_deprecated(re.sub(r"_.+", "_New", self._current_solution.name))
        text = ""

        return ExplanationDeprecated(text, newSolution, solution_is_feasible=True)

    ##################################
    # Explanation computation - Swap #
    ##################################

    def answerQuestionAboutIntraSwapping(self, employeeName, firstTaskName, secondTaskName):

        # Define variables
        employee = self._current_solution.instance.get_employee_by_name(employeeName)
        sequence = self._current_solution.get_sequence(employee)
        firstTask = self._current_solution.instance.get_task_by_name(firstTaskName)
        secondTask = self._current_solution.instance.get_task_by_name(secondTaskName)

        #
        print("To be completed")
        newSolution = self._current_solution.copy_deprecated(re.sub(r"_.+", "_New", self._current_solution.name))
        text = ""

        return ExplanationDeprecated(text, newSolution, solution_is_feasible=True)
