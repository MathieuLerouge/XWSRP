# Standard library
import os

# Third-party library
import pytest

# Local library
from src.utils.files.solutions import *


@pytest.mark.parametrize("file_name, expected", [
    pytest.param("solution_demo", True, id="snake_case"),
    pytest.param("SolutionDemo", True, id="camel_case"),
    pytest.param("not_a_solution", False, id="not_a_solution"),
])
def test_is_a_solution_file_name_checks_the_prefix(file_name, expected):
    assert is_a_solution_file_name(file_name) is expected


@pytest.mark.parametrize("file_name_with_extension, expected", [
    pytest.param("solution_demo_by_greedy.txt", True, id="solution_extension"),
    pytest.param("solution_demo.xlsx", False, id="non_solution_extension"),
    pytest.param("solution_demo", False, id="no_extension"),
])
def test_is_a_solution_file_name_with_extension_checks_prefix_and_extension(file_name_with_extension, expected):
    assert is_a_solution_file_name_with_extension(file_name_with_extension) is expected


@pytest.mark.parametrize("file_name, expected_case_type", [
    pytest.param("solution_demo", SNAKE_CASE, id="snake_case"),
    pytest.param("SolutionDemo", CAMEL_CASE, id="camel_case"),
])
def test_get_solution_file_name_case_type_identifies_the_case(file_name, expected_case_type):
    assert get_solution_file_name_case_type(file_name) == expected_case_type


def test_get_solution_file_name_case_type_raises_when_the_file_name_is_not_a_solution_file_name():
    with pytest.raises(ValueError):
        _ = get_solution_file_name_case_type("not_a_solution")


@pytest.mark.parametrize("file_name, expected", [
    pytest.param("solution_demo", "demo", id="snake_case"),
    pytest.param("SolutionDemo", "Demo", id="camel_case"),
])
def test_remove_solution_file_name_prefix_strips_the_prefix(file_name, expected):
    assert remove_solution_file_name_prefix(file_name) == expected


@pytest.mark.parametrize("file_name, expected", [
    pytest.param("solution_demoV2", True, id="mentions_version"),
    pytest.param("solution_demo", False, id="no_version"),
])
def test_does_solution_file_name_mention_version_checks_for_the_version_symbol(file_name, expected):
    assert does_solution_file_name_mention_version(file_name) is expected


def test_get_instance_version_in_solution_file_name_returns_the_version():
    assert get_instance_version_in_solution_file_name("solution_demoV2") == 2


def test_get_instance_version_in_solution_file_name_raises_when_there_is_no_version():
    with pytest.raises(ValueError):
        _ = get_instance_version_in_solution_file_name("solution_demo")


def test_remove_instance_version_from_solution_file_name_strips_the_version():
    assert remove_instance_version_from_solution_file_name("solution_demoV2_by_greedy.txt") == \
           "solution_demo_by_greedy.txt"


@pytest.mark.parametrize("file_name, expected", [
    pytest.param("solution_demo_by_greedy.txt", True, id="snake_case"),
    pytest.param("SolutionDemoByGreedy.txt", True, id="camel_case"),
    pytest.param("solution_demo.txt", False, id="no_solving_method"),
])
def test_does_solution_file_name_mention_solving_method_checks_for_the_method_symbol(file_name, expected):
    assert does_solution_file_name_mention_solving_method(file_name) is expected


def test_does_solution_file_path_mention_solving_method_checks_the_file_name_in_the_path():
    assert does_solution_file_path_mention_solving_method("outputs/solution_demo_by_greedy.txt") is True


@pytest.mark.parametrize("file_name, expected_method", [
    pytest.param("solution_demo_by_greedy.txt", "greedy", id="snake_case"),
    pytest.param("SolutionDemoByGreedy.txt", "Greedy", id="camel_case"),
    pytest.param("solution_demo_by_greedy(p1,p2).txt", "greedy", id="with_solving_parameters"),
])
def test_get_solving_method_in_solution_file_name_extracts_the_method(file_name, expected_method):
    assert get_solving_method_in_solution_file_name(file_name) == expected_method


def test_get_solving_method_in_solution_file_name_raises_when_there_is_no_solving_method():
    with pytest.raises(ValueError):
        _ = get_solving_method_in_solution_file_name("solution_demo.txt")


def test_get_solving_method_in_solution_file_path_extracts_the_method_from_the_path():
    assert get_solving_method_in_solution_file_path("outputs/solution_demo_by_greedy.txt") == "greedy"


def test_remove_solving_method_from_solution_file_name_strips_the_method():
    assert remove_solving_method_from_solution_file_name("solution_demo_by_greedy.txt") == "solution_demo.txt"


@pytest.mark.parametrize("file_name, expected", [
    pytest.param("solution_demo_by_greedy(p1,p2).txt", True, id="with_parameters"),
    pytest.param("solution_demo_by_greedy.txt", False, id="without_parameters"),
])
def test_does_solution_file_name_mention_solving_parameters_checks_for_bracketed_values(file_name, expected):
    assert does_solution_file_name_mention_solving_parameters(file_name) is expected


