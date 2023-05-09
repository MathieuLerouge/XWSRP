# Local libraries
from src.explaining.modeling.employee import EditableEmployee
from src.explaining.modeling.instance import EditableInstance
from src.explaining.modeling.sequence import EditableSequence
from src.modeling.solution import Solution
from src.optimization.heuristics.solution import SolutionForHeuristics


# def recreate_sequences_with_reference_to_instance(solution: Solution, instance: Instance):
#     sequences_reproduction = dict()
#     for employee in instance.employees:
#         if employee.name not in solution.instance.employees_names:
#             raise ValueError("The employee named {employee.name} is not an employee of the solution")
#         sequence = solution.get_sequence_by_name(employee.name)
#         news_steps = [StepLS(instance.get_hypothetical_activity_by_names(step.activity.name, employee.name),
#                              step.arrival_time, step.start_time, step.end_time) for step in sequence]
#         sequences_reproduction[employee.name] = SequenceLS(instance, employee, news_steps)
#     return sequences_reproduction


# Class EditableSolution
class EditableSolution(SolutionForHeuristics):

    def __init__(self, instance: EditableInstance, name: str = None, sequences: dict[str, EditableSequence] = None,
                 tasks_performances: dict = None):
        super().__init__(instance, name, sequences, tasks_performances)
        self._name = name
        self.compute_KPIs()

    @classmethod
    def from_Solution(cls, solution: Solution, instance: EditableInstance = None):
        instance = EditableInstance.from_Instance(solution.instance) if instance is None else instance
        sequences = dict(
            [(employee.name, EditableSequence.from_Sequence(solution.get_sequence_by_name(employee.name), instance))
             for employee in instance.employees]
        )
        return cls(instance, solution.name, sequences, solution._copy_tasks_realizations())

    @property
    def instance(self):
        return self._instance

    @instance.setter
    def instance(self, instance: EditableInstance):
        self._instance = instance
        for sequence in self._sequences.values():
            if isinstance(sequence, EditableSequence):
                sequence.instance = instance
            else:
                raise TypeError(f"The sequence {sequence} should be of type EditableSequence")
        self.compute_KPIs()

    def copy(self, name: str = None):
        name = self._name + "_copy" if name is None else name
        solution = EditableSolution(self._instance, name, self._copy_sequences(), self._copy_tasks_realizations())
        solution.name = name
        solution._KPIs = self._copy_KPIs()
        return solution

    def replace_sequence_by_another(self, employee: EditableEmployee, new_sequence: EditableSequence,
                                    update_KPIs: bool = True):
        self._replace_sequence_by_another(employee, new_sequence, update_KPIs)
