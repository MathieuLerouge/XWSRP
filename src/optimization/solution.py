# Local libraries
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.utils.constants import SOLUTION_NAME_PREFIX, SOLUTION_NAME_PREFIX_BIS, SOLUTION_SOLVING_METHOD_SYMBOL_BIS, \
    SNAKE_CASE, CAMEL_CASE
from src.utils.files import remove_solving_method_from_solution_file_name

# Global variables
SOLVING_METHOD_ID_KEY = 'solving_method_id'
SOLVING_METHOD_PARAMS_KEY = 'solving_method_params'
SOLVING_TIME_KEY = 'solving_time'
OPTIMALITY_GAP_KEY = 'optimality_gap'
OBJECTIVE_VALUE_KEY = 'objective_value'


######################
# Class SolutionOpti #
######################

class SolutionOpti(Solution):

    def __init__(self, instance: Instance, name: str = None, sequences: dict = None, tasks_performances: dict = None,
                 lunch_breaks_performances: dict = None, solving_method_id: str = 'NA'):
        self._optimization_data = dict()
        self._optimization_data[SOLVING_METHOD_ID_KEY] = solving_method_id
        self._optimization_data[SOLVING_METHOD_PARAMS_KEY] = None
        self._optimization_data[SOLVING_TIME_KEY] = None
        self._optimization_data[OPTIMALITY_GAP_KEY] = None
        self._optimization_data[OBJECTIVE_VALUE_KEY] = None
        super().__init__(instance, name, sequences, tasks_performances, lunch_breaks_performances)

    ############################################
    # Conversion from Solution to SolutionOpti #
    ############################################

    @classmethod
    def from_Solution(cls, solution: Solution):
        solution_for_optimization = cls(solution.instance, solution.name, solution._copy_sequences(),
                                        solution._copy_tasks_realizations(), solution._copy_lunch_breaks_realizations())
        solution_for_optimization._KPIs = solution._copy_KPIs()
        return solution_for_optimization

    ########
    # Name #
    ########

    def _create_name(self):
        if self.instance.name_case_type_is_snake_case:
            return f"{SOLUTION_NAME_PREFIX}{self.instance.core_name}_" \
                   f"{SOLUTION_SOLVING_METHOD_SYMBOL_BIS}_{self.solving_method_id}"
        elif self.instance.name_case_type_is_camel_case:
            return f"{SOLUTION_NAME_PREFIX_BIS}{self.instance.core_name_with_version}" \
                   f"{SOLUTION_SOLVING_METHOD_SYMBOL_BIS}{self.solving_method_id}"
        else:
            raise ValueError(f"The instance name case type must be either {SNAKE_CASE} or {CAMEL_CASE}")

    @property
    def name_with_solving_method(self):
        return self.name

    @property
    def name_without_solving_method(self):
        return remove_solving_method_from_solution_file_name(self.name)

    ##################
    # Solving method #
    ##################

    @property
    def solving_method_id(self):
        return self._optimization_data[SOLVING_METHOD_ID_KEY]

    @property
    def solving_method_parameters(self):
        return self._optimization_data[SOLVING_METHOD_PARAMS_KEY]

    @solving_method_parameters.setter
    def solving_method_parameters(self, params):
        self._optimization_data[SOLVING_METHOD_PARAMS_KEY] = params

    ########################
    # Optimization results #
    ########################

    @property
    def solving_time(self):
        return self._optimization_data[SOLVING_TIME_KEY]

    @solving_time.setter
    def solving_time(self, solving_time: float):
        self._optimization_data[SOLVING_TIME_KEY] = str(solving_time)

    @property
    def optimality_gap(self):
        return self._optimization_data[OPTIMALITY_GAP_KEY]

    @optimality_gap.setter
    def optimality_gap(self, optimality_gap: float):
        self._optimization_data[OPTIMALITY_GAP_KEY] = str(optimality_gap)

    @property
    def objective_value(self):
        return self._optimization_data[OBJECTIVE_VALUE_KEY]

    @objective_value.setter
    def objective_value(self, objective_value: float):
        self._optimization_data[OBJECTIVE_VALUE_KEY] = str(objective_value)

    ########
    # Copy #
    ########

    def copy(self, name: str = None):
        return SolutionOpti.from_Solution(super().copy(name))
