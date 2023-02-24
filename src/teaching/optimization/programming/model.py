# Local libraries
from src.optimization.IP.WSRPmodel import WSRPIPModel
from src.teaching.modeling.instance import InstanceForTeaching
from src.teaching.optimization.solution import SolutionForTeaching
from src.utils.constants import SOLUTION_SOLVING_METHOD_SYMBOL_BIS

# Global variables
IP_MODEL_VERSION_SYMBOL = 'M'


################################
# Class WSRPIPModelForTeaching #
################################


class WSRPIPModelForTeaching(WSRPIPModel):

    def __init__(self, instance: InstanceForTeaching):
        if instance.version == 1:
            self._version = 1
        elif instance.version in [2, 3]:
            self._version = 2
        else:
            raise ValueError(f"Given instance has a version {instance.version} "
                             f"but its version must be either 1, 2 or 3")
        super().__init__(instance)
        if self._version == 1:
            self.is_making_all_tasks_covered = True
        elif self._version == 2:
            self.is_making_all_tasks_covered = False
        else:
            raise ValueError(f"Given model has a version {self._version} but its version must be either 1 or 2")
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
