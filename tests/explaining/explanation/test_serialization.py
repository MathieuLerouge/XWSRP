# Standard libraries
import glob
import json

# Third-party library
import pytest

# Local libraries
from src.explaining.explanation.predefined.explanation import (
    TRANSFORMATION_KEY, create_explanation_from_dict
)
from src.importing.instance import extract_instance_from_file
from src.importing.solution import import_solution
from src.modeling.solution import Solution
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY

# Global variables
# Every explanation file committed under data/, paired with the instance and solution it was computed for.
# These files are a stored format, not a fixture: a change that silently stops reading them is a regression,
# which is what this module exists to catch.
STORED_EXPLANATIONS = [
    (
        "data/demo/explanations/explanations_solution_demo.json",
        "data/demo/instances/instance_demo.xlsx",
        "data/demo/solutions/solution_demo.txt",
    ),
] + [
    (
        f"data/evaluation/explanations/explanations_evaluation_{index}.json",
        f"data/evaluation/instances/instance_evaluation_{index}.xlsx",
        f"data/evaluation/solutions/solution_evaluation_{index}.txt",
    )
    for index in (0, 1, 2)
]
SUPPORTED_LANGUAGES = (LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY)


def test_every_stored_explanations_file_is_covered():
    """
    Every explanation file under data/ must be listed above.

    Without this, adding a file would leave it silently untested - which is how the two formats
    diverged unnoticed in the first place.
    """
    files_on_disk = set(glob.glob("data/*/explanations/*.json"))
    listed_files = {explanations_path for explanations_path, _, _ in STORED_EXPLANATIONS}
    assert files_on_disk == listed_files, (
        f"stored explanation files not covered by these tests: {sorted(files_on_disk - listed_files)}; "
        f"listed but missing from disk: {sorted(listed_files - files_on_disk)}"
    )


def get_english_description(explanation_dictionary) -> str:
    """
    Returns the English description of the applied transformation, whichever format it was stored in.

    Used by the tests below that build a deliberately malformed payload: they exercise the reader,
    so they must not themselves depend on the shape the stored files happen to use.

    Args:
        explanation_dictionary: The stored explanation to read the description off.

    Returns:
        The English description.
    """
    descriptions = explanation_dictionary[TRANSFORMATION_KEY]
    return descriptions[LANGUAGE_ENGLISH_KEY] if isinstance(descriptions, dict) else descriptions


def load_solution(instance_path: str, solution_path: str) -> Solution:
    """
    Loads the solution the stored explanations of a file were computed about.

    Args:
        instance_path: Path of the instance file.
        solution_path: Path of the solution file.

    Returns:
        The loaded solution.
    """
    instance = extract_instance_from_file(instance_path, True, True, True)
    return import_solution(solution_path, instance, True, True, True)


@pytest.mark.parametrize("explanations_path,_instance_path,_solution_path", STORED_EXPLANATIONS)
def test_stored_transformations_are_keyed_by_language(explanations_path, _instance_path, _solution_path):
    """
    Every stored explanation must describe its transformation as one sentence per language.

    An earlier format stored a single already-resolved string instead, which carries no language and so
    cannot be read back in the other one. Nothing rejected it, so the two formats coexisted under data/
    until the older files stopped rendering entirely.
    """
    with open(explanations_path) as explanations_file:
        explanations_dictionaries = json.load(explanations_file)
    assert explanations_dictionaries, f"{explanations_path} holds no explanation"
    for index, explanation_dictionary in enumerate(explanations_dictionaries):
        descriptions = explanation_dictionary[TRANSFORMATION_KEY]
        assert isinstance(descriptions, dict), (
            f"{explanations_path}[{index}] stores its transformation as a {type(descriptions).__name__} "
            f"rather than one sentence per language"
        )
        assert set(descriptions) == set(SUPPORTED_LANGUAGES), (
            f"{explanations_path}[{index}] describes its transformation in {sorted(descriptions)} "
            f"rather than in every supported language"
        )


