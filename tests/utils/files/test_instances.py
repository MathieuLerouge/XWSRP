# Standard library
import os

# Third-party library
import pytest

# Local library
from src.utils.files.instances import *


@pytest.mark.parametrize("file_name, expected", [
    pytest.param("instance_demo", True, id="snake_case"),
    pytest.param("InstanceDemo", True, id="camel_case"),
    pytest.param("not_an_instance", False, id="not_an_instance"),
])
def test_is_an_instance_file_name_checks_the_prefix(file_name, expected):
    assert is_an_instance_file_name(file_name) is expected


@pytest.mark.parametrize("file_name_with_extension, expected", [
    pytest.param("instance_demo.xlsx", True, id="instance_extension"),
    pytest.param("instance_demo.txt", False, id="non_instance_extension"),
])
def test_is_an_instance_file_name_with_extension_checks_prefix_and_extension(file_name_with_extension, expected):
    assert is_an_instance_file_name_with_extension(file_name_with_extension) is expected


def test_is_an_instance_file_name_with_extension_raises_when_there_is_no_extension():
    with pytest.raises(ValueError):
        _ = is_an_instance_file_name_with_extension("instance_demo")


@pytest.mark.parametrize("file_name, expected_case_type", [
    pytest.param("instance_demo", SNAKE_CASE, id="snake_case"),
    pytest.param("InstanceDemo", CAMEL_CASE, id="camel_case"),
])
def test_get_instance_file_name_case_type_identifies_the_case(file_name, expected_case_type):
    assert get_instance_file_name_case_type(file_name) == expected_case_type


def test_get_instance_file_name_case_type_raises_when_the_file_name_is_not_an_instance_file_name():
    with pytest.raises(ValueError):
        _ = get_instance_file_name_case_type("not_an_instance")


@pytest.mark.parametrize("file_name, expected", [
    pytest.param("instance_demo", "demo", id="snake_case"),
    pytest.param("InstanceDemo", "Demo", id="camel_case"),
])
def test_remove_instance_file_name_prefix_strips_the_prefix(file_name, expected):
    assert remove_instance_file_name_prefix(file_name) == expected


@pytest.mark.parametrize("file_name, expected", [
    pytest.param("instance_demoV2", True, id="mentions_version"),
    pytest.param("instance_demo", False, id="no_version"),
])
def test_does_instance_file_name_mention_version_checks_for_the_version_symbol(file_name, expected):
    assert does_instance_file_name_mention_version(file_name) is expected


def test_get_instance_version_in_instance_file_name_returns_the_version():
    assert get_instance_version_in_instance_file_name("instance_demoV2") == 2


def test_get_instance_version_in_instance_file_name_raises_when_there_is_no_version():
    with pytest.raises(ValueError):
        _ = get_instance_version_in_instance_file_name("instance_demo")


def test_remove_instance_version_from_instance_file_name_strips_the_version():
    assert remove_instance_version_from_instance_file_name("instance_demoV2") == "instance_demo"


@pytest.mark.parametrize("file_name, expected_core", [
    pytest.param("instance_demoV2.xlsx", "demo", id="with_version_and_extension"),
    pytest.param("instance_demo", "demo", id="without_version_or_extension"),
])
def test_get_core_in_instance_file_name_strips_prefix_version_and_extension(file_name, expected_core):
    assert get_core_in_instance_file_name(file_name) == expected_core


@pytest.mark.parametrize("file_name", [
    pytest.param("instance_demo.xlsx", id="with_extension"),
    pytest.param("instance_demo", id="without_extension"),
])
def test_get_instance_name_in_instance_file_name_strips_the_extension_if_any(file_name):
    assert get_instance_name_in_instance_file_name(file_name) == "instance_demo"


def test_get_instance_name_in_instance_file_path_extracts_the_name_from_the_path():
    assert get_instance_name_in_instance_file_path("data/demo/instances/instance_demo.xlsx") == "instance_demo"


