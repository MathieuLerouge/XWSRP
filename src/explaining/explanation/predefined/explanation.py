# Standard libraries
from abc import abstractmethod
from typing import Optional

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.question.predefined.bank import \
    BASED_ON_MOST_RELEVANT_NEIGHBORING_SOLUTION_QUESTIONS_TEMPLATES_IDS
from src.modeling.solution import Solution
from src.explaining.explanation.explanation import Explanation
from src.explaining.question.predefined.question import \
    PredefinedQuestion, ContrastiveQuestion, ScenarioQuestion, CounterfactualQuestion
from src.explaining.explanation.predefined.bank import EXPLANATIONS_TEMPLATES
from src.explaining.computing.conflict import Conflict, SkillConflict, TimeConflict
from src.explaining.computing.templates.common.result import TransformationResult
from src.utils.constants import LINE_BREAK_STRING
from src.utils.time import convert_nb_minutes_to_time_string

# Global variables
QUESTION_KEY = 'question'
SUPPORT_SOLUTION_KEY = 'support solution'
TRANSFORMATION_KEY = 'transformation'
# WIP: Spelled 'infeasibility' rather than 'conflict' on purpose:
# it is the key of already-saved explanation JSON files (see data/*/explanations/),
# which renaming the classes must not invalidate.
CONFLICT_KEY = 'infeasibility'


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


def create_explanation(question: PredefinedQuestion, result: TransformationResult):
    """
    Return the explanation answering the given question, of the kind the transformation's result calls for.

    Args:
        question: The question to answer.
        result: The result of the transformation the question induced.

    Returns:
        A positive, non-improving negative, skill negative or time negative explanation.

    Raises:
        TypeError: if the result holds a conflict that is neither a SkillConflict nor a TimeConflict.
    """
    support_solution = result.support_solution
    conflict = result.conflict
    descriptions = result.descriptions
    instance_alterations = result.instance_alterations
    if conflict is None:
        if support_solution > question.solution:
            return PositiveExplanation(question, support_solution, descriptions, instance_alterations)
        else:
            return NonImprovingNegativeExplanation(question, support_solution, descriptions, instance_alterations)
    else:
        if isinstance(conflict, SkillConflict):
            return SkillNegativeExplanation(question, support_solution, conflict, descriptions, instance_alterations)
        elif isinstance(conflict, TimeConflict):
            return TimeNegativeExplanation(question, support_solution, conflict, descriptions, instance_alterations)
        else:
            raise TypeError(f"There is a problem with the type of conflict which is {type(conflict)}")


def create_explanation_from_dict(dictionary, solution: Solution):
    question = PredefinedQuestion.from_dict(dictionary[QUESTION_KEY], solution)
    support_solution = Solution.from_dict(dictionary[SUPPORT_SOLUTION_KEY], solution.instance)
    conflict = None
    if CONFLICT_KEY in dictionary:
        conflict = Conflict.from_dict(dictionary[CONFLICT_KEY], solution.instance)
    if isinstance(conflict, TimeConflict):
        employee, task = conflict.conflicting_employee, conflict.conflicting_task
        sequence = support_solution.get_sequence(employee)
        index = sequence.get_step_index_of(task)
        if index == 1:
            departure_step = sequence[0]
            traveling_time_from_departure = \
                solution.instance.compute_traveling_duration(departure_step.activity, task)
            departure_time = \
                conflict.earliest_upstream_feasible_start_time_of_conflicting_task - traveling_time_from_departure
            departure_step.arrival_time, departure_step.start_time, departure_step.end_time = \
                departure_time, departure_time, departure_time
        if index == sequence.nb_steps - 2:
            return_step = sequence[-1]
            traveling_time_to_return = \
                solution.instance.compute_traveling_duration(task, return_step.activity)
            return_time = conflict.latest_downstream_feasible_start_time_of_conflicting_task + \
                task.duration + traveling_time_to_return
            return_step.arrival_time, return_step.start_time, return_step.end_time = \
                return_time, return_time, return_time
    descriptions = dictionary[TRANSFORMATION_KEY]
    return create_explanation(question, TransformationResult(support_solution, conflict, descriptions))


