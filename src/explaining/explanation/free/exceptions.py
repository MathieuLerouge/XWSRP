###########################
# ExplanationWritingError #
###########################

class ExplanationWritingError(Exception):
    """
    Raised when the LLM fails to word an explanation from the facts it is given:
    it exhausted its retries without producing schema-valid output,
    or kept stating times or names the facts do not hold.
    """

    def __init__(self, message: str = "No explanation could be worded for this question."):
        """
        Args:
            message: User-facing explanation of the failure, deliberately generic.
        """
        super().__init__(message)
