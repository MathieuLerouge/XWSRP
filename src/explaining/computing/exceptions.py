#######################################
# Impossible transformation exception #
#######################################

class ImpossibleTransformationException(Exception):

    def __init__(self, message="Transformation is impossible"):
        self.message = message
        super().__init__(self.message)


##################################################
# Unattributable feasibility shortfall exception #
##################################################

class UnattributableFeasibilityShortfallException(Exception):
    """
    Raised when a solved feasibility shortfall cannot be attributed to the conflicting task's position,
    so that no TimeConflict describes it (see ConflictExtractor.extract).

    Both symptoms this covers come from the same place:
    the conflicting task's slack variables relax the time-sequence constraints on either side of it,
    and those constraints are also what keeps the rest of the formulation honest about ordering.

    - The shortfall pays for a restriction rather than for a position. A Precedence, PrecedenceChain or
      ImmediatePrecedence restriction constrains the tasks' start times directly, so the solver can satisfy
      one that the route order contradicts by spending shortfall at the conflicting task instead.
    - The solved route is not one route. With the sequencing relaxed at the conflicting task, a cycle of
      tasks disconnected from the leaving-home/coming-back-home path can satisfy every remaining constraint,
      leaving the conflicting task off the route altogether.

    Either way the shortfall is real, but it measures the contradiction rather than a gap the conflicting
    task has to be squeezed into, and no position exists to examine that would reproduce it.
    """

    def __init__(self, message="The feasibility shortfall is not attributable to the conflicting task"):
        self.message = message
        super().__init__(self.message)
