# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.conflict import SkillConflict
from src.explaining.computing.progress import (
    analyze_solution, build_and_solve_model, describe_skill_check, report_evaluation_verdicts
)
from src.explaining.computing.templates.common.conflict import TailoredConflictBuilder
from src.explaining.computing.templates.common.description import TransformationDescriptionBuilder
from src.explaining.computing.templates.common.preconditions import TransformationPreconditionChecker, \
    EXCHANGING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.computing.templates.contrastive_and_scenario.result import \
    build_transformation_result_from_milp_model
from src.explaining.computing.templates.contrastive_and_scenario.milp.swap import SwapModel
from src.explaining.modeling.solution import EditableSolution
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.optimization.heuristics.evaluation import ReplacementEvaluation
from src.optimization.heuristics.evaluator import Evaluator
from src.utils.progress import SILENT_PROGRESS_REPORTER, ProgressReporter, ProgressStep


###############
# SwapApplier #
###############

class SwapApplier:
    """
    Applies the transformation each swap question induces, and reports what it ran into.

    The transformations related to (Swp,1) to (Swp,2c) templates are computed with polynomial algorithms,
    using Evaluator, while (Swp,3) may reorder the rest of the route and so goes through a MILP model,
    which is why it alone takes a solving time limit.
    """

    ##############
    # Polynomial #
    ##############

    @staticmethod
    def _build_result_from_evaluation(solution: EditableSolution, employee: Employee, replacing_task: Task,
                                      leaving_task: Task, evaluation: ReplacementEvaluation) -> TransformationResult:
        """
        Build the result of the swap the given evaluation evaluated.

        Args:
            solution: The solution to explain.
            employee: The employee whose sequence is to be transformed.
            replacing_task: The task that will replace the leaving task.
            leaving_task: The task that will be replaced by the replacing task.
            evaluation: The evaluation of the swap.

        Returns:
            The result of the applied transformation.
        """
        transformation_is_feasible = evaluation.is_feasible  # Sequence-wise
        support_solution = solution.copy(solution.name + "_support")
        conflict = None
        if transformation_is_feasible:
            support_solution.replace_task_by_another(leaving_task, replacing_task, evaluation.start_time)
        else:
            if not evaluation.is_time_feasible:
                support_solution.replace_task_by_another(
                    leaving_task, replacing_task, evaluation.start_time,
                    evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
                    False, False, (not evaluation.is_skill_feasible)
                )
            else:
                support_solution.replace_task_by_another(
                    leaving_task, replacing_task, evaluation.start_time, None, None, False, False, True
                )
            sequence = support_solution.get_sequence(employee)
            conflict = TailoredConflictBuilder.build_from_evaluation(
                employee, replacing_task, sequence, sequence.get_step_index_of(replacing_task), evaluation
            )
        descriptions = TransformationDescriptionBuilder.for_replacing_task_with_another(
            leaving_task, replacing_task, employee)
        return TransformationResult(support_solution, conflict, descriptions)

    @staticmethod
    def _report_evaluation(step: ProgressStep, employee: Employee, replacing_task: Task, leaving_task: Task,
                           evaluation: ReplacementEvaluation):
        """
        Report the swap the evaluation settled on, and its verdicts, as details of the step evaluating it.

        Args:
            step: The step evaluating the swap.
            employee: The employee whose sequence is to be transformed.
            replacing_task: The task that will replace the leaving task.
            leaving_task: The task that will be replaced by the replacing task.
            evaluation: The evaluation of the swap.
        """
        step.info("Swap", f"{replacing_task.name} in place of {leaving_task.name} in {employee.name}'s route")
        report_evaluation_verdicts(step, evaluation)

    @staticmethod
    def apply_1(solution: EditableSolution, employee_name: str, task1_name: str, task2_name: str,
                progress_reporter: ProgressReporter = SILENT_PROGRESS_REPORTER) -> TransformationResult:
        """
        Apply swap corresponding to the (Swp,1) question:
        "Why is employee {Employee} not performing task {Task1} in place of task {Task2}?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task1_name: The name of the first task mentioned in the question, the one taking the other's place.
            task2_name: The name of the second task mentioned in the question, the one being replaced.
            progress_reporter: What each step of the transformation is reported to as it runs.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        task1 = solution.instance.get_task_by_name(task1_name)
        task2 = solution.instance.get_task_by_name(task2_name)
        with progress_reporter.step("Evaluating the swap") as step:
            evaluation = Evaluator.evaluate_replacing_task_with_another(
                solution.get_sequence(employee), task2, task1, False)
            SwapApplier._report_evaluation(step, employee, task1, task2, evaluation)
        return analyze_solution(progress_reporter, lambda: SwapApplier._build_result_from_evaluation(
            solution, employee, task1, task2, evaluation))

    @staticmethod
    def apply_2a(solution: EditableSolution, employee_name: str, task_name: str,
                 progress_reporter: ProgressReporter = SILENT_PROGRESS_REPORTER) -> TransformationResult:
        """
        Apply swap corresponding to the (Swp,2a) question:
        "Why is employee {Employee} not performing task {Task} in place of one of their tasks?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.
            progress_reporter: What each step of the transformation is reported to as it runs.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        entering_task = solution.instance.get_task_by_name(task_name)
        with progress_reporter.step("Evaluating the swap") as step:
            evaluation = Evaluator.find_best_task_to_be_replaced_with_given_task(
                solution.get_sequence(employee), entering_task, False)
            replaced_task = evaluation.replaced_task
            SwapApplier._report_evaluation(step, employee, entering_task, replaced_task, evaluation)
        return analyze_solution(progress_reporter, lambda: SwapApplier._build_result_from_evaluation(
            solution, employee, entering_task, replaced_task, evaluation))

    @staticmethod
    def apply_2b(solution: EditableSolution, employee_name: str,
                 progress_reporter: ProgressReporter = SILENT_PROGRESS_REPORTER) -> TransformationResult:
        """
        Apply swap corresponding to the (Swp,2b) question:
        "Why is employee {Employee} not performing any non-performed task one of their tasks?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            progress_reporter: What each step of the transformation is reported to as it runs.

        Returns:
            The result of the applied transformation.

        Raises:
            ImpossibleTransformationException: if the solution performs every task,
                or if the employee is not skilled enough for any of the non-performed ones.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        with progress_reporter.step("Evaluating the swap") as step:
            performable_non_performed_tasks = TransformationPreconditionChecker.get_performable_non_performed_tasks(
                solution, employee, EXCHANGING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE
            )
            evaluation = Evaluator.find_best_replacement_among_sets(
                solution, [employee], performable_non_performed_tasks, False)
            replacing_task = evaluation.replacing_task
            replaced_task = evaluation.replaced_task
            SwapApplier._report_evaluation(step, employee, replacing_task, replaced_task, evaluation)
        return analyze_solution(progress_reporter, lambda: SwapApplier._build_result_from_evaluation(
            solution, employee, replacing_task, replaced_task, evaluation))

    @staticmethod
    def apply_2c(solution: EditableSolution, task_name: str,
                 progress_reporter: ProgressReporter = SILENT_PROGRESS_REPORTER) -> TransformationResult:
        """
        Apply swap corresponding to the (Swp,2c) question:
        "Why is any employee is not performing task {Task} in place of one of their tasks?"

        Args:
            solution: The solution to explain.
            task_name: The name of the task mentioned in the question.
            progress_reporter: What each step of the transformation is reported to as it runs.

        Returns:
            The result of the applied transformation.
        """
        replacing_task = solution.instance.get_task_by_name(task_name)
        with progress_reporter.step("Evaluating the swap") as step:
            evaluation = Evaluator.find_best_replacement_among_sets(
                solution, solution.performing_employees, [replacing_task], False)
            employee = evaluation.employee
            replaced_task = evaluation.replaced_task
            SwapApplier._report_evaluation(step, employee, replacing_task, replaced_task, evaluation)
        return analyze_solution(progress_reporter, lambda: SwapApplier._build_result_from_evaluation(
            solution, employee, replacing_task, replaced_task, evaluation))

    ########
    # MILP #
    ########

    @staticmethod
    def _describe(model: SwapModel, employee: Employee, route_description: str) -> dict[str, str]:
        """Describe the swap the given model computed, in every language."""
        return TransformationDescriptionBuilder.for_replacing_task_in_route(
            model.leaving_task, model.pivot_task, employee, route_description)

    @staticmethod
    def _build_model_3(solution: EditableSolution, employee_name: str, task_name: str,
                       solving_time_limit: Optional[int] = None) -> SwapModel:
        """
        Build the MILP model answering the (Swp,3) question, without solving it.

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The model, ready to be solved.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        task = solution.instance.get_task_by_name(task_name)
        model = SwapModel(solution.get_sequence(employee), task)
        if solving_time_limit is not None:
            model.solving_time_limit = solving_time_limit
        return model

    @staticmethod
    def apply_3(solution: EditableSolution, employee_name: str, task_name: str,
                solving_time_limit: Optional[int] = None,
                progress_reporter: ProgressReporter = SILENT_PROGRESS_REPORTER) -> TransformationResult:
        """
        Apply swap corresponding to the (Swp,3) question:
        "Why is employee {Employee} not performing task {Task} instead of any of their already-performed tasks
        (even if it means changing their order)?"

        An employee who is not skilled enough for the task is reported without solving anything: the model
        cannot relax a skill constraint, so there would be nothing for it to find.

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.
            solving_time_limit: The solving time limit in seconds, or None for no limit.
            progress_reporter: What each step of the transformation is reported to as it runs.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        task = solution.instance.get_task_by_name(task_name)
        with progress_reporter.step("Checking skills") as step:
            skill_conflict = None if employee.is_capable_of_performing(task) else SkillConflict(employee, task)
            step.info("Skill conflict", describe_skill_check(skill_conflict))
        if skill_conflict is not None:
            return analyze_solution(progress_reporter, lambda: TransformationResult(
                solution.copy(solution.name + "_support"), skill_conflict, TransformationDescriptionBuilder.none()
            ))
        model = build_and_solve_model(
            progress_reporter, SwapModel.__name__,
            lambda: SwapApplier._build_model_3(solution, employee_name, task_name, solving_time_limit)
        )
        return analyze_solution(progress_reporter, lambda: build_transformation_result_from_milp_model(
            solution, model, SwapApplier._describe))
