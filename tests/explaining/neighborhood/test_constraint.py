# Third-party library
import pytest

# Local libraries
from src.explaining.neighborhood.constraint import ImmediatePrecedence, SequenceFixed, SequenceOrderFixed
from tests.modeling.helpers import build_employee, build_instance, build_task


######################
# SequenceOrderFixed #
######################

def test_sequence_order_fixed_employee_and_scope():
    instance = build_instance()
    employee = build_employee(instance)
    constraint = SequenceOrderFixed(employee)
    assert constraint.employee == employee
    assert constraint.scope == frozenset({employee})


#################
# SequenceFixed #
#################

def test_sequence_fixed_employee_and_scope():
    instance = build_instance()
    employee = build_employee(instance)
    constraint = SequenceFixed(employee)
    assert constraint.employee == employee
    assert constraint.scope == frozenset({employee})


#######################
# ImmediatePrecedence #
#######################

def test_immediate_precedence_employee_predecessor_and_successor():
    instance = build_instance()
    employee = build_employee(instance)
    predecessor = build_task(instance, 0)
    successor = build_task(instance, 1)
    constraint = ImmediatePrecedence(employee, predecessor, successor)
    assert constraint.employee == employee
    assert constraint.predecessor == predecessor
    assert constraint.successor == successor
    assert constraint.scope == frozenset({employee})


def test_immediate_precedence_with_same_predecessor_and_successor_raises():
    instance = build_instance()
    employee = build_employee(instance)
    activity = build_task(instance)
    with pytest.raises(ValueError):
        ImmediatePrecedence(employee, activity, activity)
