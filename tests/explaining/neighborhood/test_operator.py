# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.operator import (
    SequenceReordering, TaskDeletion, TaskInsertion, TaskRelocation, TaskRepositioning
)
from tests.modeling.helpers import build_employee, build_instance, build_task


#################
# TaskInsertion #
#################

def test_task_insertion_target_tasks_and_scope_return_the_candidate_sets():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
    assert operator.target_tasks == frozenset({task})
    assert operator.scope == frozenset({employee, task})


def test_task_insertion_with_empty_candidate_employees_raises():
    instance = build_instance()
    task = build_task(instance)
    with pytest.raises(ValueError):
        TaskInsertion(frozenset(), frozenset({task}))


def test_task_insertion_with_empty_candidate_tasks_raises():
    instance = build_instance()
    employee = build_employee(instance)
    with pytest.raises(ValueError):
        TaskInsertion(frozenset({employee}), frozenset())


################
# TaskDeletion #
################

def test_task_deletion_target_tasks_and_scope_return_the_candidate_sets():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskDeletion(frozenset({employee}), frozenset({task}))
    assert operator.target_tasks == frozenset({task})
    assert operator.scope == frozenset({employee, task})


def test_task_deletion_with_empty_candidate_employees_raises():
    instance = build_instance()
    task = build_task(instance)
    with pytest.raises(ValueError):
        TaskDeletion(frozenset(), frozenset({task}))


def test_task_deletion_with_empty_candidate_tasks_raises():
    instance = build_instance()
    employee = build_employee(instance)
    with pytest.raises(ValueError):
        TaskDeletion(frozenset({employee}), frozenset())


##################
# TaskRelocation #
##################

def test_task_relocation_scope_deduplicates_when_origin_equals_destination():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskRelocation(employee, employee, task)
    assert operator.scope == frozenset({employee, task})


def test_task_relocation_scope_includes_both_when_origin_and_destination_differ():
    instance = build_instance()
    origin = build_employee(instance, 0)
    destination = build_employee(instance, 1)
    task = build_task(instance)
    operator = TaskRelocation(origin, destination, task)
    assert operator.scope == frozenset({origin, destination, task})


def test_task_relocation_target_tasks_returns_a_single_element_frozenset():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskRelocation(employee, employee, task)
    assert operator.target_tasks == frozenset({task})


#####################
# TaskRepositioning #
#####################

def test_task_repositioning_target_tasks_and_scope_return_the_employee_and_task():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskRepositioning(employee, task)
    assert operator.target_tasks == frozenset({task})
    assert operator.scope == frozenset({employee, task})


######################
# SequenceReordering #
######################

def test_sequence_reordering_target_tasks_is_empty_and_scope_is_the_employee():
    instance = build_instance()
    employee = build_employee(instance)
    operator = SequenceReordering(employee)
    assert operator.target_tasks == frozenset()
    assert operator.scope == frozenset({employee})