#########################
# PredefinedExplanation #
#########################

class PredefinedExplanation(Explanation):
    """
    An answer to a predefined question, worded from the ExplanationTemplate matching the question's own template.

    Every sentence it can say comes from that template's typical expressions,
    with the question's field values spliced into them,
    which is what ties a question of the catalogue to the wording answering it.
    """

    def __init__(self, question: PredefinedQuestion, support_solution: Solution,
                 all_descriptions_of_applied_transformation: Optional[dict[str, str]] = None,
                 instance_alterations: Optional[InstanceChanges] = None):
        """
        Args:
            question: The predefined question being answered.
            support_solution: The solution found while answering it, backing the explanation.
            all_descriptions_of_applied_transformation: The sentence describing the transformation applied
                to reach the support solution, keyed by language, or None when no transformation was applied.
            instance_alterations: The instance parameter changes the support solution needed to become feasible,
                or None when the question called for no alteration.
        """
        self._is_based_on_most_relevant_neighboring_solution = \
            question.template.id in BASED_ON_MOST_RELEVANT_NEIGHBORING_SOLUTION_QUESTIONS_TEMPLATES_IDS
        fields_key_value_map = dict(zip(question.template.fields_keys, question.fields_values))
        fields_key_value_map['SolutionName'] = question.solution.name
        template = EXPLANATIONS_TEMPLATES[question.template.id]
        template.set_language(question.language)
        self._typical_expressions: dict[str, str] = dict(
            [(id, complete_expression_with_field_values(expression, fields_key_value_map))
             for (id, expression) in template.typical_expressions.items()]
        )
        self._typical_expressions['applying_support_solution_transformation'] = \
            all_descriptions_of_applied_transformation
        super().__init__(question, support_solution, instance_alterations)
        self._question = question

    ############
    # Question #
    ############

    @property
    def question(self) -> PredefinedQuestion:
        """The question being answered."""
        return self._question

    @property
    def is_contrastive(self) -> bool:
        """Whether the question answered is a plain contrastive one."""
        return isinstance(self._question, ContrastiveQuestion)

    @property
    def is_scenario(self) -> bool:
        """Whether the question answered is a scenario one, asked about an altered instance."""
        return isinstance(self._question, ScenarioQuestion)

    @property
    def is_counterfactual(self) -> bool:
        """Whether the question answered is a counterfactual one, asking which alterations would help."""
        return isinstance(self._question, CounterfactualQuestion)

    @property
    def is_based_on_most_relevant_neighboring_solution(self):
        """Whether the question answered leaves the pipeline free to pick the best neighboring solution."""
        return self._is_based_on_most_relevant_neighboring_solution

    #########################
    # Template expressions #
    #########################

    @property
    def applying_support_solution_transformation(self):
        """
        The sentence describing the transformation applied to reach the support solution,
        in the language the explanation is phrased in, or None when no transformation was applied.

        Raises:
            TypeError: if the descriptions come from an explanation file exported in the old format,
                which stored one already-resolved sentence rather than one per language.
            KeyError: if they carry no sentence in the explanation's own language.
        """
        descriptions = self._typical_expressions['applying_support_solution_transformation']
        if descriptions is None:
            return None
        if isinstance(descriptions, str):
            raise TypeError(
                f"The description of the applied transformation is a bare string ({descriptions!r}) "
                f"rather than one sentence per language. It comes from an explanation file exported in the old "
                f"single-language format, which has to be regenerated before the explanation can be read."
            )
        if self.language not in descriptions:
            raise KeyError(
                f"The explanation carries no {self.language} description of the applied transformation, "
                f"only {sorted(descriptions)}. It comes from an explanation file exported in a "
                f"single-language format, which has to be regenerated before the explanation can be read."
            )
        return descriptions[self.language]

    @property
    def _the_fact(self):
        """The template's wording of what the current solution does."""
        return self._typical_expressions['the_fact']

    @property
    def _the_foil(self):
        """The template's wording of what the end user expected instead."""
        return self._typical_expressions['the_foil']

    @property
    def _having_the_foil(self):
        """The template's wording of the expected situation holding."""
        return self._typical_expressions['having_the_foil']

    @property
    def _applying_the_foil_transformation(self):
        """The template's wording of the change bringing the expected situation about."""
        return self._typical_expressions['applying_the_foil_transformation']

    @property
    def _neighbors(self):
        """The template's wording of the neighboring solutions the question opens up."""
        return self._typical_expressions['neighbors']

    @property
    def _all_the_neighbors(self):
        if self.language_is_english:
            return "all the " + self._neighbors
        elif self.language_is_french:
            return "toutes les " + self._neighbors
        else:
            raise NotImplementedError("Non-supported language")

    @property
    def _all_the_feasible_neighbors(self):
        if self.language_is_english:
            return "all the feasible " + self._neighbors
        elif self.language_is_french:
            return "toutes les " + self._neighbors + " qui sont faisables"
        else:
            raise NotImplementedError("Non-supported language")

    @property
    def _none_of_the_neighbors(self):
        if self.language_is_english:
            return "none of the " + self._neighbors
        elif self.language_is_french:
            return "aucune des " + self._neighbors
        else:
            raise NotImplementedError("Non-supported language")

    @property
    def _None_of_the_neighbors(self):
        if self.language_is_english:
            return "None of the " + self._neighbors
        elif self.language_is_french:
            return "Aucune des " + self._neighbors
        else:
            raise NotImplementedError("Non-supported language")

    @property
    def _none_of_the_feasible_neighbors(self):
        if self.language_is_english:
            return "none of the feasible " + self._neighbors
        elif self.language_is_french:
            return "aucune des " + self._neighbors.replace("solutions", "solutions faisables", 1)
        else:
            raise NotImplementedError("Non-supported language")

    @property
    def _None_of_the_feasible_neighbors(self):
        if self.language_is_english:
            return "None of the feasible " + self._neighbors
        elif self.language_is_french:
            return "Aucune des " + self._neighbors.replace("solutions", "solutions faisables", 1)
        else:
            raise NotImplementedError("Non-supported language")

    def to_dict(self):
        dictionary = {
            QUESTION_KEY: self.question.to_dict(),
            SUPPORT_SOLUTION_KEY: self.support_solution.to_dict(with_sequences=not self.support_solution_is_feasible)
        }
        if self.applying_support_solution_transformation is not None:
            dictionary[TRANSFORMATION_KEY] = self._typical_expressions['applying_support_solution_transformation']
        return dictionary


