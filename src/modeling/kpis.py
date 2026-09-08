########
# KPIs #
########

class KPIs:
    """
    The key performance indicators (KPIs) computed for a Sequence or a Solution, including:
    the number of tasks performed, the total working duration, the total traveling duration and distance,
    and the total idle time.
    """

    def __init__(self, nb_performed_tasks: int = 0, total_working_duration: int = 0,
                 total_traveling_duration: int = 0, total_traveling_distance: float = 0.0,
                 total_idle_time: int = 0):
        """
        Args:
            nb_performed_tasks: Number of tasks performed.
            total_working_duration: Total time, in minutes, spent performing tasks.
            total_traveling_duration: Total time, in minutes, spent traveling.
            total_traveling_distance: Total distance traveled, in km.
            total_idle_time: Total idle time, in minutes, spent waiting.
        """
        self._nb_performed_tasks = nb_performed_tasks
        self._total_working_duration = total_working_duration
        self._total_traveling_duration = total_traveling_duration
        self._total_traveling_distance = total_traveling_distance
        self._total_idle_time = total_idle_time

    @property
    def nb_performed_tasks(self) -> int:
        """Number of tasks performed."""
        return self._nb_performed_tasks

    @nb_performed_tasks.setter
    def nb_performed_tasks(self, nb_performed_tasks: int):
        self._nb_performed_tasks = nb_performed_tasks

    @property
    def total_working_duration(self) -> int:
        """Total time, in minutes, spent performing tasks."""
        return self._total_working_duration

    @total_working_duration.setter
    def total_working_duration(self, total_working_duration: int):
        self._total_working_duration = total_working_duration

    @property
    def total_traveling_duration(self) -> int:
        """Total time, in minutes, spent traveling."""
        return self._total_traveling_duration

    @total_traveling_duration.setter
    def total_traveling_duration(self, total_traveling_duration: int):
        self._total_traveling_duration = total_traveling_duration

    @property
    def total_traveling_distance(self) -> float:
        """Total distance traveled, in km."""
        return self._total_traveling_distance

    @total_traveling_distance.setter
    def total_traveling_distance(self, total_traveling_distance: float):
        self._total_traveling_distance = total_traveling_distance

    @property
    def total_idle_time(self) -> int:
        """Total idle time, in minutes, spent waiting."""
        return self._total_idle_time

    @total_idle_time.setter
    def total_idle_time(self, total_idle_time: int):
        self._total_idle_time = total_idle_time

    def __add__(self, other: "KPIs") -> "KPIs":
        """
        Returns new KPIs whose values are the field-wise sum of these KPIs and other.

        Raises:
            TypeError: If other is not a KPIs.
        """
        if not isinstance(other, KPIs):
            raise TypeError(f"Cannot add {type(other).__name__} to {KPIs.__name__}")
        return KPIs(
            self._nb_performed_tasks + other._nb_performed_tasks,
            self._total_working_duration + other._total_working_duration,
            self._total_traveling_duration + other._total_traveling_duration,
            self._total_traveling_distance + other._total_traveling_distance,
            self._total_idle_time + other._total_idle_time,
        )

    def __sub__(self, other: "KPIs") -> "KPIs":
        """
        Returns new KPIs whose values are the field-wise difference of these KPIs minus others.

        Raises:
            TypeError: If other is not a KPIs.
        """
        if not isinstance(other, KPIs):
            raise TypeError(f"Cannot subtract {type(other).__name__} from {KPIs.__name__}")
        return KPIs(
            self._nb_performed_tasks - other._nb_performed_tasks,
            self._total_working_duration - other._total_working_duration,
            self._total_traveling_duration - other._total_traveling_duration,
            self._total_traveling_distance - other._total_traveling_distance,
            self._total_idle_time - other._total_idle_time,
        )
