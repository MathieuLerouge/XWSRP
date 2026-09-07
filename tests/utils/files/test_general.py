# Standard library
import os

# Third-party library
import pytest

# Local library
from src.utils.files.general import *


###########
# General #
###########

@pytest.mark.parametrize("file_name, expected", [
    pytest.param("instance_demo.xlsx", True, id="known_extension"),
    pytest.param("instance_demo.unknown", False, id="unrecognized_extension"),
])
def test_has_a_file_extension_checks_against_the_known_extensions(file_name, expected):
    assert has_a_file_extension(file_name) is expected


def test_get_file_extension_returns_the_extension():
    assert get_file_extension("instance_demo.xlsx") == ".xlsx"


def test_get_file_extension_raises_when_there_is_no_recognized_extension():
    with pytest.raises(ValueError):
        _ = get_file_extension("instance_demo.unknown")


def test_remove_file_extension_strips_the_extension():
    assert remove_file_extension("instance_demo.xlsx") == "instance_demo"


#####################
# Project directory #
#####################

def test_get_project_directory_path_returns_the_repo_root():
    # The project root is the one directory whose identity this module can verify without
    # hardcoding a machine-specific path: it's the parent of a real `src` directory.
    assert os.path.isdir(os.path.join(get_project_directory_path(), "src"))


def test_make_absolute_path_from_relative_one_prefixes_the_project_directory():
    assert make_absolute_path_from_relative_one("inputs") == f"{get_project_directory_path()}/inputs"


def test_make_relative_path_from_absolute_one_reverses_make_absolute_path_from_relative_one():
    absolute_path = make_absolute_path_from_relative_one("inputs")
    assert make_relative_path_from_absolute_one(absolute_path) == "inputs"


@pytest.mark.parametrize("with_extension, expected", [
    pytest.param(True, "instance_demo.xlsx", id="with_extension"),
    pytest.param(False, "instance_demo", id="without_extension"),
])
def test_get_file_name_from_path_extracts_the_file_name(with_extension, expected):
    assert get_file_name_from_path("data/demo/instances/instance_demo.xlsx", with_extension) == expected


def test_get_default_inputs_directory_path_is_the_real_inputs_directory():
    result = get_default_inputs_directory_path()
    assert result == make_absolute_path_from_relative_one("inputs")
    assert os.path.isdir(result)


def test_get_default_outputs_directory_path_is_the_real_outputs_directory():
    result = get_default_outputs_directory_path()
    assert result == make_absolute_path_from_relative_one("outputs")
    assert os.path.isdir(result)


@pytest.mark.parametrize("inputs_directory_relative_path, expected", [
    pytest.param(None, "inputs/instance.xlsx", id="default_directory"),
    pytest.param("custom_dir", "custom_dir/instance.xlsx", id="given_directory"),
])
def test_make_inputs_file_relative_path_from_file_name_joins_directory_and_file_name(
        inputs_directory_relative_path, expected):
    assert make_inputs_file_relative_path_from_file_name("instance.xlsx", inputs_directory_relative_path) == expected


def test_check_inputs_file_existence_returns_true_for_a_file_that_exists():
    # inputs/.gitkeep is checked into the repo specifically to keep the otherwise-empty
    # inputs/ directory tracked, so it's a stable, always-present fixture for this check.
    assert check_inputs_file_existence(".gitkeep") is True


def test_check_inputs_file_existence_returns_false_for_a_file_that_does_not_exist():
    assert check_inputs_file_existence("does_not_exist.xlsx") is False