#######################
# PositiveExplanation #
#######################

class PositiveExplanation(PredefinedExplanation):

    def is_positive(self):
        return True

    def is_negative(self):
        return False

    @property
    def support_solution_is_feasible(self):
        return True

    def _compute_text(self, with_bold_emphasis: bool = False):
        text = ""
        if self.is_contrastive:
            if self.language_is_english:
                text += f"Because the current solution is actually not optimal, {self._the_fact}." \
                        f"However, indeed, "
            elif self.language_is_french:
                text += f"Parce la solution n'est en fait pas optimale, {self._the_fact}." \
                        f"{LINE_BREAK_STRING}" \
                        f"Cependant, en effet, "
        elif self.is_scenario:
            if self.language_is_english:
                text += f"Thanks to the changes in the instance, "
            elif self.language_is_french:
                text += f"Grâce aux changements dans l'instance, "
        elif self.is_counterfactual:
            text += f"{self._Assume_the_current_is_altered}"
            if self.language_is_english:
                text += f"Then, "
            elif self.language_is_french:
                text += f"Alors, "
        else:
            raise ValueError("The explanation should be contrastive, scenario or counterfactual")
        if self.is_based_on_most_relevant_neighboring_solution:
            if self.language_is_english:
                text += f"{self._having_the_foil} can be observed in better solutions than the current one such as " \
                        f"the solution obtained by {self.applying_support_solution_transformation}:"
            elif self.language_is_french:
                text += f"{self._having_the_foil} peut être observé dans des solutions meilleures que la solution " \
                        f"courante telle que la solution obtenue en {self.applying_support_solution_transformation} : "
        else:
            if self.language_is_english:
                text += f"{self._having_the_foil} is possible and provides a better solution than the current one: "
            elif self.language_is_french:
                text += f"{self._having_the_foil} est possible et donne une meilleure solution " \
                        f"que la solution courante  :"
        text += f"{LINE_BREAK_STRING}" \
                f"- {self._compare_total_working_duration()};{LINE_BREAK_STRING}" \
                f"- {self._compare_total_traveling_duration()}."
        return text


