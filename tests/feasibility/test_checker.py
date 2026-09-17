# Local libraries
from src.feasibility.checker import FeasibilityChecker
from src.feasibility.violation.covering import CoveringViolation
from src.feasibility.violation.employee_end_time import EmployeeEndTimeViolation
from src.feasibility.violation.employee_start_time import EmployeeStartTimeViolation
from src.feasibility.violation.employee_unavailability import EmployeeUnavailabilityViolation
from src.feasibility.violation.sequence_end import SequenceEndViolation
from src.feasibility.violation.sequence_start import SequenceStartViolation
from src.feasibility.violation.sequence_step import SequenceStepViolation
from src.feasibility.violation.skill import SkillViolation
from src.feasibility.violation.task_time_window import TaskTimeWindowViolation
from src.utils.location import Location
from tests.modeling.helpers import build_employee, build_instance, build_sequence, build_solution, build_task


def perform_all_tasks(instance, solution, assignee):
    """Marks every task of instance as performed by assignee in solution, at its own start_time_lb."""
    for task in instance.tasks:
        solution.set_task_performance_status(task, True)
        solution.set_task_assignee(task, assignee)
        solution.set_task_start_time(task, task.start_time_lb)


###############################
# compute_covering_violations #
###############################

def test_compute_covering_violations_returns_no_violation_when_every_task_is_performed():
    instance = build_instance()
    employee = build_employee(instance)
    solution = build_solution(instance, "solution", {})
    perform_all_tasks(instance, solution, employee)
    assert FeasibilityChecker(solution).compute_covering_violations() == []


def test_compute_covering_violations_returns_one_violation_per_non_performed_task():
    instance = build_instance()
    employee = build_employee(instance)
    solution = build_solution(instance, "solution", {})
    perform_all_tasks(instance, solution, employee)
    held_out_task = build_task(instance, 0)
    solution.set_task_performance_status(held_out_task, False)
    violations = FeasibilityChecker(solution).compute_covering_violations()
    assert len(violations) == 1
    assert isinstance(violations[0], CoveringViolation)
    assert violations[0].task == held_out_task


###################################
# compute_time_windows_violations #
###################################

def test_compute_time_windows_violations_returns_no_violation_for_a_well_placed_task():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    solution = build_solution(instance, "solution", {})
    solution.set_task_performance_status(task, True)
    solution.set_task_assignee(task, employee)
    solution.set_task_start_time(task, max(task.start_time_lb, employee.start_time_lb))
    assert FeasibilityChecker(solution).compute_time_windows_violations() == []


def test_compute_time_windows_violations_flags_a_task_started_before_its_own_time_window():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    solution = build_solution(instance, "solution", {})
    solution.set_task_performance_status(task, True)
    solution.set_task_assignee(task, employee)
    solution.set_task_start_time(task, task.start_time_lb - 10)
    violations = FeasibilityChecker(solution).compute_time_windows_violations()
    assert any(isinstance(violation, TaskTimeWindowViolation) for violation in violations)


def test_compute_time_windows_violations_flags_a_task_started_before_the_employee_start_time_lb():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    solution = build_solution(instance, "solution", {})
    solution.set_task_performance_status(task, True)
    solution.set_task_assignee(task, employee)
    solution.set_task_start_time(task, employee.start_time_lb - 5)
    violations = FeasibilityChecker(solution).compute_time_windows_violations()
    assert any(isinstance(violation, EmployeeStartTimeViolation) for violation in violations)


def test_compute_time_windows_violations_flags_a_task_ending_after_the_employee_end_time_ub():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    solution = build_solution(instance, "solution", {})
    solution.set_task_performance_status(task, True)
    solution.set_task_assignee(task, employee)
    solution.set_task_start_time(task, employee.end_time_ub - task.duration + 5)
    violations = FeasibilityChecker(solution).compute_time_windows_violations()
    assert any(isinstance(violation, EmployeeEndTimeViolation) for violation in violations)


