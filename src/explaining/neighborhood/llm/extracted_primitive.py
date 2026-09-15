# Standard library
from typing import NewType

# Third-party library
from pydantic import BaseModel, ConfigDict


# Entity names, as an LLM extraction names them (raw strings) rather than as domain objects -
# resolved against a Solution/Instance and turned into actual Employee/Task objects at grounding time.
EmployeeName = NewType("EmployeeName", str)
TaskName = NewType("TaskName", str)
# An activity is a task, or the LEAVING_HOME_STRING/COMING_BACK_HOME_STRING sentinel naming the
# employee's departure from or return home - a strictly wider set of names than TaskName's.
ActivityName = NewType("ActivityName", str)


######################
# ExtractedPrimitive #
######################

class ExtractedPrimitive(BaseModel):
    """
    An elementary building block an LLM extraction may pick to compose an ExtractedNeighborhood,
    naming its candidates by their solution/instance names rather than by domain object.

    The raw-string counterpart of Primitive, meant to be grounded into an actual Operator/
    Restriction object once its names are resolved against a Solution/Instance.
    """

    # Reject unexpected fields rather than silently ignoring them (pydantic's default):
    # an LLM hallucinating a field name should surface as a validation error instructor can retry on,
    # not disappear silently.
    model_config = ConfigDict(extra="forbid")
