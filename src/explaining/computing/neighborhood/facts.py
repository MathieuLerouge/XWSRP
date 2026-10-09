# Standard libraries
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

# Local libraries
from src.explaining.computing.conflict import SkillConflict, TimeConflict
from src.explaining.computing.neighborhood.exceptions import UnattributableFeasibilityShortfallException
from src.explaining.computing.neighborhood.extractor import ConflictExtractor
from src.explaining.computing.neighborhood.model import NeighborhoodModel
from src.explaining.computing.neighborhood.solving import reorder_support_sequences_to_solved_routes
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import (
    Operator, SequenceReordering, TaskDeletion, TaskInsertion, TaskRelocation, TaskRepositioning
)
from src.explaining.neighborhood.restriction import (
    ForbiddenBackwardSubsequence, ForbiddenSequence, ImmediatePrecedence, Precedence, PrecedenceChain, Restriction
)
from src.explaining.question.question import Question
from src.modeling.employee import Employee
from src.modeling.sequence import Sequence
from src.modeling.solution import Solution
from src.modeling.task import Task

# The name standing for an employee's home, at either end of their route, wherever the facts name an activity.
HOME = "home"

# Keys of the dictionaries the facts are serialized to.
KIND_KEY = "kind"
SKILL_CONFLICT_KIND = "skill"
TIME_CONFLICT_KIND = "time"
UNATTRIBUTED_TIME_CONFLICT_KIND = "unattributed time"


#######################
# ExplanationOutcomes #
#######################

class ExplanationOutcomes(Enum):
    """
    What answering a question settled on, decided from the solved neighborhood alone, never by an LLM.

    The positive/negative split follows the predefined explanations' (see create_explanation):
    only a feasible support solution strictly better than the current one (Solution.__gt__) is positive.
    """
    SKILL_BLOCKED = "skill blocked"
    TIME_INFEASIBLE = "time infeasible"
    INFEASIBLE_UNATTRIBUTED = "infeasible unattributed"
    FEASIBLE_IMPROVING = "feasible improving"
    FEASIBLE_NON_IMPROVING = "feasible non improving"

    @property
    def is_feasible(self) -> bool:
        """Whether the support solution of this outcome is feasible."""
        return self in (ExplanationOutcomes.FEASIBLE_IMPROVING, ExplanationOutcomes.FEASIBLE_NON_IMPROVING)

    @property
    def is_positive(self) -> bool:
        """Whether this outcome confirms what the question asked about is possible and worthwhile."""
        return self is ExplanationOutcomes.FEASIBLE_IMPROVING


#############
# StepFacts #
#############

