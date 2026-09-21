# Local libraries
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.task import Task
from src.modeling.unavailability import Unavailability
from src.utils.location import Location


def build_instance() -> Instance:
    return Instance()


def build_employee(name: str = "E1", start_time_lb: int = 0, end_time_ub: int = 1000,
                   skill_level: int = 1) -> Employee:
    return Employee(name, start_time_lb, end_time_ub, Location(0, 0), skill_level)


def build_task(name: str = "T1", duration: int = 30, start_time_lb: int = 0, end_time_ub: int = 1000,
              skill_level: int = 1) -> Task:
    return Task(name, duration, start_time_lb, end_time_ub, skill_level, Location(0, 0))


def build_unavailability(employee: Employee, name: str = "U1", start_time: int = 300,
                         end_time: int = 330) -> Unavailability:
    return Unavailability(employee, name, start_time, end_time, Location(0, 0))
