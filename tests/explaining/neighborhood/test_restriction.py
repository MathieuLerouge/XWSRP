# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.restriction import ImmediatePrecedence, SequenceOrderFixed
from tests.modeling.helpers import build_instance, build_task


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