#######################
# NegativeExplanation #
#######################

class NegativeExplanation(PredefinedExplanation):

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


###################################
# NonImprovingNegativeExplanation #
###################################

class NonImprovingNegativeExplanation(NegativeExplanation):

    @property
    def support_solution_is_feasible(self):
        return True

    def _compute_text(self, with_bold_emphasis: bool = False):
        text = ""
        if self.is_based_on_most_relevant_neighboring_solution:
            if self.is_contrastive:
                if self.language_is_english:
                    text += f"In the current solution, {self._the_fact} because " \
                            f"{self._none_of_the_feasible_neighbors} is better than the current solution." \
                            f"{LINE_BREAK_STRING}"
                elif self.language_is_french:
                    text += f"Dans la solution courante, {self._the_fact} car " \
                            f"{self._none_of_the_feasible_neighbors} n'est meilleure que la solution courante." \
                            f"{LINE_BREAK_STRING}"
            elif self.is_scenario:
                if self.language_is_english:
                    text += f"Despite the changes in the instance, " \
                            f"{self._having_the_foil} remains not interesting.{LINE_BREAK_STRING}"
                elif self.language_is_french:
                    text += f"Malgré les changements dans l'instance, " \
                            f"{self._having_the_foil} n'est toujours pas intéressant.{LINE_BREAK_STRING}"
            elif self.is_counterfactual:
                text += f"{self._Assume_the_current_is_altered}"
                if self.language_is_english:
                    text += f"Then, {self._having_the_foil} remains not interesting.{LINE_BREAK_STRING}"
                elif self.language_is_french:
                    text += f"Alors, {self._having_the_foil} n'est toujours pas intéressant.{LINE_BREAK_STRING}"
            else:
                raise ValueError("The explanation should be contrastive, scenario and counterfactual")
            if self.language_is_english:
                text += f"Indeed, among all these solutions, the best feasible one is obtained " \
                        f"from the current one by {self.applying_support_solution_transformation}. " \
                        f"However, this new solution is not better than the current one because "
            elif self.language_is_french:
                text += f"En effet, parmi toutes ces solutions, la meilleure solution faisable est obtenue " \
                        f"à partir de la solution courante en {self.applying_support_solution_transformation}. " \
                        f"Cependant, cette nouvelle solution n'est pas meilleure que la solution courante car "
        else:
            if self.is_contrastive:
                if self.language_is_english:
                    text += f"The reason why {self._the_fact} is that "
                elif self.language_is_french:
                    text += f"La raison pour laquelle {self._the_fact} est que "
            elif self.is_scenario:
                if self.language_is_english:
                    text += f"Despite the changes in the instance, " \
                            f"{self._having_the_foil} remains not interesting.{LINE_BREAK_STRING} " \
                            f"Indeed, "
                elif self.language_is_french:
                    text += f"Malgré les changements dans l'instance, " \
                            f"{self._having_the_foil} n'est toujours pas intéressant.{LINE_BREAK_STRING} " \
                            f"En effet, "
            elif self.is_counterfactual:
                text += f"{self._Assume_the_current_is_altered}"
                if self.language_is_english:
                    text += f"Then, {self._having_the_foil} remains not interesting.{LINE_BREAK_STRING}" \
                            f"Indeed, "
                elif self.language_is_french:
                    text += f"Alors, {self._having_the_foil} n'est toujours pas intéressant.{LINE_BREAK_STRING}" \
                            f"En effet, "
            else:
                raise ValueError("The explanation should be contrastive, scenario or counterfactual")
            if self.language_is_english:
                text += f"the new solution obtained from the current one by {self._applying_the_foil_transformation} " \
                        f"is feasible but not better than the current solution: "
            elif self.language_is_french:
                text += f"la nouvelle solution obtenue à partir de la solution courante en " \
                        f"{self._applying_the_foil_transformation} " \
                        f"est faisable mais pas meilleure que la solution courante : "
        new_solution = self._support_solution
        current_solution = self.current_solution
        if new_solution.total_working_duration < current_solution.total_working_duration:
            text += f"{self._compare_total_working_duration(False, True)}."
        elif new_solution.total_working_duration == current_solution.total_working_duration:
            if self.language_is_english:
                too_str = "too"
            elif self.language_is_french:
                too_str = "également "
            else:
                raise NotImplementedError
            text += f"{LINE_BREAK_STRING}"\
                    f"- {self._compare_total_working_duration(False, True)} {too_str};" \
                    f"{LINE_BREAK_STRING}"
            if self.language_is_english:
                text += f"- but {self._compare_total_traveling_duration(False, True)}."
            elif self.language_is_french:
                text += f"- mais {self._compare_total_traveling_duration(False, True)}."
        else:
            raise ValueError("The new solution should have a total working duration "
                             "less than or equal to the current one")
        return text


