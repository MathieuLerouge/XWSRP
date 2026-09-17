# Standard library
from abc import abstractmethod, ABC


#############
# Violation #
#############

class Violation(ABC):
    """
    A single constraint violation detected while checking a solution's feasibility.
    """

    @property
    @abstractmethod
    def text(self):
        """Human-readable description of this violation."""

    def __repr__(self):
        return self.text
