# Standard library
from typing import Annotated, Literal, Union

# Third-party library
from pydantic import Field

# Local library
from src.explaining.neighborhood.llm.primitive import ActivityName, EmployeeName, ExtractedPrimitive, TaskName


################################
# ExtractedImmediatePrecedence #
################################

class ExtractedImmediatePrecedence(ExtractedPrimitive):
    """
    The raw-string counterpart of ImmediatePrecedence: requires successor to occur immediately
    after predecessor, regardless of which employee ends up performing them.
    """

    kind: Literal["immediate_precedence"] = "immediate_precedence"
    predecessor: ActivityName = Field(description="The activity that successor must immediately follow.")
    successor: ActivityName = Field(description="The activity that must immediately follow predecessor.")


#######################
# ExtractedPrecedence #
#######################

class ExtractedPrecedence(ExtractedPrimitive):
    """
    The raw-string counterpart of Precedence: requires successor to start no earlier than
    predecessor finishes, without requiring immediate adjacency.
    """

    kind: Literal["precedence"] = "precedence"
    predecessor: TaskName = Field(description="The task that must finish no later than successor starts.")
    successor: TaskName = Field(description="The task that must start no earlier than predecessor finishes.")


############################
# ExtractedPrecedenceChain #
############################

class ExtractedPrecedenceChain(ExtractedPrimitive):
    """
    The raw-string counterpart of PrecedenceChain: keeps the relative order of tasks, an explicit
    ordered list, unchanged.
    """

    kind: Literal["precedence_chain"] = "precedence_chain"
    tasks: list[TaskName] = Field(description="The tasks, in the relative order they must keep.")


##############################
# ExtractedForbiddenSequence #
##############################

class ExtractedForbiddenSequence(ExtractedPrimitive):
    """
    The raw-string counterpart of ForbiddenSequence: forbids employee's sequence from containing
    activities, an explicit ordered chain, as a contiguous run.
    """

    kind: Literal["forbidden_sequence"] = "forbidden_sequence"
    employee: EmployeeName = Field(description="The employee whose sequence must not contain the forbidden chain.")
    activities: list[ActivityName] = Field(
        description="The forbidden chain of activities, in the order they must not appear contiguously in."
    )


#########################################
# ExtractedForbiddenBackwardSubsequence #
#########################################

class ExtractedForbiddenBackwardSubsequence(ExtractedPrimitive):
    """
    The raw-string counterpart of ForbiddenBackwardSubsequence: requires employee's route to never
    travel from a later task to an earlier one within tasks, an explicit ordered list - whichever
    of them remain performed keep their original relative order, any of them may become unperformed.
    """

    kind: Literal["forbidden_backward_subsequence"] = "forbidden_backward_subsequence"
    employee: EmployeeName = Field(description="The employee whose route must not travel backward within tasks.")
    tasks: list[TaskName] = Field(
        description="The tasks, in the relative order that whichever of them remain performed must keep."
    )


# The scope restrictions an extraction may pick, zero or more of, to narrow how its
# ExtractedFeasibilityShortfallOperator/ExtractedTaskDeletion may transform the in-scope sequences.
# This Union is discriminated (a.k.a. tagged): each member's kind Literal tells pydantic - and the
# LLM's tool call - unambiguously which variant a given value is, instead of guessing from shape.
ExtractedRestriction = Annotated[
    Union[ExtractedPrecedenceChain, ExtractedImmediatePrecedence, ExtractedPrecedence,
          ExtractedForbiddenSequence, ExtractedForbiddenBackwardSubsequence],
    Field(discriminator="kind"),
]
