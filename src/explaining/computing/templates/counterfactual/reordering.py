# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.templates.common.description import TransformationDescriptionBuilder
from src.explaining.computing.templates.common.preconditions import TransformationPreconditionChecker
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.computing.templates.common.runner import MILPTransformationRunner
from src.explaining.computing.templates.counterfactual.result import build_transformation_result_from_milp_model
from src.explaining.computing.templates.counterfactual.milp.reordering.reordering1 import \
    Reordering1aWithAlterationsModel, Reordering1bWithAlterationsModel
from src.explaining.computing.templates.counterfactual.milp.reordering.reordering2 import \
    Reordering2aWithAlterationsModel, Reordering2bWithAlterationsModel, Reordering2cWithAlterationsModel
from src.explaining.computing.templates.counterfactual.milp.reordering.reordering3 import \
    Reordering3WithAlterationsModel
from src.explaining.computing.templates.counterfactual.milp.reordering.base import ReorderingWithAlterationsBaseModel
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.solution import EditableSolution
from src.modeling.employee import Employee


####################################
# ReorderingWithAlterationsApplier #
####################################

class ReorderingWithAlterationsApplier:
    """
    Applies the transformation each counterfactual reordering question induces, and reports what it needed.
    """

    @staticmethod
    def _describe_task_repositioning(model: ReorderingWithAlterationsBaseModel, employee: Employee,
                                     route_description: str) -> dict[str, str]:
        """Describe the repositioning of the model's moving task, in every language."""
        return TransformationDescriptionBuilder.for_repositioning_task_in_route(
            model.moving_task, employee, route_description
        )

    @staticmethod
    def _describe_reordering(model: ReorderingWithAlterationsBaseModel, employee: Employee,
                             route_description: str) -> dict[str, str]:
        """
        Describe the reordering of the whole route, in every language.

        NB: The model is not read. (Ord,3) asks for another order without naming a task, so the sentence names
        none either, even though the model did pick a pivot task of its own to reorder around.
        """
        return TransformationDescriptionBuilder.for_reordering_route(employee, route_description)

    @staticmethod
    def apply_1a(solution: EditableSolution, employee_name: str, task1_name: str, task2_name: str,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply reordering corresponding to the (Ord,1a) counterfactual question:
        "How to make possible that employee {Employee} performs task {Task1} later in their route,
        just after task {Task2}?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task1_name: The name of the first task mentioned in the question, the one being moved.
            task2_name: The name of the second task mentioned in the question, the one staying put.
            instance_parameter_alteration_bounds: The allowed variations of instance parameters.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        moving_task = solution.instance.get_task_by_name(task1_name)
        fixed_task = solution.instance.get_task_by_name(task2_name)
        model = Reordering1aWithAlterationsModel(
            solution.get_sequence(employee), moving_task, fixed_task,
            instance_parameter_alteration_bounds, solving_time_limit)
        MILPTransformationRunner.solve_or_raise(model)
        return build_transformation_result_from_milp_model(
            solution, model, ReorderingWithAlterationsApplier._describe_task_repositioning
        )

    @staticmethod
    def apply_1b(solution: EditableSolution, employee_name: str, task1_name: str, task2_name: str,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply reordering corresponding to the (Ord,1b) counterfactual question:
        "How to make possible that employee {Employee} performs task {Task1} earlier in their route,
        just before task {Task2}?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task1_name: The name of the first task mentioned in the question, the one being moved.
            task2_name: The name of the second task mentioned in the question, the one staying put.
            instance_parameter_alteration_bounds: The allowed variations of instance parameters.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        moving_task = solution.instance.get_task_by_name(task1_name)
        fixed_task = solution.instance.get_task_by_name(task2_name)
        model = Reordering1bWithAlterationsModel(
            solution.get_sequence(employee), moving_task, fixed_task,
            instance_parameter_alteration_bounds, solving_time_limit)
        MILPTransformationRunner.solve_or_raise(model)
        return build_transformation_result_from_milp_model(
            solution, model, ReorderingWithAlterationsApplier._describe_task_repositioning
        )

    @staticmethod
    def apply_2a(solution: EditableSolution, employee_name: str, task_name: str,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply reordering corresponding to the (Ord,2a) counterfactual question:
        "How to make possible that employee {Employee} performs task {Task} later in their route?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.
            instance_parameter_alteration_bounds: The allowed variations of instance parameters.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.

        Raises:
            ImpossibleTransformationException: if the sequence has 3 activities or fewer.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        sequence = solution.get_sequence(employee)
        TransformationPreconditionChecker.check_sequence_is_reorderable(sequence)
        moving_task = solution.instance.get_task_by_name(task_name)
        model = Reordering2aWithAlterationsModel(
            sequence, moving_task, instance_parameter_alteration_bounds, solving_time_limit)
        MILPTransformationRunner.solve_or_raise(model)
        return build_transformation_result_from_milp_model(
            solution, model, ReorderingWithAlterationsApplier._describe_task_repositioning
        )

    @staticmethod
    def apply_2b(solution: EditableSolution, employee_name: str, task_name: str,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply reordering corresponding to the (Ord,2b) counterfactual question:
        "How to make possible that employee {Employee} performs task {Task} earlier in their route?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.
            instance_parameter_alteration_bounds: The allowed variations of instance parameters.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.

        Raises:
            ImpossibleTransformationException: if the sequence has 3 activities or fewer.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        sequence = solution.get_sequence(employee)
        TransformationPreconditionChecker.check_sequence_is_reorderable(sequence)
        moving_task = solution.instance.get_task_by_name(task_name)
        model = Reordering2bWithAlterationsModel(
            sequence, moving_task, instance_parameter_alteration_bounds, solving_time_limit)
        MILPTransformationRunner.solve_or_raise(model)
        return build_transformation_result_from_milp_model(
            solution, model, ReorderingWithAlterationsApplier._describe_task_repositioning
        )

    @staticmethod
    def apply_2c(solution: EditableSolution, employee_name: str, task_name: str,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply reordering corresponding to the (Ord,2c) counterfactual question:
        "How to make possible that employee {Employee} performs task {Task} at another position in their route?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.
            instance_parameter_alteration_bounds: The allowed variations of instance parameters.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.

        Raises:
            ImpossibleTransformationException: if the sequence has 3 activities or fewer.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        sequence = solution.get_sequence(employee)
        TransformationPreconditionChecker.check_sequence_is_reorderable(sequence)
        moving_task = solution.instance.get_task_by_name(task_name)
        model = Reordering2cWithAlterationsModel(
            sequence, moving_task, instance_parameter_alteration_bounds, solving_time_limit)
        MILPTransformationRunner.solve_or_raise(model)
        return build_transformation_result_from_milp_model(
            solution, model, ReorderingWithAlterationsApplier._describe_task_repositioning
        )

    @staticmethod
    def apply_3(solution: EditableSolution, employee_name: str,
                instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply reordering corresponding to the (Ord,3) counterfactual question:
        "How to make possible that employee {Employee} performs the activities of their route in another order?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            instance_parameter_alteration_bounds: The allowed variations of instance parameters.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.

        Raises:
            ImpossibleTransformationException: if the sequence has 3 activities or fewer.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        sequence = solution.get_sequence(employee)
        TransformationPreconditionChecker.check_sequence_is_reorderable(sequence)
        model = Reordering3WithAlterationsModel(
            sequence, instance_parameter_alteration_bounds, solving_time_limit)
        MILPTransformationRunner.solve_or_raise(model)
        return build_transformation_result_from_milp_model(
            solution, model, ReorderingWithAlterationsApplier._describe_reordering
        )
