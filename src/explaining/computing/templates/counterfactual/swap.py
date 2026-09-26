# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.templates.common.description import TransformationDescriptionBuilder
from src.explaining.computing.templates.common.preconditions import TransformationPreconditionChecker, \
    EXCHANGING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.computing.templates.common.solver import TransformationModelSolver
from src.explaining.computing.templates.counterfactual.result import build_transformation_result_from_milp_model
from src.explaining.computing.templates.counterfactual.milp.swap.swap1 import Swap1WithAlterationsModel
from src.explaining.computing.templates.counterfactual.milp.swap.swap2 import \
    Swap2aWithAlterationsModel, Swap2bWithAlterationsModel
from src.explaining.computing.templates.counterfactual.milp.swap.swap3 import Swap3WithAlterationsModel
from src.explaining.computing.templates.counterfactual.milp.swap.base import SwapWithAlterationsBaseModel
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.solution import EditableSolution
from src.modeling.employee import Employee


##############################
# SwapWithAlterationsApplier #
##############################

class SwapWithAlterationsApplier:
    """
    Applies the transformation each counterfactual swap question induces, and reports what it needed.
    """

    @staticmethod
    def _describe(model: SwapWithAlterationsBaseModel, employee: Employee,
                  route_description: str) -> dict[str, str]:
        """Describe the swap the given model computed, in every language."""
        return TransformationDescriptionBuilder.for_replacing_task_in_route(
            model.replaced_task, model.replacing_task, employee, route_description)

    @staticmethod
    def apply_1(solution: EditableSolution, employee_name: str, task1_name: str, task2_name: str,
                instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply swap corresponding to the (Swp,1) counterfactual question:
        "How to make possible that employee {Employee} performs task {Task1} in place of task {Task2}?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task1_name: The name of the first task mentioned in the question, the one taking the other's place.
            task2_name: The name of the second task mentioned in the question, the one being replaced.
            instance_parameter_alteration_bounds: The allowed variations of instance parameters.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        replacing_task = solution.instance.get_task_by_name(task1_name)
        replaced_task = solution.instance.get_task_by_name(task2_name)
        model = Swap1WithAlterationsModel(
            solution.get_sequence(employee), replacing_task, replaced_task,
            instance_parameter_alteration_bounds, solving_time_limit)
        TransformationModelSolver.solve_or_raise(model)
        return build_transformation_result_from_milp_model(solution, model, SwapWithAlterationsApplier._describe)

    @staticmethod
    def apply_2a(solution: EditableSolution, employee_name: str, task_name: str,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply swap corresponding to the (Swp,2a) counterfactual question:
        "How to make possible that employee {Employee} performs task {Task} in place of one of their tasks?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.
            instance_parameter_alteration_bounds: The allowed variations of instance parameters.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        replacing_task = solution.instance.get_task_by_name(task_name)
        model = Swap2aWithAlterationsModel(
            solution.get_sequence(employee), replacing_task,
            instance_parameter_alteration_bounds, solving_time_limit)
        TransformationModelSolver.solve_or_raise(model)
        return build_transformation_result_from_milp_model(solution, model, SwapWithAlterationsApplier._describe)

    @staticmethod
    def apply_2b(solution: EditableSolution, employee_name: str,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply swap corresponding to the (Swp,2b) counterfactual question:
        "How to make possible that employee {Employee} performs any non-performed task
        in place of one of their tasks?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            instance_parameter_alteration_bounds: The allowed variations of instance parameters.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.

        Raises:
            ImpossibleTransformationException: if the solution performs every task,
                or if the employee is not skilled enough for any of the non-performed ones.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        performable_non_performed_tasks = TransformationPreconditionChecker.get_performable_non_performed_tasks(
            solution, employee, EXCHANGING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE
        )
        model = Swap2bWithAlterationsModel(
            solution.get_sequence(employee), performable_non_performed_tasks,
            instance_parameter_alteration_bounds, solving_time_limit)
        TransformationModelSolver.solve_or_raise(model)
        return build_transformation_result_from_milp_model(solution, model, SwapWithAlterationsApplier._describe)

    @staticmethod
    def apply_3(solution: EditableSolution, employee_name: str, task_name: str,
                instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply swap corresponding to the (Swp,3) counterfactual question:
        "How to make possible that employee {Employee} performs task {Task} in place of one of their activities?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.
            instance_parameter_alteration_bounds: The allowed variations of instance parameters.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        replacing_task = solution.instance.get_task_by_name(task_name)
        model = Swap3WithAlterationsModel(
            solution.get_sequence(employee), replacing_task,
            instance_parameter_alteration_bounds, solving_time_limit)
        TransformationModelSolver.solve_or_raise(model)
        return build_transformation_result_from_milp_model(solution, model, SwapWithAlterationsApplier._describe)