@dataclass(frozen=True)
class StepFacts:
    """
    One activity of a route, with its time window and, when they are meaningful, its solved times.
    All times are in minutes since midnight.

    Attributes:
        activity: Name of the activity.
        duration: Duration of the activity, in minutes.
        time_window_start: Earliest time the activity may start, or None if it has no such bound.
        time_window_end: Latest time the activity may end, or None if it has no such bound.
        start_time: Time the activity starts, or None when the route's times are not meaningful.
        end_time: Time the activity ends, or None when the route's times are not meaningful.
    """
    activity: str
    duration: int
    time_window_start: Optional[int]
    time_window_end: Optional[int]
    start_time: Optional[int] = None
    end_time: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Return these facts as a dictionary, as read back by from_dict."""
        return {"activity": self.activity, "duration": self.duration,
                "time window start": self.time_window_start, "time window end": self.time_window_end,
                "start time": self.start_time, "end time": self.end_time}

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> "StepFacts":
        """
        Rebuild the facts the given dictionary describes.

        Args:
            dictionary: The dictionary to read, as produced by to_dict.

        Returns:
            The rebuilt facts.
        """
        return cls(dictionary["activity"], dictionary["duration"],
                   dictionary["time window start"], dictionary["time window end"],
                   dictionary["start time"], dictionary["end time"])


##############
# RouteFacts #
##############

@dataclass(frozen=True)
class RouteFacts:
    """
    The activities an employee performs between leaving home and coming back home, in route order.

    Attributes:
        employee: Name of the employee.
        availability_start: Earliest time, in minutes since midnight, the employee may leave home.
        availability_end: Latest time, in minutes since midnight, the employee must be back home.
        steps: The activities performed, in route order, home excluded.
    """
    employee: str
    availability_start: int
    availability_end: int
    steps: tuple[StepFacts, ...]

    @property
    def activities(self) -> tuple[str, ...]:
        """Names of the activities performed, in route order."""
        return tuple(step.activity for step in self.steps)

    def to_dict(self) -> dict[str, Any]:
        """Return these facts as a dictionary, as read back by from_dict."""
        return {"employee": self.employee, "availability start": self.availability_start,
                "availability end": self.availability_end, "steps": [step.to_dict() for step in self.steps]}

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> "RouteFacts":
        """
        Rebuild the facts the given dictionary describes.

        Args:
            dictionary: The dictionary to read, as produced by to_dict.

        Returns:
            The rebuilt facts.
        """
        return cls(dictionary["employee"], dictionary["availability start"], dictionary["availability end"],
                   tuple(StepFacts.from_dict(step) for step in dictionary["steps"]))


###############
# RouteChange #
###############

@dataclass(frozen=True)
class RouteChange:
    """
    How an employee's route differs between the current solution and the support solution.

    Attributes:
        employee: Name of the employee.
        current_route: The employee's route in the current solution.
        support_route: The employee's route in the support solution.
        added_tasks: Names of the tasks the support route performs and the current one does not.
        removed_tasks: Names of the tasks the current route performs and the support one does not.
    """
    employee: str
    current_route: RouteFacts
    support_route: RouteFacts
    added_tasks: tuple[str, ...]
    removed_tasks: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return these facts as a dictionary, as read back by from_dict."""
        return {"employee": self.employee, "current route": self.current_route.to_dict(),
                "support route": self.support_route.to_dict(),
                "added tasks": list(self.added_tasks), "removed tasks": list(self.removed_tasks)}

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> "RouteChange":
        """
        Rebuild the facts the given dictionary describes.

        Args:
            dictionary: The dictionary to read, as produced by to_dict.

        Returns:
            The rebuilt facts.
        """
        return cls(dictionary["employee"], RouteFacts.from_dict(dictionary["current route"]),
                   RouteFacts.from_dict(dictionary["support route"]),
                   tuple(dictionary["added tasks"]), tuple(dictionary["removed tasks"]))


############
# KPIFacts #
############

@dataclass(frozen=True)
class KPIFacts:
    """
    The KPIs a solution is compared on, in the priority order of Solution.__gt__.

    Attributes:
        total_working_duration: Total duration of the tasks performed, in minutes (the higher, the better).
        total_traveling_duration: Total traveling duration, in minutes (the lower, the better).
    """
    total_working_duration: int
    total_traveling_duration: int

    @classmethod
    def from_solution(cls, solution: Solution) -> "KPIFacts":
        """
        Read the KPIs off the given solution, computing them first if they are not yet.

        Args:
            solution: The solution to read the KPIs of.

        Returns:
            The facts.
        """
        if not solution.has_kpis:
            solution.compute_kpis()
        return cls(solution.total_working_duration, solution.total_traveling_duration)

    def to_dict(self) -> dict[str, Any]:
        """Return these facts as a dictionary, as read back by from_dict."""
        return {"total working duration": self.total_working_duration,
                "total traveling duration": self.total_traveling_duration}

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> "KPIFacts":
        """
        Rebuild the facts the given dictionary describes.

        Args:
            dictionary: The dictionary to read, as produced by to_dict.

        Returns:
            The rebuilt facts.
        """
        return cls(dictionary["total working duration"], dictionary["total traveling duration"])


#################
# ConflictFacts #
#################

