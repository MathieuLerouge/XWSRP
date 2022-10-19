# Standard library
from abc import abstractmethod

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.modeling.solution import Solution
from src.explaining.questioning.question import Question, ContrastiveQuestion, ScenarioQuestion, CounterfactualQuestion
from src.explaining.answering.explanations_templates_bank import EXPLANATIONS_TEMPLATES
from src.explaining.transforming.infeasibility import Infeasibility, SkillInfeasibility, TimeInfeasibility
from src.utils.constants import LINE_BREAK_STRING
from src.utils.time import convert_nb_minutes_to_time_string


####################
# Global functions #
####################


def complete_expression_with_field_values(expression: str, fields_key_value_map: dict[str, str]):
    for key, value in fields_key_value_map.items():
        if key in expression:
            expression = expression.replace(key, value)
    return expression


def emphasize(text: str, make_bold: bool = False):
    if make_bold:
        return f"<b>{text}</b>"
    else:
        return text


def create_explanation(question: Question, support_solution: Solution, infeasibility: Infeasibility,
                       description_of_applied_transformation: str, instance_alterations: InstanceChanges = None):
    if infeasibility is None:
        if support_solution > question.solution:
            return PositiveExplanation(question, support_solution,
                                       description_of_applied_transformation, instance_alterations)
        else:
            return NonImprovingNegativeExplanation(question, support_solution,
                                                   description_of_applied_transformation, instance_alterations)
    else:
        if isinstance(infeasibility, SkillInfeasibility):
            return SkillNegativeExplanation(question, support_solution, infeasibility,
                                            description_of_applied_transformation, instance_alterations)
        elif isinstance(infeasibility, TimeInfeasibility):
            return TimeNegativeExplanation(question, support_solution, infeasibility,
                                           description_of_applied_transformation, instance_alterations)
        else:
            raise TypeError(f"There is a problem with the type of infeasibility which is {type(infeasibility)}")


###############
# Explanation #
###############


# Class Explanation
class Explanation:

    def __init__(self, question: Question, support_solution: Solution,
                 description_of_applied_transformation: str = None, instance_alterations: InstanceChanges = None):
        self._question = question
        self._support_solution = support_solution
        self._is_based_on_most_relevant_neighboring_solution = (question.template.id[-1] != '1')
        fields_key_value_map = dict(zip(question.template.fields_keys, question.fields_values))
        fields_key_value_map['SolutionName'] = self._question.solution.name
        template = EXPLANATIONS_TEMPLATES[question.template.id]
        self._typical_expressions = dict(
            [(id, complete_expression_with_field_values(expression, fields_key_value_map))
             for (id, expression) in template.typical_expressions.items()]
        )
        self._typical_expressions['applying_support_solution_transformation'] = description_of_applied_transformation
        self._instance_alterations = instance_alterations
        self._text = self._compute_text()

    @property
    def is_contrastive(self):
        return isinstance(self._question, ContrastiveQuestion)

    @property
    def is_scenario(self):
        return isinstance(self._question, ScenarioQuestion)

    @property
    def is_counterfactual(self):
        return isinstance(self._question, CounterfactualQuestion)

    @abstractmethod
    def is_positive(self):
        pass

    @abstractmethod
    def is_negative(self):
        pass

    @property
    def question(self):
        return self._question

    @property
    def current_solution(self):
        return self._question.solution

    @property
    def solution(self):
        print("explanation.solution is deprecated!")
        return self._support_solution

    @property
    def support_solution(self):
        return self._support_solution

    @property
    def new_solution(self):
        return self.support_solution

    @property
    @abstractmethod
    def support_solution_is_feasible(self):
        pass

    @property
    def is_based_on_most_relevant_neighboring_solution(self):
        return self._is_based_on_most_relevant_neighboring_solution

    @property
    def applying_support_solution_transformation(self):
        return self._typical_expressions['applying_support_solution_transformation']

    @property
    def _the_fact(self):
        return self._typical_expressions['the_fact']

    @property
    def _the_foil(self):
        return self._typical_expressions['the_foil']

    @property
    def _having_the_foil(self):
        return self._typical_expressions['having_the_foil']

    @property
    def _applying_the_foil_transformation(self):
        return self._typical_expressions['applying_the_foil_transformation']

    @property
    def _neighbors(self):
        return self._typical_expressions['neighbors']

    @property
    def _all_the_neighbors(self):
        return "all the " + self._neighbors

    @property
    def _all_the_feasible_neighbors(self):
        return "all the feasible " + self._neighbors

    @property
    def text(self):
        return self._text

    @abstractmethod
    def _compute_text(self, with_bold_emphasis: bool = False):
        pass

    def _compare_total_working_duration(self, start_with_cap: bool = False):
        if not self.support_solution_is_feasible:
            raise AttributeError("Current and new solutions cannot be compared as new solution is infeasible.")
        current_solution = self._question.solution
        new_solution = self.support_solution
        # text = f"{'The' if start_with_cap else 'the'} total working duration of {new_solution.name} is " \
        #        f"{new_solution.total_working_duration}min " \
        #        f"while the one of {current_solution.name} is " \
        #        f"{current_solution.total_working_duration}min"
        text = f"{'The' if start_with_cap else 'the'} total working duration of the new solution is " \
               f"{new_solution.total_working_duration}min while the one of the current solution is " \
               f"{current_solution.total_working_duration}min"
        return text

    def _compare_total_traveling_duration(self, start_with_cap: bool = False):
        if not self.support_solution_is_feasible:
            raise AttributeError("Current and new solutions cannot be compared as new solution is infeasible.")
        current_solution = self._question.solution
        new_solution = self.support_solution
        # text = f"{'The' if start_with_cap else 'the'} total traveling duration of the {new_solution.name} is " \
        #        f"{new_solution.total_traveling_duration}min while the one of {current_solution.name} is " \
        #        f"{current_solution.total_traveling_duration}min"
        text = f"{'The' if start_with_cap else 'the'} total traveling duration of the new solution is " \
               f"{new_solution.total_traveling_duration}min while the one of the current one is " \
               f"{current_solution.total_traveling_duration}min"
        return text


