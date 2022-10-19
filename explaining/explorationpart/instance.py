from explaining.explorationpart.instance_changes import InstanceChanges
from explaining.explorationpart.employee import EditableEmployee
from explaining.explorationpart.task import EditableTask
from model.instance import Instance
from utils.location import Location


# Class EditableInstance
class EditableInstance(Instance):

    def __init__(self, name: str = "Untitled", speed: float = 1):
        super().__init__(name, speed)

    @classmethod
    def from_Instance(cls, instance: Instance, name: str = None):
        editable_instance_name = instance.name if name is None else name
        editable_instance = cls(instance.name, instance.speed)
        for employee in instance.employees:
            editable_instance.add_employee(employee.name, employee.start_time_LB, employee.end_time_UB,
                                           employee.location, employee.skill_level)
        for task in instance.tasks:
            editable_instance.add_task(task.name, task.duration, task.start_time_LB, task.end_time_UB,
                                       task.skill_level, task.location)
        editable_instance.update()
        return editable_instance

    @property
    def employees(self) -> list[EditableEmployee]:
        return list(self._employees.values())

    def get_employee_by_name(self, employee_name: str) -> EditableEmployee:
        try:
            return self._employees[employee_name]
        except KeyError:
            raise ValueError(f"The given employee's name {employee_name} is not one of the employees' names")

    def add_employee(self, name: str, start_time_LB: int, end_time_UB: int, location: Location, skill_level: int):
        if name in self._employees.keys():
            raise ValueError(f"The given employee {name} is already among the employees of this instance")
        else:
            self._employees[name] = EditableEmployee(name, start_time_LB, end_time_UB, location, skill_level)

    @property
    def tasks(self) -> list[EditableTask]:
        return list(self._tasks.values())

    def add_task(self, name: str, duration: int, start_time_LB: int, end_time_UB: int,
                 skill_level: int, location: Location):
        if name in self._tasks.keys():
            raise ValueError(f"The given task {name} is already among the tasks of the instance")
        else:
            self._tasks[name] = EditableTask(name, duration, start_time_LB, end_time_UB, skill_level, location)

    def alter(self, instance_alterations: InstanceChanges):
        for employee in self.employees:
            if instance_alterations.is_affecting_employee(employee):
                new_start_time_LB = instance_alterations.get_employee_start_time_LB(employee)
                if new_start_time_LB is not None:
                    employee.start_time_LB = new_start_time_LB
                new_end_time_UB = instance_alterations.get_employee_end_time_UB(employee)
                if new_end_time_UB is not None:
                    employee.end_time_UB = new_end_time_UB
        for task in self.tasks:
            if instance_alterations.is_affecting_task(task):
                new_duration = instance_alterations.get_task_duration(task)
                if new_duration is not None:
                    task.duration = new_duration
                new_start_time_LB = instance_alterations.get_task_start_time_LB(task)
                if new_start_time_LB is not None:
                    task.start_time_LB = new_start_time_LB
                new_end_time_UB = instance_alterations.get_task_end_time_UB(task)
                if new_end_time_UB is not None:
                    task.end_time_UB = new_end_time_UB

    def copy(self, name: str = None):
        if self.has_task_unavailabilities:
            raise NotImplementedError("Instance copy for instance having task unavailabilities is not implemented")
        instance_name = self._name + "_copy" if name is None else name
        instance = EditableInstance(instance_name, self._speed)
        for employee in self.employees:
            instance.add_employee(employee.name, employee.start_time_LB, employee.end_time_UB,
                                  employee.location, employee.skill_level)
            employee_copy = instance.get_employee_by_name(employee.name)
            for unavailability in employee.unavailabilities:
                employee_copy.add_unavailability(unavailability.location, unavailability.start_time_LB,
                                                 unavailability.end_time_UB)
        for task in self.tasks:
            instance.add_task(task.name, task.duration, task.start_time_LB, task.end_time_UB,
                              task.skill_level, task.location)
        instance.update()
        return instance