@dataclass(frozen=True)
class ConflictFacts(ABC):
    """
    Why the support solution is infeasible, as an (employee, task) pair that clashes.

    Attributes:
        employee: Name of the employee the task cannot be fitted for.
        task: Name of the task that cannot be fitted.
    """
    employee: str
    task: str

    @property
    @abstractmethod
    def kind(self) -> str:
        """Key of the kind of conflict, as written under KIND_KEY."""

    def to_dict(self) -> dict[str, Any]:
        """Return these facts as a dictionary, as read back by from_dict."""
        return {KIND_KEY: self.kind, "employee": self.employee, "task": self.task}

    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> "ConflictFacts":
        """
        Rebuild the facts the given dictionary describes, of whichever kind it names.

        Args:
            dictionary: The dictionary to read, as produced by to_dict.

        Returns:
            The rebuilt facts.

        Raises:
            ValueError: if the dictionary names no known kind of conflict.
        """
        kind = dictionary[KIND_KEY]
        if kind == SKILL_CONFLICT_KIND:
            return SkillConflictFacts(dictionary["employee"], dictionary["task"],
                                      dictionary["employee skill level"], dictionary["task skill level"])
        if kind == TIME_CONFLICT_KIND:
            return TimeConflictFacts(
                dictionary["employee"], dictionary["task"], dictionary["task duration"],
                dictionary["task time window start"], dictionary["task time window end"],
                dictionary["feasibility shortfall"],
                dictionary["is upstream feasible"], dictionary["is downstream feasible"],
                dictionary["earliest start time"], dictionary["latest start time"],
                dictionary["activity before"], dictionary["activity after"],
                dictionary["upstream binding activity"], dictionary["upstream binding time"],
                dictionary["downstream binding activity"], dictionary["downstream binding time"]
            )
        if kind == UNATTRIBUTED_TIME_CONFLICT_KIND:
            return UnattributedTimeConflictFacts(dictionary["employee"], dictionary["task"],
                                                 dictionary["feasibility shortfall"])
        raise ValueError(f"Unknown kind of conflict {kind!r}")


######################
# SkillConflictFacts #
######################

@dataclass(frozen=True)
class SkillConflictFacts(ConflictFacts):
    """
    A conflict whose cause is the employee not being skilled enough to perform the task at all.

    Attributes:
        employee_skill_level: The employee's skill level.
        task_skill_level: The skill level the task requires.
    """
    employee_skill_level: int
    task_skill_level: int

    @property
    def kind(self) -> str:
        """Key of the kind of conflict, as written under KIND_KEY."""
        return SKILL_CONFLICT_KIND

    def to_dict(self) -> dict[str, Any]:
        """Return these facts as a dictionary, as read back by ConflictFacts.from_dict."""
        dictionary = super().to_dict()
        dictionary["employee skill level"] = self.employee_skill_level
        dictionary["task skill level"] = self.task_skill_level
        return dictionary


#####################
# TimeConflictFacts #
#####################

@dataclass(frozen=True)
class TimeConflictFacts(ConflictFacts):
    """
    A conflict whose cause is the task not fitting, in time, where the support solution puts it:
    the route before it cannot get the employee there before earliest_start_time,
    while the route after it has to be left by latest_start_time.
    It is TimeConflict with its step indices resolved into the activities and the time bounds they stand for.
    All times are in minutes since midnight.

    Attributes:
        task_duration: Duration of the task, in minutes.
        task_time_window_start: Earliest time the task may start.
        task_time_window_end: Latest time the task may end.
        feasibility_shortfall: By how many minutes earliest_start_time overshoots latest_start_time.
        is_upstream_feasible: Whether the route before the task lets it end within its own time window.
            If not, the conflict is told from the upstream side alone.
        is_downstream_feasible: Whether the route after the task lets it start within its own time window.
        earliest_start_time: Earliest time the task can start, given the route before it.
        latest_start_time: Latest time the task can start, given the route after it.
        activity_before: Name of the activity right before the task in the support route, or HOME.
        activity_after: Name of the activity right after the task in the support route, or HOME.
        upstream_binding_activity: Name of the activity, before the task, whose earliest start time holds the route
            back, or HOME when it is the time the employee may leave home at.
        upstream_binding_time: That earliest start time (the employee's availability start for HOME).
        downstream_binding_activity: Name of the activity, after the task, whose latest end time holds the route back,
            or HOME when it is the time the employee must be back home by.
        downstream_binding_time: That latest end time (the employee's availability end for HOME).
    """
    task_duration: int
    task_time_window_start: int
    task_time_window_end: int
    feasibility_shortfall: int
    is_upstream_feasible: bool
    is_downstream_feasible: bool
    earliest_start_time: int
    latest_start_time: int
    activity_before: str
    activity_after: str
    upstream_binding_activity: str
    upstream_binding_time: Optional[int]
    downstream_binding_activity: str
    downstream_binding_time: Optional[int]

    @property
    def kind(self) -> str:
        """Key of the kind of conflict, as written under KIND_KEY."""
        return TIME_CONFLICT_KIND

    @property
    def earliest_end_time(self) -> int:
        """Earliest time the task can end, given the route before it."""
        return self.earliest_start_time + self.task_duration

    def to_dict(self) -> dict[str, Any]:
        """Return these facts as a dictionary, as read back by ConflictFacts.from_dict."""
        dictionary = super().to_dict()
        dictionary.update({
            "task duration": self.task_duration,
            "task time window start": self.task_time_window_start,
            "task time window end": self.task_time_window_end,
            "feasibility shortfall": self.feasibility_shortfall,
            "is upstream feasible": self.is_upstream_feasible,
            "is downstream feasible": self.is_downstream_feasible,
            "earliest start time": self.earliest_start_time, "latest start time": self.latest_start_time,
            "activity before": self.activity_before, "activity after": self.activity_after,
            "upstream binding activity": self.upstream_binding_activity,
            "upstream binding time": self.upstream_binding_time,
            "downstream binding activity": self.downstream_binding_activity,
            "downstream binding time": self.downstream_binding_time,
        })
        return dictionary


