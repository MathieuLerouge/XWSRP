# Local libraries
from src.modeling.instance import Instance
from src.modeling.solution import Solution


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
        self._name = "Solution" + self._instance.name + "By" + solving_method_id

    @classmethod
    def from_Solution(cls, solution: Solution):
        solving_method_id = "NA"
        solutionForLS = cls(solving_method_id, solution.instance, solution.name, solution._copy_sequences(),
                            solution._copy_tasks_realizations(), solution._copy_lunch_breaks_realizations())
        solutionForLS._KPIs = solution._copy_KPIs()
        return solutionForLS

    @property
    def solving_method_id(self):
        return self._optimization_data[SOLVING_METHOD_ID_KEY]

    @property
    def solving_method_parameters(self):
        return self._optimization_data[SOLVING_METHOD_PARAMS_KEY]

    @solving_method_parameters.setter
    def solving_method_parameters(self, params):
        self._optimization_data[SOLVING_METHOD_PARAMS_KEY] = params

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

    def copy(self, name: str = None):
        return SolutionOpti.from_Solution(super().copy(name))
