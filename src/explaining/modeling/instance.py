from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.modeling.employee import EditableEmployee
from src.explaining.modeling.task import EditableTask
from src.modeling.instance import Instance
from src.utils.location import Location


# Class EditableInstance
class EditableInstance(Instance):

    def __init__(self, name: str = "Untitled", speed: float = 1):
        super().__init__(name, speed)

    @classmethod
    def from_Instance(cls, instance: Instance, name: str = None):
        editable_instance_name = instance.name if name is None else name
        editable_instance = cls(instance.name, instance.speed)
        for employee in instance.employees:
            editable_instance.add_employee(employee.name, employee.start_time_lb, employee.end_time_ub,
                                           employee.location, employee.skill_level)
        for task in instance.tasks:
            editable_instance.add_task(task.name, task.duration, task.start_time_lb, task.end_time_ub,
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

    def add_employee(self, name: str, start_time_lb: int, end_time_ub: int, location: Location, skill_level: int):
        if name in self._employees.keys():
            raise ValueError(f"The given employee {name} is already among the employees of this instance")
        else:
            self._employees[name] = EditableEmployee(name, start_time_lb, end_time_ub, location, skill_level)

    @property
    def tasks(self) -> list[EditableTask]:
        return list(self._tasks.values())

    def add_task(self, name: str, duration: int, start_time_lb: int, end_time_ub: int,
                 skill_level: int, location: Location):
        if name in self._tasks.keys():
            raise ValueError(f"The given task {name} is already among the tasks of the instance")
        else:
            self._tasks[name] = EditableTask(name, duration, start_time_lb, end_time_ub, skill_level, location)

    def alter(self, instance_alterations: InstanceChanges):
        for employee in self.employees:
            if instance_alterations.is_affecting_employee(employee):
                new_start_time_lb = instance_alterations.get_employee_start_time_lb(employee)
                if new_start_time_lb is not None:
                    employee.start_time_lb = new_start_time_lb
                new_end_time_ub = instance_alterations.get_employee_end_time_ub(employee)
                if new_end_time_ub is not None:
                    employee.end_time_ub = new_end_time_ub
        for task in self.tasks:
            if instance_alterations.is_affecting_task(task):
                new_duration = instance_alterations.get_task_duration(task)
                if new_duration is not None:
                    task.duration = new_duration
                new_start_time_lb = instance_alterations.get_task_start_time_lb(task)
                if new_start_time_lb is not None:
                    task.start_time_lb = new_start_time_lb
                new_end_time_ub = instance_alterations.get_task_end_time_ub(task)
                if new_end_time_ub is not None:
                    task.end_time_ub = new_end_time_ub

    def copy(self, name: str = None):
        if self.has_task_unavailabilities:
            raise NotImplementedError("Instance copy for instance having task unavailabilities is not implemented")
        instance_name = self._name + "_copy" if name is None else name
        instance = EditableInstance(instance_name, self._speed)
        for employee in self.employees:
            instance.add_employee(employee.name, employee.start_time_lb, employee.end_time_ub,
                                  employee.location, employee.skill_level)
            employee_copy = instance.get_employee_by_name(employee.name)
            for unavailability in employee.unavailabilities:
                employee_copy.add_unavailability(unavailability.location, unavailability.start_time_lb,
                                                 unavailability.end_time_ub)
        for task in self.tasks:
            instance.add_task(task.name, task.duration, task.start_time_lb, task.end_time_ub,
                              task.skill_level, task.location)
        instance.update()
        return instance