########################
# Positive Explanation #
########################


# Class PositiveExplanation
class PositiveExplanation(Explanation):

    def is_positive(self):
        return True

    def is_negative(self):
        return False

    @property
    def support_solution_is_feasible(self):
        return True

    def _compute_text(self, with_bold_emphasis: bool = False):
        # current_solution = self._question.solution
        # new_solution = self._support_solution
        text = ""
        if self.is_contrastive:
            # text = f"The reason for why {self._the_fact} in the current solution {current_solution.name} " \
            #        f"is that this solution is not optimal.{LINE_BREAK_STRING}"
            text += f"The reason for why {self._the_fact} is that the current solution is not optimal." \
                    f"{LINE_BREAK_STRING}" \
                    f"Therefore, "
        elif self.is_scenario:
            text += f"Thanks to the changes in the instance, " \
                    f"{self._having_the_foil} becomes interesting.{LINE_BREAK_STRING}" \
                    f"Indeed, "
        elif self.is_counterfactual:
            text += f"Assume that the following change" \
                    f"{'s are ' if self._instance_alterations.nb_changes > 1 else ' is '}" \
                    f"applied to the instance: " \
                    f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                    f"{self._instance_alterations.as_string()}"\
                    f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                    f"Then, {self._having_the_foil} becomes interesting.{LINE_BREAK_STRING}" \
                    f"Indeed, "
        else:
            raise ValueError("The explanation should be contrastive, scenario or counterfactual")
        if self.is_based_on_most_relevant_neighboring_solution:
            # text += f"Indeed, among {self._all_the_neighbors}, " \
            #         f"the best feasible solution, which we call {new_solution.name}, " \
            #         f"is better than {current_solution.name}:{LINE_BREAK_STRING}"
            text += f"among {self._all_the_neighbors}, " \
                    f"a new feasible solution can be found that is better than the current one:"
        else:
            # text += f"Indeed, by {self._applying_the_foil_transformation} to {current_solution.name}, " \
            #         f"the resulting solution, which we call {new_solution.name}, " \
            #         f"is feasible and better than {current_solution.name}:{LINE_BREAK_STRING}"
            text += f"by {self._applying_the_foil_transformation} to the current solution, " \
                    f"a new feasible solution can be found that is better than the current one:"
        text += f"{LINE_BREAK_STRING}" \
                f"- {self._compare_total_working_duration()};{LINE_BREAK_STRING}" \
                f"- {self._compare_total_traveling_duration()}."
        return text


