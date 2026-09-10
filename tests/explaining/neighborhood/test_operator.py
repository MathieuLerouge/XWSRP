# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.operator import (
    POSITION_SIDE_AFTER, POSITION_SIDE_BEFORE, TaskDeletion, TaskInsertion, TaskRelocation
)
from tests.modeling.helpers import build_employee, build_instance, build_task


#################
# TaskInsertion #
#################

def test_task_insertion_employees_and_target_tasks_return_the_candidate_sets():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}))
    assert operator.employees == frozenset({employee})
    assert operator.target_tasks == frozenset({task})


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


def test_task_insertion_with_anchor_activity_and_no_side_raises():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance, 0)
    anchor = build_task(instance, 1)
    with pytest.raises(ValueError):
        TaskInsertion(frozenset({employee}), frozenset({task}), anchor_activity=anchor)


def test_task_insertion_with_side_and_no_anchor_activity_raises():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    with pytest.raises(ValueError):
        TaskInsertion(frozenset({employee}), frozenset({task}), anchor_side=POSITION_SIDE_AFTER)


def test_task_insertion_with_invalid_anchor_side_raises():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance, 0)
    anchor = build_task(instance, 1)
    with pytest.raises(ValueError):
        TaskInsertion(frozenset({employee}), frozenset({task}), anchor_activity=anchor, anchor_side="sideways")


def test_task_insertion_with_anchor_activity_and_side_is_accepted():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance, 0)
    anchor = build_task(instance, 1)
    operator = TaskInsertion(frozenset({employee}), frozenset({task}),
                             anchor_activity=anchor, anchor_side=POSITION_SIDE_AFTER)
    assert operator.anchor_activity == anchor
    assert operator.anchor_side == POSITION_SIDE_AFTER


################
# TaskDeletion #
################

def test_task_deletion_employees_and_target_tasks_return_the_candidate_sets():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskDeletion(frozenset({employee}), frozenset({task}))
    assert operator.employees == frozenset({employee})
    assert operator.target_tasks == frozenset({task})


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

def test_task_relocation_employees_deduplicates_when_origin_equals_destination():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskRelocation(employee, employee, task)
    assert operator.employees == frozenset({employee})


def test_task_relocation_employees_includes_both_when_origin_and_destination_differ():
    instance = build_instance()
    origin = build_employee(instance, 0)
    destination = build_employee(instance, 1)
    task = build_task(instance)
    operator = TaskRelocation(origin, destination, task)
    assert operator.employees == frozenset({origin, destination})


def test_task_relocation_target_tasks_returns_a_single_element_frozenset():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskRelocation(employee, employee, task)
    assert operator.target_tasks == frozenset({task})


def test_task_relocation_with_anchor_side_alone_is_accepted_as_directional():
    # Unlike TaskInsertion, a relocated task has a current position to be directional about, so
    # anchor_side alone (no anchor_activity) is a valid, non-pinned direction.
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    operator = TaskRelocation(employee, employee, task, anchor_side=POSITION_SIDE_BEFORE)
    assert operator.anchor_activity is None
    assert operator.anchor_side == POSITION_SIDE_BEFORE


def test_task_relocation_with_anchor_activity_and_no_side_raises():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance, 0)
    anchor = build_task(instance, 1)
    with pytest.raises(ValueError):
        TaskRelocation(employee, employee, task, anchor_activity=anchor)


def test_task_relocation_with_invalid_anchor_side_raises():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    with pytest.raises(ValueError):
        TaskRelocation(employee, employee, task, anchor_side="sideways")
