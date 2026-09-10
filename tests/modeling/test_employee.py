# Local libraries
from src.modeling.employee import Employee
from src.utils.location import Location
from tests.modeling.helpers import build_employee, build_instance


###########
# __eq__  #
###########

def test_employee_eq_with_same_name_returns_true():
    # Two separate loads of the same instance file: same name, but not the same Employee object.
    employee_1 = build_employee(build_instance())
    employee_2 = build_employee(build_instance())
    assert employee_1 == employee_2


def test_employee_eq_with_different_name_returns_false():
    instance = build_instance()
    employee_1 = build_employee(instance, 0)
    employee_2 = build_employee(instance, 1)
    assert employee_1 != employee_2


def test_employee_eq_ignores_other_fields():
    employee_1 = Employee("Alice", start_time_lb=480, end_time_ub=1020, location=Location(0, 0), skill_level=1)
    employee_2 = Employee("Alice", start_time_lb=540, end_time_ub=900, location=Location(10, 10), skill_level=3)
    assert employee_1 == employee_2


def test_employee_eq_with_non_employee_returns_false():
    employee = build_employee(build_instance())
    assert employee != "not an employee"