#################################
# InfeasibleNegativeExplanation #
#################################

class InfeasibleNegativeExplanation(NegativeExplanation):

    def __init__(self, question: PredefinedQuestion, support_solution: Solution, conflict: Conflict,
                 all_descriptions_of_applied_transformation: Optional[dict[str, str]] = None,
                 instance_alterations: Optional[InstanceChanges] = None):
        """
        Args:
            question: The predefined question being answered.
            support_solution: The infeasible solution found while answering it.
            conflict: The conflict making that solution infeasible.
            all_descriptions_of_applied_transformation: The sentence describing the transformation applied
                to reach the support solution, keyed by language, or None when no transformation was applied.
            instance_alterations: The instance parameter changes the support solution needed to become feasible,
                or None when the question called for no alteration.
        """
        # Set before delegating: the base class ends its own __init__ by wording the text, which reads the conflict.
        self._conflict = conflict
        super().__init__(question, support_solution, all_descriptions_of_applied_transformation, instance_alterations)

    @property
    def conflict(self):
        return self._conflict

    @property
    def support_solution_is_feasible(self):
        return False

    @property
    def _conflicting_employee(self):
        return self._conflict.conflicting_employee

    @property
    def _conflicting_task(self):
        return self._conflict.conflicting_task

    @abstractmethod
    def _compute_text(self, with_bold_emphasis: bool = False):
        pass

    def to_dict(self):
        dictionary = super().to_dict()
        dictionary[CONFLICT_KEY] = self.conflict.to_dict()
        return dictionary


############################
# SkillNegativeExplanation #
############################

