# Local libraries
from src.optimization.milp.milpmodel import MILPModel
from src.teaching.modeling.instance import InstanceForTeaching
from src.teaching.optimization.solution import SolutionForTeaching
from src.utils.constants import SOLUTION_SOLVING_METHOD_SYMBOL_BIS

# Global variables
IP_MODEL_VERSION_SYMBOL = 'M'


##########################
# WSRPIPModelForTeaching #
##########################


class WSRPIPModelForTeaching(MILPModel):

    def __init__(self, instance: InstanceForTeaching):
        # NB: instance.version is already validated to be 1, 2 or 3 by InstanceForTeaching.__init__,
        # which also derives must_cover_all_tasks from it
        self._version = 1 if instance.version == 1 else 2
        super().__init__(instance)
        self._name = f"{instance.core_name_with_version}{SOLUTION_SOLVING_METHOD_SYMBOL_BIS}{self._solving_method_id}"

    ####################
    # Instance version #
    ####################

    @property
    def version(self):
        """
        Returns the version of the model.

        :return: the version of the model (int)
        """
        return self._version

    ##################
    # Solving method #
    ##################

    @property
    def _solving_method_id(self):
        """
        Returns the solving method ID of the model.

        :return: the solving method ID of the model (str)
        """
        return f"M{self.version}"

    ############
    # Solution #
    ############

    def _initialize_solution(self):
        """
        Initializes the teaching solution which will be completed based on the optimization result of this model.
        The teaching solution is associated with the teaching instance of the model and the solving method.

        :return: an initialized teaching solution (SolutionForTeaching)
        """
        self._solution = SolutionForTeaching(self._data.instance, solving_method_id=self._solving_method_id)

    @property
    def solution(self):
        """
        Returns the teaching solution built from the optimization result of this model.

        :return: the teaching solution built from the optimization result of this model (SolutionForTeaching)
        """
        return self._solution