########################
# Negative Explanation #
########################


# Class NegativeExplanation
class NegativeExplanation(Explanation):

    def is_positive(self):
        return False

    def is_negative(self):
        return True

    @property
    @abstractmethod
    def support_solution_is_feasible(self):
        pass

    @abstractmethod
    def _compute_text(self, with_bold_emphasis: bool = False):
        pass


# Class NonImprovingNegativeExplanation
class NonImprovingNegativeExplanation(NegativeExplanation):

    @property
    def support_solution_is_feasible(self):
        return True

    def _compute_text(self, with_bold_emphasis: bool = False):
        # current_solution = self._question.solution
        # new_solution = self._support_solution
        text = ""
        if self.is_based_on_most_relevant_neighboring_solution:
            # text = f"The reason for why {self._the_fact} in the solution {current_solution.name} " \
            #        f"is that {self._all_the_feasible_neighbors} are not better than this solution." \
            #        f"{LINE_BREAK_STRING}" \
            #        f"Indeed, among {self._all_the_neighbors}, " \
            #        f"the best feasible solution, which we call {new_solution.name}, " \
            #        f"is better than {current_solution.name}:"
            if self.is_contrastive:
                text += f"The reason for why {self._the_fact} is that {self._all_the_feasible_neighbors} " \
                        f"are not better than the current solution.{LINE_BREAK_STRING}"
            elif self.is_scenario:
                text += f"Despite the changes in the instance, " \
                        f"{self._having_the_foil} remains not interesting.{LINE_BREAK_STRING}"
            elif self.is_counterfactual:
                text += f"Assume that the following change" \
                        f"{'s are ' if self._instance_alterations.nb_changes > 1 else ' is '}" \
                        f"applied to the instance: " \
                        f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                        f"{self._instance_alterations.as_string()}"\
                        f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                        f"Then, {self._having_the_foil} remains not interesting.{LINE_BREAK_STRING}"
            else:
                raise ValueError("The explanation should be contrastive, scenario and counterfactual")
            text += f"Indeed, among {self._all_the_neighbors}, the best feasible solution is obtained " \
                    f"from the current one by {self.applying_support_solution_transformation}; " \
                    f"however this new solution is not better than the current one:"
        else:
            # text = f"The reason for why {self._the_fact} in the solution {current_solution.name} "\
            #        f"is that, by {self._applying_the_foil_transformation} to {current_solution.name}, " \
            #        f"the resulting solution, which we call {new_solution.name}, " \
            #        f"is feasible but not better than {current_solution.name}:"
            if self.is_contrastive:
                text += f"The reason for why {self._the_fact} is that "
            elif self.is_scenario:
                text += f"Despite the changes in the instance, " \
                        f"{self._having_the_foil} remains not interesting.{LINE_BREAK_STRING} " \
                        f"Indeed, "
            elif self.is_counterfactual:
                text += f"Assume that the following change" \
                        f"{'s are ' if self._instance_alterations.nb_changes > 1 else ' is '}" \
                        f"applied to the instance: " \
                        f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                        f"{self._instance_alterations.as_string()}" \
                        f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                        f"Then, {self._having_the_foil} remains not interesting.{LINE_BREAK_STRING}" \
                        f"Indeed, "
            else:
                raise ValueError("The explanation should be contrastive, scenario or couterfactual")
            text += f"the new solution obtained from the current one by {self._applying_the_foil_transformation} " \
                    f"is feasible but not better than the current solution:"
        text += f"{LINE_BREAK_STRING}" \
                f"- {self._compare_total_working_duration()};{LINE_BREAK_STRING}" \
                f"- {self._compare_total_traveling_duration()}."
        return text


