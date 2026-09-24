# Standard library
import json
import os

# Third-party library
import pytest

# Local libraries
from src.exporting.solution import export_solution, export_solution_as_json_file, export_solution_as_txt_file
from src.modeling.solution import INSTANCE_KEY, KPIS_KEY, SEQUENCES_KEY, TASKS_PERFORMANCES_KEY
from src.modeling.taskperformance import TASK_ASSIGNEE_KEY, TASK_PERFORMANCE_STATUS_KEY, TASK_START_TIME_KEY
from tests.importing.helpers import build_solution


@pytest.fixture
def solution():
    return build_solution()


def _export_and_read_json(solution, tmp_path, **options) -> dict:
    """Exports the solution as a json file in tmp_path and returns the dictionary it holds."""
    file_path = export_solution_as_json_file(solution, os.path.relpath(tmp_path), **options)
    with open(file_path) as file:
        return json.load(file)


@pytest.mark.parametrize("as_json, expected_extension", [
    pytest.param(True, ".json", id="json_by_default"),
    pytest.param(False, ".txt", id="txt_when_asked"),
])
def test_export_solution_picks_the_file_extension_from_the_json_flag(solution, tmp_path, as_json,
                                                                     expected_extension):
    file_path = export_solution(solution, os.path.relpath(tmp_path), as_json=as_json)
    assert os.path.basename(file_path) == f"{solution.name}{expected_extension}"
    assert os.path.exists(file_path)


def test_export_solution_defaults_to_json(solution, tmp_path):
    file_path = export_solution(solution, os.path.relpath(tmp_path))
    assert file_path.endswith(".json")


def test_export_solution_as_json_file_records_the_data_needed_to_rebuild_the_solution(solution, tmp_path):
    dictionary = _export_and_read_json(solution, tmp_path)
    assert dictionary['instance name'] == solution.instance.name
    assert dictionary['name'] == solution.name
    performed_task = solution.performed_tasks[0]
    performed_task_dictionary = dictionary[TASKS_PERFORMANCES_KEY][performed_task.name]
    assert performed_task_dictionary[TASK_PERFORMANCE_STATUS_KEY] == 1
    assert performed_task_dictionary[TASK_ASSIGNEE_KEY] == solution.get_task_assignee(performed_task).name
    assert performed_task_dictionary[TASK_START_TIME_KEY] == solution.get_task_start_time(performed_task)
    non_performed_task = solution.non_performed_tasks[0]
    assert dictionary[TASKS_PERFORMANCES_KEY][non_performed_task.name] == {TASK_PERFORMANCE_STATUS_KEY: 0}


def test_export_solution_as_json_file_records_every_task_of_the_instance(solution, tmp_path):
    dictionary = _export_and_read_json(solution, tmp_path)
    assert set(dictionary[TASKS_PERFORMANCES_KEY]) == set(solution.instance.tasks_names)


@pytest.mark.parametrize("optional_key", [
    pytest.param(SEQUENCES_KEY, id="sequences"),
    pytest.param(KPIS_KEY, id="kpis"),
    pytest.param(INSTANCE_KEY, id="instance"),
])
def test_export_solution_as_json_file_omits_the_optional_content_by_default(solution, tmp_path, optional_key):
    assert optional_key not in _export_and_read_json(solution, tmp_path)


@pytest.mark.parametrize("option, optional_key", [
    pytest.param("with_sequences", SEQUENCES_KEY, id="sequences"),
    pytest.param("with_kpis", KPIS_KEY, id="kpis"),
    pytest.param("with_instance", INSTANCE_KEY, id="instance"),
])
def test_export_solution_as_json_file_records_the_optional_content_when_asked(solution, tmp_path, option,
                                                                              optional_key):
    assert optional_key in _export_and_read_json(solution, tmp_path, **{option: True})


def test_export_solution_as_json_file_records_the_sequences_in_their_order(solution, tmp_path):
    dictionary = _export_and_read_json(solution, tmp_path, with_sequences=True)
    employee = solution.get_task_assignee(solution.performed_tasks[0])
    expected_tasks_names = [task.name for task in solution.get_tasks_performed_by(employee)]
    assert dictionary[SEQUENCES_KEY][employee.name] == expected_tasks_names


def test_export_solution_as_txt_file_writes_a_header_then_one_line_per_task(solution, tmp_path):
    file_path = export_solution_as_txt_file(solution, os.path.relpath(tmp_path))
    with open(file_path) as file:
        lines = file.read().splitlines()
    assert lines[0] == "taskId;performed;employee_name;start_time;"
    assert len(lines) == 1 + len(solution.instance.tasks)
    performed_task = solution.performed_tasks[0]
    expected_line = (f"{performed_task.name};1;{solution.get_task_assignee(performed_task).name};"
                     f"{solution.get_task_start_time(performed_task)};")
    assert expected_line in lines
    assert f"{solution.non_performed_tasks[0].name};0;;;" in lines
