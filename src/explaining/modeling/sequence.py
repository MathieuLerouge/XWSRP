# Local libraries
from src.explaining.modeling.employee import EditableEmployee
from src.explaining.modeling.instance import EditableInstance
from src.modeling.sequence import Sequence
from src.optimization.localsearch.sequence import SequenceLS
from src.optimization.localsearch.step import StepLS


# Class EditableSequence
class EditableSequence(SequenceLS):

    def __init__(self, instance: EditableInstance, employee: EditableEmployee, steps: list[StepLS] = None):
        super().__init__(instance, employee, steps)
        self._instance = instance
        self._employee = employee
        self._steps = steps
        self.update_time_slacks()

    @classmethod
    def from_Sequence(cls, sequence: Sequence, instance: EditableInstance = None):
        instance = EditableInstance.from_Instance(sequence.instance) if instance is None else instance
        employee = instance.get_employee_by_name(sequence.employee.name)
        steps = [StepLS(instance.get_hypothetical_activity_by_names(step.activity.name, employee.name),
                        step.arrival_time, step.start_time, step.end_time) for step in sequence]
        return cls(instance, employee, steps)

    @property
    def instance(self):
        return self._instance

    @instance.setter
    def instance(self, instance: EditableInstance):
        self._instance = instance
        self._employee = instance.get_employee_by_name(self.employee.name)
        self._steps = [StepLS(instance.get_hypothetical_activity_by_names(step.activity.name, self._employee.name),
                              start_time=step.start_time) for step in self._steps]
        self.compute_times_based_on_fixed_start_times()
        self.update_time_slacks()
        self.compute_KPIs()

    ########
    # Copy #
    ########

    def copy(self):
        sequence = EditableSequence(self._instance, self._employee, self._copy_steps())
        sequence._KPIs = self._copy_KPIs()
        return sequence