def test_compute_time_windows_violations_flags_a_task_performed_during_an_unavailability():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    start_time = max(task.start_time_lb, employee.start_time_lb)
    employee.add_unavailability(Location(0, 0), start_time, start_time + task.duration)
    solution = build_solution(instance, "solution", {})
    solution.set_task_performance_status(task, True)
    solution.set_task_assignee(task, employee)
    solution.set_task_start_time(task, start_time)
    violations = FeasibilityChecker(solution).compute_time_windows_violations()
    assert any(isinstance(violation, EmployeeUnavailabilityViolation) for violation in violations)


####################################
# compute_time_sequence_violations #
####################################

def test_compute_time_sequence_violations_returns_no_violation_for_a_consistent_sequence():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    start_time = max(task.start_time_lb, employee.start_time_lb)
    sequence = build_sequence(instance, employee, [(task, start_time)])
    solution = build_solution(instance, "solution", {employee.name: sequence})
    assert FeasibilityChecker(solution).compute_time_sequence_violations() == []


def test_compute_time_sequence_violations_flags_a_departure_scheduled_before_the_employee_start_time_lb():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    start_time = max(task.start_time_lb, employee.start_time_lb)
    sequence = build_sequence(instance, employee, [(task, start_time)])
    sequence[0].start_time = employee.start_time_lb - 50
    solution = build_solution(instance, "solution", {employee.name: sequence})
    violations = FeasibilityChecker(solution).compute_time_sequence_violations()
    assert any(isinstance(violation, SequenceStartViolation) for violation in violations)


def test_compute_time_sequence_violations_flags_a_step_arriving_after_it_is_supposed_to_start():
    instance = build_instance()
    employee = build_employee(instance)
    task_1 = build_task(instance, 0)
    task_2 = build_task(instance, 1)
    start_time_1 = max(task_1.start_time_lb, employee.start_time_lb)
    start_time_2 = start_time_1 + task_1.duration + 120
    sequence = build_sequence(instance, employee, [(task_1, start_time_1), (task_2, start_time_2)])
    sequence[2].arrival_time = sequence[2].start_time + 100
    solution = build_solution(instance, "solution", {employee.name: sequence})
    violations = FeasibilityChecker(solution).compute_time_sequence_violations()
    step_violations = [violation for violation in violations if isinstance(violation, SequenceStepViolation)]
    assert len(step_violations) == 1
    assert step_violations[0].crosses_lunch_break is False


def test_compute_time_sequence_violations_flags_a_comeback_arriving_after_the_employee_end_time_ub():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    start_time = max(task.start_time_lb, employee.start_time_lb)
    sequence = build_sequence(instance, employee, [(task, start_time)])
    sequence[-1].arrival_time = employee.end_time_ub + 50
    solution = build_solution(instance, "solution", {employee.name: sequence})
    violations = FeasibilityChecker(solution).compute_time_sequence_violations()
    assert any(isinstance(violation, SequenceEndViolation) for violation in violations)


def test_compute_time_sequence_violations_tolerance_in_minutes_absorbs_a_small_arrival_delay():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    start_time = max(task.start_time_lb, employee.start_time_lb)
    sequence = build_sequence(instance, employee, [(task, start_time)])
    sequence[-1].arrival_time = employee.end_time_ub + 5
    solution = build_solution(instance, "solution", {employee.name: sequence})
    assert FeasibilityChecker(solution, tolerance_in_minutes=4).compute_time_sequence_violations() != []
    assert FeasibilityChecker(solution, tolerance_in_minutes=10).compute_time_sequence_violations() == []


############################
# compute_skill_violations #
############################

def test_compute_skill_violations_returns_no_violation_for_a_qualified_employee():
    instance = build_instance()
    employee = build_employee(instance)
    task = build_task(instance)
    solution = build_solution(instance, "solution", {})
    solution.set_task_performance_status(task, True)
    solution.set_task_assignee(task, employee)
    solution.set_task_start_time(task, max(task.start_time_lb, employee.start_time_lb))
    assert FeasibilityChecker(solution).compute_skill_violations() == []


