#####################
# NeighborhoodError #
#####################

class NeighborhoodError(Exception):
    """
    Raised when a Neighborhood cannot be turned into something NeighborhoodModel can solve:
    either Neighborhood's own constructor rejects it (no operators and no restrictions at all),
    or NeighborhoodModel's capability check (its NotImplementedError) rejects
    the combination of operators/restrictions it carries.
    """

    def __init__(self, message: str = "This neighborhood cannot be solved by NeighborhoodModel."):
        """
        Args:
            message: User-facing explanation of the failure. Kept deliberately generic - the same
                message is reused across every failure site rather than exposing internal detail
                to the end user.
        """
        self.message = message
        super().__init__(self.message)
