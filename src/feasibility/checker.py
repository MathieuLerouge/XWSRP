# Local libraries
from src.feasibility.violation import *
from src.modeling.solution import Solution
from src.modeling.task import Task
from src.utils.constants import LINE_BREAK_STRING
#from tests.explaining.neighborhood.llm.test_extractor_quality import solution


######################
# FeasibilityChecker #
######################

class FeasibilityChecker:
    """
    Checks whether a solution satisfies the covering, time-window, time-sequence, and skill constraints.

    Which families compute_violations() and is_feasible() account for is controlled by the covering,
    time_windows, time_sequence, and skill properties. time_windows, time_sequence, and skill default to
    True; covering defaults to the solution's instance's must_cover_all_tasks.
    """

    def __init__(self, solution: Solution, tolerance_in_minutes: int = 0):
        """
        Args:
            solution: Solution to check.
            tolerance_in_minutes: Tolerance, in minutes, used when checking the time sequence constraints to
                consider that two times are equal.
        """
        self._solution = solution
        self._tolerance_in_minutes = tolerance_in_minutes
        self._covering = solution.instance.must_cover_all_tasks
        self._time_windows = True
        self._time_sequence = True
        self._skill = True

    @property
    def solution(self):
        """Solution to check."""
        return self._solution

    @property
    def tolerance_in_minutes(self):
        """Tolerance, in minutes, used when checking the time sequence constraints to consider two times equal."""
        return self._tolerance_in_minutes

    @property
    def covering(self) -> bool:
        """Whether covering violations are computed, default from the instance's must_cover_all_tasks."""
        return self._covering

    @covering.setter
    def covering(self, covering: bool):
        self._covering = covering

    @property
    def time_windows(self) -> bool:
        """Whether time window violations are computed. Defaults to True."""
        return self._time_windows

    @time_windows.setter
    def time_windows(self, time_windows: bool):
        self._time_windows = time_windows

    @property
    def time_sequence(self) -> bool:
        """Whether time sequence violations are computed. Defaults to True."""
        return self._time_sequence

    @time_sequence.setter
    def time_sequence(self, time_sequence: bool):
        self._time_sequence = time_sequence

    @property
    def skill(self) -> bool:
        """Whether skill violations are computed. Defaults to True."""
        return self._skill

    @skill.setter
    def skill(self, skill: bool):
        self._skill = skill

    def compute_covering_violations(self) -> list[Violation]:
        """
        Checks that every task of the instance is performed.

        Returns:
            A CoveringViolation for each task that is not performed.
        """
        return [CoveringViolation(task) for task in self._solution.instance.tasks
                if not self._solution.get_task_performance_status(task)]

    def compute_time_windows_violations(self) -> list[Violation]:
        """
        Checks that every performed task, and every employee's lunch break, is taken within its time window.

        Returns:
            A TaskTimeWindowViolation, EmployeeStartTimeViolation, EmployeeEndTimeViolation, or
            EmployeeUnavailabilityViolation per offending task, and a LunchBreakWindowViolation per employee
            whose lunch break falls outside of the instance's dedicated lunch break time window.
        """
        violations: list[Violation] = []

        # Check that tasks are performed within availability time windows
        for task in self._solution.instance.tasks:
            if self._solution.get_task_performance_status(task):
                start_time = self._solution.get_task_start_time(task)
                end_time = start_time + task.duration
                employee = self._solution.get_task_assignee(task)

                # - Task
                task_available_when_performed = False
                for availability_TW in task.time_windows.intervals:
                    if availability_TW.contain_all([start_time, end_time]):
                        task_available_when_performed = True
                        break
                if not task_available_when_performed:
                    violations.append(TaskTimeWindowViolation(task, employee, start_time, end_time))

                # - Employee
                if start_time < employee.start_time_lb:
                    violations.append(EmployeeStartTimeViolation(task, employee, start_time, end_time))
                if employee.end_time_ub < end_time:
                    violations.append(EmployeeEndTimeViolation(task, employee, start_time, end_time))
                for unavailability in employee.unavailabilities:
                    if (unavailability.time_windows[0].contain(start_time) or
                            unavailability.time_windows[0].contain(end_time)):
                        violations.append(
                            EmployeeUnavailabilityViolation(task, employee, start_time, end_time, unavailability)
                        )

        # Check that lunch breaks are taken within dedicated time windows
        if self._solution.instance.has_lunch_break:
            for employee in self._solution.instance.employees:
                lunch_break_start_time = self._solution.get_employee_lunch_break_start_time(employee)
                lunch_break_end_time = lunch_break_start_time + self._solution.instance.lunch_break_duration
                if (lunch_break_start_time < self._solution.instance.lunch_break_time_lb or
                        self._solution.instance.lunch_break_time_ub < lunch_break_end_time):
                    violations.append(LunchBreakWindowViolation(
                        employee, lunch_break_start_time, lunch_break_end_time,
                        self._solution.instance.lunch_break_time_lb, self._solution.instance.lunch_break_time_ub,
                    ))

        return violations

    def compute_time_sequence_violations(self) -> list[Violation]:
        """
        Checks that every employee's sequence of steps is consistent time-wise.

        Returns:
            A SequenceStartViolation, SequenceStepViolation, or SequenceEndViolation per offending employee.
        """
        violations: list[Violation] = []

        for employee in self._solution.instance.employees:
            sequence = self._solution[employee.name]
            if len(sequence) > 2:

                # Check start-to-first-step sequence (if first step is a task)
                first_step = sequence[1]
                if isinstance(first_step.activity, Task):
                    if sequence[0].start_time < employee.start_time_lb - self._tolerance_in_minutes:
                        violations.append(SequenceStartViolation(employee, sequence[0], first_step))

                # Check step-to-step sequence (including unavailabilities)
                for previous_step_index, step in enumerate(sequence[1: -1]):
                    if step.arrival_time > step.start_time + self._tolerance_in_minutes:
                        previous_step = sequence[previous_step_index]
                        crosses_lunch_break = (
                            self._solution.instance.has_lunch_break and
                            self._solution.get_activity_after_employee_lunch(employee) == step.activity
                        )
                        actual_traveling_duration = self._solution.compute_traveling_duration(previous_step, step)
                        if crosses_lunch_break:
                            allowed_traveling_duration = (step.start_time - previous_step.end_time -
                                                          self._solution.instance.lunch_break_duration)
                        else:
                            allowed_traveling_duration = step.start_time - previous_step.end_time
                        violations.append(SequenceStepViolation(
                            employee, previous_step, step, crosses_lunch_break,
                            allowed_traveling_duration, actual_traveling_duration,
                        ))

                # Check last-step-to-end sequence (if last step is a task)
                last_step = sequence[-2]
                if isinstance(last_step.activity, Task):
                    if sequence[-1].arrival_time > employee.end_time_ub + self._tolerance_in_minutes:
                        violations.append(SequenceEndViolation(employee, last_step, sequence[-1]))

        return violations

    def compute_skill_violations(self) -> list[Violation]:
        """
        Checks that every performed task is performed by an employee with a sufficient skill level.

        Returns:
            A SkillViolation per task performed by an under-qualified employee.
        """
        violations = []
        for task in self._solution.instance.tasks:
            if self._solution.get_task_performance_status(task):
                employee = self._solution.get_task_assignee(task)
                if not employee.is_capable_of_performing(task):
                    violations.append(SkillViolation(task, employee))
        return violations

    def compute_violations(self) -> list[Violation]:
        """
        Computes the violations of every enabled constraint family.

        Which families are enabled is controlled by the covering, time_windows, time_sequence, and skill
        properties.

        Returns:
            The violations found by the enabled families, in covering/time-window/time-sequence/skill order.
        """
        violations: list[Violation] = []
        if self._covering:
            violations += self.compute_covering_violations()
        if self._time_windows:
            violations += self.compute_time_windows_violations()
        if self._time_sequence:
            violations += self.compute_time_sequence_violations()
        if self._skill:
            violations += self.compute_skill_violations()
        return violations

    def is_feasible(self) -> bool:
        """
        Returns whether the solution satisfies the enabled constraint families.

        Which families are enabled is controlled by the covering, time_windows, time_sequence, and skill
        properties.

        Returns:
            True if none of the enabled families has any violation, False otherwise.
        """
        return not self.compute_violations()

    def report(self) -> str:
        """
        Renders the human-readable feasibility report for the enabled constraint families.

        Returns:
            "Solution <name> is feasible" if compute_violations() finds no violation, otherwise
            "Solution <name> is not feasible" followed by each violation's text.
        """
        violations = self.compute_violations()
        if not violations:
            return f"Solution {self.solution.name} is feasible"
        else:
            return (f"Solution {self.solution.name} is not feasible" + LINE_BREAK_STRING +
                    LINE_BREAK_STRING.join(violation.text for violation in violations))
