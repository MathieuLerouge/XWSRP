# Standard library
import time
from typing import TYPE_CHECKING, cast

# Local libraries
from src.explaining.computing.bridge.result import solve_neighborhood_into_transformation_result
from src.explaining.computing.neighborhood.facts import ExplanationFactsBuilder, ExplanationOutcomes
from src.explaining.computing.neighborhood.solving import solve_neighborhood
from src.explaining.explanation.explanation import ExplanationComputationModes
from src.explaining.explanation.predefined.explanation import *
from src.explaining.interacting.configuration import FreeTextExplanationModes, Pipelines, TemplateComputationModes
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.instance import EditableInstance
from src.explaining.modeling.solution import EditableSolution
from src.explaining.neighborhood.bridge.mapper import Mapper
from src.explaining.interacting.configuration import ExplainerConfiguration
from src.explaining.interacting.counter import ExplanationCounter
from src.explaining.interacting.history import History
from src.explaining.neighborhood.exceptions import NeighborhoodError
from src.explaining.neighborhood.neighborhood import Neighborhood, NeighborhoodExtractionModes
from src.explaining.question.free.question import FreeTextQuestion
from src.explaining.question.question import Question
from src.explaining.question.predefined.question import ContrastiveQuestion, CounterfactualQuestion, ScenarioQuestion
from src.explaining.question.predefined.bank import *
from src.explaining.importing.explanation import (
    import_single_explanation_from_json_file, import_multiple_explanations_from_json_file
)
from src.explaining.computing.templates.dispatch import TransformationDispatcher
from src.explaining.exporting.explanation import (
    define_single_contrastive_explanation_json_file_name, export_single_contrastive_explanation_to_json_file,
    define_multiple_contrastive_explanations_json_file_name, export_multiple_contrastive_explanations_to_json_file
)
from src.modeling.solution import Solution
from src.utils.files import check_inputs_file_existence
from src.utils.language import check_if_language_is_english, check_if_language_is_french
from src.utils.progress import ProgressReporter

# Library for type checking only (to avoid circular imports)
if TYPE_CHECKING:
    from src.explaining.explanation.free.writer import ExplanationWriter
    from src.explaining.neighborhood.llm.extractor import Extractor


#############
# Explainer #
#############


