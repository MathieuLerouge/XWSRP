# Local libraries
from src.modeling.sequence import Sequence
from src.optimization.localsearch.solution import SolutionLS
from src.teaching.modeling.instance import InstanceForTeaching
from src.utils.constants import SOLUTION_NAME_PREFIX_BIS, CAMEL_CASE, SOLUTION_SOLVING_METHOD_SYMBOL_BIS


#############################
# Class SolutionForTeaching #
#############################

class SolutionForTeaching(SolutionLS):

    def __init__(self, instance: InstanceForTeaching, name: str = None, sequences: dict[str, Sequence] = None,
                 tasks_performances: dict = None, lunch_breaks_performances: dict = None,
                 solving_method_id: str = None):
        self._solving_method_id = solving_method_id
        super().__init__(instance, name, sequences, tasks_performances, lunch_breaks_performances)
        self._instance = instance

    ############
    # Instance #
    ############

    @property
    def instance(self):
        """
        Returns the teaching instance associated to this teaching solution.

        :return: the teaching instance associated to this teaching solution (InstanceForTeaching)
        """
        return self._instance

    ########
    # Name #
    ########

    def _create_name(self):
        """
        Creates the name of the solution with the right suffix.

        :return: the name of the solution (str)
        """
        if self.instance.name_case_type_is_camel_case:
            return f"{SOLUTION_NAME_PREFIX_BIS}{self.instance.core_name_with_version}" \
                   f"{SOLUTION_SOLVING_METHOD_SYMBOL_BIS}{self._solving_method_id}"
        else:
            raise ValueError(f"The instance name case type is not {CAMEL_CASE}")
