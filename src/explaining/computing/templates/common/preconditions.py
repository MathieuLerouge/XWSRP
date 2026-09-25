# Local libraries
from src.explaining.computing.exceptions import ImpossibleTransformationException
from src.explaining.modeling.solution import EditableSolution
from src.modeling.employee import Employee
from src.modeling.sequence import Sequence
from src.modeling.task import Task

# Global variables
INSERTING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE = \
    "Inserting any non-performed task is impossible given a solution performing all the tasks"
EXCHANGING_ANY_NON_PERFORMED_TASK_IS_IMPOSSIBLE_MESSAGE = \
    "Exchanging a task with any non-performed task is impossible given a solution performing all the tasks"
NO_PERFORMABLE_NON_PERFORMED_TASK_MESSAGE = "All the non-performed task are too much skilled for the employee"
SEQUENCE_IS_TOO_SHORT_TO_REORDER_MESSAGE = "Reordering a sequence with 3 activities or fewer is impossible"


###############################
# TransformationPreconditions #
###############################

class TransformationPreconditions:
    """
    Checks the conditions a solution must meet for a transformation to be applicable at all.
    """

    @staticmethod
    def get_performable_non_performed_tasks(solution: EditableSolution, employee: Employee,
                                            no_non_performed_task_message: str) -> list[Task]:
        """
        Return the solution's non-performed tasks the employee is skilled enough to perform.

        Args:
            solution: The solution to explain.
            employee: The employee the question is about.
            no_non_performed_task_message: The message to raise with when the solution performs every task,
                naming the transformation that cannot be applied.

        Returns:
            The non-performed tasks the employee is capable of performing, never empty.

        Raises:
            ImpossibleTransformationException: if the solution performs every task, or if the employee is
                not skilled enough for any of the non-performed ones.
        """
        if len(solution.non_performed_tasks) == 0:
            raise ImpossibleTransformationException(no_non_performed_task_message)
        performable_non_performed_tasks = [task for task in solution.non_performed_tasks
                                           if employee.is_capable_of_performing(task)]
        if len(performable_non_performed_tasks) == 0:
            raise ImpossibleTransformationException(NO_PERFORMABLE_NON_PERFORMED_TASK_MESSAGE)
        return performable_non_performed_tasks

    @staticmethod
    def check_sequence_is_reorderable(sequence: Sequence):
        """
        Check the sequence holds enough activities for reordering it to mean anything.

        Args:
            sequence: The sequence the transformation would reorder.

        Raises:
            ImpossibleTransformationException: if the sequence has 3 activities or fewer, its departure and
                come-back steps leaving at most one task to move around.
        """
        if sequence.nb_steps <= 3:
            raise ImpossibleTransformationException(SEQUENCE_IS_TOO_SHORT_TO_REORDER_MESSAGE)