class Explainer:
    """
    Answers predefined and free-text questions about a solution's plan, and tracks the questioning session.

    A predefined contrastive, scenario or counterfactual question is routed through the tailored MILP-based pipeline;
    a free-text one is routed through the llm-neighborhood pipeline, which extracts and solves the induced search space,
    then has an LLM word the facts of the solution found
    (or, when the configuration says free-text questions are template equivalents,
    phrases the predefined explanation of the template recognized from that search space).
    The explainer also tracks, across the session, which language explanations are phrased in,
    the history of instances and solutions questioned so far,
    and the cached contrastive explanations available for reuse.
    """

    def __init__(self, solution: Solution, configuration: Optional[ExplainerConfiguration] = None):
        """
        Args:
            solution: The solution every question asked of this explainer is about.
            configuration: The construction-time settings to build this explainer with,
                defaulting to ExplainerConfiguration()'s own defaults (every optional behaviour off) when not given.
        """
        # Configuration
        self._configuration = configuration if configuration is not None else ExplainerConfiguration()
        # NB: Reports nothing until an interface asks to follow the computation steps (see progress_reporter).
        self._progress_reporter = ProgressReporter()
        # Free-text questions
        self._extractor: Optional["Extractor"] = None
        self._solution_the_extractor_was_built_for: Optional[EditableSolution] = None
        self._writer: Optional["ExplanationWriter"] = None
        # Predefined questions
        self._activated_question_templates: dict[str, QuestionTemplate] = dict(
            [(template_id, QUESTIONS_TEMPLATES[template_id])
             for template_id in self._configuration.activated_question_template_ids]
        )
        self._explanation_counter = ExplanationCounter(list(self._activated_question_templates.keys()))
        self.language = self._configuration.language
        # History
        self._root_solution = EditableSolution.from_solution(solution)
        self._history = History(self._root_solution)
        self._current_solution = self._root_solution
        if self._configuration.history_enabled:
            self._enable_history()
        # Contrastive explanations
        self._last_contrastive_explanation: Optional[Explanation] = None
        self._last_contrastive_explanation_was_reused = False
        self._last_scenario_explanation: Optional[Explanation] = None
        self._last_counterfactual_explanation: Optional[Explanation] = None
        self._cached_contrastive_explanations: dict[str, dict[str, Explanation]] = dict()
        if self._configuration.using_cached_contrastive_explanations_enabled:
            self._enable_using_cached_contrastive_explanations()

    #################
    # Configuration #
    #################

    @property
    def configuration(self) -> ExplainerConfiguration:
        """The construction-time settings this explainer was built with."""
        return self._configuration

    ############
    # Progress #
    ############

    @property
    def progress_reporter(self) -> ProgressReporter:
        """What each step of computing an explanation is reported to as it runs."""
        return self._progress_reporter

    @progress_reporter.setter
    def progress_reporter(self, progress_reporter: ProgressReporter):
        """
        Set what each step of computing an explanation is reported to as it runs.

        Args:
            progress_reporter: The reporter, e.g. a ProgressReporter itself to report nothing.
        """
        self._progress_reporter = progress_reporter

    ############
    # Language #
    ############

    @property
    def language(self):
        """The language key questions and explanations are currently phrased in."""
        return self._configuration.language

    @language.setter
    def language(self, language_key: str):
        """
        Sets the language every activated question template is phrased in from now on.

        Args:
            language_key: The language key to switch to.
        """
        self._configuration.language = language_key
        for question_template in self._activated_question_templates.values():
            question_template.set_language(language_key)

    @property
    def language_is_english(self):
        """Whether the current language is English."""
        return check_if_language_is_english(self._configuration.language)

    @property
    def language_is_french(self):
        """Whether the current language is French."""
        return check_if_language_is_french(self._configuration.language)

    ######################
    # Question templates #
    ######################

    @property
    def activated_question_templates(self) -> list[QuestionTemplate]:
        """Every question template activated for this explainer, fixed by its configuration at construction."""
        return list(self._activated_question_templates.values())

    @property
    def explanation_counter(self) -> ExplanationCounter:
        """The counter tracking how many times each question template has been asked, for each question type."""
        return self._explanation_counter

    ###########
    # History #
    ###########

    def _enable_history(self):
        """
        Starts a fresh copy of the root solution/instance so the root itself stays untouched, and questions it.

        Called once, from __init__, when the configuration enables history.
        """
        solution = self._root_solution.copy(name=f"{self._root_solution.name}.1.1")
        solution.instance = self._root_solution.instance.copy(name=f"{solution.instance.name}.1")
        self._history = History(solution)
        self._current_solution = solution

    @property
    def history(self) -> History:
        """The store of every instance and solution questioned or saved so far, keyed by name."""
        return self._history

    def store_solution(self, solution: Solution):
        """
        Stores the given solution in history, converting it to an EditableSolution first if it is not one.

        Args:
            solution: The solution to store.

        Raises:
            PermissionError: if history is disabled.
        """
        if self._configuration.history_enabled:
            if not isinstance(solution, EditableSolution):
                solution = EditableSolution.from_solution(solution)
            self._history.store_solution(solution)
        else:
            raise PermissionError("Historizing is disabled")

    def find_stored_solution_with_same_content(self, solution: Solution) -> Optional[EditableSolution]:
        """
        Returns the stored solution of the given solution's instance with the same sequences as it, if any.

        NB: Matched on content (Solution.__eq__ compares sequences, ignoring names), not on name as History does,
        because two computations of the same support solution yield distinct objects with distinct names.

        Args:
            solution: The solution to look for.

        Returns:
            The stored solution with the same content, or None if there is none.
        """
        for stored_solution in self._history.solutions:
            if stored_solution.instance.name == solution.instance.name and stored_solution == solution:
                return stored_solution
        return None

    @property
    def current_instance(self):
        """The instance of the solution the next question will be asked about."""
        return self._current_solution.instance

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

    ################
    # Any question #
    ################

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

    #######################
    # Free-text questions #
    #######################

    @property
    def neighborhood_extraction_llm_model(self):
        """The instructor model string used in the llm pipeline to extract a neighborhood from a free-text question."""
        return self._configuration.neighborhood_extraction_llm_model

    def set_neighborhood_extraction_llm_model(self, neighborhood_extraction_llm_model: Optional[str]):
        """
        Sets the instructor model string free-text questions are extracted with from now on.

        Args:
            neighborhood_extraction_llm_model: The instructor model string to switch to ("provider/model-name"),
                or None to go back to answering predefined questions only.
        """
        self._configuration.neighborhood_extraction_llm_model = neighborhood_extraction_llm_model
        self._extractor = None
        self._solution_the_extractor_was_built_for = None

    @neighborhood_extraction_llm_model.setter
    def neighborhood_extraction_llm_model(self, neighborhood_extraction_llm_model: Optional[str]):
        self.set_neighborhood_extraction_llm_model(neighborhood_extraction_llm_model)

    def _get_extractor(self) -> "Extractor":
        """
        Returns the Extractor turning a free-text question about the current solution into a neighborhood.

        Built on first use and rebuilt whenever the solution being questioned changes,
        since an Extractor grounds names against one solution and refuses a question asked about another.

        Returns:
            The Extractor bound to the current solution.

        Raises:
            ValueError: if this explainer was built with no neighborhood_extraction_llm_model,
                so free-text questions cannot be answered at all.
        """
        neighborhood_extraction_llm_model = self._configuration.neighborhood_extraction_llm_model
        if neighborhood_extraction_llm_model is None:
            raise ValueError(
                "This explainer answers predefined questions only: it was built with no neighborhood_llm_model, "
                "so there is no LLM backend to turn a free-text question into a neighborhood. "
                "Pass neighborhood_llm_model (e.g. main_configuration.EXTRACTOR_MODEL) to its constructor."
            )
        else:
            # NB: Imported here rather than at module level so that asking predefined questions needs
            # neither the instructor package nor any LLM backend.
            from src.explaining.neighborhood.llm.extractor import Extractor
            if self._extractor is None or self._solution_the_extractor_was_built_for is not self._current_solution:
                self._extractor = Extractor(self._current_solution, neighborhood_extraction_llm_model)
                self._solution_the_extractor_was_built_for = self._current_solution
            return cast("Extractor", self._extractor)

    def prepare_extractor(self):
        """
        Builds the Extractor for the current solution now, rather than on the first question needing it.

        Lets a caller surface a misconfigured LLM backend as soon as it is chosen:
        a ValueError if no neighborhood_extraction_llm_model is set,
        a RuntimeError if the model's provider needs an API key that is not set,
        or an ImportError if the instructor package is not installed.
        """
        self._get_extractor()

    @property
    def explanation_writing_llm_model(self) -> Optional[str]:
        """The instructor model string used in the llm pipeline to word a free-text question's explanation."""
        return self._configuration.explanation_writing_llm_model

    def set_explanation_writing_llm_model(self, explanation_writing_llm_model: Optional[str]):
        """
        Sets the instructor model string free-text questions' explanations are worded with from now on.

        Args:
            explanation_writing_llm_model: The instructor model string to switch to ("provider/model-name"),
                or None to word no explanation with an LLM anymore.
        """
        self._configuration.explanation_writing_llm_model = explanation_writing_llm_model
        self._writer = None

    @explanation_writing_llm_model.setter
    def explanation_writing_llm_model(self, explanation_writing_llm_model: Optional[str]):
        self.set_explanation_writing_llm_model(explanation_writing_llm_model)

    def _get_writer(self) -> "ExplanationWriter":
        """
        Returns the ExplanationWriter wording a free-text question's explanation,
        from the facts of its solved neighborhood.

        Built on first use, and rebuilt only when its model is changed: unlike the Extractor,
        it is bound to no solution, every call being handed the question and the facts to word.

        Returns:
            The ExplanationWriter.

        Raises:
            ValueError: if this explainer was built with no explanation_writing_llm_model,
                so free-text questions' explanations cannot be worded.
        """
        explanation_writing_llm_model = self._configuration.explanation_writing_llm_model
        if explanation_writing_llm_model is None:
            raise ValueError(
                "This explainer was built with no explanation_writing_llm_model, "
                "so there is no LLM backend to word a free-text question's explanation. "
                "Pass explanation_writing_llm_model (e.g. main_configuration.WRITER_MODEL) to its configuration, "
                f"or set its free_text_explanation_mode to '{FreeTextExplanationModes.TEMPLATED.value}' "
                "if free-text questions are known to be the equivalents of question templates."
            )
        else:
            # NB: Imported here rather than at module level,
            # for the same reason as the Extractor's (see _get_extractor).
            from src.explaining.explanation.free.writer import ExplanationWriter
            if self._writer is None:
                self._writer = ExplanationWriter(
                    explanation_writing_llm_model,
                    with_json_context=self._configuration.explanation_writing_with_json_context
                )
            return cast("ExplanationWriter", self._writer)

    def prepare_writer(self):
        """
        Builds the ExplanationWriter now, rather than on the first free-text question needing it.

        Lets a caller surface a misconfigured LLM backend as soon as it is chosen:
        a ValueError if no explanation_writing_llm_model is set,
        a RuntimeError if the model's provider needs an API key that is not set,
        or an ImportError if the instructor package is not installed.
        """
        self._get_writer()

    def _set_up_llm_models(self, with_writer: bool):
        """
        Builds the LLM-backed objects the question about to be answered needs, if they are not built yet,
        so that a missing model is reported before any LLM call is spent on a question that cannot be answered,
        and so that setting them up is reported as a step of its own, timed apart from the computation.

        The step is only reported when something is actually built:
        the Extractor is (re)built on first use and whenever the solution being questioned changes,
        the ExplanationWriter only on first use.
        The Extractor is set up first, being the first one the pipeline needs.

        Args:
            with_writer: Whether the ExplanationWriter is needed too (written free-text explanations only).

        Raises:
            ValueError: if no neighborhood_extraction_llm_model is set,
                or no explanation_writing_llm_model while the ExplanationWriter is needed.
        """
        is_extractor_to_build = (
            self._extractor is None or self._solution_the_extractor_was_built_for is not self._current_solution
        )
        is_writer_to_build = with_writer and self._writer is None
        if not (is_extractor_to_build or is_writer_to_build):
            return
        with self._progress_reporter.step("Setting up the LLM models") as step:
            if is_extractor_to_build:
                self._get_extractor()
                step.info("Neighborhood extraction LLM model", self.neighborhood_extraction_llm_model)
            if is_writer_to_build:
                self._get_writer()
                step.info("Explanation writing LLM model", self.explanation_writing_llm_model)

    def set_pipeline(self, pipeline: str, llm_model: Optional[str] = None):
        """
        Sets every mode (and, for the llm pipeline, both LLM models) to run the given pipeline end to end,
        all or nothing (see ExplainerConfiguration.apply_pipeline).

        For the llm pipeline, the Extractor and the ExplanationWriter are set up right away,
        so that a misconfigured LLM backend is reported now rather than on the next question.
        If either cannot be, every setting is put back as it was.

        Args:
            pipeline: One of Pipelines' values.
            llm_model: For the llm pipeline, the instructor model string both extracting neighborhoods
                and writing explanations, or None to keep the two LLM models already set.

        Raises:
            ValueError: If the pipeline cannot be applied (see ExplainerConfiguration.apply_pipeline),
                or no LLM model is set for it.
            RuntimeError: If an LLM model's provider needs an API key that is not set.
            ImportError: If the instructor package is not installed.
        """
        configuration = self._configuration
        previous_settings = (
            configuration.template_computation_mode, configuration.neighborhood_extraction_mode,
            configuration.free_text_explanation_mode,
            configuration.neighborhood_extraction_llm_model, configuration.explanation_writing_llm_model
        )
        configuration.apply_pipeline(pipeline, llm_model)
        # NB: Set back through the setters, so that an Extractor or a writer built for another model is dropped.
        self.set_neighborhood_extraction_llm_model(configuration.neighborhood_extraction_llm_model)
        self.set_explanation_writing_llm_model(configuration.explanation_writing_llm_model)
        if pipeline == Pipelines.LLM.value:
            try:
                self.prepare_extractor()
                self.prepare_writer()
            except (ValueError, RuntimeError, ImportError):
                (configuration.template_computation_mode, configuration.neighborhood_extraction_mode,
                 configuration.free_text_explanation_mode) = previous_settings[:3]
                self.set_neighborhood_extraction_llm_model(previous_settings[3])
                self.set_explanation_writing_llm_model(previous_settings[4])
                raise

    def _extract_neighborhood(self, question: Question) -> Neighborhood:
        """
        Extracts the neighborhood the given question induces, reporting it as a step.

        A free-text question always goes through the LLM Extractor.
        A contrastive one goes through it too in llm neighborhood extraction mode, from its text,
        and through the Mapper otherwise.

        Args:
            question: The free-text or contrastive question to extract the neighborhood of.

        Returns:
            The neighborhood the question induces.
        """
        with self._progress_reporter.step("Extracting the neighborhood") as step:
            is_extracted_by_llm = (
                isinstance(question, FreeTextQuestion)
                or self._configuration.neighborhood_extraction_mode == NeighborhoodExtractionModes.LLM.value
            )
            if isinstance(question, FreeTextQuestion):
                neighborhood = self._get_extractor().extract(question)
            elif is_extracted_by_llm:
                neighborhood = self._get_extractor().extract(
                    FreeTextQuestion(self._current_solution, question.text, self.language)
                )
            else:
                neighborhood = Mapper().map(cast(PredefinedQuestion, question))
            step.info("Extraction mode", neighborhood.extraction_mode)
            if is_extracted_by_llm:
                step.info("LLM model", self.neighborhood_extraction_llm_model)
            step.info("Scope", neighborhood.scope)
            step.info("Primitives", neighborhood)
        return neighborhood

    def _compute_free_text_explanation(self, question: FreeTextQuestion) -> Explanation:
        """
        Answers a free-text question through the llm-neighborhood pipeline,
        worded the way the configuration's free_text_explanation_mode says.

        Args:
            question: The free-text question to answer, asked about the current solution.

        Returns:
            The explanation answering it.
        """
        if self._configuration.free_text_explanation_mode == FreeTextExplanationModes.TEMPLATED.value:
            free_text_explanation = self._compute_templated_free_text_explanation(question)
        else:
            free_text_explanation = self._compute_written_free_text_explanation(question)
        self._last_contrastive_explanation = free_text_explanation
        self._last_contrastive_explanation_was_reused = False
        self._last_scenario_explanation = None
        self._last_counterfactual_explanation = None
        return free_text_explanation

    def _compute_written_free_text_explanation(self, question: FreeTextQuestion) -> Explanation:
        """
        Answers a free-text question by having an LLM word the facts of the solved neighborhood it induces,
        whatever that neighborhood, in or out of the question template catalogue.

        Args:
            question: The free-text question to answer, asked about the current solution.

        Returns:
            The FreeTextExplanation answering it.

        Raises:
            ValueError: if no neighborhood_llm_model or no explanation_writing_llm_model is set.
            NeighborhoodExtractionError: if the question cannot be turned into a solvable neighborhood.
            ExplanationWritingError: if the LLM fails to word a grounded explanation from the facts.
        """
        self._set_up_llm_models(with_writer=True)
        start_time = time.perf_counter()
        neighborhood = self._extract_neighborhood(question)
        model, skill_conflict = solve_neighborhood(
            neighborhood, self._configuration.time_limit_for_contrastive_explanation_milp_computation,
            self._progress_reporter
        )
        with self._progress_reporter.step("Analyzing the solution") as step:
            facts = ExplanationFactsBuilder.build(question, neighborhood, model, skill_conflict)
            support_solution = ExplanationFactsBuilder.get_support_solution(neighborhood, model)
            step.info("Outcome", facts.outcome.value)
            if facts.outcome is ExplanationOutcomes.INFEASIBLE_UNATTRIBUTED:
                step.warning("The feasibility shortfall could not be attributed to the conflicting task's position")
        # NB: The computation time covers extracting and solving, as a templated one's does, not the wording.
        elapsed_time = time.perf_counter() - start_time
        # NB: Not counted and not cached, for the same reason as a templated one's (see below).
        with self._progress_reporter.step("Writing the explanation") as step:
            step.info("LLM model", self.explanation_writing_llm_model)
            writing_start_time = time.perf_counter()
            free_text_explanation = self._get_writer().write(
                question, facts, support_solution, ExplanationComputationModes.NEIGHBORHOOD.value, elapsed_time
            )
            free_text_explanation.writing_time = time.perf_counter() - writing_start_time
        free_text_explanation.neighborhood = neighborhood
        free_text_explanation.milp_statistics = model.statistics if model is not None else None
        return free_text_explanation

    def _compute_templated_free_text_explanation(self, question: FreeTextQuestion) -> Explanation:
        """
        Answers a free-text question known to be the equivalent of a question template,
        by recognizing that template from the neighborhood it induces (see computing.bridge).

        NB: The explanation is phrased from the template of the question the neighborhood is recognized as,
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
        self._set_up_llm_models(with_writer=False)
        start_time = time.perf_counter()
        neighborhood = self._extract_neighborhood(question)
        try:
            recognized_question, transformation_result = solve_neighborhood_into_transformation_result(
                neighborhood, self._configuration.time_limit_for_contrastive_explanation_milp_computation,
                self._progress_reporter
            )
        except NeighborhoodError as error:
            raise NeighborhoodError(
                f"The question {question.text!r} was understood and the search space it induces was solved, "
                f"but that space matches no question template, so no explanation can be phrased from it yet"
            ) from error
        recognized_question.set_language(self.language)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        # NB: Not counted and not cached: both are keyed by template id and field values,
        # which the question the end user actually asked has neither of.
        free_text_explanation = create_explanation(
            recognized_question, transformation_result,
            ExplanationComputationModes.NEIGHBORHOOD.value, elapsed_time
        )
        free_text_explanation.neighborhood = neighborhood
        free_text_explanation.milp_statistics = transformation_result.milp_statistics
        return free_text_explanation

    def get_free_text_explanation(self, question_text: str) -> Explanation:
        """
        Answers a question the end user phrased themselves, about the solution currently being questioned.

        Args:
            question_text: The question as the end user typed it.

        Returns:
            The explanation answering it.
        """
        return self.get_explanation(FreeTextQuestion(self._current_solution, question_text, self.language))

    ###########################################################
    # Predefined question - Contrastive - Cached explanations #
    ###########################################################

    @property
    def cached_contrastive_explanations(self) -> list[Explanation]:
        """Every contrastive explanation cached so far, across every template, in no particular order."""
        explanations = []
        for template_id in self._cached_contrastive_explanations.keys():
            for explanation in self._cached_contrastive_explanations[template_id].values():
                explanations.append(explanation)
        return explanations

    def clear_cached_contrastive_explanations(self) -> int:
        """
        Forgets every cached contrastive explanation.

        NB: Only the in-memory cache is cleared.
        A question whose single-explanation JSON file sits in the inputs directory is still imported from it
        rather than recomputed; the multi-explanation file loaded at construction is not loaded again.

        Returns:
            The number of explanations that were cleared.
        """
        nb_cleared_explanations = len(self.cached_contrastive_explanations)
        self._cached_contrastive_explanations.clear()
        return nb_cleared_explanations

    def _add_contrastive_explanation_to_cached_ones(self, explanation: Explanation):
        """
        Stores the given contrastive explanation among the cached ones, if not already there.

        Args:
            explanation: The contrastive explanation to store.

        Raises:
            ValueError: if the given explanation is not contrastive.
            PermissionError: if using cached contrastive explanations is disabled.
        """
        if not isinstance(explanation, PredefinedExplanation):
            raise ValueError("The given explanation is not predefined")
        else:
            if not explanation.is_contrastive:
                raise ValueError("The given explanation is not contrastive")
            if not self._configuration.using_cached_contrastive_explanations_enabled:
                raise PermissionError("Storing any contrastive explanation in cached ones is not allowed "
                                      "as using cached contrastive explanations is disabled")
            template_id = explanation.question.template.id
            if template_id not in self._cached_contrastive_explanations.keys():
                self._cached_contrastive_explanations[template_id] = dict()
            fields_values_str = str(explanation.question.fields_values)
            if fields_values_str not in self._cached_contrastive_explanations[template_id]:
                self._cached_contrastive_explanations[template_id][fields_values_str] = explanation

    def _add_contrastive_explanations_to_cached_ones(self, explanations: list[Explanation]):
        """
        Stores every given contrastive explanation among the cached ones, skipping duplicates.

        Args:
            explanations: The contrastive explanations to store.
        """
        for explanation in explanations:
            self._add_contrastive_explanation_to_cached_ones(explanation)

    def _check_if_contrastive_explanation_is_in_cached_ones(self, contrastive_question: ContrastiveQuestion):
        """
        Returns whether the explanation answering the given contrastive question is cached.

        Args:
            contrastive_question: The contrastive question to check.

        Returns:
            True if an explanation for that question's template and fields values is already stored.
        """
        template_id = contrastive_question.template.id
        if template_id not in self._cached_contrastive_explanations.keys():
            return False
        fields_values_str = str(contrastive_question.fields_values)
        return fields_values_str in self._cached_contrastive_explanations[template_id]

    def _get_cached_contrastive_explanation(self, contrastive_question: ContrastiveQuestion):
        """
        Returns the cached explanation answering the given contrastive question.

        Args:
            contrastive_question: The contrastive question to retrieve the stored explanation of.

        Returns:
            The explanation stored for that question's template and fields values.

        Raises:
            ValueError: if no explanation is stored for that question yet.
        """
        if not self._check_if_contrastive_explanation_is_in_cached_ones(contrastive_question):
            raise ValueError("Explanation associated to given question is not cached")
        template_id, fields_values_str = contrastive_question.template.id, str(contrastive_question.fields_values)
        return self._cached_contrastive_explanations[template_id][fields_values_str]

    def _enable_using_cached_contrastive_explanations(self):
        """
        Loads any already-exported explanations for the current solution into the cache.

        Called once, from __init__, when the configuration enables reuse —
        using_cached_contrastive_explanations_enabled cannot change afterward, so there is never
        a later point at which this needs to run again.
        """
        input_directory = self._configuration.contrastive_explanation_input_directory_relative_path
        multiple_explanations_json_file_name = define_multiple_contrastive_explanations_json_file_name(
            self._current_solution
        )
        if check_inputs_file_existence(multiple_explanations_json_file_name, input_directory):
            self._add_contrastive_explanations_to_cached_ones(
                import_multiple_explanations_from_json_file(
                    multiple_explanations_json_file_name, self._current_solution, input_directory
                )
            )

    def export_all_cached_contrastive_explanations(
            self, outputs_directory_relative_path: Optional[str] = None
    ):
        """
        Exports every explanation computed so far into one JSON file.

        Args:
            outputs_directory_relative_path: The directory to write into,
                defaulting to the one this explainer is configured with, as the single-explanation exports do.
        """
        if outputs_directory_relative_path is None:
            outputs_directory_relative_path = self._configuration.contrastive_explanation_output_directory_relative_path
        export_multiple_contrastive_explanations_to_json_file(
            self.cached_contrastive_explanations, outputs_directory_relative_path
        )

    ###########################################################
    # Predefined question - Contrastive - Compute explanation #
    ###########################################################

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

        In neighborhood computation mode, the neighborhood the question induces is extracted by the Mapper or,
        in llm neighborhood extraction mode, by the Extractor from the question's text,
        which can then fail with a ValueError (no LLM model set) or a NeighborhoodExtractionError.

        Args:
            contrastive_question: The contrastive question to answer.

        Returns:
            The explanation answering it.
        """
        computation_mode_is_tailored = (
            self._configuration.template_computation_mode == TemplateComputationModes.TAILORED.value
        )
        if not computation_mode_is_tailored:
            if self._configuration.neighborhood_extraction_mode == NeighborhoodExtractionModes.LLM.value:
                self._set_up_llm_models(with_writer=False)
        start_time = time.perf_counter()
        solving_time_limit = self._configuration.time_limit_for_contrastive_explanation_milp_computation
        if computation_mode_is_tailored:
            mode = ExplanationComputationModes.TAILORED.value
            neighborhood = None
            with self._progress_reporter.step("Computing the transformation"):
                transformation_result = TransformationDispatcher.handle_contrastive_or_scenario_question(
                    self.current_solution, contrastive_question, solving_time_limit
                )
        else:
            mode = ExplanationComputationModes.NEIGHBORHOOD.value
            neighborhood = self._extract_neighborhood(contrastive_question)
            _, transformation_result = solve_neighborhood_into_transformation_result(
                neighborhood, solving_time_limit, self._progress_reporter
            )
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        contrastive_explanation = create_explanation(contrastive_question, transformation_result, mode, elapsed_time)
        contrastive_explanation.neighborhood = neighborhood
        contrastive_explanation.milp_statistics = transformation_result.milp_statistics
        if self._configuration.using_cached_contrastive_explanations_enabled:
            self._add_contrastive_explanation_to_cached_ones(contrastive_explanation)
        if self._configuration.exporting_each_contrastive_explanation_automatically_enabled:
            export_single_contrastive_explanation_to_json_file(
                contrastive_explanation, self._configuration.contrastive_explanation_output_directory_relative_path
            )
        return contrastive_explanation

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
        Answers the given contrastive question, reusing a cached explanation for it when possible.

        Reuse first checks the cache,
        then falls back to importing a previously exported single-explanation JSON file,
        before computing the explanation from scratch.

        Args:
            contrastive_question: The contrastive question to answer.

        Returns:
            The explanation answering it.
        """
        self.explanation_counter.increase_question_count(contrastive_question)
        contrastive_explanation = None
        if self._configuration.using_cached_contrastive_explanations_enabled:
            if self._check_if_contrastive_explanation_is_in_cached_ones(contrastive_question):
                with self._progress_reporter.step("Reusing the cached explanation") as step:
                    contrastive_explanation = self._get_cached_contrastive_explanation(contrastive_question)
                    step.info("Source", "memory")
            else:
                file_name = define_single_contrastive_explanation_json_file_name(contrastive_question)
                input_directory = self._configuration.contrastive_explanation_input_directory_relative_path
                if check_inputs_file_existence(file_name, input_directory):
                    with self._progress_reporter.step("Reusing the cached explanation") as step:
                        contrastive_explanation = import_single_explanation_from_json_file(
                            file_name, contrastive_question.solution, input_directory
                        )
                        self._add_contrastive_explanation_to_cached_ones(contrastive_explanation)
                        step.info("Source", f"file {file_name}")
        self._last_contrastive_explanation_was_reused = contrastive_explanation is not None
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
            f".{str(len(self._history.get_solutions_of_instance_by_name(current_instance_name)) + 1)}"
        )

    ########################################################
    # Predefined question - Contrastive - Last explanation #
    ########################################################

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

    @property
    def last_contrastive_explanation_was_reused(self) -> bool:
        """Whether the last contrastive explanation was reused from the cache (memory or file) rather than computed."""
        return self._last_contrastive_explanation_was_reused

    def save_last_contrastive_support_solution(self) -> bool:
        """
        Stores the last contrastive explanation's support solution in history, if it is feasible and not yet stored.

        Returns:
            True if this call stored it, False if a solution with the same content was already stored
            (see find_stored_solution_with_same_content).

        Raises:
            PermissionError: if that support solution is not feasible.
        """
        last_contrastive_support_solution = self.last_contrastive_explanation.support_solution
        if self.find_stored_solution_with_same_content(last_contrastive_support_solution) is not None:
            return False
        if self.last_contrastive_explanation.support_solution_is_feasible:
            last_contrastive_support_solution.name = self._get_name_for_contrastive_support_solution()
            self.store_solution(last_contrastive_support_solution)
            return True
        else:
            raise PermissionError("Cannot save the last contrastive support solution as it is not feasible")

    def export_last_contrastive_explanation(self):
        """Exports the last contrastive explanation to its own JSON file."""
        print(f"Exporting explanation to the question: {self.last_contrastive_explanation.question.text}")
        export_single_contrastive_explanation_to_json_file(
            self.last_contrastive_explanation,
            self._configuration.contrastive_explanation_output_directory_relative_path
        )

    ########################################################
    # Predefined question - Scenario - Compute explanation #
    ########################################################

    def _create_scenario_question(self, scenario_instance: EditableInstance):
        """
        Creates the scenario question turning the last contrastive question's instance into the given one.

        Args:
            scenario_instance: The altered instance to ask the scenario question about.

        Returns:
            The scenario question so created.

        Raises:
            PermissionError: if no contrastive question has been asked yet,
                or if the last one is a free-text one answered without any question template.
        """
        last_contrastive_question = self.last_contrastive_explanation.question
        _refuse_follow_up_of_free_text_question(last_contrastive_question, "scenario")
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
        if self._configuration.scenario_explanations_enabled:
            scenario_question = self._create_scenario_question(scenario_instance)
            self.explanation_counter.increase_question_count(scenario_question)
            current_solution = self.current_solution
            scenario_current_solution = current_solution.copy(current_solution.name + "_scenario")
            scenario_current_solution.instance = scenario_instance
            mode = ExplanationComputationModes.TAILORED.value
            start_time = time.perf_counter()
            transformation_result = TransformationDispatcher.handle_contrastive_or_scenario_question(
                scenario_current_solution, scenario_question
            )
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            scenario_explanation = create_explanation(scenario_question, transformation_result, mode, elapsed_time)
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
        return f"{self._root_solution.instance.name}.{str(self._history.nb_instances + 1)}"

    def _get_name_for_next_support_solution(self):
        """
        Builds the name of the next scenario or counterfactual support solution.

        Returns:
            The name to give it, of the form "<root solution name>.<next instance index>.1".
        """
        return f"{self._root_solution.name}.{str(self._history.nb_instances + 1)}.1"

    #####################################################
    # Predefined question - Scenario - Last explanation #
    #####################################################

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

    ##############################################################
    # Predefined question - Counterfactual - Compute explanation #
    ##############################################################

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
            PermissionError: if no contrastive question has been asked yet,
                or if the last one is a free-text one answered without any question template.
        """
        if contrastive_question is None:
            contrastive_question = self.last_contrastive_explanation.question
        _refuse_follow_up_of_free_text_question(contrastive_question, "counterfactual")
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
        if self._configuration.counterfactual_explanations_enabled:
            if (question_template_id is None) and (fields_values is None):
                contrastive_question = None
            elif (question_template_id is not None) and (fields_values is not None):
                contrastive_question = self._create_contrastive_question(question_template_id, fields_values)
            else:
                raise ValueError("Question template id and fields values must be either both None or both not None")
            counterfactual_question = self._create_counterfactual_question(contrastive_question, instance_slacks)
            self.explanation_counter.increase_question_count(counterfactual_question)
            current_solution = self.current_solution
            counterfactual_solution = self.current_solution.copy(current_solution.name + "_counterfactual")
            mode = ExplanationComputationModes.TAILORED.value
            start_time = time.perf_counter()
            result = TransformationDispatcher.handle_counterfactual_question(
                counterfactual_solution, counterfactual_question,
                self._configuration.time_limit_for_counterfactual_explanation_milp_computation
            )
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            counterfactual_explanation = create_explanation(counterfactual_question, result, mode, elapsed_time)
            self._last_counterfactual_explanation = counterfactual_explanation
            return counterfactual_explanation
        else:
            raise PermissionError("Counterfactual explanations are not enabled")

    ###########################################################
    # Predefined question - Counterfactual - Last explanation #
    ###########################################################

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


###########
# Helpers #
###########

def _refuse_follow_up_of_free_text_question(question: Question, follow_up_kind: str):
    """
    Refuses to build a follow-up question on a free-text question answered without any question template.

    A scenario or counterfactual question is built on a ContrastiveQuestion's template and field values,
    which a free-text question has none of - unless it was answered in templated mode,
    in which case the explanation carries the ContrastiveQuestion recognized from it instead.

    Args:
        question: The question the follow-up would be built on.
        follow_up_kind: The kind of follow-up ("scenario" or "counterfactual"), for the message.

    Raises:
        PermissionError: if question is a free-text one.
    """
    if isinstance(question, FreeTextQuestion):
        raise PermissionError(
            f"Cannot create a {follow_up_kind} question: the last contrastive question was a free-text one, "
            f"answered without any question template, while a {follow_up_kind} follow-up is built on one"
        )
