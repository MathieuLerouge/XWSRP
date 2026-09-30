# Standard library
from typing import TYPE_CHECKING, cast

# Local libraries
from src.explaining.computing.neighborhood.result import solve_neighborhood_into_transformation_result
from src.explaining.explanation.predefined.explanation import *
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.instance import EditableInstance
from src.explaining.modeling.solution import EditableSolution
from src.explaining.interacting.history import History
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.question.free.question import FreeTextQuestion
from src.explaining.question.question import Question
from src.explaining.question.predefined.question import (
    ContrastiveQuestion, CounterfactualQuestion, PredefinedQuestion, ScenarioQuestion
)
from src.explaining.question.predefined.bank import *
from src.explaining.importing.explanation import (
    import_single_explanation_from_json_file, import_multiple_explanations_from_json_file
)
from src.explaining.computing.templates.dispatch import TransformationDispatcher
from src.explaining.exporting.explanation import (
    define_single_contrastive_explanation_json_file_name, export_single_contrastive_explanation_to_json_file,
    define_multiple_contrastive_explanations_json_file_name, export_multiple_contrastive_explanations_to_json_file
)
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.utils.files import check_inputs_file_existence
from src.utils.language import check_if_language_is_english, check_if_language_is_french
from src.utils.constants import DEFAULT_INPUTS_DIRECTORY_RELATIVE_PATH, DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH

if TYPE_CHECKING:
    from src.explaining.neighborhood.llm.extractor import Extractor


#############
# Explainer #
#############


