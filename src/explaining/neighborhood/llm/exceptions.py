###############################
# NeighborhoodExtractionError #
###############################

class NeighborhoodExtractionError(Exception):
    """
    Raised when a free-text question cannot be turned into a Neighborhood that NeighborhoodModel can solve:
    an unresolvable entity name, an ambiguous route-boundary reference,
    or a primitive combination NeighborhoodModel doesn't support yet.
    """

    def __init__(self, message: str = "This question cannot be answered with the currently supported primitives."):
        """
        Args:
            message: User-facing explanation of the failure. Kept deliberately generic
                - the same message is reused across every failure site rather than exposing internal detail
                (e.g. which name failed to resolve) to the end user.
        """
        self.message = message
        super().__init__(self.message)
