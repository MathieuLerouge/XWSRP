# Local libraries
from src.modeling.employee import Employee
from src.modeling.task import Task
from src.utils.location import Location


def build_task(name: str = "T1", duration: int = 30, start_time_lb: int = 480, end_time_ub: int = 600,
              skill_level: int = 1) -> Task:
    return Task(name, duration, start_time_lb, end_time_ub, skill_level, Location(0, 0))


def build_employee(name: str = "E1", start_time_lb: int = 480, end_time_ub: int = 1020,
                   skill_level: int = 1) -> Employee:
    return Employee(name, start_time_lb, end_time_ub, Location(0, 0), skill_level)