#################################
# UnattributedTimeConflictFacts #
#################################

@dataclass(frozen=True)
class UnattributedTimeConflictFacts(ConflictFacts):
    """
    A time conflict the solved model reports, but that no single position of the task accounts for
    (see UnattributableFeasibilityShortfallException), so that only its size is known.

    Attributes:
        feasibility_shortfall: The minimized shortfall, in minutes.
    """
    feasibility_shortfall: int

    @property
    def kind(self) -> str:
        """Key of the kind of conflict, as written under KIND_KEY."""
        return UNATTRIBUTED_TIME_CONFLICT_KIND

    def to_dict(self) -> dict[str, Any]:
        """Return these facts as a dictionary, as read back by ConflictFacts.from_dict."""
        dictionary = super().to_dict()
        dictionary["feasibility shortfall"] = self.feasibility_shortfall
        return dictionary


####################
# ExplanationFacts #
####################

@dataclass(frozen=True)
class ExplanationFacts:
    """
    Everything an explanation of a solved neighborhood may state, computed deterministically,
    so that whoever words it (an LLM) has nothing left to compute or decide.

    It names employees, tasks and activities rather than holding them, so that it serializes as is.
    It is language-agnostic: times are in minutes since midnight, and are formatted when worded.

    Attributes:
        question: The question as the end user asked it.
        language: Key of the language the question is asked in, and the explanation is to be phrased in.
        outcome: What answering the question settled on.
        operators: The neighborhood's operators, each described as a dictionary keyed by KIND_KEY.
        restrictions: The neighborhood's restrictions, each described as a dictionary keyed by KIND_KEY.
        conflict: Why the support solution is infeasible, or None when it is feasible.
        route_changes: How each employee whose route changed differs between the two solutions.
            The support routes' times are left out when the support solution is infeasible,
            since a strictly positive feasibility shortfall leaves them inconsistent.
        newly_performed_tasks: Names of the tasks the support solution performs and the current one does not.
        no_longer_performed_tasks: Names of the tasks the current solution performs and the support one does not.
        current_kpis: The current solution's KPIs.
        support_kpis: The support solution's KPIs, or None when it is infeasible.
    """
    question: str
    language: str
    outcome: ExplanationOutcomes
    operators: tuple[dict[str, Any], ...]
    restrictions: tuple[dict[str, Any], ...]
    conflict: Optional[ConflictFacts]
    route_changes: tuple[RouteChange, ...]
    newly_performed_tasks: tuple[str, ...]
    no_longer_performed_tasks: tuple[str, ...]
    current_kpis: KPIFacts
    support_kpis: Optional[KPIFacts]

    @property
    def is_positive(self) -> bool:
        """Whether the facts confirm what the question asked about is possible and worthwhile."""
        return self.outcome.is_positive

    @property
    def support_solution_is_feasible(self) -> bool:
        """Whether the support solution is feasible."""
        return self.outcome.is_feasible

    def to_dict(self) -> dict[str, Any]:
        """Return these facts as a dictionary, as read back by from_dict."""
        return {
            "question": self.question,
            "language": self.language,
            "outcome": self.outcome.value,
            "operators": list(self.operators),
            "restrictions": list(self.restrictions),
            "conflict": self.conflict.to_dict() if self.conflict is not None else None,
            "route changes": [route_change.to_dict() for route_change in self.route_changes],
            "newly performed tasks": list(self.newly_performed_tasks),
            "no longer performed tasks": list(self.no_longer_performed_tasks),
            "current kpis": self.current_kpis.to_dict(),
            "support kpis": self.support_kpis.to_dict() if self.support_kpis is not None else None,
        }

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> "ExplanationFacts":
        """
        Rebuild the facts the given dictionary describes.

        Args:
            dictionary: The dictionary to read, as produced by to_dict.

        Returns:
            The rebuilt facts.
        """
        return cls(
            dictionary["question"],
            dictionary["language"],
            ExplanationOutcomes(dictionary["outcome"]),
            tuple(dictionary["operators"]),
            tuple(dictionary["restrictions"]),
            ConflictFacts.from_dict(dictionary["conflict"]) if dictionary["conflict"] is not None else None,
            tuple(RouteChange.from_dict(route_change) for route_change in dictionary["route changes"]),
            tuple(dictionary["newly performed tasks"]),
            tuple(dictionary["no longer performed tasks"]),
            KPIFacts.from_dict(dictionary["current kpis"]),
            KPIFacts.from_dict(dictionary["support kpis"]) if dictionary["support kpis"] is not None else None,
        )