def test_compute_skill_violations_flags_a_task_performed_by_an_under_qualified_employee():
    instance = build_instance()
    task = next(task for task in instance.tasks if task.skill_level > 1)
    employee = next(employee for employee in instance.employees if employee.skill_level < task.skill_level)
    solution = build_solution(instance, "solution", {})
    solution.set_task_performance_status(task, True)
    solution.set_task_assignee(task, employee)
    solution.set_task_start_time(task, max(task.start_time_lb, employee.start_time_lb))
    violations = FeasibilityChecker(solution).compute_skill_violations()
    assert len(violations) == 1
    assert isinstance(violations[0], SkillViolation)


####################
# Default toggles  #
####################

def test_covering_defaults_to_false_when_the_instance_does_not_require_covering_all_tasks():
    instance = build_instance()
    instance.must_cover_all_tasks = False
    solution = build_solution(instance, "solution", {})
    checker = FeasibilityChecker(solution)
    assert checker.covering is False
    assert checker.time_windows is True
    assert checker.time_sequence is True
    assert checker.skill is True


def test_covering_defaults_to_true_when_the_instance_requires_covering_all_tasks():
    instance = build_instance()
    instance.must_cover_all_tasks = True
    solution = build_solution(instance, "solution", {})
    assert FeasibilityChecker(solution).covering is True


def test_toggle_setters_override_the_default():
    instance = build_instance()
    instance.must_cover_all_tasks = False
    solution = build_solution(instance, "solution", {})
    checker = FeasibilityChecker(solution)
    checker.covering = True
    checker.time_windows = False
    checker.time_sequence = False
    checker.skill = False
    assert checker.covering is True
    assert checker.time_windows is False
    assert checker.time_sequence is False
    assert checker.skill is False


######################
# compute_violations #
######################

def test_compute_violations_defaults_to_time_windows_sequence_and_skill_without_covering():
    instance = build_instance()
    instance.must_cover_all_tasks = False
    solution = build_solution(instance, "solution", {})
    violations = FeasibilityChecker(solution).compute_violations()
    assert not any(isinstance(violation, CoveringViolation) for violation in violations)


def test_compute_violations_with_covering_enabled_includes_covering_violations():
    instance = build_instance()
    solution = build_solution(instance, "solution", {})
    checker = FeasibilityChecker(solution)
    checker.covering = True
    checker.time_windows = False
    checker.time_sequence = False
    checker.skill = False
    violations = checker.compute_violations()
    assert len(violations) == instance.nb_tasks
    assert all(isinstance(violation, CoveringViolation) for violation in violations)


def test_compute_violations_with_every_toggle_disabled_returns_no_violation():
    instance = build_instance()
    solution = build_solution(instance, "solution", {})
    checker = FeasibilityChecker(solution)
    checker.covering = False
    checker.time_windows = False
    checker.time_sequence = False
    checker.skill = False
    assert checker.compute_violations() == []


def test_is_feasible_matches_the_emptiness_of_compute_violations():
    instance = build_instance()
    employee = build_employee(instance)
    solution = build_solution(instance, "solution", {})
    perform_all_tasks(instance, solution, employee)
    checker = FeasibilityChecker(solution)
    checker.covering = True
    assert checker.is_feasible() == (not checker.compute_violations())


##########
# report #
##########

def test_report_with_no_violation_returns_the_feasible_message():
    instance = build_instance()
    instance.must_cover_all_tasks = False
    solution = build_solution(instance, "solution", {})
    assert FeasibilityChecker(solution).report() == f"Solution {solution.name} is feasible"


def test_report_with_violations_joins_their_text():
    instance = build_instance()
    solution = build_solution(instance, "solution", {})
    checker = FeasibilityChecker(solution)
    checker.covering = True
    checker.time_windows = False
    checker.time_sequence = False
    checker.skill = False
    violations = checker.compute_violations()
    report = checker.report()
    assert report.startswith(f"Solution {solution.name} is not feasible")
    for violation in violations:
        assert violation.text in report