class SkillNegativeExplanation(InfeasibleNegativeExplanation):

    def __init__(self, question: PredefinedQuestion, support_solution: Solution, conflict: SkillConflict,
                 all_descriptions_of_applied_transformation: Optional[dict[str, str]] = None,
                 instance_alterations: Optional[InstanceChanges] = None):
        super().__init__(question, support_solution, conflict,
                         all_descriptions_of_applied_transformation, instance_alterations)

    def _compute_text(self, with_bold_emphasis: bool = False):
        employee = self._conflicting_employee
        task = self._conflicting_task
        text = ""
        if self.is_contrastive:
            if self.language_is_english:
                text += f"In the current solution, {self._the_fact} " \
                        f"because {employee.name} is not skilled enough.{LINE_BREAK_STRING}"
            elif self.language_is_french:
                text += f"Dans la solution courante, {self._the_fact} " \
                        f"car {employee.name} n'a pas les compétences suffisantes.{LINE_BREAK_STRING}"
        elif self.is_scenario:
            if self.language_is_english:
                text += f"Despite the changes in the instance, " \
                        f"{self._having_the_foil} remains impossible " \
                        f"because {employee.name} is not skilled enough.{LINE_BREAK_STRING}"
            elif self.language_is_french:
                text += f"Malgré les changements dans l'instance, " \
                        f"{self._having_the_foil} demeure impossible " \
                        f"car {employee.name} n'a pas les compétences suffisantes.{LINE_BREAK_STRING}"
        else:
            if self.language_is_english:
                text += f"Despite all the possible changes that could be applied to the instance, " \
                        f"{self._having_the_foil} remains impossible " \
                        f"because {employee.name} is not skilled enough.{LINE_BREAK_STRING}"
            elif self.language_is_french:
                text += f"Malgré tous les changements qui pourraient être appliqués à l'instance, " \
                        f"{self._having_the_foil} demeure impossible " \
                        f"car {employee.name} n'a pas les compétences suffisantes.{LINE_BREAK_STRING}"
        if self.language_is_english:
            text += f"Indeed, {employee.name} has a skill level of {employee.skill_level} while " \
                    f"{task.name} requires a level of at least {task.skill_level}."
        elif self.language_is_french:
            text += f"En effet, {employee.name} a un niveau de compétence de {employee.skill_level} alors que " \
                    f"{task.name} requiert un niveau au moins égal à {task.skill_level}."
        return text


###########################
# TimeNegativeExplanation #
###########################

