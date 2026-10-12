# Third-party library
import pytest

# Local libraries
from src.explaining.interacting.configuration import (
    ExplainerConfiguration, FreeTextExplanationModes, Pipelines, TemplateComputationModes
)
from src.explaining.neighborhood.neighborhood import NeighborhoodExtractionModes


def test_the_tailored_pipeline_uses_no_llm_anywhere():
    configuration = ExplainerConfiguration(neighborhood_llm_model="stub/model")
    configuration.apply_pipeline(Pipelines.TAILORED.value)
    assert configuration.template_computation_mode == TemplateComputationModes.TAILORED.value
    assert configuration.neighborhood_extraction_mode == NeighborhoodExtractionModes.TAILORED.value
    assert configuration.free_text_explanation_mode == FreeTextExplanationModes.TEMPLATED.value
    assert configuration.neighborhood_extraction_llm_model == "stub/model", "The LLM models are left as they were"
    assert configuration.pipeline == Pipelines.TAILORED.value


def test_the_llm_pipeline_uses_the_given_model_for_both_extracting_and_writing():
    configuration = ExplainerConfiguration()
    configuration.apply_pipeline(Pipelines.LLM.value, "stub/model")
    assert configuration.template_computation_mode == TemplateComputationModes.NEIGHBORHOOD.value
    assert configuration.neighborhood_extraction_mode == NeighborhoodExtractionModes.LLM.value
    assert configuration.free_text_explanation_mode == FreeTextExplanationModes.WRITTEN.value
    assert configuration.neighborhood_extraction_llm_model == "stub/model"
    assert configuration.explanation_writing_llm_model == "stub/model"
    assert configuration.pipeline == Pipelines.LLM.value


def test_the_llm_pipeline_keeps_the_models_already_set_when_none_is_given():
    configuration = ExplainerConfiguration(neighborhood_llm_model="stub/extractor",
                                           explanation_writing_llm_model="stub/writer")
    configuration.apply_pipeline(Pipelines.LLM.value)
    assert configuration.neighborhood_extraction_llm_model == "stub/extractor"
    assert configuration.explanation_writing_llm_model == "stub/writer"
    assert configuration.pipeline == Pipelines.LLM.value


@pytest.mark.parametrize("pipeline, llm_model", [
    ("magic", None),
    (Pipelines.TAILORED.value, "stub/model"),
    (Pipelines.LLM.value, None),
])
def test_a_pipeline_that_cannot_be_applied_is_refused_without_changing_anything(pipeline, llm_model):
    configuration = ExplainerConfiguration(neighborhood_llm_model="stub/extractor")
    template_computation_mode = configuration.template_computation_mode
    with pytest.raises(ValueError):
        configuration.apply_pipeline(pipeline, llm_model)
    assert configuration.template_computation_mode == template_computation_mode
    assert configuration.explanation_writing_llm_model is None


def test_settings_mixed_by_hand_match_no_pipeline():
    configuration = ExplainerConfiguration()
    assert configuration.pipeline is None, "By default, free-text explanations are written but templates tailored"
    configuration.apply_pipeline(Pipelines.TAILORED.value)
    configuration.neighborhood_extraction_mode = NeighborhoodExtractionModes.LLM.value
    assert configuration.pipeline is None


def test_the_llm_settings_without_both_models_match_no_pipeline():
    configuration = ExplainerConfiguration()
    configuration.apply_pipeline(Pipelines.LLM.value, "stub/model")
    configuration.explanation_writing_llm_model = None
    assert configuration.pipeline is None
