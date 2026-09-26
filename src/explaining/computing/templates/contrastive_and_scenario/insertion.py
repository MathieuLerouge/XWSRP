# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.conflict import SkillConflict
from src.explaining.computing.templates.common.conflict import TailoredConflictBuilder
from src.explaining.computing.templates.common.description import TransformationDescriptionBuilder
from src.explaining.computing.templates.common.preconditions import TransformationPreconditionChecker, \
    INSERTING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.computing.templates.common.solver import TransformationModelSolver
from src.explaining.computing.templates.contrastive_and_scenario.result import \
    build_transformation_result_from_milp_model
from src.explaining.computing.templates.contrastive_and_scenario.milp.insertion import InsertionModel
from src.explaining.modeling.solution import EditableSolution
from src.modeling.activity import Activity
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.optimization.heuristics.evaluation import InsertionEvaluation
from src.optimization.heuristics.evaluator import Evaluator


####################
# InsertionApplier #
####################

class InsertionApplier:
    """
    Applies the transformation each insertion question induces, and reports what it ran into.

    The transformations related to (Ins,1) to (Ins,2c) templates are computed with polynomial algorithms,
    using Evaluator, while (Ins,3) rearranges the whole route and so goes through a MILP model,
    which is why it alone takes a solving time limit.
    """

    ##############
    # Polynomial #
    ##############

    @staticmethod
    def _build_result_from_evaluation(solution: EditableSolution, employee: Employee, task: Task,
                                      activity: Activity, evaluation: InsertionEvaluation) -> TransformationResult:
        """
        Build the result of the insertion the given evaluation evaluated.

        Args:
            solution: The solution to explain.
            employee: The employee whose sequence is to be transformed.
            task: The task to insert.
            activity: The activity after which the task is to be inserted.
            evaluation: The evaluation of the insertion.

        Returns:
            The result of the applied transformation.
        """
        transformation_is_feasible = evaluation.is_feasible
        support_solution = solution.copy(solution.name + "_support")
        if support_solution.get_task_performance_status(task):
            support_solution.remove_task(task, transformation_is_feasible, transformation_is_feasible)
        conflict = None
        if transformation_is_feasible:
            support_solution.insert_task_after_activity(task, activity, start_time=evaluation.start_time)
        else:
            if not evaluation.is_time_feasible:
                support_solution.insert_task_after_activity(
                    task, activity, evaluation.start_time,
                    evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
                    False, False, (not evaluation.is_skill_feasible)
                )
            else:
                support_solution.insert_task_after_activity(
                    task, activity, evaluation.start_time, None, None, False, False, True
                )
            sequence = support_solution.get_sequence(employee)
            conflict = TailoredConflictBuilder.build_from_evaluation(
                employee, task, sequence, sequence.get_step_index_of(activity) + 1, evaluation
            )
        descriptions = TransformationDescriptionBuilder.for_inserting_task_after_activity(task, activity, employee)
        return TransformationResult(support_solution, conflict, descriptions)

    @staticmethod
    def apply_1(solution: EditableSolution, employee_name: str, task_name: str,
                activity_name: str) -> TransformationResult:
        """
        Apply insertion corresponding to the (Ins,1) question:
        "Why is employee {Employee} not performing task {Task} just after activity {Activity}?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.
            activity_name: The name of the activity mentioned in the question.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        task = solution.instance.get_task_by_name(task_name)
        activity = solution.instance.get_hypothetical_activity_by_names(activity_name, employee_name)
        evaluation = Evaluator.evaluate_insertion_after(solution.get_sequence(employee), task, activity, False)
        return InsertionApplier._build_result_from_evaluation(solution, employee, task, activity, evaluation)

    @staticmethod
    def apply_2a(solution: EditableSolution, employee_name: str, task_name: str) -> TransformationResult:
        """
        Apply insertion corresponding to the (Ins,2a) question:
        "Why is employee {Employee} not performing task {Task} between two consecutive activities of their planning?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        task = solution.instance.get_task_by_name(task_name)
        evaluation = Evaluator.find_best_insertion_between_consecutive_activities(
            solution.get_sequence(employee), task, compute_times_only_if_skill_constraints_satisfied=False)
        activity = evaluation.activity_before_insertion
        return InsertionApplier._build_result_from_evaluation(solution, employee, task, activity, evaluation)

    @staticmethod
    def apply_2b(solution: EditableSolution, employee_name: str) -> TransformationResult:
        """
        Apply insertion corresponding to the (Ins,2b) question:
        "Why is employee {Employee} not performing any non-performed task
        between two consecutive activities of their planning?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.

        Returns:
            The result of the applied transformation.

        Raises:
            ImpossibleTransformationException: if the solution performs every task,
                or if the employee is not skilled enough for any of the non-performed ones.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        performable_non_performed_tasks = TransformationPreconditionChecker.get_performable_non_performed_tasks(
            solution, employee, INSERTING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE
        )
        evaluation = Evaluator.find_best_insertion_between_consecutive_activities_among_sets(
            solution, performable_non_performed_tasks, [employee], False
        )
        task = evaluation.inserted_task
        activity = evaluation.activity_before_insertion
        return InsertionApplier._build_result_from_evaluation(solution, employee, task, activity, evaluation)

    @staticmethod
    def apply_2c(solution: EditableSolution, task_name: str) -> TransformationResult:
        """
        Apply insertion corresponding to the (Ins,2c) question:
        "Why is any employee not performing task {Task} between two consecutive activities of their planning?"

        Args:
            solution: The solution to explain.
            task_name: The name of the task mentioned in the question.

        Returns:
            The result of the applied transformation.
        """
        task = solution.instance.get_task_by_name(task_name)
        evaluation = Evaluator.find_best_insertion_between_consecutive_activities_among_sets(
            solution, [task], solution.instance.employees, False
        )
        employee = evaluation.employee
        activity = evaluation.activity_before_insertion
        return InsertionApplier._build_result_from_evaluation(solution, employee, task, activity, evaluation)

    ########
    # MILP #
    ########

    @staticmethod
    def _describe(model: InsertionModel, employee: Employee, route_description: str) -> dict[str, str]:
        """Describe the insertion the given model computed, in every language."""
        return TransformationDescriptionBuilder.for_inserting_task_in_route(
            model.pivot_task, employee, route_description)

    @staticmethod
    def _build_model_3(solution: EditableSolution, employee_name: str, task_name: str,
                       solving_time_limit: Optional[int] = None) -> InsertionModel:
        """
        Build the MILP model answering the (Ins,3) question, without solving it.

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task to be inserted mentioned in the question.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The model, ready to be solved.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        task = solution.instance.get_task_by_name(task_name)
        model = InsertionModel(solution.get_sequence(employee), task)
        if solving_time_limit is not None:
            model.solving_time_limit = solving_time_limit
        return model

    @staticmethod
    def apply_3(solution: EditableSolution, employee_name: str, task_name: str,
                solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply insertion corresponding to the (Ins,3) question:
        "Why is employee {Employee} not performing task {Task} in addition to their activities?"

        An employee who is not skilled enough for the task is reported without solving anything: the model
        cannot relax a skill constraint, so there would be nothing for it to find.

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task to be inserted mentioned in the question.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        task = solution.instance.get_task_by_name(task_name)
        if not employee.is_capable_of_performing(task):
            return TransformationResult(
                solution.copy(solution.name + "_support"), SkillConflict(employee, task),
                TransformationDescriptionBuilder.for_inserting_task_in_route(task, employee, "")
            )
        model = InsertionApplier._build_model_3(solution, employee_name, task_name, solving_time_limit)
        TransformationModelSolver.solve_or_raise(model)
        return build_transformation_result_from_milp_model(solution, model, InsertionApplier._describe)
