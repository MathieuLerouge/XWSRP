# Local libraries
from src.modeling.activity import Activity
from src.modeling.comeback import ComeBack
from src.modeling.departure import Departure
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.task import Task


# Global variables
LEAVING_HOME_INDEX = 0
COMING_BACK_HOME_INDEX = -1


##################
# MILPModelIndex #
##################

class MILPModelIndex:
    """
    Index-translation layer between an Instance's domain objects and the small integer indices
    that MILPModel's decision variables and constraints are built around.
    """

    def __init__(self, instance: Instance):
        """
        Args:
            instance: the instance to build the index for.
        """

        # Instance
        self._instance = instance

        # Employees
        self._employees: dict[int, Employee] = dict()
        self._employees_indices: list[int] = []
        for i, employee in enumerate(instance.employees):
            self._employees[i + 1] = employee
            self._employees_indices.append(i + 1)
        self._employee_indices_by_employee: dict[Employee, int] = \
            dict([(employee, index) for index, employee in self._employees.items()])

        # Tasks
        self._tasks: dict[int, Task] = dict()
        self._tasks_indices: list[int] = []
        for j, task in enumerate(instance.tasks):
            self._tasks[j + 1] = task
            self._tasks_indices.append(j + 1)
        self._task_indices_by_task: dict[Task, int] = \
            dict([(task, index) for index, task in self._tasks.items()])

        # Hypothetical activities
        self._hypothetical_activities: dict[int, dict[int, Activity]] = dict()
        self._hypothetical_activities_indices: dict[int, list[int]] = dict()
        for i in self._employees_indices:
            self._hypothetical_activities[i] = dict()
            self._hypothetical_activities_indices[i] = []

            # Departure
            self._hypothetical_activities[i][LEAVING_HOME_INDEX] = Departure(self._employees[i])
            self._hypothetical_activities_indices[i].append(LEAVING_HOME_INDEX)

            # Tasks
            j = 1
            for task in instance.tasks:
                self._hypothetical_activities[i][j] = task
                self._hypothetical_activities_indices[i].append(j)
                j += 1

            # Unavailabilities
            for unavailability in self._employees[i].unavailabilities:
                self._hypothetical_activities[i][j] = unavailability
                self._hypothetical_activities_indices[i].append(j)
                j += 1

            # Comeback
            self._hypothetical_activities[i][COMING_BACK_HOME_INDEX] = ComeBack(self._employees[i])
            self._hypothetical_activities_indices[i].append(COMING_BACK_HOME_INDEX)

    ############
    # Instance #
    ############

    @property
    def instance(self) -> Instance:
        """The instance this index is built for."""
        return self._instance

    #############
    # Employees #
    #############

    @property
    def employees_indices(self):
        """The indices of all employees of the instance."""
        return self._employees_indices

    def get_employee_by_index(self, employee_index: int) -> Employee:
        """
        Return the employee corresponding to the given index.

        Args:
            employee_index: the index of the employee.

        Raises:
            IndexError: if the given index does not correspond to an employee.
        """
        try:
            return self._employees[employee_index]
        except KeyError:
            raise IndexError(f"The given index {employee_index} does not correspond to an employee")

    def get_employee_index_by_employee(self, employee: Employee) -> int:
        """
        Return the index corresponding to the given employee.

        Args:
            employee: the employee to look up.

        Raises:
            IndexError: if the given employee is not indexed.
        """
        try:
            return self._employee_indices_by_employee[employee]
        except KeyError:
            raise IndexError(f"The given employee {employee} is not indexed")

    #########
    # Tasks #
    #########

    @property
    def tasks_indices(self):
        """The indices of all tasks of the instance."""
        return self._tasks_indices

    def get_task_by_index(self, task_index: int) -> Task:
        """
        Return the task corresponding to the given index.

        Args:
            task_index: the index of the task.

        Raises:
            IndexError: if the given index does not correspond to a task.
        """
        try:
            return self._tasks[task_index]
        except KeyError:
            raise IndexError(f"The given index {task_index} does not correspond to a task")

    def get_task_index_by_task(self, task: Task) -> int:
        """
        Return the index corresponding to the given task.

        Args:
            task: the task to look up.

        Raises:
            IndexError: if the given task is not indexed.
        """
        try:
            return self._task_indices_by_task[task]
        except KeyError:
            raise IndexError(f"The given task {task} is not indexed")

    ###########################
    # Hypothetical activities #
    ###########################

    def get_hyp_activities_indices(self, employee_index: int, including_departure=True,
                                   including_comeback=True, including_unavailabilities=True):
        """
        Return the indices of the given employee's hypothetical activities,
        i.e. the ordered list of activities (departure, tasks, unavailabilities, comeback)
        that this MILP considers when deciding that employee's sequence,
        optionally excluding some of its ends.

        Args:
            employee_index: the index of the employee.
            including_departure: if True, include the departure index (LEAVING_HOME_INDEX).
            including_comeback: if True, include the comeback index (COMING_BACK_HOME_INDEX).
            including_unavailabilities: if True, include the employee's unavailabilities' indices.

        Returns:
            the list of hypothetical activities' indices, in departure/tasks/unavailabilities/comeback order.
        """
        first_index = 0
        if not including_departure:
            first_index = 1
        second_index = len(self._hypothetical_activities_indices[employee_index]) - 1
        if not including_unavailabilities:
            second_index = len(self._tasks_indices) + 1
        indices = self._hypothetical_activities_indices[employee_index][first_index:second_index]
        if including_comeback:
            indices.append(COMING_BACK_HOME_INDEX)
        return indices

    def get_hyp_activity_by_indices(self, employee_index: int, activity_index: int) -> Activity:
        """
        Return the hypothetical activity corresponding to the given employee/activity indices.

        Args:
            employee_index: the index of the employee.
            activity_index: the index of the activity, among that employee's hypothetical activities.

        Raises:
            IndexError: if the given indices do not correspond to a hypothetical activity.
        """
        try:
            return self._hypothetical_activities[employee_index][activity_index]
        except KeyError:
            raise IndexError(
                f"The given indices {employee_index, activity_index} does not correspond to a hypothetical activity"
            )

    def get_hyp_activity_index_by_activity(self, employee_index: int, activity: Activity) -> int:
        """
        Return the index of the given activity among the given employee's hypothetical activities.

        A Departure/ComeBack always indexes to LEAVING_HOME_INDEX/COMING_BACK_HOME_INDEX regardless of
        which employee constructed it, since MILPModelIndex builds one afresh per employee at __init__
        time rather than reusing the instance's own Departure/ComeBack objects.

        Args:
            employee_index: the index of the employee.
            activity: the activity to look up (a Departure, ComeBack, Task or Unavailability).

        Raises:
            IndexError: if the given employee has no hypothetical activity equal to the given activity.
        """
        if isinstance(activity, Departure):
            return LEAVING_HOME_INDEX
        if isinstance(activity, ComeBack):
            return COMING_BACK_HOME_INDEX
        if isinstance(activity, Task):
            return self.get_task_index_by_task(activity)
        for index, candidate in self._hypothetical_activities[employee_index].items():
            if candidate is activity:
                return index
        raise IndexError(f"Employee {employee_index} has no hypothetical activity equal to {activity}")

    def get_hyp_activities_TW_indices(self, employee_index: int, activity_index: int):
        """
        Return the range of time-window indices of the given hypothetical activity,
        i.e. the valid values for the U decision variable's time-window index.

        Args:
            employee_index: the index of the employee.
            activity_index: the index of the activity, among that employee's hypothetical activities.
        """
        return range(len(self._hypothetical_activities[employee_index][activity_index].time_windows))

    def get_traveling_duration(self, employee_index: int, activity_index1: int, activity_index2: int):
        """
        Return the given employee's traveling duration between two of their hypothetical activities.

        Args:
            employee_index: the index of the employee.
            activity_index1: the index of the first activity, among that employee's hypothetical activities.
            activity_index2: the index of the second activity, among that employee's hypothetical activities.
        """
        return self._instance.compute_traveling_duration(
            activity1=self.get_hyp_activity_by_indices(employee_index, activity_index1),
            activity2=self.get_hyp_activity_by_indices(employee_index, activity_index2)
        )

    ####################
    # Unavailabilities #
    ####################

    def get_employee_unavailability_by_indices(self, employee_index: int, unavailability_index: int) -> Activity:
        """
        Return the unavailability corresponding to the given employee/unavailability indices.

        Args:
            employee_index: the index of the employee.
            unavailability_index: the index of the unavailability, among that employee's hypothetical activities.

        Raises:
            IndexError: if the given indices do not correspond to an unavailability.
        """
        try:
            return self.get_hyp_activity_by_indices(employee_index, unavailability_index)
        except IndexError:
            raise IndexError(
                f"The given indices {employee_index, unavailability_index} does not correspond to a unavailability"
            )

    def get_employee_unavailabilities_indices(self, employee_index: int):
        """
        Return the indices of the given employee's unavailabilities, among their hypothetical activities.

        Args:
            employee_index: the index of the employee.

        Raises:
            IndexError: if the given index does not correspond to an employee.
        """
        try:
            first_index = len(self._tasks_indices) + 1
            second_index = len(self._hypothetical_activities_indices[employee_index]) - 1
            return self._hypothetical_activities_indices[employee_index][first_index:second_index]
        except KeyError:
            raise IndexError(f"The given index {employee_index} does not correspond to an employee")
