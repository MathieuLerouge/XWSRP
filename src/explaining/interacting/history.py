# Standard library
from typing import Union

# Local libraries
from src.modeling.instance import Instance
from src.optimization.localsearch.solution import SolutionLS


# Class History
class History:

    def __init__(self, solution: SolutionLS):
        self._memory = dict()
        self._memory[solution.instance.name] = dict(
            instance=solution.instance,
            solutions={solution.name: solution}
        )
        self._map_solution_name_to_instance_name = dict()
        self._map_solution_name_to_instance_name[solution.name] = solution.instance.name

    def contain_instance(self, instance: Instance):
        return instance.name in self._memory.keys()

    def contain_solution(self, solution: SolutionLS):
        if self.contain_instance(solution.instance):
            if solution.name in self._memory[solution.instance.name]['solutions']:
                return True
        return False

    def __contains__(self, obj: Union[Instance, SolutionLS]):
        if isinstance(obj, Instance):
            return self.contain_instance(obj)
        elif isinstance(obj, SolutionLS):
            return self.contain_solution(obj)
        else:
            return TypeError(f"The object type which is {type(obj)} must be {Instance} or {SolutionLS}")

    @property
    def nb_instances(self):
        return len(self._memory)

    @property
    def instances(self):
        return [memory_value['instance'] for memory_value in self._memory.values()]

    @property
    def instances_names(self):
        return list(self._memory.keys())

    @property
    def solutions(self):
        solutions = []
        for memory_value in self._memory.values():
            solutions += list(memory_value['solutions'].values())
        return solutions

    @property
    def solutions_names(self):
        solutions = []
        for memory_value in self._memory.values():
            solutions += list(memory_value['solutions'].keys())
        return solutions

    def get_instance_by_name(self, instance_name: str):
        return self._memory[instance_name]['instance']

    def get_solution_by_name(self, solution_name: str):
        instance_name = self._map_solution_name_to_instance_name[solution_name]
        return self._memory[instance_name]['solutions'][solution_name]

    def get_solutions_of_instance(self, instance: Instance):
        return list(self._memory[instance.name]['solutions'].values())

    def get_solutions_names_of_instance(self, instance: Instance):
        return list(self._memory[instance.name]['solutions'].keys())

    def get_solutions_of_instance_by_name(self, instance_name: str):
        return list(self._memory[instance_name]['solutions'].values())

    def get_solutions_names_of_instance_by_name(self, instance_name: str):
        return list(self._memory[instance_name]['solutions'].keys())

    def store_solution(self, solution: SolutionLS):
        if not self.contain_solution(solution):
            if self.contain_instance(solution.instance):
                self._memory[solution.instance.name]['solutions'][solution.name] = solution
            else:
                self._memory[solution.instance.name] = dict(
                    instance=solution.instance,
                    solutions={solution.name: solution}
                )
            self._map_solution_name_to_instance_name[solution.name] = solution.instance.name
