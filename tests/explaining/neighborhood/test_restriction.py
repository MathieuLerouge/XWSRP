# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.restriction import (
    ForbiddenSequence, ImmediatePrecedence, Precedence, SequenceOrderFixed
)
from tests.modeling.helpers import build_employee, build_instance, build_task


######################
# SequenceOrderFixed #
######################

def test_sequence_order_fixed_tasks():
    instance = build_instance()
    task_1 = build_task(instance, 0)
    task_2 = build_task(instance, 1)
    tasks = [task_1, task_2]
    restriction = SequenceOrderFixed(tasks)
    assert restriction.tasks == tasks


#######################
# ImmediatePrecedence #
#######################

def test_immediate_precedence_predecessor_and_successor():
    instance = build_instance()
    predecessor = build_task(instance, 0)
    successor = build_task(instance, 1)
    restriction = ImmediatePrecedence(predecessor, successor)
    assert restriction.predecessor == predecessor
    assert restriction.successor == successor


def test_immediate_precedence_with_same_predecessor_and_successor_raises():
    instance = build_instance()
    activity = build_task(instance)
    with pytest.raises(ValueError):
        ImmediatePrecedence(activity, activity)


##############
# Precedence #
##############

def test_precedence_predecessor_and_successor():
    instance = build_instance()
    predecessor = build_task(instance, 0)
    successor = build_task(instance, 1)
    restriction = Precedence(predecessor, successor)
    assert restriction.predecessor == predecessor
    assert restriction.successor == successor


def test_precedence_with_same_predecessor_and_successor_raises():
    instance = build_instance()
    task = build_task(instance)
    with pytest.raises(ValueError):
        Precedence(task, task)


#####################
# ForbiddenSequence #
#####################

def test_forbidden_sequence_employee_and_activities():
    instance = build_instance()
    employee = build_employee(instance)
    task_1 = build_task(instance, 0)
    task_2 = build_task(instance, 1)
    activities = [task_1, task_2]
    restriction = ForbiddenSequence(employee, activities)
    assert restriction.employee == employee
    assert restriction.activities == activities


def test_forbidden_sequence_with_fewer_than_two_activities_raises():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    with pytest.raises(ValueError):
        ForbiddenSequence(employee, [task])