class TimeNegativeExplanation(InfeasibleNegativeExplanation):

    def __init__(self, question: PredefinedQuestion, support_solution: Solution, conflict: TimeConflict,
                 all_descriptions_of_applied_transformation: Optional[dict[str, str]] = None,
                 instance_alterations: Optional[InstanceChanges] = None):
        super().__init__(question, support_solution, conflict,
                         all_descriptions_of_applied_transformation, instance_alterations)
        self._conflict = conflict

    @property
    def _is_upstream_feasible(self):
        return self._conflict.is_upstream_feasible

    @property
    def _earliest_upstream_feasible_start_time_of_conflicting_task(self):
        return self._conflict.earliest_upstream_feasible_start_time_of_conflicting_task

    @property
    def _latest_downstream_feasible_start_time_of_conflicting_task(self):
        return self._conflict.latest_downstream_feasible_start_time_of_conflicting_task

    @property
    def _upstream_binding_step_index(self):
        return self._conflict.upstream_binding_step_index

    @property
    def _downstream_binding_step_index(self):
        return self._conflict.downstream_binding_step_index

    def _compute_text(self, with_bold_emphasis: bool = False):

        #######################
        # General explanation #
        #######################

        hour_format = self._hour_format
        new_solution = self._support_solution
        text = ""

        # First part - affirmation
        if self.is_contrastive:
            if self.language_is_english:
                text += f"In the current solution, {self._the_fact} "
                text += f"because of time constraints.{LINE_BREAK_STRING}"
            elif self.language_is_french:
                text += f"Dans la solution courante, {self._the_fact} "
                text += f"à cause des contraintes de temps.{LINE_BREAK_STRING}"
        elif self.is_scenario:
            if self.language_is_english:
                text += f"Despite the changes in the instance, " \
                        f"{self._having_the_foil} remains impossible due to time constraints." \
                        f"{LINE_BREAK_STRING}"
            elif self.language_is_french:
                text += f"Malgré les changements dans l'instance, " \
                        f"{self._having_the_foil} demeure impossible à cause des contraintes de temps." \
                        f"{LINE_BREAK_STRING}"
        else:
            if self.language_is_english:
                text += f"Despite all the possible changes that could be applied to the current instance, " \
                        f"{self._having_the_foil} remains impossible due to time constraints." \
                        f"For example, {self._assume_the_current_is_altered}" \
                        f"{LINE_BREAK_STRING}"
            elif self.language_is_french:
                text += f"Malgré tous les changements qui pourraient être appliqués à l'instance, " \
                        f"{self._having_the_foil} demeure impossible à cause des contraintes de temps." \
                        f"Par exemple, {self._assume_the_current_is_altered}" \
                        f"{LINE_BREAK_STRING}"

        # Second part - whether using support content
        if self.is_based_on_most_relevant_neighboring_solution:
            if self.language_is_english:
                text += f"{self._None_of_the_neighbors} are feasible. " \
                        f"For example, consider the new solution obtained from the current one " \
                        f"by {self.applying_support_solution_transformation}. "
            elif self.language_is_french:
                text += f"{self._None_of_the_neighbors} n'est faisable. " \
                        f"Par exemple, considérons la solution obtenue à partir de la solution courante " \
                        f"en {self.applying_support_solution_transformation}. "
        else:
            if self.language_is_english:
                text += f"Consider the new solution obtained from the current one " \
                        f"by {self._applying_the_foil_transformation}. "
            elif self.language_is_french:
                text += f"Considérons la solution obtenue à partir de la solution courante " \
                        f"en {self._applying_the_foil_transformation}. "
        if self.language_is_english:
            text += "This new solution is not feasible. "
        elif self.language_is_french:
            text += "Cette solution n'est pas faisable. "

        #############################################
        # Specific explanation of the time conflict #
        #############################################

        if self.language_is_english:
            text += "Indeed, "
        elif self.language_is_french:
            text += "En effet, "

        # - Part of the text about upstream steps
        employee = self._conflicting_employee
        sequence = new_solution.get_sequence(employee)
        task = self._conflicting_task
        step_index = sequence.get_step_index_of(task)
        upstream_binding_step_index = self._upstream_binding_step_index
        if step_index == 1:
            if self.language_is_english:
                text += f"by performing {task.name} at the earliest possible time after leaving home, "
            elif self.language_is_french:
                text += f"en réalisant {task.name} le plus tôt possible après avoir quitté son domicile, "
        elif upstream_binding_step_index == 0:
            if self.language_is_english:
                text += f"by performing all the {self._activities} from home to " \
                        f"{task.name} at the earliest possible time, "
            elif self.language_is_french:
                text += f"en réalisant toutes les {self._activities} du domicile jusque " \
                        f"{task.name} le plus tôt possible, "
        elif upstream_binding_step_index == step_index - 1:
            activity_before = sequence[step_index - 1].activity
            if self.language_is_english:
                text += f"by performing {activity_before.name} and {task.name} at the earliest possible time, "
            elif self.language_is_french:
                text += f"en réalisant {activity_before.name} et {task.name} le plus tôt possible, "
        elif upstream_binding_step_index < step_index - 1:
            upstream_binding_activity = sequence[upstream_binding_step_index].activity
            if self.language_is_english:
                text += f"by performing all the {self._activities} from {upstream_binding_activity.name} to " \
                        f"{task.name} at the earliest possible time, "
            elif self.language_is_french:
                text += f"en réalisant toutes les {self._activities} de {upstream_binding_activity.name} à " \
                        f"{task.name} le plus tôt possible, "
        else:
            raise ValueError(f"There is something wrong with the upstream binding step index which value "
                             f"{upstream_binding_step_index} is larger than the one of the step index {step_index}")

        # - Part of the text about time conflict at task with upstream steps (if upstream-infeasible)
        if not self._is_upstream_feasible:
            earliest_end_time = self._earliest_upstream_feasible_start_time_of_conflicting_task + task.duration
            earliest_end_time = convert_nb_minutes_to_time_string(earliest_end_time, hour_format)
            if self.language_is_english:
                text += f"{employee.name} can end {task.name} at the earliest at {earliest_end_time}. " \
                        f"However, {task.name} must be ended by {task.get_end_time_ub(False, hour_format)}. "
            elif self.language_is_french:
                text += f"{employee.name} peut terminer {task.name} au plus tôt à {earliest_end_time}. " \
                        f"Cependant, {task.name} doit être terminée avant {task.get_end_time_ub(False, hour_format)}. "

        # - Part of the text about time conflict at task with downstream steps (if downstream-infeasible)
        else:
            earliest_start_time = self._earliest_upstream_feasible_start_time_of_conflicting_task
            earliest_start_time = convert_nb_minutes_to_time_string(earliest_start_time, hour_format)
            latest_start_time = self._latest_downstream_feasible_start_time_of_conflicting_task
            latest_start_time = convert_nb_minutes_to_time_string(latest_start_time, hour_format)
            if self.language_is_english:
                text += f"{employee.name} can start {task.name} at the earliest at {earliest_start_time}. " \
                        f"However {task.name} must be started at the latest at {latest_start_time} so that "
            elif self.language_is_french:
                text += f"{employee.name} peut commencer {task.name} au plus tôt à {earliest_start_time}. " \
                        f"Cependant {task.name} doit être commencée au plus tard à {latest_start_time} pour "
            downstream_binding_step_index = self._downstream_binding_step_index
            downstream_binding_activity = sequence[downstream_binding_step_index].activity
            if step_index == sequence.nb_steps - 2:
                if self.language_is_english:
                    text += f"{employee.name} can then be at home by {employee.get_end_time_ub(False, hour_format)}. "
                elif self.language_is_french:
                    text += f"permettre à {employee.name} d'être de retour à son domicile " \
                            f"avant {employee.get_end_time_ub(False, hour_format)}. "
            elif downstream_binding_step_index == sequence.nb_steps - 1:
                if self.language_is_english:
                    text += f"{employee.name} can perform all the {self._activities} from {task.name} to home " \
                            f"and be back at home by {employee.get_end_time_ub(False, hour_format)}. "
                elif self.language_is_french:
                    text += f"permettre à {employee.name} de réaliser toutes les {self._activities} à partir de " \
                            f"{task.name} et d'être de retour à son domicile avant " \
                            f"{employee.get_end_time_ub(False, hour_format)}. "
            elif downstream_binding_step_index < sequence.nb_steps - 1:
                if self.language_is_english:
                    text += f"{employee.name} can perform all the {self._activities} from {task.name} " \
                            f"to {downstream_binding_activity.name} " \
                            f"and end {downstream_binding_activity.name} " \
                            f"by {downstream_binding_activity.get_end_time_ub(False, hour_format)}. "
                elif self.language_is_french:
                    text += f"permettre à {employee.name} de réaliser toutes les {self._activities} de {task.name} " \
                            f"jusque {downstream_binding_activity.name} " \
                            f"et terminer {downstream_binding_activity.name} " \
                            f"avant {downstream_binding_activity.get_end_time_ub(False, hour_format)}. "
            else:
                raise ValueError(f"There is something wrong with the downstream binding step index which value is "
                                 f"{downstream_binding_step_index} while the one of the step index is {step_index} "
                                 f"and the number of steps is {sequence.nb_steps}")

        # Fourth part - conclusion
        if self.language_is_english:
            text += f"Thus, {self._having_the_foil} is impossible."
        elif self.language_is_french:
            text += f"Ainsi, {self._having_the_foil} n'est pas faisable."
        return text