# Class InfeasibleNegativeExplanation
class InfeasibleNegativeExplanation(NegativeExplanation):

    def __init__(self, question: Question, support_solution: Solution, infeasibility: Infeasibility,
                 description_of_applied_transformation: str = None, instance_alterations: InstanceChanges = None):
        self._infeasibility = infeasibility
        super().__init__(question, support_solution, description_of_applied_transformation, instance_alterations)

    @property
    def infeasibility(self):
        return self._infeasibility

    @property
    def support_solution_is_feasible(self):
        return False

    @property
    def _conflicting_employee(self):
        return self._infeasibility.conflicting_employee

    @property
    def _conflicting_task(self):
        return self._infeasibility.conflicting_task

    @abstractmethod
    def _compute_text(self, with_bold_emphasis: bool = False):
        pass


# Class SkillNegativeExplanation
class SkillNegativeExplanation(InfeasibleNegativeExplanation):

    def __init__(self, question: Question, support_solution: Solution, infeasibility: SkillInfeasibility,
                 description_of_applied_transformation: str = None, instance_alterations: InstanceChanges = None):
        super().__init__(question, support_solution, infeasibility,
                         description_of_applied_transformation, instance_alterations)

    def _compute_text(self, with_bold_emphasis: bool = False):
        employee = self._conflicting_employee
        task = self._conflicting_task
        text = ""
        if self.is_contrastive:
            # text += f"The reason for why {self._the_fact} in the current solution {self.current_solution.name} " \
            #        f"is that {employee.name} is not skilled enough for performing {task.name}: "
            # OR
            text += f"The reason for why {self._the_fact} in the current solution " \
                    f"is that {employee.name} is not skilled enough.{LINE_BREAK_STRING}"
        elif self.is_scenario:
            text += f"Despite the changes in the instance, " \
                    f"{self._having_the_foil} remains impossible.{LINE_BREAK_STRING}"
        else:
            raise ValueError("The explanation should be contrastive or scenario")
        if self.is_based_on_most_relevant_neighboring_solution:
            text += f"Indeed, {self._all_the_neighbors} are not feasible. For instance, "
            # text += f"let {self.new_solution.name} be the solution that is the nearest to be feasible. "
            # OR
            text += f"consider the new solution obtained from the current one " \
                    f"by {self.applying_support_solution_transformation}. "
        else:
            text += f"Indeed, consider the new solution obtained from the current one " \
                    f"by {self._applying_the_foil_transformation}. "
        text += f"{employee.name} has a skill level of {employee.skill_level} while " \
                f"{task.name} has one of {task.skill_level}. " \
                f"Therefore, this new solution is infeasible."
        return text


