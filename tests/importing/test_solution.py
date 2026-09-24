# Standard libraries
import os
import shutil

# Third-party library
import pytest

# Local libraries
from src.exporting.solution import export_solution, export_solution_as_json_file, export_solution_as_txt_file
from src.importing.instance import extract_instance_from_file
from src.importing.solution import import_solution, import_solution_from_json_file, import_solution_from_txt_file
from src.optimization.heuristics.solution import SolutionForHeuristics
from src.utils.constants import GREEDY_SOLVING_METHOD
from tests.importing.helpers import build_solution, INSTANCE_FILE_PATH, SOLUTION_FILE_PATH


@pytest.fixture
def solution():
    return build_solution()


@pytest.fixture
def directory_with_the_instance(tmp_path):
    """A relative path to an empty directory holding a copy of the reference instance file."""
    shutil.copy(INSTANCE_FILE_PATH, tmp_path)
    return os.path.relpath(tmp_path)


def _assert_is_the_reference_solution(imported, solution):
    """Asserts that the imported solution is the reference one, beyond what Solution.__eq__ compares."""
    assert imported == solution
    assert imported.name == solution.name
    assert imported.instance.name == solution.instance.name
    assert set(imported.performed_tasks_names) == set(solution.performed_tasks_names)
    for task in solution.performed_tasks:
        imported_task = imported.instance.get_task_by_name(task.name)
        assert imported.get_task_assignee(imported_task).name == solution.get_task_assignee(task).name
        assert imported.get_task_start_time(imported_task) == solution.get_task_start_time(task)


###############
# Round trips #
###############

def test_a_solution_exported_as_a_json_file_is_imported_back_unchanged(solution, directory_with_the_instance):
    file_path = export_solution_as_json_file(solution, directory_with_the_instance)
    _assert_is_the_reference_solution(import_solution(file_path), solution)


def test_a_solution_exported_as_a_txt_file_is_imported_back_unchanged(solution, directory_with_the_instance):
    file_path = export_solution_as_txt_file(solution, directory_with_the_instance)
    _assert_is_the_reference_solution(import_solution(file_path), solution)


def test_a_solution_exported_with_all_the_optional_content_is_imported_back_unchanged(
        solution, directory_with_the_instance):
    file_path = export_solution(solution, directory_with_the_instance, with_sequences=True, with_kpis=True,
                                with_instance=True)
    _assert_is_the_reference_solution(import_solution(file_path), solution)


def test_a_solution_exported_with_its_instance_is_imported_back_without_the_instance_file(solution, tmp_path):
    """The embedded instance must make the exported file self-contained, hence the instance-free directory."""
    file_path = export_solution(solution, os.path.relpath(tmp_path), with_instance=True)
    _assert_is_the_reference_solution(import_solution(file_path), solution)


############
# Dispatch #
############

@pytest.mark.parametrize("as_json", [
    pytest.param(True, id="json_file"),
    pytest.param(False, id="txt_file"),
])
def test_import_solution_reads_the_file_matching_its_extension(solution, directory_with_the_instance, as_json):
    file_path = export_solution(solution, directory_with_the_instance, as_json=as_json)
    assert import_solution(file_path) == solution


def test_import_solution_raises_when_the_file_extension_is_not_supported():
    with pytest.raises(ValueError):
        _ = import_solution("tests/data/solution_test.csv")


def test_import_solution_from_json_file_raises_when_the_file_is_not_a_json_one():
    with pytest.raises(FileNotFoundError):
        _ = import_solution_from_json_file(SOLUTION_FILE_PATH)


#######################
# Instance resolution #
#######################

def test_import_solution_from_json_file_uses_the_given_instance(solution, tmp_path):
    """Given an instance, the importer must not need the instance file, nor an embedded instance."""
    file_path = export_solution_as_json_file(solution, os.path.relpath(tmp_path))
    instance = extract_instance_from_file(INSTANCE_FILE_PATH)
    imported = import_solution_from_json_file(file_path, instance)
    assert imported.instance is instance
    _assert_is_the_reference_solution(imported, solution)


def test_import_solution_from_json_file_raises_when_the_instance_can_be_found_nowhere(solution, tmp_path):
    file_path = export_solution_as_json_file(solution, os.path.relpath(tmp_path))
    with pytest.raises(FileExistsError):
        _ = import_solution_from_json_file(file_path)


def test_import_solution_from_txt_file_finds_the_instance_next_to_the_solution(solution,
                                                                               directory_with_the_instance):
    file_path = export_solution_as_txt_file(solution, directory_with_the_instance)
    assert import_solution_from_txt_file(file_path).instance.name == solution.instance.name


def test_import_solution_reads_a_heuristic_solution_as_a_solution_for_heuristics(solution,
                                                                                 directory_with_the_instance):
    exported_file_path = export_solution_as_txt_file(solution, directory_with_the_instance)
    heuristic_file_path = os.path.join(directory_with_the_instance,
                                       f"{solution.name}_by_{GREEDY_SOLVING_METHOD}.txt")
    shutil.move(exported_file_path, heuristic_file_path)
    imported = import_solution(heuristic_file_path)
    assert isinstance(imported, SolutionForHeuristics)
    assert imported == solution
