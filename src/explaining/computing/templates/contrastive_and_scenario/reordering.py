# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.templates.common.conflict import TailoredConflictBuilder
from src.explaining.computing.templates.common.description import TransformationDescriptionBuilder
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.computing.templates.common.runner import MILPTransformationRunner
from src.explaining.computing.templates.contrastive_and_scenario.result import \
    build_transformation_result_from_milp_model
from src.explaining.computing.templates.contrastive_and_scenario.milp.reordering import ReorderingModel
from src.explaining.modeling.solution import EditableSolution
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.optimization.heuristics.evaluation import ReorderEvaluation
from src.optimization.heuristics.evaluator import Evaluator


#####################
# ReorderingApplier #
#####################

class ReorderingApplier:
    """
    Applies the transformation each reordering question induces, and reports what it ran into.

    The transformations related to (Ord,1a) to (Ord,2c) templates move one task and are computed with
    polynomial algorithms, using Evaluator, while (Ord,3) reorders the whole route and so goes through
    a MILP model, which is why it alone takes a solving time limit.
    """

    ##############
    # Polynomial #
    ##############

    @staticmethod
    def _build_result_from_evaluation(solution: EditableSolution, employee: Employee, moving_task: Task,
                                      fixed_task: Task, evaluation: ReorderEvaluation) -> TransformationResult:
        """
        Build the result of the repositioning the given evaluation evaluated.

        Which side of the fixed task the moving task lands on is read off the sequence rather than passed in:
        a task standing before the fixed one can only be moved after it, and the other way round.

        Args:
            solution: The solution to explain.
            employee: The employee whose sequence is to be transformed.
            moving_task: The task to be moved within the employee's sequence.
            fixed_task: The fixed task before or after which the moving task is repositioned.
            evaluation: The evaluation of the repositioning.

        Returns:
            The result of the applied transformation.

        Raises:
            ValueError: if the repositioning is infeasible for anything but time reasons, which a
                repositioning cannot be: it leaves every task with the employee already performing it.
        """
        support_sequence = solution.get_sequence(employee)
        moves_after_fixed_task = \
            support_sequence.get_step_index_of(moving_task) < support_sequence.get_step_index_of(fixed_task)
        transformation_is_feasible = evaluation.is_feasible
        support_solution = solution.copy(solution.name + "_support")
        conflict = None
        if transformation_is_feasible:
            if moves_after_fixed_task:
                support_solution.reposition_task_in_sequence_after_activity(
                    moving_task, fixed_task, evaluation.start_time)
            else:
                support_solution.reposition_task_in_sequence_before_activity(
                    moving_task, fixed_task, evaluation.start_time)
        else:
            if not evaluation.is_time_feasible:
                if moves_after_fixed_task:
                    support_solution.reposition_task_in_sequence_after_activity(
                        moving_task, fixed_task, evaluation.start_time,
                        evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
                        False, False
                    )
                else:
                    support_solution.reposition_task_in_sequence_before_activity(
                        moving_task, fixed_task, evaluation.start_time,
                        evaluation.earliest_start_time_for_upstream, evaluation.latest_start_time_for_downstream,
                        False, False
                    )
                support_sequence = support_solution.get_sequence(employee)
                conflict = TailoredConflictBuilder.build_from_evaluation(
                    employee, moving_task, support_sequence,
                    support_sequence.get_step_index_of(moving_task), evaluation
                )
            else:
                raise ValueError("The conflict should only be due to time considerations.")
        if moves_after_fixed_task:
            descriptions = TransformationDescriptionBuilder.for_repositioning_after(moving_task, fixed_task, employee)
        else:
            descriptions = TransformationDescriptionBuilder.for_repositioning_before(moving_task, fixed_task, employee)
        return TransformationResult(support_solution, conflict, descriptions)

    @staticmethod
    def apply_1a(solution: EditableSolution, employee_name: str,
                 task_name_1: str, task_name_2: str) -> TransformationResult:
        """
        Apply reordering corresponding to the (Ord,1a) question:
        "Why is employee {Employee} not performing task {Task1} later in their route, just after task {Task2}?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name_1: The name of the first task mentioned in the question, the one being moved.
            task_name_2: The name of the second task mentioned in the question, the one staying put.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        task_1 = solution.instance.get_task_by_name(task_name_1)
        task_2 = solution.instance.get_task_by_name(task_name_2)
        evaluation = Evaluator.evaluate_moving_after_a_task(solution.get_sequence(employee), task_1, task_2)
        return ReorderingApplier._build_result_from_evaluation(solution, employee, task_1, task_2, evaluation)

    @staticmethod
    def apply_1b(solution: EditableSolution, employee_name: str,
                 task_name_1: str, task_name_2: str) -> TransformationResult:
        """
        Apply reordering corresponding to the (Ord,1b) question:
        "Why is employee {Employee} not performing task {Task1} earlier in their route, just before task {Task2}?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name_1: The name of the first task mentioned in the question, the one being moved.
            task_name_2: The name of the second task mentioned in the question, the one staying put.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        task_1 = solution.instance.get_task_by_name(task_name_1)
        task_2 = solution.instance.get_task_by_name(task_name_2)
        evaluation = Evaluator.evaluate_moving_before_a_task(solution.get_sequence(employee), task_1, task_2)
        return ReorderingApplier._build_result_from_evaluation(solution, employee, task_1, task_2, evaluation)

    @staticmethod
    def apply_2a(solution: EditableSolution, employee_name: str, task_name: str) -> TransformationResult:
        """
        Apply reordering corresponding to the (Ord,2a) question:
        "Why is employee {Employee} not performing task {Task} later in their route?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        moving_task = solution.instance.get_task_by_name(task_name)
        evaluation = Evaluator.find_best_reorder_to_perform_task_later(solution.get_sequence(employee), moving_task)
        fixed_task = evaluation.activity_before
        return ReorderingApplier._build_result_from_evaluation(
            solution, employee, moving_task, fixed_task, evaluation)

    @staticmethod
    def apply_2b(solution: EditableSolution, employee_name: str, task_name: str) -> TransformationResult:
        """
        Apply reordering corresponding to the (Ord,2b) question:
        "Why is employee {Employee} not performing task {Task} earlier in their route?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        moving_task = solution.instance.get_task_by_name(task_name)
        evaluation = Evaluator.find_best_reorder_to_perform_task_earlier(solution.get_sequence(employee), moving_task)
        fixed_task = evaluation.activity_after
        return ReorderingApplier._build_result_from_evaluation(
            solution, employee, moving_task, fixed_task, evaluation)

    @staticmethod
    def apply_2c(solution: EditableSolution, employee_name: str, task_name: str) -> TransformationResult:
        """
        Apply reordering corresponding to the (Ord,2c) question:
        "Why is employee {Employee} not performing task {Task} at another position in their route?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.

        Returns:
            The result of the applied transformation.

        Raises:
            ValueError: if the best repositioning found leaves the moving task where it already stands.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        moving_task = solution.instance.get_task_by_name(task_name)
        evaluation = Evaluator.find_best_task_reorder(solution.get_sequence(employee), moving_task)
        sequence = solution.get_sequence(employee)
        if sequence.get_step_index_of(moving_task) < sequence.get_step_index_of(evaluation.activity_before):
            fixed_task = evaluation.activity_before
        elif sequence.get_step_index_of(moving_task) > sequence.get_step_index_of(evaluation.activity_after):
            fixed_task = evaluation.activity_after
        else:
            raise ValueError("The moving task is not moved")
        return ReorderingApplier._build_result_from_evaluation(
            solution, employee, moving_task, fixed_task, evaluation)

    ########
    # MILP #
    ########

    @staticmethod
    def _describe(model: ReorderingModel, employee: Employee, route_description: str) -> dict[str, str]:
        """
        Describe the reordering of the whole route, in every language.

        NB: The model is not read. (Ord,3) asks for another order without naming a task, so the sentence
        names none either, even though the model did pick a pivot task of its own to reorder around.
        """
        return TransformationDescriptionBuilder.for_reordering_route(employee, route_description)

    @staticmethod
    def _build_model_3(solution: EditableSolution, employee_name: str,
                       solving_time_limit: Optional[int] = None) -> ReorderingModel:
        """
        Build the MILP model answering the (Ord,3) question, without solving it.

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The model, ready to be solved.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        model = ReorderingModel(solution.get_sequence(employee))
        if solving_time_limit is not None:
            model.solving_time_limit = solving_time_limit
        return model

    @staticmethod
    def apply_3(solution: EditableSolution, employee_name: str,
                solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply reordering corresponding to the (Ord,3) question:
        "Why is employee {Employee} not performing the activities of their route in another order?"

        Unlike the insertions and the swaps, this needs no skill check: reordering leaves every task with
        the employee already performing it.

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.
        """
        model = ReorderingApplier._build_model_3(solution, employee_name, solving_time_limit)
        MILPTransformationRunner.solve_or_raise(model)
        return build_transformation_result_from_milp_model(solution, model, ReorderingApplier._describe)