@pytest.mark.parametrize("explanations_path,instance_path,solution_path", STORED_EXPLANATIONS)
def test_stored_explanations_rebuild_and_render_in_every_language(explanations_path, instance_path, solution_path):
    """
    Every stored explanation must rebuild and word itself, in each language explanations are given in.

    This is the round trip that no test covered while the two stored formats drifted apart.
    """
    solution = load_solution(instance_path, solution_path)
    with open(explanations_path) as explanations_file:
        explanations_dictionaries = json.load(explanations_file)
    for language_key in SUPPORTED_LANGUAGES:
        for index, explanation_dictionary in enumerate(explanations_dictionaries):
            explanation = create_explanation_from_dict(explanation_dictionary, solution)
            explanation.question.set_language(language_key)
            # Rebuilt rather than merely relabelled: the wording is fixed when the explanation is built.
            explanation = create_explanation_from_dict(explanation_dictionary, solution)
            assert explanation.language == language_key
            assert explanation.text, f"{explanations_path}[{index}] words itself as an empty text"
            assert explanation.applying_support_solution_transformation


@pytest.mark.parametrize("explanations_path,instance_path,solution_path", STORED_EXPLANATIONS)
def test_stored_explanations_survive_a_dictionary_round_trip(explanations_path, instance_path, solution_path):
    """
    Re-exporting a rebuilt explanation must reproduce what it was rebuilt from.

    NB: the support solution is compared through the dictionary rather than field by field, since
    create_explanation_from_dict deliberately mutates its departure/comeback steps for a TimeConflict.
    """
    solution = load_solution(instance_path, solution_path)
    with open(explanations_path) as explanations_file:
        explanations_dictionaries = json.load(explanations_file)
    for index, explanation_dictionary in enumerate(explanations_dictionaries):
        re_exported = create_explanation_from_dict(explanation_dictionary, solution).to_dict()
        assert re_exported[TRANSFORMATION_KEY] == explanation_dictionary[TRANSFORMATION_KEY], (
            f"{explanations_path}[{index}] does not re-export the transformation it was built from"
        )
        assert re_exported['question'] == explanation_dictionary['question'], (
            f"{explanations_path}[{index}] does not re-export the question it was built from"
        )


def test_reading_an_old_single_string_transformation_reports_the_format():
    """
    An explanation carrying the old single-string transformation must say so, rather than fail obscurely.

    Before, the property indexed the string by language key and raised
    "TypeError: string indices must be integers", which named neither the file nor the format.
    """
    explanations_path, instance_path, solution_path = STORED_EXPLANATIONS[0]
    solution = load_solution(instance_path, solution_path)
    with open(explanations_path) as explanations_file:
        explanation_dictionary = json.load(explanations_file)[0]
    old_format_dictionary = dict(explanation_dictionary)
    old_format_dictionary[TRANSFORMATION_KEY] = get_english_description(explanation_dictionary)

    explanation = create_explanation_from_dict(old_format_dictionary, solution)
    with pytest.raises(TypeError, match="single-language format"):
        _ = explanation.applying_support_solution_transformation


def test_reading_a_transformation_missing_the_current_language_reports_it():
    """
    An explanation whose transformation lacks the language it is being read in must name the languages it has.
    """
    explanations_path, instance_path, solution_path = STORED_EXPLANATIONS[0]
    solution = load_solution(instance_path, solution_path)
    with open(explanations_path) as explanations_file:
        explanation_dictionary = json.load(explanations_file)[0]
    english_only_dictionary = dict(explanation_dictionary)
    english_only_dictionary[TRANSFORMATION_KEY] = {
        LANGUAGE_ENGLISH_KEY: get_english_description(explanation_dictionary)
    }

    explanation = create_explanation_from_dict(english_only_dictionary, solution)
    explanation.question.set_language(LANGUAGE_FRENCH_KEY)
    with pytest.raises(KeyError, match="single-language format"):
        _ = explanation.applying_support_solution_transformation
