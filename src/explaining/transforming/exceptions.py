#######################################
# Impossible transformation exception #
#######################################

class ImpossibleTransformationException(Exception):

    def __init__(self, message="Transformation is impossible"):
        self.message = message
        super().__init__(self.message)
