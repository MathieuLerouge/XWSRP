# Local libraries
from model.solution import Solution


# Class Explanation
class Explanation:

    def __init__(self, text: str, solution: Solution = None, solution_is_feasible: bool = False,
                 infeasibility=None, critical_bounds=None):
        self._text = text
        self._solution = solution
        self._feasible = solution_is_feasible
        self.infeasibility = infeasibility
        self.critical_bounds = critical_bounds

    @property
    def text(self):
        return self._text

    @property
    def solution(self):
        return self._solution

    @property
    def has_new_solution(self) -> bool:
        return self._solution is not None

    @property
    def solution_is_feasible(self):
        return self.has_new_solution and self._feasible
