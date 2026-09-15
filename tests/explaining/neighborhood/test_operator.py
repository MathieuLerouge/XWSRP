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

def test_task_insertion_scope_returns_the_candidate_sets():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
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

def test_task_deletion_scope_returns_the_freed_employees_and_candidate_tasks():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskDeletion(frozenset({employee}), frozenset({task}))
    assert operator.scope == frozenset({employee, task})


def test_task_deletion_min_and_max_nb_removals_default_to_one():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskDeletion(frozenset({employee}), frozenset({task}))
    assert operator.min_nb_removals == 1
    assert operator.max_nb_removals == 1


def test_task_deletion_min_and_max_nb_removals_are_settable():
    instance = build_instance()
    employee = build_employee(instance)
    task_1 = build_task(instance, 0)
    task_2 = build_task(instance, 1)
    operator = TaskDeletion(frozenset({employee}), frozenset({task_1, task_2}), min_nb_removals=1, max_nb_removals=2)
    assert operator.min_nb_removals == 1
    assert operator.max_nb_removals == 2


def test_task_deletion_with_empty_freed_employees_raises():
    instance = build_instance()
    task = build_task(instance)
    with pytest.raises(ValueError):
        TaskDeletion(frozenset(), frozenset({task}))


def test_task_deletion_with_empty_candidate_tasks_raises():
    instance = build_instance()
    employee = build_employee(instance)
    with pytest.raises(ValueError):
        TaskDeletion(frozenset({employee}), frozenset())


def test_task_deletion_with_negative_min_nb_removals_raises():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    with pytest.raises(ValueError):
        TaskDeletion(frozenset({employee}), frozenset({task}), min_nb_removals=-1, max_nb_removals=1)


def test_task_deletion_with_min_nb_removals_exceeding_max_raises():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    with pytest.raises(ValueError):
        TaskDeletion(frozenset({employee}), frozenset({task}), min_nb_removals=1, max_nb_removals=0)


def test_task_deletion_with_max_nb_removals_exceeding_candidate_tasks_raises():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    with pytest.raises(ValueError):
        TaskDeletion(frozenset({employee}), frozenset({task}), min_nb_removals=1, max_nb_removals=2)


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


#####################
# TaskRepositioning #
#####################

def test_task_repositioning_scope_returns_the_employee_and_task():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskRepositioning(employee, task)
    assert operator.scope == frozenset({employee, task})


######################
# SequenceReordering #
######################

def test_sequence_reordering_scope_is_the_employee():
    instance = build_instance()
    employee = build_employee(instance)
    operator = SequenceReordering(employee)
    assert operator.scope == frozenset({employee})