@pytest.mark.parametrize("file_name_with_extension, expected_version", [
    pytest.param("instance_demoV2.xlsx", 2, id="with_version"),
    pytest.param("instance_demo.xlsx", None, id="without_version"),
])
def test_identify_meta_data_in_instance_file_name_reports_core_case_and_version(
        file_name_with_extension, expected_version):
    meta_data = identify_meta_data_in_instance_file_name(file_name_with_extension)
    assert meta_data == {
        META_DATA_CORE_KEY: "demo",
        META_DATA_CASE_KEY: SNAKE_CASE,
        META_DATA_VERSION_KEY: expected_version,
    }


def test_identify_meta_data_in_instance_file_path_reports_the_same_meta_data_as_by_name():
    meta_data = identify_meta_data_in_instance_file_path("data/demo/instances/instance_demoV2.xlsx")
    assert meta_data == {META_DATA_CORE_KEY: "demo", META_DATA_CASE_KEY: SNAKE_CASE, META_DATA_VERSION_KEY: 2}


@pytest.mark.parametrize("core, version, case_type, expected", [
    pytest.param("demo", 2, SNAKE_CASE, "instance_demoV2", id="snake_case_with_version"),
    # create_instance_file_name only concatenates prefix + core + suffix — it doesn't capitalize
    # the core, so a proper CamelCase result relies on the caller passing an already-capitalized core.
    pytest.param("Demo", None, CAMEL_CASE, "InstanceDemo", id="camel_case_without_version"),
])
def test_create_instance_file_name_builds_the_name_from_its_parts(core, version, case_type, expected):
    assert create_instance_file_name(core, version, case_type) == expected


def test_create_instance_file_name_raises_on_an_unsupported_case_type():
    with pytest.raises(ValueError):
        _ = create_instance_file_name("demo", case_type="unsupported_case")


def test_create_instance_file_path_joins_the_directory_name_and_extension():
    path = create_instance_file_path("demo", None, SNAKE_CASE, ".xlsx", "inputs")
    assert path == f"{get_project_directory_path()}/inputs/instance_demo.xlsx"


def test_create_instance_file_paths_with_various_extensions_returns_one_path_per_extension():
    paths = create_instance_file_paths_with_various_extensions("demo", None, SNAKE_CASE, "inputs")
    assert paths == [
        f"{get_project_directory_path()}/inputs/instance_demo.xlsx",
        f"{get_project_directory_path()}/inputs/instance_demo.json",
    ]


def test_get_paths_of_instances_files_in_given_directory_lists_only_instance_files(tmp_path):
    (tmp_path / "instance_demo.xlsx").touch()
    (tmp_path / "not_an_instance.xlsx").touch()
    relative_path = os.path.relpath(tmp_path, get_project_directory_path())

    paths = get_paths_of_instances_files_in_given_directory(relative_path)

    # The path is built by string concatenation with relative_path's own ".." segments (not
    # normalized), so compare resolved paths rather than the raw strings.
    assert [os.path.realpath(p) for p in paths] == [str(tmp_path / "instance_demo.xlsx")]


def test_get_paths_of_instances_files_in_given_directory_raises_when_the_directory_does_not_exist(tmp_path):
    relative_path = os.path.relpath(tmp_path / "does_not_exist", get_project_directory_path())
    with pytest.raises(FileNotFoundError):
        _ = get_paths_of_instances_files_in_given_directory(relative_path)


@pytest.mark.parametrize("absolute_path, expected", [
    pytest.param(True, f"{get_project_directory_path()}/data/teaching/V2/instances", id="absolute"),
    pytest.param(False, "data/teaching/V2/instances", id="relative"),
])
def test_get_path_of_directory_of_instances_of_given_version_builds_the_versioned_path(absolute_path, expected):
    assert get_path_of_directory_of_instances_of_given_version(2, absolute_path) == expected
