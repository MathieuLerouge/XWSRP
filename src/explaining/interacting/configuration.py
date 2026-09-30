# Standard library
from typing import Optional

# Local libraries
from src.explaining.question.predefined.constants import (
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)
from src.utils.constants import DEFAULT_INPUTS_DIRECTORY_RELATIVE_PATH, DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
from src.utils.language import LANGUAGE_ENGLISH_KEY

# The predefined question templates Explainer can handle, and the subset of those that also support
# being turned into a counterfactual question.
AVAILABLE_QUESTION_TEMPLATE_IDS: list[str] = [
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
]
AVAILABLE_COUNTERFACTUAL_QUESTION_TEMPLATE_IDS: list[str] = [
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_3,
    WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
]


##########################
# ExplainerConfiguration #
##########################

class ExplainerConfiguration:
    """
    The construction-time settings an Explainer is built from: language, the extractor model,
    every enable_*/disable_* toggle, the contrastive-explanation directories and the MILP time limits.
    """

    def __init__(
            self, extractor_model: Optional[str] = None, language: str = LANGUAGE_ENGLISH_KEY,
            activated_question_template_ids: Optional[list[str]] = None,
            history_enabled: bool = False, scenario_explanations_enabled: bool = False,
            counterfactual_explanations_enabled: bool = False,
            using_already_computed_contrastive_explanations_enabled: bool = False,
            exporting_each_contrastive_explanation_automatically_enabled: bool = False,
            contrastive_explanation_input_directory_relative_path: str = DEFAULT_INPUTS_DIRECTORY_RELATIVE_PATH,
            contrastive_explanation_output_directory_relative_path: str = DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH,
            time_limit_for_contrastive_explanation_milp_computation: Optional[int] = None,
            time_limit_for_counterfactual_explanation_milp_computation: Optional[int] = None
    ):
        """
        Args:
            extractor_model: The instructor model string the llm pipeline extracts a free-text question with.
                Left as None when only predefined questions are asked, which is what keeps the LLM backend optional.
            language: The language to phrase questions and explanations in.
            activated_question_template_ids: Ids of the question templates to activate, skipping any not in
                AVAILABLE_QUESTION_TEMPLATE_IDS, or None to activate every available one.
            history_enabled: Whether to keep every solution asked about or saved.
            scenario_explanations_enabled: Whether to allow scenario follow-up questions.
            counterfactual_explanations_enabled: Whether to allow counterfactual follow-up questions.
            using_already_computed_contrastive_explanations_enabled: Whether to reuse already computed
                contrastive explanations instead of recomputing them.
            exporting_each_contrastive_explanation_automatically_enabled: Whether to export each computed
                contrastive explanation to its own JSON file as soon as it is computed.
            contrastive_explanation_input_directory_relative_path: Directory already computed contrastive
                explanations are imported from.
            contrastive_explanation_output_directory_relative_path: Directory contrastive explanations are
                exported to.
            time_limit_for_contrastive_explanation_milp_computation: Time limit, in seconds, given to the MILP
                solve of a contrastive or scenario explanation, or None for no limit.
            time_limit_for_counterfactual_explanation_milp_computation: Time limit, in seconds, given to the
                MILP solve of a counterfactual explanation, or None for no limit.
        """
        self._extractor_model: Optional[str] = extractor_model
        self._language = language
        if activated_question_template_ids is None:
            activated_question_template_ids = AVAILABLE_QUESTION_TEMPLATE_IDS
        self._activated_question_template_ids: list[str] = [
            template_id for template_id in activated_question_template_ids
            if template_id in AVAILABLE_QUESTION_TEMPLATE_IDS
        ]
        self._history_enabled = history_enabled
        self._scenario_explanations_enabled = scenario_explanations_enabled
        self._counterfactual_explanations_enabled = counterfactual_explanations_enabled
        self._using_already_computed_contrastive_explanations_enabled = \
            using_already_computed_contrastive_explanations_enabled
        self._exporting_each_contrastive_explanation_automatically_enabled = \
            exporting_each_contrastive_explanation_automatically_enabled
        self._contrastive_explanation_input_directory_relative_path = \
            contrastive_explanation_input_directory_relative_path
        self._contrastive_explanation_output_directory_relative_path = \
            contrastive_explanation_output_directory_relative_path
        self._time_limit_for_contrastive_explanation_milp_computation: Optional[int] = \
            time_limit_for_contrastive_explanation_milp_computation
        self._time_limit_for_counterfactual_explanation_milp_computation: Optional[int] = \
            time_limit_for_counterfactual_explanation_milp_computation

    @classmethod
    def batch(
            cls, extractor_model: Optional[str] = None,
            using_already_computed_contrastive_explanations_enabled: bool = False, **overrides
    ) -> "ExplainerConfiguration":
        """
        Returns the configuration shared by every batch/evaluation script:
        history, scenario and counterfactual explanations, and automatic export, all disabled.

        Args:
            extractor_model: The instructor model string the llm pipeline extracts a free-text question with.
            using_already_computed_contrastive_explanations_enabled: Whether to reuse already computed
                contrastive explanations instead of recomputing them.
            **overrides: Any other ExplainerConfiguration constructor argument to set instead of its default
                (e.g. the directories, the MILP time limits, or language).

        Returns:
            The configuration so built.
        """
        return cls(
            extractor_model=extractor_model,
            using_already_computed_contrastive_explanations_enabled=(
                using_already_computed_contrastive_explanations_enabled
            ),
            history_enabled=False, scenario_explanations_enabled=False,
            counterfactual_explanations_enabled=False,
            exporting_each_contrastive_explanation_automatically_enabled=False,
            **overrides
        )

    @classmethod
    def web_ui(
            cls, extractor_model: Optional[str] = None, language: str = LANGUAGE_ENGLISH_KEY,
            history_enabled: bool = True, scenario_explanations_enabled: bool = True,
            counterfactual_explanations_enabled: bool = True,
            using_already_computed_contrastive_explanations_enabled: bool = False,
            contrastive_explanation_input_directory_relative_path: str = DEFAULT_INPUTS_DIRECTORY_RELATIVE_PATH
    ) -> "ExplainerConfiguration":
        """
        Returns the configuration shared by the interactive web UI launchers:
        history, scenario and counterfactual explanations enabled by default, automatic export disabled.

        Args:
            extractor_model: The instructor model string the llm pipeline extracts a free-text question with.
            language: The language to phrase questions and explanations in.
            history_enabled: Whether to keep every solution asked about or saved.
            scenario_explanations_enabled: Whether to allow scenario follow-up questions.
            counterfactual_explanations_enabled: Whether to allow counterfactual follow-up questions.
            using_already_computed_contrastive_explanations_enabled: Whether to reuse already computed
                contrastive explanations instead of recomputing them.
            contrastive_explanation_input_directory_relative_path: Directory already computed contrastive
                explanations are imported from, when using_already_computed_contrastive_explanations_enabled is True.

        Returns:
            The configuration so built.
        """
        return cls(
            extractor_model=extractor_model, language=language,
            history_enabled=history_enabled, scenario_explanations_enabled=scenario_explanations_enabled,
            counterfactual_explanations_enabled=counterfactual_explanations_enabled,
            using_already_computed_contrastive_explanations_enabled=(
                using_already_computed_contrastive_explanations_enabled
            ),
            exporting_each_contrastive_explanation_automatically_enabled=False,
            contrastive_explanation_input_directory_relative_path=(
                contrastive_explanation_input_directory_relative_path
            )
        )

    @property
    def extractor_model(self) -> Optional[str]:
        """The instructor model string the llm pipeline extracts a free-text question with, if any."""
        return self._extractor_model

    @extractor_model.setter
    def extractor_model(self, extractor_model: Optional[str]):
        self._extractor_model = extractor_model

    @property
    def language(self) -> str:
        """The language to phrase questions and explanations in."""
        return self._language

    @language.setter
    def language(self, language: str):
        self._language = language

    @property
    def activated_question_template_ids(self) -> list[str]:
        """
        Id of every question template activated for the Explainer built from this configuration.

        Fixed at construction; not settable afterward, since no Explainer application is expected to
        activate or deactivate a question template while already using an Explainer.
        """
        return self._activated_question_template_ids

    @property
    def activated_counterfactual_questions_templates_ids(self) -> list[str]:
        """Id of every activated question template that also supports counterfactual questions."""
        return [
            template_id for template_id in self._activated_question_template_ids
            if template_id in AVAILABLE_COUNTERFACTUAL_QUESTION_TEMPLATE_IDS
        ]

    @property
    def history_enabled(self) -> bool:
        """
        Whether every solution asked about or saved is kept, so it can be retrieved again later.

        Fixed at construction; not settable afterward, since enabling history does more than store this
        flag (Explainer also copies the root solution/instance and rebinds its History to the copy).
        """
        return self._history_enabled

    @property
    def scenario_explanations_enabled(self) -> bool:
        """Whether scenario follow-up questions are allowed."""
        return self._scenario_explanations_enabled

    @scenario_explanations_enabled.setter
    def scenario_explanations_enabled(self, enabled: bool):
        self._scenario_explanations_enabled = enabled

    @property
    def counterfactual_explanations_enabled(self) -> bool:
        """Whether counterfactual follow-up questions are allowed."""
        return self._counterfactual_explanations_enabled

    @counterfactual_explanations_enabled.setter
    def counterfactual_explanations_enabled(self, enabled: bool):
        self._counterfactual_explanations_enabled = enabled

    @property
    def using_already_computed_contrastive_explanations_enabled(self) -> bool:
        """
        Whether already computed contrastive explanations are reused instead of recomputed.

        Fixed at construction; not settable afterward, since enabling this does more than store this flag
        (Explainer also loads any already-exported explanations for its solution from disk).
        """
        return self._using_already_computed_contrastive_explanations_enabled

    @property
    def exporting_each_contrastive_explanation_automatically_enabled(self) -> bool:
        """Whether each computed contrastive explanation is automatically exported to its own JSON file."""
        return self._exporting_each_contrastive_explanation_automatically_enabled

    @exporting_each_contrastive_explanation_automatically_enabled.setter
    def exporting_each_contrastive_explanation_automatically_enabled(self, enabled: bool):
        self._exporting_each_contrastive_explanation_automatically_enabled = enabled

    @property
    def contrastive_explanation_input_directory_relative_path(self) -> str:
        """Directory already computed contrastive explanations are imported from."""
        return self._contrastive_explanation_input_directory_relative_path

    @contrastive_explanation_input_directory_relative_path.setter
    def contrastive_explanation_input_directory_relative_path(self, directory_relative_path: str):
        self._contrastive_explanation_input_directory_relative_path = directory_relative_path

    @property
    def contrastive_explanation_output_directory_relative_path(self) -> str:
        """Directory contrastive explanations are exported to."""
        return self._contrastive_explanation_output_directory_relative_path

    @contrastive_explanation_output_directory_relative_path.setter
    def contrastive_explanation_output_directory_relative_path(self, directory_relative_path: str):
        self._contrastive_explanation_output_directory_relative_path = directory_relative_path

    @property
    def time_limit_for_contrastive_explanation_milp_computation(self) -> Optional[int]:
        """Time limit, in seconds, given to the MILP solve of a contrastive or scenario explanation, if any."""
        return self._time_limit_for_contrastive_explanation_milp_computation

    @time_limit_for_contrastive_explanation_milp_computation.setter
    def time_limit_for_contrastive_explanation_milp_computation(self, time_limit: Optional[int]):
        self._time_limit_for_contrastive_explanation_milp_computation = time_limit

    @property
    def time_limit_for_counterfactual_explanation_milp_computation(self) -> Optional[int]:
        """Time limit, in seconds, given to the MILP solve of a counterfactual explanation, if any."""
        return self._time_limit_for_counterfactual_explanation_milp_computation

    @time_limit_for_counterfactual_explanation_milp_computation.setter
    def time_limit_for_counterfactual_explanation_milp_computation(self, time_limit: Optional[int]):
        self._time_limit_for_counterfactual_explanation_milp_computation = time_limit