###########################
# ExplanationFactsBuilder #
###########################

class ExplanationFactsBuilder:
    """
    Stateless collection of static methods reading, off a neighborhood and the model solved from it,
    the ExplanationFacts an explanation of it may state.

    It is the neighborhood computation pipeline's template-free counterpart
    to build_transformation_result_from_neighborhood: it never recognizes the neighborhood as a question template,
    so any neighborhood NeighborhoodModel solves can be explained.
    """

    @staticmethod
    def get_support_solution(neighborhood: Neighborhood, model: Optional[NeighborhoodModel]) -> Solution:
        """
        Return the support solution a neighborhood and the model solved from it settled on.

        Args:
            neighborhood: The neighborhood the question induced.
            model: The model solved from it, or None when a skill conflict blocked it before any was built.

        Returns:
            The solved model's solution, or the neighborhood's own solution, unchanged, when no model was built.
        """
        return model.solution if model is not None else neighborhood.solution

    @staticmethod
    def build(question: Question, neighborhood: Neighborhood, model: Optional[NeighborhoodModel],
              skill_conflict: Optional[SkillConflict] = None) -> ExplanationFacts:
        """
        Read the facts off a neighborhood and the model solved from it (see solve_neighborhood).

        NB: When the model's feasibility shortfall is strictly positive,
        the support solution's sequences are put back into solved-route order in place (as in
        build_transformation_result_from_neighborhood), and its KPIs are computed when it is feasible.

        Args:
            question: The question the neighborhood was induced by.
            neighborhood: The neighborhood the question induced.
            model: The model solved from it, or None when a skill conflict blocked it before any was built.
            skill_conflict: The skill conflict blocking the neighborhood, given exactly when model is None.

        Returns:
            The facts.

        Raises:
            ValueError: if exactly one of model and skill_conflict is not given.
            AttributeError: if the given model hasn't been solved yet, or found no feasible solution.
        """
        if (model is None) == (skill_conflict is None):
            raise ValueError("Exactly one of a solved model and a skill conflict must be given")
        current_solution = neighborhood.solution
        operators = tuple(_describe_operator(operator) for operator in neighborhood.operators)
        restrictions = tuple(_describe_restriction(restriction) for restriction in neighborhood.restrictions)
        current_kpis = KPIFacts.from_solution(current_solution)
        if model is None:
            return ExplanationFacts(
                question.text, question.language, ExplanationOutcomes.SKILL_BLOCKED, operators, restrictions,
                _build_skill_conflict_facts(skill_conflict), (), (), (), current_kpis, None
            )
        support_solution = model.solution
        conflict_facts = None
        support_kpis = None
        if model.feasibility_shortfall > 0:
            reorder_support_sequences_to_solved_routes(neighborhood, model)
            conflict_facts = _build_time_conflict_facts(model)
            if isinstance(conflict_facts, TimeConflictFacts):
                outcome = ExplanationOutcomes.TIME_INFEASIBLE
            else:
                outcome = ExplanationOutcomes.INFEASIBLE_UNATTRIBUTED
        else:
            support_kpis = KPIFacts.from_solution(support_solution)
            if support_solution > current_solution:
                outcome = ExplanationOutcomes.FEASIBLE_IMPROVING
            else:
                outcome = ExplanationOutcomes.FEASIBLE_NON_IMPROVING
        current_performed_tasks = set(current_solution.performed_tasks_names)
        support_performed_tasks = set(support_solution.performed_tasks_names)
        return ExplanationFacts(
            question.text, question.language, outcome, operators, restrictions, conflict_facts,
            _build_route_changes(current_solution, support_solution, with_support_times=outcome.is_feasible),
            tuple(sorted(support_performed_tasks - current_performed_tasks)),
            tuple(sorted(current_performed_tasks - support_performed_tasks)),
            current_kpis, support_kpis
        )


