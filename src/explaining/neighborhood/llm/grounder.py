# Standard library
from typing import Optional

# Local libraries
from src.explaining.neighborhood.llm.exceptions import NeighborhoodExtractionError
from src.explaining.neighborhood.llm.neighborhood import ExtractedNeighborhood
from src.explaining.neighborhood.llm.operator import (
    ExtractedFeasibilityShortfallOperator, ExtractedSequenceReordering, ExtractedTaskDeletion, ExtractedTaskInsertion,
    ExtractedTaskRepositioning
)
from src.explaining.neighborhood.llm.restriction import (
    ExtractedForbiddenBackwardSubsequence, ExtractedForbiddenSequence, ExtractedImmediatePrecedence,
    ExtractedPrecedence, ExtractedPrecedenceChain, ExtractedRestriction
)
from src.explaining.neighborhood.operator import (
    Operator, SequenceReordering, TaskDeletion, TaskInsertion, TaskRepositioning
)
from src.explaining.neighborhood.restriction import (
    ForbiddenBackwardSubsequence, ForbiddenSequence, ImmediatePrecedence, Precedence, PrecedenceChain, Restriction
)
from src.modeling.instance import Instance
from src.modeling.solution import Solution


############
# Grounder #
############

class Grounder:
    """
    Grounds an ExtractedNeighborhood's raw solution/instance names
    into the actual Operator/Restriction domain objects Neighborhood expects.
    """

    @staticmethod
    def ground(extracted: ExtractedNeighborhood, solution: Solution) -> tuple[list[Operator], list[Restriction]]:
        """
        Args:
            extracted: The LLM extraction to ground.
            solution: The solution the extraction's names are resolved against.

        Returns:
            A (operators, restrictions) pair ready to build a Neighborhood from:
            operators holds the grounded feasibility-shortfall operator,
            plus the grounded task deletion if extracted carries one.

        Raises:
            NeighborhoodExtractionError: If any name doesn't resolve against solution's instance,
                or an ImmediatePrecedence restriction names a route-boundary sentinel ("Start"/"Return")
                while the operator doesn't name a single unambiguous employee to anchor it to.
        """
        instance = solution.instance
        try:
            operators = [Grounder._ground_operator(extracted.operator, instance)]
            if extracted.deletion is not None:
                operators.append(Grounder._ground_task_deletion(extracted.deletion, instance))
            anchor_employee_name = Grounder._get_singleton_employee_name(extracted.operator)
            restrictions = [
                Grounder._ground_restriction(restriction, instance, anchor_employee_name)
                for restriction in extracted.restrictions
            ]
        except ValueError as error:
            raise NeighborhoodExtractionError() from error
        return operators, restrictions

    @staticmethod
    def _ground_operator(extracted_operator: ExtractedFeasibilityShortfallOperator, instance: Instance) -> Operator:
        """
        Raises:
            ValueError: If any name extracted_operator carries doesn't resolve against instance.
        """
        if isinstance(extracted_operator, ExtractedTaskInsertion):
            candidate_employees = frozenset(
                instance.get_employee_by_name(name) for name in extracted_operator.candidate_employees
            )
            candidate_tasks = frozenset(
                instance.get_task_by_name(name) for name in extracted_operator.candidate_tasks
            )
            return TaskInsertion(candidate_employees, candidate_tasks)
        elif isinstance(extracted_operator, ExtractedTaskRepositioning):
            employee = instance.get_employee_by_name(extracted_operator.employee)
            target_task = instance.get_task_by_name(extracted_operator.target_task)
            return TaskRepositioning(employee, target_task)
        else:
            assert isinstance(extracted_operator, ExtractedSequenceReordering)
            employee = instance.get_employee_by_name(extracted_operator.employee)
            return SequenceReordering(employee)

    @staticmethod
    def _ground_task_deletion(extracted_deletion: ExtractedTaskDeletion, instance: Instance) -> TaskDeletion:
        """
        Raises:
            ValueError: If any name extracted_deletion carries doesn't resolve against instance.
        """
        freed_employees = frozenset(
            instance.get_employee_by_name(name) for name in extracted_deletion.freed_employees
        )
        candidate_tasks = frozenset(
            instance.get_task_by_name(name) for name in extracted_deletion.candidate_tasks
        )
        return TaskDeletion(freed_employees, candidate_tasks,
                             min_nb_removals=extracted_deletion.min_nb_removals,
                             max_nb_removals=extracted_deletion.max_nb_removals)

    @staticmethod
    def _get_singleton_employee_name(extracted_operator: ExtractedFeasibilityShortfallOperator) -> Optional[str]:
        """
        Returns the single employee name extracted_operator unambiguously names, or None if it
        names several (only task_insertion can) - used to anchor an ImmediatePrecedence
        restriction's route-boundary sentinel ("Start"/"Return") to a specific employee.
        """
        if isinstance(extracted_operator, ExtractedTaskInsertion):
            candidate_employees = extracted_operator.candidate_employees
            return candidate_employees[0] if len(candidate_employees) == 1 else None
        else:
            assert isinstance(extracted_operator, (ExtractedTaskRepositioning, ExtractedSequenceReordering))
            return extracted_operator.employee

    @staticmethod
    def _ground_restriction(extracted_restriction: ExtractedRestriction, instance: Instance,
                            anchor_employee_name: Optional[str]) -> Restriction:
        """
        Raises:
            ValueError: If any name extracted_restriction carries doesn't resolve against instance.
            NeighborhoodExtractionError: If extracted_restriction is an ImmediatePrecedence naming
                a route-boundary sentinel while anchor_employee_name is None (the operator doesn't
                name a single, unambiguous employee to anchor it to).
        """
        if isinstance(extracted_restriction, ExtractedPrecedenceChain):
            tasks = [instance.get_task_by_name(name) for name in extracted_restriction.tasks]
            return PrecedenceChain(tasks)
        elif isinstance(extracted_restriction, ExtractedPrecedence):
            predecessor = instance.get_task_by_name(extracted_restriction.predecessor)
            successor = instance.get_task_by_name(extracted_restriction.successor)
            return Precedence(predecessor, successor)
        elif isinstance(extracted_restriction, ExtractedImmediatePrecedence):
            if anchor_employee_name is None:
                raise NeighborhoodExtractionError()
            predecessor = instance.get_hypothetical_activity_by_names(
                extracted_restriction.predecessor, anchor_employee_name
            )
            successor = instance.get_hypothetical_activity_by_names(
                extracted_restriction.successor, anchor_employee_name
            )
            return ImmediatePrecedence(predecessor, successor)
        elif isinstance(extracted_restriction, ExtractedForbiddenSequence):
            employee = instance.get_employee_by_name(extracted_restriction.employee)
            activities = [
                instance.get_hypothetical_activity_by_names(name, extracted_restriction.employee)
                for name in extracted_restriction.activities
            ]
            return ForbiddenSequence(employee, activities)
        else:
            assert isinstance(extracted_restriction, ExtractedForbiddenBackwardSubsequence)
            employee = instance.get_employee_by_name(extracted_restriction.employee)
            tasks = [instance.get_task_by_name(name) for name in extracted_restriction.tasks]
            return ForbiddenBackwardSubsequence(employee, tasks)