def test_get_solving_parameters_in_solution_file_name_extracts_the_parameters():
    assert get_solving_parameters_in_solution_file_name("solution_demo_by_greedy(p1,p2).txt") == ["p1", "p2"]


def test_get_solving_parameters_in_solution_file_name_raises_when_there_are_no_parameters():
    with pytest.raises(ValueError):
        _ = get_solving_parameters_in_solution_file_name("solution_demo_by_greedy.txt")


def test_remove_solving_parameters_from_solution_file_name_strips_the_parameters():
    assert remove_solving_parameters_from_solution_file_name("solution_demo_by_greedy(p1,p2).txt") == \
           "solution_demo_by_greedy.txt"


@pytest.mark.parametrize("file_name, expected_core", [
    pytest.param("solution_demoV2_by_greedy(p1,p2).txt", "demo", id="version_method_and_parameters"),
    pytest.param("solution_demo.txt", "demo", id="bare"),
])
def test_get_core_in_solution_file_name_strips_every_optional_component(file_name, expected_core):
    assert get_core_in_solution_file_name(file_name) == expected_core


def test_identify_meta_data_in_solution_file_name_reports_every_component_when_present():
    meta_data = identify_meta_data_in_solution_file_name("solution_demoV2_by_greedy(p1,p2).txt")
    assert meta_data == {
        META_DATA_CORE_KEY: "demo",
        META_DATA_CASE_KEY: SNAKE_CASE,
        META_DATA_VERSION_KEY: 2,
        META_DATA_SOLVING_METHOD_KEY: "greedy",
        META_DATA_SOLVING_PARAMETERS_KEY: ["p1", "p2"],
    }


def test_identify_meta_data_in_solution_file_name_reports_none_for_absent_optional_components():
    meta_data = identify_meta_data_in_solution_file_name("solution_demo.txt")
    assert meta_data == {
        META_DATA_CORE_KEY: "demo",
        META_DATA_CASE_KEY: SNAKE_CASE,
        META_DATA_VERSION_KEY: None,
        META_DATA_SOLVING_METHOD_KEY: None,
        META_DATA_SOLVING_PARAMETERS_KEY: None,
    }


def test_identify_meta_data_in_solution_file_path_reports_the_same_meta_data_as_by_name():
    meta_data = identify_meta_data_in_solution_file_path("outputs/solution_demoV2_by_greedy(p1,p2).txt")
    assert meta_data[META_DATA_CORE_KEY] == "demo"
    assert meta_data[META_DATA_SOLVING_METHOD_KEY] == "greedy"


def test_get_paths_of_solutions_files_in_given_directory_lists_only_solution_files(tmp_path):
    (tmp_path / "solution_demo_by_greedy.txt").touch()
    (tmp_path / "not_a_solution.txt").touch()
    relative_path = os.path.relpath(tmp_path, get_project_directory_path())

    paths = get_paths_of_solutions_files_in_given_directory(relative_path)

    assert [os.path.realpath(p) for p in paths] == [str(tmp_path / "solution_demo_by_greedy.txt")]


def test_get_paths_of_solutions_files_in_given_directory_raises_when_the_directory_does_not_exist(tmp_path):
    relative_path = os.path.relpath(tmp_path / "does_not_exist", get_project_directory_path())
    with pytest.raises(FileNotFoundError):
        _ = get_paths_of_solutions_files_in_given_directory(relative_path)


def test_get_solutions_files_paths_given_meta_data_filters_by_core_version_and_case_type(tmp_path):
    (tmp_path / "solution_demoV2_by_greedy.txt").touch()
    (tmp_path / "solution_otherV2_by_greedy.txt").touch()
    (tmp_path / "solution_demoV3_by_greedy.txt").touch()
    relative_path = os.path.relpath(tmp_path, get_project_directory_path())

    paths = get_solutions_files_paths_given_meta_data(
        "demo", version=2, case_type=SNAKE_CASE, solutions_directory_relative_path=relative_path
    )

    assert [os.path.realpath(p) for p in paths] == [str(tmp_path / "solution_demoV2_by_greedy.txt")]


@pytest.mark.parametrize("absolute_path, expected", [
    # Unlike get_path_of_directory_of_instances_of_given_version, the absolute path here is
    # nested under the outputs directory, not the bare project directory.
    pytest.param(True, f"{get_project_directory_path()}/outputs/data/teaching/V2/solutions", id="absolute"),
    pytest.param(False, "data/teaching/V2/solutions", id="relative"),
])
def test_get_directory_of_solutions_of_given_version_builds_the_versioned_path(absolute_path, expected):
    assert get_directory_of_solutions_of_given_version(2, absolute_path) == expected


def test_get_demo_solution_path_points_to_a_real_file():
    assert os.path.isfile(get_demo_solution_path())
