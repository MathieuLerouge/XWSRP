#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from src.modeling.activity import Activity
from src.utils.timeset import TimeInterval
from src.utils.location import Location


# Class Task
class Task(Activity):

    def __init__(self, name: str, duration: int, start_time_LB: int, end_time_UB: int,
                 skill_level: int, location: Location):
        super().__init__(name, duration, start_time_LB, end_time_UB, skill_level, location)

    def __eq__(self, task):
        if isinstance(task, Task) and task.name == self.name:
            return True
        else:
            return False

    def __lt__(self, task):
        return self.name < task.name

    def __hash__(self):
        return hash(self._name)

    def __repr__(self):
        return f"{self._name}: {self._duration}min in {self._TWs} "\
               f"at {self._location} requiring level {self._skill_level}"

    def apply_unavailability(self, unavailability_start_time: int, unavailability_end_time: int):
        self._TWs = self._TWs.subtract(
            TimeInterval(lower_bound=unavailability_start_time, upper_bound=unavailability_end_time)
        )

    @property
    def has_unavailability(self):
        return len(self._TWs) > 1


def main():
    task = Task("T1", 40, 8*60, 18*60, 1, Location(0, 0))
    task.apply_unavailability(10*60, 12*60)
    print(task)
    print(task.has_unavailability)


if __name__ == '__main__':
    main()
