# Standard library
from abc import abstractmethod

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.questioning.questions_templates_bank import \
    BASED_ON_MOST_RELEVANT_NEIGHBORING_SOLUTION_QUESTIONS_TEMPLATES_IDS
from src.modeling.solution import Solution
from src.explaining.questioning.question import Question, ContrastiveQuestion, ScenarioQuestion, CounterfactualQuestion
from src.explaining.answering.explanations_templates_bank import EXPLANATIONS_TEMPLATES
from src.explaining.computing.templates.infeasibility import Infeasibility, SkillInfeasibility, TimeInfeasibility
from src.utils.constants import LINE_BREAK_STRING
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY
from src.utils.time import convert_nb_minutes_to_time_string, get_hour_format_associated_with_language

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
                       all_descriptions_of_applied_transformation: dict[str, str],
                       instance_alterations: InstanceChanges = None):
    if infeasibility is None:
        if support_solution > question.solution:
            return PositiveExplanation(question, support_solution,
                                       all_descriptions_of_applied_transformation, instance_alterations)
        else:
            return NonImprovingNegativeExplanation(question, support_solution,
                                                   all_descriptions_of_applied_transformation, instance_alterations)
    else:
        if isinstance(infeasibility, SkillInfeasibility):
            return SkillNegativeExplanation(question, support_solution, infeasibility,
                                            all_descriptions_of_applied_transformation, instance_alterations)
        elif isinstance(infeasibility, TimeInfeasibility):
            return TimeNegativeExplanation(question, support_solution, infeasibility,
                                           all_descriptions_of_applied_transformation, instance_alterations)
        else:
            raise TypeError(f"There is a problem with the type of infeasibility which is {type(infeasibility)}")


def create_explanation_from_dict(dictionary, solution: Solution):
    question = Question.from_dict(dictionary[QUESTION_KEY], solution)
    support_solution = Solution.from_dict(dictionary[SUPPORT_SOLUTION_KEY], solution.instance)
    infeasibility = None
    if INFEASIBILITY_KEY in dictionary:
        infeasibility = Infeasibility.from_dict(dictionary[INFEASIBILITY_KEY], solution.instance)
    if isinstance(infeasibility, TimeInfeasibility):
        employee, task = infeasibility.conflicting_employee, infeasibility.conflicting_task
        sequence = support_solution.get_sequence(employee)
        index = sequence.get_step_index_of(task)
        if index == 1:
            departure_step = sequence[0]
            traveling_time_from_departure = \
                solution.instance.compute_traveling_duration(departure_step.activity, task)
            departure_time = \
                infeasibility.earliest_upstream_feasible_start_time_of_conflicting_task - traveling_time_from_departure
            departure_step.arrival_time, departure_step.start_time, departure_step.end_time = \
                departure_time, departure_time, departure_time
        if index == sequence.nb_steps - 2:
            return_step = sequence[-1]
            traveling_time_to_return = \
                solution.instance.compute_traveling_duration(task, return_step.activity)
            return_time = infeasibility.latest_downstream_feasible_start_time_of_conflicting_task + \
                task.duration + traveling_time_to_return
            return_step.arrival_time, return_step.start_time, return_step.end_time = \
                return_time, return_time, return_time
    all_descriptions_of_applied_transformation = dictionary[TRANSFORMATION_KEY]
    return create_explanation(question, support_solution, infeasibility, all_descriptions_of_applied_transformation)


#####################
# Class Explanation #
#####################