# Class TimeNegativeExplanation
class TimeNegativeExplanation(InfeasibleNegativeExplanation):

    def __init__(self, question: Question, support_solution: Solution, infeasibility: TimeInfeasibility,
                 description_of_applied_transformation: str = None, instance_alterations: InstanceChanges = None):
        super().__init__(question, support_solution, infeasibility,
                         description_of_applied_transformation, instance_alterations)
        self._infeasibility = infeasibility

    @property
    def _solution_is_upstream_feasible(self):
        return self._infeasibility.solution_is_upstream_feasible

    @property
    def _earliest_upstream_feasible_start_time_of_conflicting_task(self):
        return self._infeasibility.earliest_upstream_feasible_start_time_of_conflicting_task

    @property
    def _latest_downstream_feasible_start_time_of_conflicting_task(self):
        return self._infeasibility.latest_downstream_feasible_start_time_of_conflicting_task

    @property
    def _upstream_critical_step_index(self):
        return self._infeasibility.upstream_critical_step_index

    @property
    def _downstream_critical_step_index(self):
        return self._infeasibility.downstream_critical_step_index

    def _compute_text(self, with_bold_emphasis: bool = False):

        #######################
        # General explanation #
        #######################

        new_solution = self._support_solution
        text = ""
        if self.is_contrastive:
            text += f"The reason for why {self._the_fact} "
            # text += f"in the current solution {self.current_solution.name} "
            text += f"is that time constraints make impossible the opposite.{LINE_BREAK_STRING}"
        elif self.is_scenario:
            text += f"Despite the changes in the instance, " \
                    f"{self._having_the_foil} remains impossible.{LINE_BREAK_STRING}"
        else:
            raise ValueError("The explanation should be contrastive or scenario")
        if self.is_based_on_most_relevant_neighboring_solution:
            text += f"Indeed, {self._all_the_neighbors} are not feasible. For instance, "
            # text += f"let {self.new_solution.name} be the solution that is the nearest to be feasible. "
            # OR
            text += f"consider the new solution obtained from the current one " \
                    f"by {self.applying_support_solution_transformation}. "
        else:
            # text += f"Indeed, let {new_solution.name} be a new solution obtained " \
            #         f"from the current one {current_solution.name} " \
            #         f"by {self._applying_the_foil_transformation}. "
            # OR
            text += f"Indeed, consider the new solution obtained from the current one " \
                    f"by {self._applying_the_foil_transformation}. "

        #############################################
        # Specific explanation of the time conflict #
        #############################################

        # - Part of the text about upstream steps
        employee = self._conflicting_employee
        sequence = new_solution.get_sequence(employee)
        task = self._conflicting_task
        step_index = sequence.get_step_index_of(task)
        upstream_critical_step_index = self._upstream_critical_step_index
        if step_index == 1:
            text += f"By performing {task.name} at the earliest possible time after leaving home, "
        elif upstream_critical_step_index == 0:
            text += f"By performing all the activities from home to {task.name} at the earliest possible time, "
        elif upstream_critical_step_index == step_index - 1:
            activity_before = sequence[step_index - 1].activity
            text += f"By performing {activity_before.name} and {task.name} at the earliest possible time, "
        elif upstream_critical_step_index < step_index - 1:
            upstream_critical_activity = sequence[upstream_critical_step_index].activity
            text += f"By performing all the activities from {upstream_critical_activity.name} to {task.name} " \
                    f"at the earliest possible time, "
        else:
            raise ValueError(f"There is something wrong with the upstream critical step index which value "
                             f"{upstream_critical_step_index} is larger than the one of the step index {step_index}")

        # - Part of the text about time conflict at task with upstream steps (if upstream-infeasible)
        if not self._solution_is_upstream_feasible:
            earliest_end_time = self._earliest_upstream_feasible_start_time_of_conflicting_task + task.duration
            earliest_end_time = convert_nb_minutes_to_time_string(earliest_end_time)
            text += f"{employee.name} can end {task.name} at the earliest at {earliest_end_time}, " \
                    f"while {task.name} must be ended by {task.get_end_time_UB(as_integer=False)}. "

        # - Part of the text about time conflict at task with downstream steps (if downstream-infeasible)
        else:
            earliest_start_time = self._earliest_upstream_feasible_start_time_of_conflicting_task
            earliest_start_time = convert_nb_minutes_to_time_string(earliest_start_time)
            latest_start_time = self._latest_downstream_feasible_start_time_of_conflicting_task
            latest_start_time = convert_nb_minutes_to_time_string(latest_start_time)
            text += f"{employee.name} can start {task.name} at the earliest at {earliest_start_time}, " \
                    f"while {task.name} must be started at the latest at {latest_start_time} so that "
            downstream_critical_step_index = self._downstream_critical_step_index
            downstream_critical_activity = sequence[downstream_critical_step_index].activity
            if step_index == sequence.nb_steps - 2:
                text += f"{employee.name} can then be at home by {employee.get_end_time_UB(as_integer=False)}. "
            elif downstream_critical_step_index == sequence.nb_steps - 1:
                text += f"{employee.name} can perform all the activities from {task.name} to home " \
                        f"and be at home by {employee.get_end_time_UB(as_integer=False)}. "
            elif downstream_critical_step_index < sequence.nb_steps - 1:
                text += f"{employee.name} can perform all the activities from {task.name} to " \
                        f"{downstream_critical_activity.name} " \
                        f"and end {downstream_critical_activity.name} " \
                        f"by {downstream_critical_activity.get_end_time_UB(as_integer=False)}. "
            else:
                raise ValueError(f"There is something wrong with the downstream critical step index which value is "
                                 f"{downstream_critical_step_index} while the one of the step index is {step_index} "
                                 f"and the number of steps is {sequence.nb_steps}")

        # text += f"Therefore, the new solution {new_solution.name} is infeasible."
        # OR
        text += "Therefore, this new solution is infeasible."
        return text
