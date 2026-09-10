# Local libraries
from src.explaining.neighborhood.constraint import SequenceFixed, SequenceOrderFixed
from tests.modeling.helpers import build_employee, build_instance


######################
# SequenceOrderFixed #
######################

def test_sequence_order_fixed_employee_and_employees():
    instance = build_instance()
    employee = build_employee(instance)
    constraint = SequenceOrderFixed(employee)
    assert constraint.employee == employee
    assert constraint.employees == frozenset({employee})


#################
# SequenceFixed #
#################

def test_sequence_fixed_employee_and_employees():
    instance = build_instance()
    employee = build_employee(instance)
    constraint = SequenceFixed(employee)
    assert constraint.employee == employee
    assert constraint.employees == frozenset({employee})
