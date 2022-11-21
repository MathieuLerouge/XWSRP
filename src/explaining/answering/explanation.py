# Standard library
from abc import abstractmethod

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.modeling.solution import Solution
from src.explaining.questioning.question import Question, ContrastiveQuestion, ScenarioQuestion, CounterfactualQuestion
from src.explaining.answering.explanations_templates_bank import EXPLANATIONS_TEMPLATES
from src.explaining.transforming.infeasibility import Infeasibility, SkillInfeasibility, TimeInfeasibility
from src.utils.constants import LINE_BREAK_STRING, LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY
from src.utils.time import convert_nb_minutes_to_time_string


# Global variables
QUESTION_KEY = 'question'
SUPPORT_SOLUTION_KEY = 'support solution'
TRANSFORMATION_KEY = 'transformation'
INFEASIBILITY_KEY = 'infeasibility'


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


def create_explanation_from_dict(dictionary, solution: Solution):
    question = Question.from_dict(dictionary[QUESTION_KEY], solution)
    support_solution = Solution.from_dict(dictionary[SUPPORT_SOLUTION_KEY], solution.instance)
    infeasibility = None
    if INFEASIBILITY_KEY in dictionary:
        infeasibility = Infeasibility.from_dict(dictionary[INFEASIBILITY_KEY], solution.instance)
    transformation_description = dictionary[TRANSFORMATION_KEY]
    return create_explanation(question, support_solution, infeasibility, transformation_description)


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
        self._instance_alterations = instance_alterations
        fields_key_value_map = dict(zip(question.template.fields_keys, question.fields_values))
        fields_key_value_map['SolutionName'] = self._question.solution.name
        template = EXPLANATIONS_TEMPLATES[question.template.id]
        template.set_language(question.language)
        self._typical_expressions = dict(
            [(id, complete_expression_with_field_values(expression, fields_key_value_map))
             for (id, expression) in template.typical_expressions.items()]
        )
        self._typical_expressions['applying_support_solution_transformation'] = description_of_applied_transformation
        self._text = self._compute_text()

    ############
    # Language #
    ############

    @property
    def language(self):
        return self._question.language

    @property
    def language_is_english(self):
        return self.language == LANGUAGE_ENGLISH_KEY

    @property
    def language_is_french(self):
        return self.language == LANGUAGE_FRENCH_KEY

    ############
    # Question #
    ############

    @property
    def question(self):
        return self._question

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
    def current_solution(self):
        return self._question.solution

    @property
    def support_solution(self):
        return self._support_solution

    @property
    def new_solution(self):
        return self.support_solution

    @property
    @abstractmethod
    def support_solution_is_feasible(self) -> bool:
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
        text = ""
        if self.language_is_english:
            text += f"{'The' if start_with_cap else 'the'} total working duration of the new solution is " \
                    f"{new_solution.total_working_duration}min while the one of the current solution is " \
                    f"{current_solution.total_working_duration}min"
        elif self.language_is_french:
            text += f"{'La' if start_with_cap else 'la'} durée totale de travail de la nouvelle solution est " \
                    f"{new_solution.total_working_duration}min tandis que celle de la solution courante est " \
                    f"{current_solution.total_working_duration}min"
        return text

    def _compare_total_traveling_duration(self, start_with_cap: bool = False):
        if not self.support_solution_is_feasible:
            raise AttributeError("Current and new solutions cannot be compared as new solution is infeasible.")
        current_solution = self._question.solution
        new_solution = self.support_solution
        text = ""
        if self.language_is_english:
            text += f"{'The' if start_with_cap else 'the'} total traveling duration of the new solution is " \
                    f"{new_solution.total_traveling_duration}min while the one of the current one is " \
                    f"{current_solution.total_traveling_duration}min"
        elif self.language_is_french:
            text += f"{'La' if start_with_cap else 'la'} durée totale de déplacement de la nouvelle solution est " \
                    f"{new_solution.total_working_duration}min tandis que celle de la solution courante est " \
                    f"{current_solution.total_working_duration}min"
        return text

    def to_dict(self):
        dictionary = {
            QUESTION_KEY: self.question.to_dict(),
            SUPPORT_SOLUTION_KEY: self.support_solution.to_dict(with_sequences=not self.support_solution_is_feasible)
        }
        if self.applying_support_solution_transformation is not None:
            dictionary[TRANSFORMATION_KEY] = self.applying_support_solution_transformation
        return dictionary


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
        text = ""
        if self.is_contrastive:
            if self.language_is_english:
                text += f"The reason for why {self._the_fact} is that the current solution is not optimal." \
                        f"{LINE_BREAK_STRING}" \
                        f"Therefore, "
            elif self.language_is_french:
                text += f"La raison pour laquelle {self._the_fact} est que la solution courante n'est pas optimale." \
                        f"{LINE_BREAK_STRING}" \
                        f"Ainsi, "
        elif self.is_scenario:
            if self.language_is_english:
                text += f"Thanks to the changes in the instance, " \
                        f"{self._having_the_foil} becomes interesting.{LINE_BREAK_STRING}" \
                        f"Indeed, "
            elif self.language_is_french:
                text += f"Grâce aux changements dans l'instance, " \
                        f"{self._having_the_foil} devient intéressant.{LINE_BREAK_STRING}" \
                        f"En effet, "
        elif self.is_counterfactual:
            if self.language_is_english:
                text += f"Assume that the following change" \
                        f"{'s are ' if self._instance_alterations.nb_changes > 1 else ' is '}" \
                        f"applied to the instance: " \
                        f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                        f"{self._instance_alterations.as_string()}"\
                        f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                        f"Then, {self._having_the_foil} becomes interesting.{LINE_BREAK_STRING}" \
                        f"Indeed, "
            elif self.language_is_french:
                text += f"Supposons que " \
                        f"{'les changements' if self._instance_alterations.nb_changes > 1 else 'le changement'} " \
                        f"suivant{'s' if self._instance_alterations.nb_changes > 1 else ''} " \
                        f"soi{'en' if self._instance_alterations.nb_changes > 1 else ''}t " \
                        f"appliqué{'s' if self._instance_alterations.nb_changes > 1 else ''} à l'instance : " \
                        f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                        f"{self._instance_alterations.as_string()}"\
                        f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                        f"Alors, {self._having_the_foil} devient intéressant.{LINE_BREAK_STRING}" \
                        f"En effet, "
        else:
            raise ValueError("The explanation should be contrastive, scenario or counterfactual")
        if self.is_based_on_most_relevant_neighboring_solution:
            if self.language_is_english:
                text += f"among {self._all_the_neighbors}, " \
                        f"a new feasible solution can be found that is better than the current one:"
            elif self.language_is_french:
                text += f"parmi {self._all_the_neighbors}, " \
                        f"une nouvelle solution réalisable peut être trouvée " \
                        f"qui est meilleure que la solution courante :"
        else:
            if self.language_is_english:
                text += f"by {self._applying_the_foil_transformation} to the current solution, " \
                        f"a new feasible solution can be found that is better than the current one:"
            elif self.language_is_french:
                text += f"en {self._applying_the_foil_transformation} à la solution courante, " \
                        f"une nouvelle solution réalisable peut être trouvée " \
                        f"qui est meilleure que la solution courante :"
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
        text = ""
        if self.is_based_on_most_relevant_neighboring_solution:
            if self.is_contrastive:
                if self.language_is_english:
                    text += f"The reason for why {self._the_fact} is that {self._all_the_feasible_neighbors} " \
                            f"are not better than the current solution.{LINE_BREAK_STRING}"
                elif self.language_is_french:
                    text += f"La raison pour laquelle {self._the_fact} est que {self._all_the_feasible_neighbors} " \
                            f"ne sont pas meilleures que la solution courante.{LINE_BREAK_STRING}"
            elif self.is_scenario:
                if self.language_is_english:
                    text += f"Despite the changes in the instance, " \
                            f"{self._having_the_foil} remains not interesting.{LINE_BREAK_STRING}"
                elif self.language_is_french:
                    text += f"Malgré les changements dans l'instance, " \
                            f"{self._having_the_foil} n'est toujours pas intéressant.{LINE_BREAK_STRING}"
            elif self.is_counterfactual:
                if self.language_is_english:
                    text += f"Assume that the following change" \
                            f"{'s are ' if self._instance_alterations.nb_changes > 1 else ' is '}" \
                            f"applied to the instance: " \
                            f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                            f"{self._instance_alterations.as_string()}"\
                            f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                            f"Then, {self._having_the_foil} remains not interesting.{LINE_BREAK_STRING}"
                elif self.language_is_french:
                    text += f"Supposons que " \
                            f"{'les changements' if self._instance_alterations.nb_changes > 1 else 'le changement'} " \
                            f"suivant{'s' if self._instance_alterations.nb_changes > 1 else ''} " \
                            f"soi{'en' if self._instance_alterations.nb_changes > 1 else ''}t " \
                            f"appliqué{'s' if self._instance_alterations.nb_changes > 1 else ''} à l'instance : " \
                            f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                            f"{self._instance_alterations.as_string()}"\
                            f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                            f"Alors, {self._having_the_foil} n'est toujours pas intéressant.{LINE_BREAK_STRING}"
            else:
                raise ValueError("The explanation should be contrastive, scenario and counterfactual")
            if self.language_is_english:
                text += f"Indeed, among {self._all_the_neighbors}, the best feasible solution is obtained " \
                        f"from the current one by {self.applying_support_solution_transformation}; " \
                        f"however this new solution is not better than the current one:"
            elif self.language_is_french:
                text += f"En effet, parmi {self._all_the_neighbors}, la meilleure solution réalisable est obtenue " \
                        f"à partir de la solution courante en {self.applying_support_solution_transformation}; " \
                        f"cependant cette nouvelle solution n'est pas meilleure que la solution courante :"
        else:
            if self.is_contrastive:
                if self.language_is_english:
                    text += f"The reason for why {self._the_fact} is that "
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
                if self.language_is_english:
                    text += f"Assume that the following change" \
                            f"{'s are ' if self._instance_alterations.nb_changes > 1 else ' is '}" \
                            f"applied to the instance: " \
                            f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                            f"{self._instance_alterations.as_string()}" \
                            f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                            f"Then, {self._having_the_foil} remains not interesting.{LINE_BREAK_STRING}" \
                            f"Indeed, "
                elif self.language_is_french:
                    text += f"Supposons que " \
                            f"{'les changements' if self._instance_alterations.nb_changes > 1 else 'le changement'} " \
                            f"suivant{'s' if self._instance_alterations.nb_changes > 1 else ''} " \
                            f"soi{'en' if self._instance_alterations.nb_changes > 1 else ''}t " \
                            f"appliqué{'s' if self._instance_alterations.nb_changes > 1 else ''} à l'instance : " \
                            f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                            f"{self._instance_alterations.as_string()}" \
                            f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"\
                            f"Alors, {self._having_the_foil} n'est toujours pas intéressant.{LINE_BREAK_STRING}" \
                            f"En effet, "
            else:
                raise ValueError("The explanation should be contrastive, scenario or couterfactual")
            if self.language_is_english:
                text += f"the new solution obtained from the current one by {self._applying_the_foil_transformation} " \
                        f"is feasible but not better than the current solution:"
            elif self.language_is_french:
                text += f"la nouvelle solution obtenue à partir de la solution courante en " \
                        f"appliquant {self._applying_the_foil_transformation} " \
                        f"est réalisable mais pas meilleure que la solution courante :"
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

    def to_dict(self):
        dictionary = super().to_dict()
        dictionary[INFEASIBILITY_KEY] = self.infeasibility.to_dict()
        return dictionary


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
            if self.language_is_english:
                text += f"The reason for why {self._the_fact} in the current solution " \
                        f"is that {employee.name} is not skilled enough.{LINE_BREAK_STRING}"
            elif self.language_is_french:
                text += f"La raison pour laquelle {self._the_fact} dans la solution courante " \
                        f"est que {employee.name} n'a pas les compétences suffisantes.{LINE_BREAK_STRING}"
        elif self.is_scenario:
            if self.language_is_english:
                text += f"Despite the changes in the instance, " \
                        f"{self._having_the_foil} remains impossible.{LINE_BREAK_STRING}"
            elif self.language_is_french:
                text += f"Malgré les changements dans l'instance, " \
                        f"{self._having_the_foil} demeure impossible.{LINE_BREAK_STRING}"
        else:
            raise ValueError("The explanation should be contrastive or scenario")
        if self.is_based_on_most_relevant_neighboring_solution:
            if self.language_is_english:
                text += f"Indeed, {self._all_the_neighbors} are not feasible. For instance, "
                text += f"consider the new solution obtained from the current one " \
                        f"by {self.applying_support_solution_transformation}. "
            elif self.language_is_french:
                text += f"En effet, {self._all_the_neighbors} ne sont pas faisable. Par exemple, "
                text += f"considérons la solution obtenue à partir de la solution courante " \
                        f"en {self.applying_support_solution_transformation}. "
        else:
            if self.language_is_english:
                text += f"Indeed, consider the new solution obtained from the current one " \
                        f"by {self._applying_the_foil_transformation}. "
            elif self.language_is_french:
                text += f"En effet, considérons la solution obtenue à partie de la solution courante " \
                        f"en {self._applying_the_foil_transformation}. "
        if self.language_is_english:
            text += f"{employee.name} has a skill level of {employee.skill_level} while " \
                    f"{task.name} has one of {task.skill_level}. " \
                    f"Therefore, this new solution is infeasible."
        elif self.language_is_french:
            text += f"{employee.name} a un niveau de compétence de {employee.skill_level} alors que " \
                    f"{task.name} en a un de {task.skill_level}. " \
                    f"Ainsi, cette nouvelle solution n'est pas faisable."
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
            if self.language_is_english:
                text += f"The reason for why {self._the_fact} "
                text += f"is that time constraints make impossible the opposite.{LINE_BREAK_STRING}"
            elif self.language_is_french:
                text += f"La raison pour laquelle {self._the_fact} "
                text += f"est que les contraintes de temps rendent le contraire impossible.{LINE_BREAK_STRING}"
        elif self.is_scenario:
            if self.language_is_english:
                text += f"Despite the changes in the instance, " \
                        f"{self._having_the_foil} remains impossible.{LINE_BREAK_STRING}"
            elif self.language_is_french:
                text += f"Malgré les changements dans l'instance, " \
                        f"{self._having_the_foil} demeure impossible.{LINE_BREAK_STRING}"
        else:
            raise ValueError("The explanation should be contrastive or scenario")
        if self.is_based_on_most_relevant_neighboring_solution:
            if self.language_is_english:
                text += f"Indeed, {self._all_the_neighbors} are not feasible. For instance, "
                text += f"consider the new solution obtained from the current one " \
                        f"by {self.applying_support_solution_transformation}. "
            elif self.language_is_french:
                text += f"En effet, {self._all_the_neighbors} ne sont pas faisables. Par exemple, "
                text += f"considérons la solution obtenue à partir de la solution courante " \
                        f"en {self.applying_support_solution_transformation}. "
        else:
            if self.language_is_english:
                text += f"Indeed, consider the new solution obtained from the current one " \
                        f"by {self._applying_the_foil_transformation}. "
            elif self.language_is_french:
                text += f"En effet, considérons la solution obtenue à partir de la solution courante " \
                        f"en {self._applying_the_foil_transformation}. "

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
            if self.language_is_english:
                text += f"By performing {task.name} at the earliest possible time after leaving home, "
            elif self.language_is_french:
                text += f"En réalisant {task.name} le plus tôt possible après avoir quitter son domicile, "
        elif upstream_critical_step_index == 0:
            if self.language_is_english:
                text += f"By performing all the activities from home to {task.name} at the earliest possible time, "
            elif self.language_is_french:
                text += f"En réalisant toutes les activités du domicile jusque {task.name} le plus tôt possible, "
        elif upstream_critical_step_index == step_index - 1:
            activity_before = sequence[step_index - 1].activity
            if self.language_is_english:
                text += f"By performing {activity_before.name} and {task.name} at the earliest possible time, "
            elif self.language_is_french:
                text += f"En réalisant {activity_before.name} et {task.name} le plus tôt possible, "
        elif upstream_critical_step_index < step_index - 1:
            upstream_critical_activity = sequence[upstream_critical_step_index].activity
            if self.language_is_english:
                text += f"By performing all the activities from {upstream_critical_activity.name} to {task.name} " \
                    f"at the earliest possible time, "
            elif self.language_is_french:
                text += f"En réalisant toutes les activités de {upstream_critical_activity.name} à {task.name} " \
                        f"le plus tôt possible, "
        else:
            raise ValueError(f"There is something wrong with the upstream critical step index which value "
                             f"{upstream_critical_step_index} is larger than the one of the step index {step_index}")

        # - Part of the text about time conflict at task with upstream steps (if upstream-infeasible)
        if not self._solution_is_upstream_feasible:
            earliest_end_time = self._earliest_upstream_feasible_start_time_of_conflicting_task + task.duration
            earliest_end_time = convert_nb_minutes_to_time_string(earliest_end_time)
            if self.language_is_english:
                text += f"{employee.name} can end {task.name} at the earliest at {earliest_end_time}, " \
                        f"while {task.name} must be ended by {task.get_end_time_UB(as_integer=False)}. "
            elif self.language_is_french:
                text += f"{employee.name} peut terminer {task.name} au plus tôt à {earliest_end_time}, " \
                        f"alors que {task.name} doit être terminé avant {task.get_end_time_UB(as_integer=False)}. "

        # - Part of the text about time conflict at task with downstream steps (if downstream-infeasible)
        else:
            earliest_start_time = self._earliest_upstream_feasible_start_time_of_conflicting_task
            earliest_start_time = convert_nb_minutes_to_time_string(earliest_start_time)
            latest_start_time = self._latest_downstream_feasible_start_time_of_conflicting_task
            latest_start_time = convert_nb_minutes_to_time_string(latest_start_time)
            if self.language_is_english:
                text += f"{employee.name} can start {task.name} at the earliest at {earliest_start_time}, " \
                        f"while {task.name} must be started at the latest at {latest_start_time} so that "
            elif self.language_is_french:
                text += f"{employee.name} peut commencer {task.name} au plus tôt à {earliest_start_time}, " \
                        f"alors que {task.name} doit être commencé au plus tard à {latest_start_time} pour "
            downstream_critical_step_index = self._downstream_critical_step_index
            downstream_critical_activity = sequence[downstream_critical_step_index].activity
            if step_index == sequence.nb_steps - 2:
                if self.language_is_english:
                    text += f"{employee.name} can then be at home by {employee.get_end_time_UB(as_integer=False)}. "
                elif self.language_is_french:
                    text += f"permettre à {employee.name} d'être de retour à son domicile " \
                            f"avant {employee.get_end_time_UB(as_integer=False)}. "
            elif downstream_critical_step_index == sequence.nb_steps - 1:
                if self.language_is_english:
                    text += f"{employee.name} can perform all the activities from {task.name} to home " \
                            f"and be at home by {employee.get_end_time_UB(as_integer=False)}. "
                elif self.language_is_french:
                    text += f"permettre à {employee.name} de réaliser toutes les activités à partir de {task.name} " \
                            f"et d'être à son domicile avant {employee.get_end_time_UB(as_integer=False)}. "
            elif downstream_critical_step_index < sequence.nb_steps - 1:
                if self.language_is_english:
                    text += f"{employee.name} can perform all the activities from {task.name} to " \
                            f"{downstream_critical_activity.name} " \
                            f"and end {downstream_critical_activity.name} " \
                            f"by {downstream_critical_activity.get_end_time_UB(as_integer=False)}. "
                elif self.language_is_french:
                    text += f"permettre à {employee.name} de réaliser toutes les activités de {task.name} jusque " \
                            f"{downstream_critical_activity.name} " \
                            f"et terminer {downstream_critical_activity.name} " \
                            f"avant {downstream_critical_activity.get_end_time_UB(as_integer=False)}. "
            else:
                raise ValueError(f"There is something wrong with the downstream critical step index which value is "
                                 f"{downstream_critical_step_index} while the one of the step index is {step_index} "
                                 f"and the number of steps is {sequence.nb_steps}")

        if self.language_is_english:
            text += "Therefore, this new solution is infeasible."
        elif self.language_is_french:
            text += "Ainsi, cette nouvelle solution n'est pas faisable."
        return text
