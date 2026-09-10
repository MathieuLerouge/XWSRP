# Standard library
from abc import abstractmethod, ABC


#########################
# NeighborhoodPrimitive #
#########################

class NeighborhoodPrimitive(ABC):
    """
    An elementary building block used to compose a Neighborhood.
    """

    @property
    @abstractmethod
    def employees(self):
        """The employees whose sequences this primitive concerns."""
        pass
