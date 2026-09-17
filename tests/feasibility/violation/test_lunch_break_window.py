# Local libraries
from src.feasibility.violation.lunch_break_window import LunchBreakWindowViolation
from src.utils.timeset import TimeInterval
from tests.feasibility.helpers import build_employee


def test_lunch_break_window_violation_text_reports_the_lunch_break_and_allowed_windows():
    employee = build_employee()
    violation = LunchBreakWindowViolation(employee, lunch_break_start_time=700, lunch_break_end_time=730,
                                          lunch_break_time_lb=660, lunch_break_time_ub=780)
    assert violation.text == (
        f"{employee.name} is supposed to have a lunch break over "
        f"{TimeInterval(700, 730)} while lunch break must be within {TimeInterval(660, 780)}."
    )


def test_lunch_break_window_violation_properties_return_constructor_arguments():
    employee = build_employee()
    violation = LunchBreakWindowViolation(employee, lunch_break_start_time=700, lunch_break_end_time=730,
                                          lunch_break_time_lb=660, lunch_break_time_ub=780)
    assert violation.employee is employee
    assert violation.lunch_break_start_time == 700
    assert violation.lunch_break_end_time == 730
    assert violation.lunch_break_time_lb == 660
    assert violation.lunch_break_time_ub == 780
