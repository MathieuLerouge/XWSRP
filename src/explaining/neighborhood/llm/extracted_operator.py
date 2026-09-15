# Standard library
from typing import Annotated, Literal, Union

# Third-party library
from pydantic import Field

# Local library
from src.explaining.neighborhood.llm.extracted_primitive import EmployeeName, ExtractedPrimitive, TaskName


##########################
# ExtractedTaskInsertion #
##########################

class ExtractedTaskInsertion(ExtractedPrimitive):
    """
    The raw-string counterpart of TaskInsertion:
    inserts one of candidate_tasks into the sequence of one of candidate_employees.
    """

    kind: Literal["task_insertion"] = "task_insertion"
    candidate_employees: list[EmployeeName] = Field(
        description="The employees among which the one to perform the inserted task is chosen."
    )
    candidate_tasks: list[TaskName] = Field(
        description="The tasks among which the one to insert is chosen."
    )


#########################
# ExtractedTaskDeletion #
#########################

class ExtractedTaskDeletion(ExtractedPrimitive):
    """
    The raw-string counterpart of TaskDeletion:
    removes between min_nb_removals and max_nb_removals of candidate_tasks,
    freeing freed_employees' other tasks to shift in time/order to close the gap left behind.
    """

    kind: Literal["task_deletion"] = "task_deletion"
    freed_employees: list[EmployeeName] = Field(
        description="The employees whose already-performed, non-candidate tasks are freed to "
                    "shift in time/order to accommodate whichever candidate task(s) get removed."
    )
    candidate_tasks: list[TaskName] = Field(
        description="The tasks among which the ones to remove are chosen."
    )
    min_nb_removals: int = Field(default=1, description="The minimum number of candidate_tasks that must be removed.")
    max_nb_removals: int = Field(default=1, description="The maximum number of candidate_tasks that may be removed.")


##############################
# ExtractedTaskRepositioning #
##############################

class ExtractedTaskRepositioning(ExtractedPrimitive):
    """
    The raw-string counterpart of TaskRepositioning:
    moves target_task to a different position within employee's own sequence.
    """

    kind: Literal["task_repositioning"] = "task_repositioning"
    employee: EmployeeName = Field(description="The employee whose sequence the target task is repositioned within.")
    target_task: TaskName = Field(description="The task to reposition.")


###############################
# ExtractedSequenceReordering #
###############################

class ExtractedSequenceReordering(ExtractedPrimitive):
    """
    The raw-string counterpart of SequenceReordering:
    frees employee's entire sequence to be reordered,
    without adding, removing or reassigning any of their tasks.
    """

    kind: Literal["sequence_reordering"] = "sequence_reordering"
    employee: EmployeeName = Field(description="The employee whose sequence is freed to be reordered.")


# The feasibility-shortfall operator an extraction may pick
# The only kind of Operator NeighborhoodModel supports on its own.
# No ExtractedTaskRelocation variant: TaskRelocation has no MILP formulation yet, so there is nothing to ground it into.
# This Union is discriminated (a.k.a. tagged): each member's kind Literal tells pydantic - and the LLM's tool call -
# unambiguously which variant a given value is, instead of guessing from shape.
ExtractedFeasibilityShortfallOperator = Annotated[
    Union[ExtractedTaskInsertion, ExtractedTaskRepositioning, ExtractedSequenceReordering],
    Field(discriminator="kind"),
]