class Explainer:
    """
    Answers predefined and free-text questions about a solution's plan, and tracks the questioning session.

    A predefined contrastive, scenario or counterfactual question is routed through the tailored MILP-based pipeline;
    a free-text one is routed through the llm-neighborhood pipeline, which extracts and solves the induced search space.
    The explainer also tracks, across the session, which language explanations are phrased in,
    the history of instances and solutions questioned so far,
    and the already computed contrastive explanations available for reuse.
    """

    _available_question_template_ids: list[str] = [
        WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
        WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
        WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
    ]
    _available_counterfactual_questions_templates_ids: list[str] = [
        WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_3,
        WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_3,
        WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
    ]

    def __init__(self, solution: Solution, extractor_model: Optional[str] = None):
        """
        Args:
            solution: The solution every question asked of this explainer is about.
            extractor_model: The instructor model string the llm pipeline extracts a free-text question with
                ("provider/model-name", e.g. main_configuration.EXTRACTOR_MODEL).
                Left as None when only predefined questions are asked, which is what keeps the LLM backend optional.
        """
        self._language_key = LANGUAGE_ENGLISH_KEY
        self._activated_question_templates: dict[str, QuestionTemplate] = dict(
            [(template_id, QUESTIONS_TEMPLATES[template_id]) for template_id in QUESTIONS_TEMPLATES.keys()
             if template_id in self._available_question_template_ids]
        )
        self._root_solution = EditableSolution.from_solution(solution)
        # Free-text questions
        self._extractor_model: Optional[str] = extractor_model
        self._extractor: Optional["Extractor"] = None
        self._solution_the_extractor_was_built_for: Optional[EditableSolution] = None
        # History
        self._history_is_enabled = False
        self._history = History(self._root_solution)
        self._current_solution = self._root_solution
        # Contrastive explanations
        self._time_limit_for_contrastive_explanation_milp_computation: Optional[int] = None
        self._contrastive_explanation_input_directory_relative_path = DEFAULT_INPUTS_DIRECTORY_RELATIVE_PATH
        self._contrastive_explanation_output_directory_relative_path = DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
        self._automatically_exporting_single_contrastive_explanations_is_enabled = False
        self._using_already_computed_contrastive_explanations_is_enabled = False
        self._already_computed_contrastive_explanations: dict[str, dict[str, Explanation]] = dict()
        self._last_contrastive_explanation: Optional[Explanation] = None
        self._nb_contrastive_explanations_asked_by_ids: dict[str, int] = dict(
            [(template_id, 0) for template_id in self._activated_question_templates.keys()]
        )
        # Scenario explanations
        self._scenario_explanations_are_enabled = False
        self._last_scenario_explanation: Optional[Explanation] = None
        self._nb_scenario_explanations_asked_by_ids: dict[str, int] = dict(
            [(template_id, 0) for template_id in self._activated_question_templates.keys()]
        )
        # Counterfactual explanations
        self._time_limit_for_counterfactual_explanation_milp_computation: Optional[int] = None
        self._counterfactual_explanations_are_enabled = False
        self._last_counterfactual_explanation: Optional[Explanation] = None
        self._nb_counterfactual_explanations_asked_by_ids: dict[str, int] = dict(
            [(template_id, 0) for template_id in self._activated_question_templates.keys()]
        )

    ############
    # Language #
    ############

    @property
    def language(self):
        """The language key questions and explanations are currently phrased in."""
        return self._language_key

    def set_language(self, language_key: str):
        """
        Sets the language every activated question template is phrased in from now on.

        Args:
            language_key: The language key to switch to.
        """
        self._language_key = language_key
        for question_template in self._activated_question_templates.values():
            question_template.set_language(language_key)

    @language.setter
    def language(self, language_key: str):
        self.set_language(language_key)

    @property
    def language_is_english(self):
        """Whether the current language is English."""
        return check_if_language_is_english(self._language_key)

    @property
    def language_is_french(self):
        """Whether the current language is French."""
        return check_if_language_is_french(self._language_key)

    #################################
    # Current instance and solution #
    #################################

    @property
    def current_solution(self):
        """The solution the next question will be asked about."""
        return self._current_solution

    @current_solution.setter
    def current_solution(self, solution: Solution):
        if not isinstance(solution, EditableSolution):
            solution = EditableSolution.from_solution(solution)
        if solution not in self._history:
            self._history.store_solution(solution)
        self._current_solution = solution

    @property
    def current_instance(self):
        """The instance of the solution the next question will be asked about."""
        return self._current_solution.instance

    #####################
    # Question template #
    #####################

    @property
    def activated_question_templates(self) -> list[QuestionTemplate]:
        """Every question template currently activated."""
        return list(self._activated_question_templates.values())

    @property
    def activated_question_template_ids(self) -> list[str]:
        """ID of every question template currently activated."""
        return list(self._activated_question_templates.keys())

    def activate_question_template(self, question_template_id: str):
        """
        Activates the given question template, if it is one of the templates this explainer can handle.

        Args:
            question_template_id: ID of the template to activate.
        """
        if question_template_id in self._available_question_template_ids:
            question_template = QUESTIONS_TEMPLATES[question_template_id]
            question_template.set_language(self._language_key)
            self._activated_question_templates[question_template_id] = question_template

    def activate_question_templates(self, question_template_ids: list[str]):
        """
        Activates every given question template, skipping any this explainer cannot handle.

        Args:
            question_template_ids: IDs of the templates to activate.
        """
        for question_template_id in question_template_ids:
            self.activate_question_template(question_template_id)

    def activate_only_question_templates(self, question_template_ids: list[str]):
        """
        Deactivates every question template, then activates only the given ones.

        Args:
            question_template_ids: IDs of the templates to activate exclusively.
        """
        self.deactivate_all_question_templates()
        self.activate_question_templates(question_template_ids)

    def deactivate_question_template(self, question_template_id: str):
        """
        Deactivates the given question template, if it is currently activated.

        Args:
            question_template_id: Id of the template to deactivate.
        """
        if question_template_id in self._activated_question_templates.keys():
            del self._activated_question_templates[question_template_id]

    def deactivate_question_templates(self, question_template_ids: list[str]):
        """
        Deactivates every given question template, skipping any that is not currently activated.

        Args:
            question_template_ids: Ids of the templates to deactivate.
        """
        for question_template_id in question_template_ids:
            self.deactivate_question_template(question_template_id)

    def deactivate_all_question_templates(self):
        """Deactivates every question template."""
        self._activated_question_templates = dict()

    ###################
    # Question counts #
    ###################

    def _increase_asked_predefined_question_count(self, question: PredefinedQuestion):
        """
        Increases by one the asked count of the given question's template, in the count dict its kind keeps.

        Args:
            question: The predefined question that was just asked.

        Raises:
            ValueError: if the question is of a kind this explainer does not keep an asked count for.
        """
        if isinstance(question, ContrastiveQuestion):
            asked_predefined_question_counts = self._nb_contrastive_explanations_asked_by_ids
        elif isinstance(question, ScenarioQuestion):
            asked_predefined_question_counts = self._nb_scenario_explanations_asked_by_ids
        elif isinstance(question, CounterfactualQuestion):
            asked_predefined_question_counts = self._nb_counterfactual_explanations_asked_by_ids
        else:
            raise ValueError(f"Unknown question type: {type(question)}")
        asked_predefined_question_counts[question.template.id] = (
            asked_predefined_question_counts.get(question.template.id, 0) + 1
        )

    def reset_asked_predefined_question_counts(self):
        """Resets to zero the asked count of every activated question template, for every question kind."""
        self._nb_contrastive_explanations_asked_by_ids = dict(
            [(template_id, 0) for template_id in self._activated_question_templates.keys()]
        )
        self._nb_scenario_explanations_asked_by_ids = dict(
            [(template_id, 0) for template_id in self._activated_question_templates.keys()]
        )
        self._nb_counterfactual_explanations_asked_by_ids = dict(
            [(template_id, 0) for template_id in self._activated_question_templates.keys()]
        )

    def get_asked_contrastive_question_count(self, question_template_id: str):
        """
        Returns how many contrastive questions were asked of the given template, zero if none was.

        Args:
            question_template_id: Id of the template to count the questions of.

        Returns:
            The number of questions asked of it since the last reset.
        """
        return self._nb_contrastive_explanations_asked_by_ids.get(question_template_id, 0)

    ###########
    # History #
    ###########

    @property
    def history_is_enabled(self):
        """Whether every solution asked about or saved is kept, so it can be retrieved again later."""
        return self._history_is_enabled

    @property
    def history_is_disabled(self):
        """Whether history is currently disabled."""
        return not self._history_is_enabled

    def enable_history(self):
        """
        Enables history, starting a fresh copy of the root solution/instance so the root itself stays untouched.
        """
        self._history_is_enabled = True
        solution = self._root_solution.copy(name=f"{self._root_solution.name}.1.1")
        solution.instance = self._root_solution.instance.copy(name=f"{solution.instance.name}.1")
        self._history = History(solution)
        self._current_solution = solution

    def disable_history(self):
        """Disables history, resetting the current solution back to the (untouched) root one."""
        self._history_is_enabled = False
        self._history = History(self._root_solution)
        self._current_solution = self._root_solution

    @property
    def nb_instances(self):
        """How many distinct instances history currently holds."""
        return self._history.nb_instances

    @property
    def instances(self) -> list[EditableInstance]:
        """Every instance history currently holds, in no particular order."""
        return self._history.instances

    @property
    def instances_names(self) -> list[str]:
        """Name of every instance history currently holds, in no particular order."""
        return self._history.instances_names

    @property
    def solutions(self) -> list[EditableSolution]:
        """Every solution history currently holds, in no particular order."""
        return self._history.solutions

    @property
    def solutions_names(self) -> list[str]:
        """Name of every solution history currently holds, in no particular order."""
        return self._history.solutions_names

    def get_instance_by_name(self, instance_name: str):
        """
        Returns the instance of the given name.

        Args:
            instance_name: Name of the instance to retrieve.

        Returns:
            The instance stored in history under that name.
        """
        return self._history.get_instance_by_name(instance_name)

    def get_solution_by_name(self, solution_name: str):
        """
        Returns the solution of the given name.

        Args:
            solution_name: Name of the solution to retrieve.

        Returns:
            The solution stored in history under that name.
        """
        return self._history.get_solution_by_name(solution_name)

    def get_solutions_of_instance(self, instance: Instance):
        """
        Returns every solution history holds for the given instance.

        Args:
            instance: The instance to retrieve the solutions of.

        Returns:
            Every solution stored in history for that instance.
        """
        return self._history.get_solutions_of_instance(instance)

    def get_solutions_of_instance_by_name(self, instance_name: str):
        """
        Returns every solution history holds for the instance of the given name.

        Args:
            instance_name: Name of the instance to retrieve the solutions of.

        Returns:
            Every solution stored in history for that instance.
        """
        return self._history.get_solutions_of_instance_by_name(instance_name)

    def store_solution(self, solution: Solution):
        """
        Stores the given solution in history, converting it to an EditableSolution first if it is not one.

        Args:
            solution: The solution to store.

        Raises:
            PermissionError: if history is disabled.
        """
        if self._history_is_enabled:
            if not isinstance(solution, EditableSolution):
                solution = EditableSolution.from_solution(solution)
            self._history.store_solution(solution)
        else:
            raise PermissionError("Historizing is disabled")

    #############################################
    # Contrastive explanation - Import / export #
    #############################################

    @property
    def contrastive_explanation_input_directory_relative_path(self):
        """Directory already computed contrastive explanations are imported from."""
        return self._contrastive_explanation_input_directory_relative_path

    @contrastive_explanation_input_directory_relative_path.setter
    def contrastive_explanation_input_directory_relative_path(self, directory_relative_path: str):
        self._contrastive_explanation_input_directory_relative_path = directory_relative_path

    @property
    def contrastive_explanation_output_directory_relative_path(self):
        """Directory contrastive explanations are exported to."""
        return self._contrastive_explanation_output_directory_relative_path

    @contrastive_explanation_output_directory_relative_path.setter
    def contrastive_explanation_output_directory_relative_path(self, directory_relative_path: str):
        self._contrastive_explanation_output_directory_relative_path = directory_relative_path

    def enable_exporting_each_contrastive_explanation_automatically(self):
        """Enables exporting each computed contrastive explanation to its own JSON file as soon as it is computed."""
        self._automatically_exporting_single_contrastive_explanations_is_enabled = True

    def disable_exporting_each_contrastive_explanation_automatically(self):
        """Disables automatically exporting each computed contrastive explanation."""
        self._automatically_exporting_single_contrastive_explanations_is_enabled = False

    @property
    def exports_each_contrastive_explanation_automatically(self):
        """Whether each computed contrastive explanation is automatically exported to its own JSON file."""
        return self._automatically_exporting_single_contrastive_explanations_is_enabled

    def export_all_already_computed_contrastive_explanations(
            self, outputs_directory_relative_path: Optional[str] = None
    ):
        """
        Exports every explanation computed so far into one JSON file.

        Args:
            outputs_directory_relative_path: The directory to write into,
                defaulting to the one this explainer is configured with, as the single-explanation exports do.
        """
        if outputs_directory_relative_path is None:
            outputs_directory_relative_path = self.contrastive_explanation_output_directory_relative_path
        export_multiple_contrastive_explanations_to_json_file(self.already_computed_contrastive_explanations,
                                                              outputs_directory_relative_path)

    #####################################################
    # Contrastive explanation - Manage already computed #
    #####################################################

    @property
    def already_computed_contrastive_explanations(self) -> list[Explanation]:
        """Every contrastive explanation already computed and stored, across every template, in no particular order."""
        explanations = []
        for template_id in self._already_computed_contrastive_explanations.keys():
            for explanation in self._already_computed_contrastive_explanations[template_id].values():
                explanations.append(explanation)
        return explanations

    def _add_contrastive_explanation_to_already_computed_ones(self, explanation: Explanation):
        """
        Stores the given contrastive explanation among the already computed ones, if not already there.

        Args:
            explanation: The contrastive explanation to store.

        Raises:
            ValueError: if the given explanation is not contrastive.
            PermissionError: if using already computed contrastive explanations is disabled.
        """
        if not isinstance(explanation, PredefinedExplanation):
            raise ValueError("The given explanation is not predefined")
        else:
            if not explanation.is_contrastive:
                raise ValueError("The given explanation is not contrastive")
            if not self._using_already_computed_contrastive_explanations_is_enabled:
                raise PermissionError("Storing any contrastive explanation in already computed ones is not allowed "
                                      "as using already computed contrastive explanations is disabled")
            template_id = explanation.question.template.id
            if template_id not in self._already_computed_contrastive_explanations.keys():
                self._already_computed_contrastive_explanations[template_id] = dict()
            fields_values_str = str(explanation.question.fields_values)
            if fields_values_str not in self._already_computed_contrastive_explanations[template_id]:
                self._already_computed_contrastive_explanations[template_id][fields_values_str] = explanation

    def _add_contrastive_explanations_to_already_computed_ones(self, explanations: list[Explanation]):
        """
        Stores every given contrastive explanation among the already computed ones, skipping duplicates.

        Args:
            explanations: The contrastive explanations to store.
        """
        for explanation in explanations:
            self._add_contrastive_explanation_to_already_computed_ones(explanation)

    def _check_if_contrastive_explanation_is_in_already_computed_ones(self, contrastive_question: ContrastiveQuestion):
        """
        Returns whether the explanation answering the given contrastive question is already computed and stored.

        Args:
            contrastive_question: The contrastive question to check.

        Returns:
            True if an explanation for that question's template and fields values is already stored.
        """
        template_id = contrastive_question.template.id
        if template_id not in self._already_computed_contrastive_explanations.keys():
            return False
        fields_values_str = str(contrastive_question.fields_values)
        return fields_values_str in self._already_computed_contrastive_explanations[template_id]

    def _get_already_computed_contrastive_explanation(self, contrastive_question: ContrastiveQuestion):
        """
        Returns the already computed explanation answering the given contrastive question.

        Args:
            contrastive_question: The contrastive question to retrieve the stored explanation of.

        Returns:
            The explanation stored for that question's template and fields values.

        Raises:
            ValueError: if no explanation is stored for that question yet.
        """
        if not self._check_if_contrastive_explanation_is_in_already_computed_ones(contrastive_question):
            raise ValueError("Explanation associated to given question is not already computed")
        template_id, fields_values_str = contrastive_question.template.id, str(contrastive_question.fields_values)
        return self._already_computed_contrastive_explanations[template_id][fields_values_str]

    def enable_using_already_computed_contrastive_explanations(self):
        """
        Enables reusing already computed contrastive explanations, loading any already exported for this solution.
        """
        self._using_already_computed_contrastive_explanations_is_enabled = True
        multiple_explanations_json_file_name = define_multiple_contrastive_explanations_json_file_name(
            self._current_solution
        )
        if check_inputs_file_existence(
                multiple_explanations_json_file_name, self.contrastive_explanation_input_directory_relative_path
        ):
            self._add_contrastive_explanations_to_already_computed_ones(
                import_multiple_explanations_from_json_file(
                    multiple_explanations_json_file_name, self._current_solution,
                    self.contrastive_explanation_input_directory_relative_path
                )
            )

    def disable_using_already_computed_contrastive_explanations(self):
        """Disables reusing already computed contrastive explanations."""
        self._using_already_computed_contrastive_explanations_is_enabled = False

    @property
    def is_using_already_computed_contrastive_explanations(self):
        """Whether already computed contrastive explanations are reused instead of recomputed."""
        return self._using_already_computed_contrastive_explanations_is_enabled

    @is_using_already_computed_contrastive_explanations.setter
    def is_using_already_computed_contrastive_explanations(self, use: bool):
        if use:
            self.enable_using_already_computed_contrastive_explanations()
        else:
            self.disable_using_already_computed_contrastive_explanations()

    #####################################
    # Contrastive explanation - Compute #
    #####################################

    @property
    def time_limit_for_contrastive_explanation_milp_computation(self):
        """Time limit, in seconds, given to the MILP solve of a contrastive or scenario explanation, if any."""
        return self._time_limit_for_contrastive_explanation_milp_computation

    @time_limit_for_contrastive_explanation_milp_computation.setter
    def time_limit_for_contrastive_explanation_milp_computation(self, time_limit: int):
        self._time_limit_for_contrastive_explanation_milp_computation = time_limit

    def _create_contrastive_question(self, question_template_id: str, fields_values: list[str]):
        """
        Creates a contrastive question about the current solution, from the given template and fields values.

        Args:
            question_template_id: Id of the template the question instantiates.
            fields_values: Value of each of the template's fields, in the order the template declares them.

        Returns:
            The contrastive question so created.

        Raises:
            ValueError: if the given template is not handled by this explainer.
        """
        if question_template_id not in self._activated_question_templates:
            raise ValueError(f"The template {question_template_id} is not handled by this explainer")
        return ContrastiveQuestion(self._current_solution, question_template_id, fields_values)

    def _compute_contrastive_explanation(self, contrastive_question: ContrastiveQuestion):
        """
        Computes the explanation answering the given contrastive question, storing/exporting it as configured.

        Args:
            contrastive_question: The contrastive question to answer.

        Returns:
            The explanation answering it.
        """
        transformation_result = TransformationDispatcher.handle_contrastive_or_scenario_question(
            self.current_solution, contrastive_question,
            self.time_limit_for_contrastive_explanation_milp_computation
        )
        contrastive_explanation = create_explanation(contrastive_question, transformation_result)
        if self.is_using_already_computed_contrastive_explanations:
            self._add_contrastive_explanation_to_already_computed_ones(contrastive_explanation)
        if self.exports_each_contrastive_explanation_automatically:
            export_single_contrastive_explanation_to_json_file(
                contrastive_explanation, self.contrastive_explanation_output_directory_relative_path
            )
        return contrastive_explanation

    def _get_extractor(self) -> "Extractor":
        """
        Returns the Extractor turning a free-text question about the current solution into a neighborhood.

        Built on first use and rebuilt whenever the solution being questioned changes,
        since an Extractor grounds names against one solution and refuses a question asked about another.

        Returns:
            The Extractor bound to the current solution.

        Raises:
            ValueError: if this explainer was built with no extractor model, so free-text questions
                cannot be answered at all.
        """
        if self._extractor_model is None:
            raise ValueError(
                "This explainer answers predefined questions only: it was built with no extractor model, "
                "so there is no LLM backend to turn a free-text question into a neighborhood. "
                "Pass extractor_model (e.g. main_configuration.EXTRACTOR_MODEL) to its constructor."
            )
        # NB: Imported here rather than at module level so that asking predefined questions needs
        # neither the instructor package nor any LLM backend.
        from src.explaining.neighborhood.llm.extractor import Extractor
        if self._extractor is None or self._solution_the_extractor_was_built_for is not self._current_solution:
            self._extractor = Extractor(self._current_solution, self._extractor_model)
            self._solution_the_extractor_was_built_for = self._current_solution
        return cast("Extractor", self._extractor)

    def _compute_free_text_explanation(self, question: FreeTextQuestion):
        """
        Answers a free-text question through the llm-neighborhood pipeline.

        NB: the explanation is phrased from the template of the question the neighborhood is recognized as,
        not from the end user's own words, which the catalogue has no way of reproducing.
        The question is only answerable at all when the neighborhood it induces is one that catalogue covers.

        Args:
            question: The free-text question to answer, asked about the current solution.

        Returns:
            The explanation answering it.

        Raises:
            NeighborhoodExtractionError: if the question cannot be turned into a solvable neighborhood.
            NeighborhoodError: if it can, but the neighborhood matches no question template.
        """
        neighborhood = self._get_extractor().extract(question)
        try:
            recognized_question, transformation_result = solve_neighborhood_into_transformation_result(
                neighborhood, self.time_limit_for_contrastive_explanation_milp_computation
            )
        except NeighborhoodError as error:
            raise NeighborhoodError(
                f"The question {question.text!r} was understood and the search space it induces was solved, "
                f"but that space matches no question template, so no explanation can be phrased from it yet"
            ) from error
        recognized_question.set_language(self.language)
        # NB: Not counted and not cached: both are keyed by template id and field values,
        # which the question the end user actually asked has neither of.
        free_text_explanation = create_explanation(recognized_question, transformation_result)
        self._last_contrastive_explanation = free_text_explanation
        self._last_scenario_explanation = None
        self._last_counterfactual_explanation = None
        return free_text_explanation

    #################################
    # Contrastive explanation - Get #
    #################################

    def get_explanation(self, question: Question) -> Explanation:
        """
        Answers the given question, through whichever pipeline can answer it.

        A predefined contrastive question goes through the tailored pipeline, which dispatches on its template.
        A free-text one goes through the llm-neighborhood pipeline,
        which extracts the search space it induces and solves it.

        Args:
            question: The question to answer.

        Returns:
            The explanation answering it.

        Raises:
            TypeError: if the question is a scenario or counterfactual one, which are follow-ups asked through
                compute_scenario_explanation and compute_counterfactual_explanation, or of an unknown kind.
        """
        if isinstance(question, ContrastiveQuestion):
            return self._get_contrastive_explanation_of_question(question)
        if isinstance(question, FreeTextQuestion):
            return self._compute_free_text_explanation(question)
        if isinstance(question, (ScenarioQuestion, CounterfactualQuestion)):
            follow_up_method_name = (
                "compute_scenario_explanation" if isinstance(question, ScenarioQuestion)
                else "compute_counterfactual_explanation"
            )
            raise TypeError(
                f"A {type(question).__name__} is a follow-up to a contrastive question, "
                f"asked through {follow_up_method_name} rather than through get_explanation"
            )
        raise TypeError(f"Questions of type {type(question).__name__} are not handled by this explainer")

    def get_free_text_explanation(self, question_text: str) -> Explanation:
        """
        Answers a question the end user phrased themselves, about the solution currently being questioned.

        Args:
            question_text: The question as the end user typed it.

        Returns:
            The explanation answering it.
        """
        return self.get_explanation(FreeTextQuestion(self._current_solution, question_text, self.language))

    def get_contrastive_explanation(self, question_template_id: str, fields_values: list[str]):
        """
        Answers a predefined contrastive question, built from the given template and fields values.

        Args:
            question_template_id: Id of the template the question instantiates.
            fields_values: Value of each of the template's fields, in the order the template declares them.

        Returns:
            The explanation answering it.
        """
        contrastive_question = self._create_contrastive_question(question_template_id, fields_values)
        return self._get_contrastive_explanation_of_question(contrastive_question)

    def _get_contrastive_explanation_of_question(self, contrastive_question: ContrastiveQuestion):
        """
        Answers the given contrastive question, reusing an already computed explanation for it when possible.

        Reuse first checks the already-computed-explanations cache,
        then falls back to importing a previously exported single-explanation JSON file,
        before computing the explanation from scratch.

        Args:
            contrastive_question: The contrastive question to answer.

        Returns:
            The explanation answering it.
        """
        self._increase_asked_predefined_question_count(contrastive_question)
        contrastive_explanation = None
        if self.is_using_already_computed_contrastive_explanations:
            if self._check_if_contrastive_explanation_is_in_already_computed_ones(contrastive_question):
                contrastive_explanation = self._get_already_computed_contrastive_explanation(contrastive_question)
            else:
                file_name = define_single_contrastive_explanation_json_file_name(contrastive_question)
                if check_inputs_file_existence(file_name, self.contrastive_explanation_input_directory_relative_path):
                    contrastive_explanation = import_single_explanation_from_json_file(
                        file_name, contrastive_question.solution,
                        self.contrastive_explanation_input_directory_relative_path
                    )
                    self._add_contrastive_explanation_to_already_computed_ones(contrastive_explanation)
        if contrastive_explanation is None:
            contrastive_explanation = self._compute_contrastive_explanation(contrastive_question)
        self._last_contrastive_explanation = contrastive_explanation
        self._last_scenario_explanation = None
        self._last_counterfactual_explanation = None
        return contrastive_explanation

    def _get_name_for_contrastive_support_solution(self):
        """
        Builds the name of the current solution's contrastive support solution, next in line among its siblings.

        Returns:
            The name to give it, of the form "<root solution name>.<instance index>.<next solution index>".
        """
        current_instance_name = self.current_solution.instance.name
        index = current_instance_name.rindex('.')
        return (
            f"{self._root_solution.name}.{current_instance_name[(index+1):]}"
            f".{str(len(self.get_solutions_of_instance_by_name(current_instance_name)) + 1)}"
        )

    @property
    def last_contrastive_explanation(self):
        """
        The explanation answering the last contrastive question asked.

        Raises:
            PermissionError: if no contrastive question has been asked yet.
        """
        if not isinstance(self._last_contrastive_explanation, Explanation):
            raise PermissionError("There is no last contrastive explanation")
        return self._last_contrastive_explanation

    def save_last_contrastive_support_solution(self):
        """
        Stores the support solution of the last contrastive explanation in history, if it is feasible.

        Raises:
            PermissionError: if that support solution is not feasible.
        """
        last_contrastive_support_solution = self.last_contrastive_explanation.support_solution
        if self.last_contrastive_explanation.support_solution_is_feasible:
            last_contrastive_support_solution.name = self._get_name_for_contrastive_support_solution()
            self.store_solution(last_contrastive_support_solution)
        else:
            raise PermissionError("Cannot save the last contrastive support solution as it is not feasible")

    def export_last_contrastive_explanation(self):
        """Exports the last contrastive explanation to its own JSON file."""
        print(f"Exporting explanation to the question: {self.last_contrastive_explanation.question.text}")
        export_single_contrastive_explanation_to_json_file(
            self.last_contrastive_explanation, self.contrastive_explanation_output_directory_relative_path
        )

    ########################
    # Scenario explanation #
    ########################

    @property
    def scenario_explanations_are_enabled(self):
        """Whether scenario explanations (follow-ups to a contrastive question, on an altered instance) are enabled."""
        return self._scenario_explanations_are_enabled

    @property
    def scenario_explanations_are_disabled(self):
        """Whether scenario explanations are currently disabled."""
        return not self._scenario_explanations_are_enabled

    def enable_scenario_explanations(self):
        """Enables computing scenario explanations."""
        self._scenario_explanations_are_enabled = True

    def disable_scenario_explanations(self):
        """Disables computing scenario explanations."""
        self._scenario_explanations_are_enabled = False

    def _create_scenario_question(self, scenario_instance: EditableInstance):
        """
        Creates the scenario question turning the last contrastive question's instance into the given one.

        Args:
            scenario_instance: The altered instance to ask the scenario question about.

        Returns:
            The scenario question so created.

        Raises:
            PermissionError: if no contrastive question has been asked yet.
        """
        last_contrastive_question = self.last_contrastive_explanation.question
        if not isinstance(last_contrastive_question, ContrastiveQuestion):
            raise PermissionError("Cannot create a scenario question as no contrastive question has been asked yet")
        else:
            return ScenarioQuestion(last_contrastive_question, scenario_instance)

    def compute_scenario_explanation(self, scenario_instance: EditableInstance):
        """
        Answers a scenario question: how the last contrastive question's transformation fares on the given instance.

        Args:
            scenario_instance: The altered instance to ask the scenario question about.

        Returns:
            The explanation answering it.

        Raises:
            PermissionError: if scenario explanations are not enabled.
        """
        if self.scenario_explanations_are_enabled:
            scenario_question = self._create_scenario_question(scenario_instance)
            self._increase_asked_predefined_question_count(scenario_question)
            current_solution = self.current_solution
            scenario_current_solution = current_solution.copy(current_solution.name + "_scenario")
            scenario_current_solution.instance = scenario_instance
            transformation_result = TransformationDispatcher.handle_contrastive_or_scenario_question(
                scenario_current_solution, scenario_question
            )
            scenario_explanation = create_explanation(scenario_question, transformation_result)
            self._last_scenario_explanation = scenario_explanation
            return scenario_explanation
        else:
            raise PermissionError("Scenario explanations are not enabled")

    def _get_name_for_next_support_solution_instance(self):
        """
        Builds the name of the next scenario or counterfactual support solution's instance.

        Returns:
            The name to give it, of the form "<root instance name>.<next instance index>".
        """
        return f"{self._root_solution.instance.name}.{str(self.nb_instances + 1)}"

    def _get_name_for_next_support_solution(self):
        """
        Builds the name of the next scenario or counterfactual support solution.

        Returns:
            The name to give it, of the form "<root solution name>.<next instance index>.1".
        """
        return f"{self._root_solution.name}.{str(self.nb_instances + 1)}.1"

    @property
    def last_scenario_explanation(self):
        """
        The explanation answering the last scenario question asked.

        Raises:
            PermissionError: if no scenario question has been asked yet.
        """
        if not isinstance(self._last_scenario_explanation, Explanation):
            raise PermissionError("There is no last scenario explanation")
        return self._last_scenario_explanation

    def save_last_scenario_support_solution(self):
        """
        Stores the support solution of the last scenario explanation in history, if it is feasible.

        Raises:
            PermissionError: if that support solution is not feasible.
        """
        last_scenario_support_solution = self.last_scenario_explanation.support_solution
        if self.last_scenario_explanation.support_solution_is_feasible:
            last_scenario_support_solution.instance.name = self._get_name_for_next_support_solution_instance()
            last_scenario_support_solution.name = self._get_name_for_next_support_solution()
            self.store_solution(last_scenario_support_solution)
        else:
            raise PermissionError("Cannot save the last scenario support solution as it is not feasible")

    ##############################
    # Counterfactual explanation #
    ##############################

    @property
    def time_limit_for_counterfactual_explanation_milp_computation(self):
        """Time limit, in seconds, given to the MILP solve of a counterfactual explanation, if any."""
        return self._time_limit_for_counterfactual_explanation_milp_computation

    @time_limit_for_counterfactual_explanation_milp_computation.setter
    def time_limit_for_counterfactual_explanation_milp_computation(self, time_limit: int):
        self._time_limit_for_counterfactual_explanation_milp_computation = time_limit

    @property
    def activated_counterfactual_questions_templates_ids(self) -> list[str]:
        """ID of every activated question template that also supports counterfactual questions."""
        return [template_id for template_id in self.activated_question_template_ids
                if template_id in self._available_counterfactual_questions_templates_ids]

    @property
    def counterfactual_explanations_are_enabled(self):
        """Whether counterfactual explanations (which instance changes would flip an infeasibility) are enabled."""
        return self._counterfactual_explanations_are_enabled

    @property
    def counterfactual_explanations_are_disabled(self):
        """Whether counterfactual explanations are currently disabled."""
        return not self._counterfactual_explanations_are_enabled

    def enable_counterfactual_explanations(self):
        """Enables computing counterfactual explanations."""
        self._counterfactual_explanations_are_enabled = True

    def disable_counterfactual_explanations(self):
        """Disables computing counterfactual explanations."""
        self._counterfactual_explanations_are_enabled = False

    def _create_counterfactual_question(self, contrastive_question: Optional[ContrastiveQuestion] = None,
                                        instance_slacks: Optional[InstanceChanges] = None):
        """
        Creates the counterfactual question turning the given (or last asked) contrastive question around.

        Args:
            contrastive_question: The contrastive question to turn around, defaulting to the last one asked.
            instance_slacks: How far each instance parameter may be altered, or None to leave the search unbounded.

        Returns:
            The counterfactual question so created.

        Raises:
            PermissionError: if no contrastive question has been asked yet.
        """
        if contrastive_question is None:
            contrastive_question = self.last_contrastive_explanation.question
        if not isinstance(contrastive_question, ContrastiveQuestion):
            raise PermissionError("Cannot create a counterfactual question "
                                  "as no contrastive question has been asked yet")
        else:
            return CounterfactualQuestion(contrastive_question, instance_slacks)

    def compute_counterfactual_explanation(self, question_template_id: Optional[str] = None,
                                           fields_values: Optional[list[str]] = None,
                                           instance_slacks: Optional[InstanceChanges] = None):
        """
        Answers a counterfactual question: which instance changes would make the underlying question's answer differ.

        Args:
            question_template_id: Id of the template of the contrastive question to turn around, defaulting to the
                last one asked. Must be given along with fields_values, or not at all.
            fields_values: Value of each of that template's fields, in the order the template declares them.
            instance_slacks: How far each instance parameter may be altered, or None to leave the search unbounded.

        Returns:
            The explanation answering it.

        Raises:
            PermissionError: if counterfactual explanations are not enabled.
            ValueError: if exactly one of question_template_id and fields_values is given.
        """
        if self.counterfactual_explanations_are_enabled:
            if (question_template_id is None) and (fields_values is None):
                contrastive_question = None
            elif (question_template_id is not None) and (fields_values is not None):
                contrastive_question = self._create_contrastive_question(question_template_id, fields_values)
            else:
                raise ValueError("Question template id and fields values must be either both None or both not None")
            counterfactual_question = self._create_counterfactual_question(contrastive_question, instance_slacks)
            self._increase_asked_predefined_question_count(counterfactual_question)
            current_solution = self.current_solution
            counterfactual_solution = self.current_solution.copy(current_solution.name + "_counterfactual")
            transformation_result = TransformationDispatcher.handle_counterfactual_question(
                counterfactual_solution, counterfactual_question,
                self.time_limit_for_counterfactual_explanation_milp_computation
            )
            counterfactual_explanation = create_explanation(counterfactual_question, transformation_result)
            self._last_counterfactual_explanation = counterfactual_explanation
            return counterfactual_explanation
        else:
            raise PermissionError("Counterfactual explanations are not enabled")

    @property
    def last_counterfactual_explanation(self):
        """
        The explanation answering the last counterfactual question asked.

        Raises:
            PermissionError: if no counterfactual question has been asked yet.
        """
        if not isinstance(self._last_counterfactual_explanation, Explanation):
            raise PermissionError("There is no last counterfactual explanation")
        return self._last_counterfactual_explanation

    def save_last_counterfactual_support_solution(self):
        """
        Stores the support solution of the last counterfactual explanation in history, if it is feasible.

        Raises:
            PermissionError: if that support solution is not feasible.
        """
        last_counterfactual_support_solution = self.last_counterfactual_explanation.support_solution
        if self.last_counterfactual_explanation.support_solution_is_feasible:
            last_counterfactual_support_solution.instance.name = self._get_name_for_next_support_solution_instance()
            last_counterfactual_support_solution.name = self._get_name_for_next_support_solution()
            self.store_solution(last_counterfactual_support_solution)
        else:
            raise PermissionError("Cannot save the last counterfactual support solution as it is not feasible")
