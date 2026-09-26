# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.templates.common.description import TransformationDescriptionBuilder
from src.explaining.computing.templates.common.preconditions import TransformationPreconditionChecker, \
    INSERTING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE
from src.explaining.computing.templates.common.result import TransformationResult
from src.explaining.computing.templates.common.runner import MILPTransformationRunner
from src.explaining.computing.templates.counterfactual.extraction import build_transformation_result_from_milp_model
from src.explaining.computing.templates.counterfactual.MILP_model.insertion1 import \
    MILPModelForInsertion1WithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.insertion2 import \
    MILPModelForInsertion2aWithInstanceAlterations, MILPModelForInsertion2bWithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.insertion3 import \
    MILPModelForInsertion3WithInstanceAlterations
from src.explaining.computing.templates.counterfactual.MILP_model.insertion_with_alterations import \
    MILPModelForInsertionWithInstanceAlterations
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.solution import EditableSolution
from src.modeling.employee import Employee


###################################
# InsertionWithAlterationsApplier #
###################################

class InsertionWithAlterationsApplier:
    """
    Applies the transformation each counterfactual insertion question induces, and reports what it needed.
    """

    @staticmethod
    def _describe(model: MILPModelForInsertionWithInstanceAlterations, employee: Employee,
                  route_description: str) -> dict[str, str]:
        """Describe the insertion the given model computed, in every language."""
        return TransformationDescriptionBuilder.for_inserting_task_in_route(
            model.task_to_insert, employee, route_description)

    @staticmethod
    def apply_1(solution: EditableSolution, employee_name: str, task_name: str, activity_name: str,
                instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply insertion corresponding to the (Ins,1) counterfactual question:
        "How to make possible that employee {Employee} performs task {Task} just after activity {Activity}?"

        Args:
            solution: The solution to explain.
            employee_name: The name of the employee mentioned in the question.
            task_name: The name of the task mentioned in the question.
            activity_name: The name of the activity mentioned in the question.
            instance_parameter_alteration_bounds: The allowed variations of instance parameters.
            solving_time_limit: The solving time limit in seconds, or None for no limit.

        Returns:
            The result of the applied transformation.
        """
        employee = solution.instance.get_employee_by_name(employee_name)
        task = solution.instance.get_task_by_name(task_name)
        activity = solution.instance.get_hypothetical_activity_by_names(activity_name, employee.name)
        model = MILPModelForInsertion1WithInstanceAlterations(
            solution.get_sequence(employee), task, activity,
            instance_parameter_alteration_bounds, solving_time_limit)
        MILPTransformationRunner.solve_or_raise(model)
        return build_transformation_result_from_milp_model(
            solution, model, InsertionWithAlterationsApplier._describe
        )

    @staticmethod
    def apply_2a(solution: EditableSolution, employee_name: str, task_name: str,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply insertion corresponding to the (Ins,2a) counterfactual question:
        "How to make possible that employee {Employee} performs task {Task}
        between two consecutive activities of their planning?"

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
        task = solution.instance.get_task_by_name(task_name)
        model = MILPModelForInsertion2aWithInstanceAlterations(
            solution.get_sequence(employee), task, instance_parameter_alteration_bounds, solving_time_limit)
        MILPTransformationRunner.solve_or_raise(model)
        return build_transformation_result_from_milp_model(
            solution, model, InsertionWithAlterationsApplier._describe
        )

    @staticmethod
    def apply_2b(solution: EditableSolution, employee_name: str,
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply insertion corresponding to the (Ins,2b) counterfactual question:
        "How to make possible that employee {Employee} performs any non-performed task
        between two consecutive activities of their planning?"

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
            solution, employee, INSERTING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE
        )
        model = MILPModelForInsertion2bWithInstanceAlterations(
            solution.get_sequence(employee), performable_non_performed_tasks,
            instance_parameter_alteration_bounds, solving_time_limit)
        MILPTransformationRunner.solve_or_raise(model)
        return build_transformation_result_from_milp_model(
            solution, model, InsertionWithAlterationsApplier._describe
        )

    @staticmethod
    def apply_3(solution: EditableSolution, employee_name: str, task_name: str,
                instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                solving_time_limit: Optional[int] = None) -> TransformationResult:
        """
        Apply insertion corresponding to the (Ins,3) counterfactual question:
        "How to make possible that employee {Employee} performs task {Task} in addition to their activities?"

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
        task = solution.instance.get_task_by_name(task_name)
        model = MILPModelForInsertion3WithInstanceAlterations(
            solution.get_sequence(employee), task, instance_parameter_alteration_bounds, solving_time_limit)
        MILPTransformationRunner.solve_or_raise(model)
        return build_transformation_result_from_milp_model(
            solution, model, InsertionWithAlterationsApplier._describe
        )
