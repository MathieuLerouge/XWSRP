# Standard library
from abc import abstractmethod, ABC
from typing import Union

# Local libraries
from src.modeling.employee import Employee
from src.modeling.task import Task


#########################
# NeighborhoodPrimitive #
#########################

class NeighborhoodPrimitive(ABC):
    """
    An elementary building block used to compose a Neighborhood.
    """

    @property
    @abstractmethod
    def scope(self) -> frozenset[Union[Employee, Task]]:
        """The employees' sequences and tasks this primitive frees from being fixed to their current state."""
        pass