###########
# Helpers #
###########

def _names(members) -> list[str]:
    """Return the names of the given employees, tasks or activities, sorted unless given as an ordered list."""
    names = [member.name for member in members]
    return names if isinstance(members, (list, tuple)) else sorted(names)


def _describe_operator(operator: Operator) -> dict[str, Any]:
    """
    Describe the given operator as a dictionary, in the vocabulary the free-text extraction uses
    (see src.explaining.neighborhood.llm.prompt).

    Args:
        operator: The operator to describe.

    Returns:
        The dictionary, keyed by KIND_KEY, or holding the operator's repr alone for an operator it has no wording for.
    """
    if isinstance(operator, TaskInsertion):
        return {KIND_KEY: "task_insertion", "candidate_employees": _names(operator.candidate_employees),
                "candidate_tasks": _names(operator.candidate_tasks)}
    if isinstance(operator, TaskDeletion):
        return {KIND_KEY: "task_deletion", "freed_employees": _names(operator.freed_employees),
                "candidate_tasks": _names(operator.candidate_tasks),
                "min_nb_removals": operator.min_nb_removals, "max_nb_removals": operator.max_nb_removals}
    if isinstance(operator, TaskRepositioning):
        return {KIND_KEY: "task_repositioning", "employee": operator.employee.name,
                "target_task": operator.target_task.name}
    if isinstance(operator, SequenceReordering):
        return {KIND_KEY: "sequence_reordering", "employee": operator.employee.name}
    if isinstance(operator, TaskRelocation):
        return {KIND_KEY: "task_relocation", "origin_employee": operator.origin_employee.name,
                "destination_employee": operator.destination_employee.name,
                "target_task": operator.target_task.name}
    return {KIND_KEY: repr(operator)}


def _describe_restriction(restriction: Restriction) -> dict[str, Any]:
    """
    Describe the given restriction as a dictionary, in the vocabulary the free-text extraction uses
    (see src.explaining.neighborhood.llm.prompt).

    Args:
        restriction: The restriction to describe.

    Returns:
        The dictionary, keyed by KIND_KEY, or holding the restriction's repr alone for one it has no wording for.
    """
    if isinstance(restriction, PrecedenceChain):
        return {KIND_KEY: "precedence_chain", "tasks": _names(restriction.tasks)}
    if isinstance(restriction, ImmediatePrecedence):
        return {KIND_KEY: "immediate_precedence", "predecessor": restriction.predecessor.name,
                "successor": restriction.successor.name}
    if isinstance(restriction, Precedence):
        return {KIND_KEY: "precedence", "predecessor": restriction.predecessor.name,
                "successor": restriction.successor.name}
    if isinstance(restriction, ForbiddenSequence):
        return {KIND_KEY: "forbidden_sequence", "employee": restriction.employee.name,
                "activities": _names(restriction.activities)}
    if isinstance(restriction, ForbiddenBackwardSubsequence):
        return {KIND_KEY: "forbidden_backward_subsequence", "employee": restriction.employee.name,
                "tasks": _names(restriction.tasks)}
    return {KIND_KEY: repr(restriction)}


def _build_skill_conflict_facts(skill_conflict: SkillConflict) -> SkillConflictFacts:
    """Return the facts of the given skill conflict."""
    employee = skill_conflict.conflicting_employee
    task = skill_conflict.conflicting_task
    return SkillConflictFacts(employee.name, task.name, employee.skill_level, task.skill_level)


