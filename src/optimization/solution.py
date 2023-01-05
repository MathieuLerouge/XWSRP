# Local libraries
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.utils.files import SOLUTION_NAME_PREFIX, SOLUTION_NAME_PREFIX_BIS


# Global variables
SOLVING_METHOD_ID_KEY = 'solving_method_id'
SOLVING_METHOD_PARAMS_KEY = 'solving_method_params'
SOLVING_TIME_KEY = 'solving_time'
OPTIMALITY_GAP_KEY = 'optimality_gap'
OBJECTIVE_VALUE_KEY = 'objective_value'


# Class SolutionOpti
class SolutionOpti(Solution):

    def __init__(self, solving_method_id: str, instance: Instance, name: str = None, sequences: dict = None,
                 tasks_realizations: dict = None, lunch_breaks_realizations: dict = None):
        super().__init__(instance, name, sequences, tasks_realizations, lunch_breaks_realizations)
        self._optimization_data = dict()
        self._optimization_data[SOLVING_METHOD_ID_KEY] = solving_method_id

    ############################################
    # Conversion from Solution to SolutionOpti #
    ############################################

    @classmethod
    def from_Solution(cls, solution: Solution):
        solving_method_id = "NA"
        solution_for_optimization = cls(solving_method_id, solution.instance, solution.name, solution._copy_sequences(),
                                        solution._copy_tasks_realizations(), solution._copy_lunch_breaks_realizations())
        solution_for_optimization._KPIs = solution._copy_KPIs()
        return solution_for_optimization

    ########
    # Name #
    ########

    @property
    def full_name(self):
        full_name = super().full_name
        if self._optimization_data[SOLVING_METHOD_ID_KEY] is not None:
            if self.instance.name_case_type_is_snake_case():
                full_name += "_by_" + self._optimization_data[SOLVING_METHOD_ID_KEY]
            elif self.instance.name_case_type_is_camel_case():
                full_name += "By" + self._optimization_data[SOLVING_METHOD_ID_KEY]
            else:
                raise ValueError(f"Unknown case type {self.instance.name_case_type}")
        return full_name

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
        return float(self._optimization_data[SOLVING_TIME_KEY])

    @solving_time.setter
    def solving_time(self, solving_time: float):
        self._optimization_data[SOLVING_TIME_KEY] = str(solving_time)

    @property
    def optimality_gap(self):
        return float(self._optimization_data[OPTIMALITY_GAP_KEY])

    @optimality_gap.setter
    def optimality_gap(self, optimality_gap: float):
        self._optimization_data[OPTIMALITY_GAP_KEY] = str(optimality_gap)

    @property
    def objective_value(self):
        return float(self._optimization_data[OBJECTIVE_VALUE_KEY])

    @objective_value.setter
    def objective_value(self, objective_value: float):
        self._optimization_data[OBJECTIVE_VALUE_KEY] = str(objective_value)

    ########
    # Copy #
    ########

    def copy(self, name: str = None):
        return SolutionOpti.from_Solution(super().copy(name))