class Explanation:

    def __init__(self, question: Question, support_solution: Solution,
                 all_descriptions_of_applied_transformation: dict[str, str] = None,
                 instance_alterations: InstanceChanges = None):
        self._question = question
        self._support_solution = support_solution
        self._is_based_on_most_relevant_neighboring_solution = \
            question.template.id in BASED_ON_MOST_RELEVANT_NEIGHBORING_SOLUTION_QUESTIONS_TEMPLATES_IDS
        self._instance_alterations = instance_alterations
        fields_key_value_map = dict(zip(question.template.fields_keys, question.fields_values))
        fields_key_value_map['SolutionName'] = self._question.solution.name
        template = EXPLANATIONS_TEMPLATES[question.template.id]
        template.set_language(question.language)
        self._typical_expressions = dict(
            [(id, complete_expression_with_field_values(expression, fields_key_value_map))
             for (id, expression) in template.typical_expressions.items()]
        )
        self._typical_expressions['applying_support_solution_transformation'] = \
            all_descriptions_of_applied_transformation
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

    @property
    def _hour_format(self):
        return get_hour_format_associated_with_language(self.language)

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
        return self._typical_expressions['applying_support_solution_transformation'][self.language]

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

    @property
    def _assume_the_current_is_altered(self):
        if self.language_is_english:
            return f"assume that the following change" \
                   f"{'s are ' if self._instance_alterations.nb_changes > 1 else ' is '}" \
                   f"applied to the current instance: " \
                   f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}" \
                   f"{self._instance_alterations.as_string(language=self.language)}" \
                   f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"
        elif self.language_is_french:
            return f"supposons que " \
                   f"{'les changements' if self._instance_alterations.nb_changes > 1 else 'le changement'} " \
                   f"suivant{'s' if self._instance_alterations.nb_changes > 1 else ''} " \
                   f"soi{'en' if self._instance_alterations.nb_changes > 1 else ''}t " \
                   f"appliqué{'s' if self._instance_alterations.nb_changes > 1 else ''} à l'instance : " \
                   f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}" \
                   f"{self._instance_alterations.as_string(language=self.language)}" \
                   f"{LINE_BREAK_STRING if self._instance_alterations.nb_changes > 1 else ''}"

    @property
    def _Assume_the_current_is_altered(self):
        if self.language_is_english:
            return "A" + self._assume_the_current_is_altered[1:]
        elif self.language_is_french:
            return "S" + self._assume_the_current_is_altered[1:]

    @property
    def _activity(self):
        if self.language_is_english:
            if self.support_solution.instance.has_employee_unavailabilities:
                return "activity"
            else:
                return "task"
        elif self.language_is_french:
            if self.support_solution.instance.has_employee_unavailabilities:
                return "activité"
            else:
                return "tâche"
        else:
            raise NotImplementedError("Non-supported language")

    @property
    def _activities(self):
        if self.language_is_english:
            if self.support_solution.instance.has_employee_unavailabilities:
                return "activities"
            else:
                return "tasks"
        elif self.language_is_french:
            if self.support_solution.instance.has_employee_unavailabilities:
                return "activités"
            else:
                return "tâches"
        else:
            raise NotImplementedError("Non-supported language")

    @property
    def text(self):
        return self._text

    @abstractmethod
    def _compute_text(self, with_bold_emphasis: bool = False):
        pass

    def _compare_total_working_duration(self, start_with_cap: bool = False, without_new_solution: bool = False):
        if not self.support_solution_is_feasible:
            raise AttributeError("Current and new solutions cannot be compared as new solution is infeasible.")
        current_solution = self._question.solution
        new_solution = self.support_solution
        text = ""
        if self.language_is_english:
            if without_new_solution:
                text += f"{'Its' if start_with_cap else 'its'} total working duration "
            else:
                text += f"{'The' if start_with_cap else 'the'} total working duration of the new solution "
            text += f" is {new_solution.total_working_duration}min, which is "
            if new_solution.total_working_duration < current_solution.total_working_duration:
                text += "shorter than "
            elif new_solution.total_working_duration > current_solution.total_working_duration:
                text += "longer than "
            else:
                text += "equal to "
            text += f"the one of the current solution {current_solution.total_working_duration}min"
        elif self.language_is_french:
            if without_new_solution:
                text += f"{'Sa' if start_with_cap else 'sa'} durée totale de travail "
            else:
                text += f"{'La' if start_with_cap else 'la'} durée totale de travail de la nouvelle solution "
            text += f" est de {new_solution.total_working_duration}min, soit une durée "
            if new_solution.total_working_duration < current_solution.total_working_duration:
                text += "inférieure "
            elif new_solution.total_working_duration > current_solution.total_working_duration:
                text += "supérieure "
            else:
                text += "égale "
            text += f"à celle de la solution courante qui est de {current_solution.total_working_duration}min"
        return text

    def _compare_total_traveling_duration(self, start_with_cap: bool = False, without_new_solution: bool = False):
        if not self.support_solution_is_feasible:
            raise AttributeError("Current and new solutions cannot be compared as new solution is infeasible.")
        current_solution = self._question.solution
        new_solution = self.support_solution
        text = ""
        if self.language_is_english:
            if without_new_solution:
                text += f"{'Its' if start_with_cap else 'its'} total traveling duration "
            else:
                text += f"{'The' if start_with_cap else 'the'} total traveling duration of the new solution "
            text += f"is {new_solution.total_traveling_duration}min, which is "
            if new_solution.total_working_duration < current_solution.total_working_duration:
                text += "shorter than "
            elif new_solution.total_working_duration > current_solution.total_working_duration:
                text += "longer than "
            else:
                text += "equal to "
            text += f"the one of the current solution {current_solution.total_traveling_duration}min"
        elif self.language_is_french:
            if without_new_solution:
                text += f"{'Sa' if start_with_cap else 'sa'} durée totale de déplacement "
            else:
                text += f"{'La' if start_with_cap else 'la'} durée totale de déplacement de la nouvelle solution "
            text += f" est de {new_solution.total_traveling_duration}min, soit une durée "
            if new_solution.total_traveling_duration < current_solution.total_traveling_duration:
                text += "inférieure "
            elif new_solution.total_traveling_duration > current_solution.total_traveling_duration:
                text += "supérieure "
            else:
                text += "égale "
            text += f"à celle de la solution courante qui est de {current_solution.total_traveling_duration}min"
        return text

    def to_dict(self):
        dictionary = {
            QUESTION_KEY: self.question.to_dict(),
            SUPPORT_SOLUTION_KEY: self.support_solution.to_dict(with_sequences=not self.support_solution_is_feasible)
        }
        if self.applying_support_solution_transformation is not None:
            dictionary[TRANSFORMATION_KEY] = self._typical_expressions['applying_support_solution_transformation']
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
                 all_descriptions_of_applied_transformation: dict[str, str] = None,
                 instance_alterations: InstanceChanges = None):
        super().__init__(question, support_solution, infeasibility,
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


# Class TimeNegativeExplanation
class TimeNegativeExplanation(InfeasibleNegativeExplanation):

    def __init__(self, question: Question, support_solution: Solution, infeasibility: TimeInfeasibility,
                 all_descriptions_of_applied_transformation: dict[str, str] = None,
                 instance_alterations: InstanceChanges = None):
        super().__init__(question, support_solution, infeasibility,
                         all_descriptions_of_applied_transformation, instance_alterations)
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
        upstream_critical_step_index = self._upstream_critical_step_index
        if step_index == 1:
            if self.language_is_english:
                text += f"by performing {task.name} at the earliest possible time after leaving home, "
            elif self.language_is_french:
                text += f"en réalisant {task.name} le plus tôt possible après avoir quitté son domicile, "
        elif upstream_critical_step_index == 0:
            if self.language_is_english:
                text += f"by performing all the {self._activities} from home to " \
                        f"{task.name} at the earliest possible time, "
            elif self.language_is_french:
                text += f"en réalisant toutes les {self._activities} du domicile jusque " \
                        f"{task.name} le plus tôt possible, "
        elif upstream_critical_step_index == step_index - 1:
            activity_before = sequence[step_index - 1].activity
            if self.language_is_english:
                text += f"by performing {activity_before.name} and {task.name} at the earliest possible time, "
            elif self.language_is_french:
                text += f"en réalisant {activity_before.name} et {task.name} le plus tôt possible, "
        elif upstream_critical_step_index < step_index - 1:
            upstream_critical_activity = sequence[upstream_critical_step_index].activity
            if self.language_is_english:
                text += f"by performing all the {self._activities} from {upstream_critical_activity.name} to " \
                        f"{task.name} at the earliest possible time, "
            elif self.language_is_french:
                text += f"en réalisant toutes les {self._activities} de {upstream_critical_activity.name} à " \
                        f"{task.name} le plus tôt possible, "
        else:
            raise ValueError(f"There is something wrong with the upstream critical step index which value "
                             f"{upstream_critical_step_index} is larger than the one of the step index {step_index}")

        # - Part of the text about time conflict at task with upstream steps (if upstream-infeasible)
        if not self._solution_is_upstream_feasible:
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
            downstream_critical_step_index = self._downstream_critical_step_index
            downstream_critical_activity = sequence[downstream_critical_step_index].activity
            if step_index == sequence.nb_steps - 2:
                if self.language_is_english:
                    text += f"{employee.name} can then be at home by {employee.get_end_time_ub(False, hour_format)}. "
                elif self.language_is_french:
                    text += f"permettre à {employee.name} d'être de retour à son domicile " \
                            f"avant {employee.get_end_time_ub(False, hour_format)}. "
            elif downstream_critical_step_index == sequence.nb_steps - 1:
                if self.language_is_english:
                    text += f"{employee.name} can perform all the {self._activities} from {task.name} to home " \
                            f"and be back at home by {employee.get_end_time_ub(False, hour_format)}. "
                elif self.language_is_french:
                    text += f"permettre à {employee.name} de réaliser toutes les {self._activities} à partir de " \
                            f"{task.name} et d'être de retour à son domicile avant " \
                            f"{employee.get_end_time_ub(False, hour_format)}. "
            elif downstream_critical_step_index < sequence.nb_steps - 1:
                if self.language_is_english:
                    text += f"{employee.name} can perform all the {self._activities} from {task.name} " \
                            f"to {downstream_critical_activity.name} " \
                            f"and end {downstream_critical_activity.name} " \
                            f"by {downstream_critical_activity.get_end_time_ub(False, hour_format)}. "
                elif self.language_is_french:
                    text += f"permettre à {employee.name} de réaliser toutes les {self._activities} de {task.name} " \
                            f"jusque {downstream_critical_activity.name} " \
                            f"et terminer {downstream_critical_activity.name} " \
                            f"avant {downstream_critical_activity.get_end_time_ub(False, hour_format)}. "
            else:
                raise ValueError(f"There is something wrong with the downstream critical step index which value is "
                                 f"{downstream_critical_step_index} while the one of the step index is {step_index} "
                                 f"and the number of steps is {sequence.nb_steps}")

        # Fourth part - conclusion
        if self.language_is_english:
            text += f"Thus, {self._having_the_foil} is impossible."
        elif self.language_is_french:
            text += f"Ainsi, {self._having_the_foil} n'est pas faisable."
        return text