def _build_time_conflict_facts(model: NeighborhoodModel) -> ConflictFacts:
    """
    Return the facts of the time conflict the given solved model's strictly positive feasibility shortfall stands for.

    The binding step indices of the TimeConflict are resolved against the support sequence,
    which must already be in solved-route order (see reorder_support_sequences_to_solved_routes):
    they are numbered as in the route with the conflicting task in it, which is exactly that sequence.
    The cases resolved to HOME are the ones TimeNegativeExplanation words as leaving or coming back home.

    Args:
        model: The solved model, with a strictly positive feasibility shortfall.

    Returns:
        The TimeConflictFacts, or UnattributedTimeConflictFacts when ConflictExtractor cannot attribute the shortfall
        to the conflicting task's position, or cannot rebuild the route around it.
    """
    try:
        conflict = ConflictExtractor.extract_from_solved_model(model)
    except (UnattributableFeasibilityShortfallException, NotImplementedError):
        employee, task = model.conflicting_employee_and_task
        return UnattributedTimeConflictFacts(employee.name, task.name, model.feasibility_shortfall)
    assert isinstance(conflict, TimeConflict)
    employee = conflict.conflicting_employee
    task = conflict.conflicting_task
    sequence = model.solution.get_sequence(employee)
    step_index = sequence.get_step_index_of(task)
    last_step_index = sequence.nb_steps - 1
    upstream_binding_step_index = conflict.upstream_binding_step_index
    downstream_binding_step_index = conflict.downstream_binding_step_index
    if step_index == 1 or upstream_binding_step_index == 0:
        upstream_binding_activity, upstream_binding_time = HOME, employee.start_time_lb
    else:
        activity = sequence[upstream_binding_step_index].activity
        upstream_binding_activity, upstream_binding_time = activity.name, activity.start_time_lb
    if step_index == last_step_index - 1 or downstream_binding_step_index == last_step_index:
        downstream_binding_activity, downstream_binding_time = HOME, employee.end_time_ub
    else:
        activity = sequence[downstream_binding_step_index].activity
        downstream_binding_activity, downstream_binding_time = activity.name, activity.end_time_ub
    return TimeConflictFacts(
        employee.name, task.name, task.duration, task.start_time_lb, task.end_time_ub, model.feasibility_shortfall,
        conflict.is_upstream_feasible, conflict.is_downstream_feasible,
        conflict.earliest_upstream_feasible_start_time_of_conflicting_task,
        conflict.latest_downstream_feasible_start_time_of_conflicting_task,
        HOME if step_index == 1 else sequence[step_index - 1].activity.name,
        HOME if step_index == last_step_index - 1 else sequence[step_index + 1].activity.name,
        upstream_binding_activity, upstream_binding_time, downstream_binding_activity, downstream_binding_time
    )


def _build_route_facts(employee: Employee, sequence: Sequence, with_times: bool) -> RouteFacts:
    """
    Return the facts of the given employee's route.

    Args:
        employee: The employee whose route it is.
        sequence: The employee's sequence, in route order.
        with_times: Whether to state the activities' solved times.

    Returns:
        The facts.
    """
    steps = []
    for step in sequence.get_steps(1, sequence.nb_steps - 1):
        activity = step.activity
        steps.append(StepFacts(
            activity.name, activity.duration, activity.start_time_lb, activity.end_time_ub,
            step.start_time if with_times else None, step.end_time if with_times else None
        ))
    return RouteFacts(employee.name, employee.start_time_lb, employee.end_time_ub, tuple(steps))


def _build_route_changes(current_solution: Solution, support_solution: Solution,
                         with_support_times: bool) -> tuple[RouteChange, ...]:
    """
    Return how each employee whose route changed differs between the two solutions, sorted by employee name.

    A route changes when the tasks it performs, or their order, do.

    Args:
        current_solution: The solution the question is asked about.
        support_solution: The solution found while answering it, with its sequences in route order.
        with_support_times: Whether to state the support routes' solved times.

    Returns:
        The route changes.
    """
    route_changes = []
    for employee in sorted(current_solution.instance.employees, key=lambda member: member.name):
        current_tasks: list[Task] = current_solution.get_tasks_performed_by(employee)
        support_tasks: list[Task] = support_solution.get_tasks_performed_by(employee)
        if [task.name for task in current_tasks] == [task.name for task in support_tasks]:
            continue
        current_task_names = {task.name for task in current_tasks}
        support_task_names = {task.name for task in support_tasks}
        route_changes.append(RouteChange(
            employee.name,
            _build_route_facts(employee, current_solution.get_sequence(employee), with_times=True),
            _build_route_facts(employee, support_solution.get_sequence(employee), with_times=with_support_times),
            tuple(sorted(support_task_names - current_task_names)),
            tuple(sorted(current_task_names - support_task_names))
        ))
    return tuple(route_changes)
