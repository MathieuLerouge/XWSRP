# Standard library
import os

# Third-party library
import pytest

# Local library
from src.utils.files import find_instance_file_path_corresponding_to_solution, get_demo_solution_path, \
    get_project_directory_path


def test_find_instance_file_path_corresponding_to_solution_uses_the_given_directory(tmp_path):
    (tmp_path / "instance_demo.xlsx").touch()
    relative_path = os.path.relpath(tmp_path, get_project_directory_path())

    result = find_instance_file_path_corresponding_to_solution("solution_demo_by_greedy.txt", relative_path)

    assert os.path.realpath(result) == str(tmp_path / "instance_demo.xlsx")


def test_find_instance_file_path_corresponding_to_solution_searches_automatically_using_real_demo_data():
    # data/demo/solutions/solution_demo.txt and data/demo/instances/instance_demo.xlsx are real,
    # checked-in fixtures — this exercises the "solutions" -> "instances" directory fallback for real.
    result = find_instance_file_path_corresponding_to_solution(get_demo_solution_path())

    assert os.path.realpath(result) == \
           os.path.realpath(f"{get_project_directory_path()}/data/demo/instances/instance_demo.xlsx")


def test_find_instance_file_path_corresponding_to_solution_raises_when_no_instance_file_exists(tmp_path):
    solution_file_path = str(tmp_path / "solution_nonexistent_by_greedy.txt")
    with pytest.raises(FileExistsError):
        _ = find_instance_file_path_corresponding_to_solution(solution_file_path)
