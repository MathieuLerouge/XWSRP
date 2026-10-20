# Standard library
from typing import Callable, Optional, TypeVar, Union

# Local libraries
from src.explaining.computing.conflict import Conflict, SkillConflict
from src.explaining.computing.solver import TransformationModelSolver
from src.explaining.computing.templates.common.result import TransformationResult
from src.optimization.heuristics.evaluation import Evaluation
from src.optimization.milp.model import Model
from src.optimization.milp.statistics import MilpStatistics
from src.optimization.milp.subproblems.sequencemodel import SequenceModel
from src.utils.progress import ProgressReporter, ProgressStep
from src.utils.time import convert_nb_minutes_to_time_string

# Type variable for a MILP model build_and_solve_model hands back as it was given
SolvableModel = TypeVar("SolvableModel", bound=Union[Model, SequenceModel])


def report_model_size(step: ProgressStep, statistics: MilpStatistics, constraint_family_prefix: Optional[str] = None):
    """
    Report the size of a built MILP model, as details of the step building it.

    Args:
        step: The step building the model.
        statistics: The model's statistics, taken once built.
        constraint_family_prefix: The prefix naming the constraint families the model adds on top of its base model's,
            to report them apart (e.g. a NeighborhoodModel's), or None to report the constraints as a whole.
    """
    step.info("Variables", f"{statistics.nb_variables} (binary: {statistics.nb_binary_variables}, "
                           f"integer: {statistics.nb_integer_variables}, "
                           f"continuous: {statistics.nb_continuous_variables})")
    step.info("Fixed variables", statistics.nb_fixed_variables)
    if constraint_family_prefix is None:
        step.info("Constraints", statistics.nb_constraints)
    else:
        nb_prefixed_constraints = statistics.count_constraints_in_families_starting_with(constraint_family_prefix)
        nb_base_constraints = statistics.nb_constraints - nb_prefixed_constraints
        step.info("Constraints", f"{statistics.nb_constraints} (base: {nb_base_constraints}, "
                                 f"{constraint_family_prefix.lower()}: {nb_prefixed_constraints})")
        for family, nb_constraints in sorted(statistics.nb_constraints_by_family.items()):
            if family.startswith(constraint_family_prefix):
                step.info(family, nb_constraints)
    step.info("Objectives", statistics.nb_objectives)


def report_solve(step: ProgressStep, statistics: MilpStatistics):
    """
    Report how a MILP model was solved, as details of the step solving it.

    Args:
        step: The step solving the model.
        statistics: The model's statistics, completed by the solve.
    """
    # NB: Only recorded once the backend has returned, so it is unknown when the backend itself failed.
    if statistics.solver_name is not None:
        step.info("Solver", statistics.solver_name)
    for level, (objective_name, outcome) in enumerate(statistics.lexicographic_outcomes, start=1):
        step.info(f"Level {level} ({objective_name})", outcome.as_string())
    nb_unsolved_levels = statistics.nb_objectives - len(statistics.lexicographic_outcomes)
    if nb_unsolved_levels > 0:
        step.warning(f"{nb_unsolved_levels} lower-priority level(s) not solved")


def describe_conflict(conflict: Optional[Conflict]) -> str:
    """
    Describe the conflict a transformation ran into, in short.

    Args:
        conflict: The conflict, or None when the transformation is feasible.

    Returns:
        The kind of conflict and who it is between (e.g. "time conflict between Ellen and T2"),
        or "none" when there is none.
    """
    if conflict is None:
        return "none"
    kind = "skill" if isinstance(conflict, SkillConflict) else "time"
    return f"{kind} conflict between {conflict.conflicting_employee.name} and {conflict.conflicting_task.name}"


def describe_skill_check(skill_conflict: Optional[SkillConflict]) -> str:
    """
    Describe the outcome of checking whether an employee is skilled enough for the task a question is about.

    Args:
        skill_conflict: The skill conflict found, or None when there is none.

    Returns:
        "none", or who is not skilled enough to perform what, which leaves no MILP to solve.
    """
    if skill_conflict is None:
        return "none"
    return (f"{skill_conflict.conflicting_employee.name} is not skilled enough "
            f"to perform {skill_conflict.conflicting_task.name}, so no MILP is needed")


def build_and_solve_model(progress_reporter: ProgressReporter, model_name: str,
                          build_model: Callable[[], SolvableModel]) -> SolvableModel:
    """
    Build a MILP model, then solve it, reporting each as a step with the model's size and how it was solved.

    Args:
        progress_reporter: What the two steps are reported to.
        model_name: The name of the model's class, to title the steps with (e.g. "InsertionModel").
        build_model: Builds the model, ready to be solved.

    Returns:
        The solved model.

    Raises:
        InfeasibleModelException: if the model has no feasible solution.
        UnboundedModelException: if the model is unbounded.
        TimeLimitReachedWithSolutionException: if the solving time limit was reached, with an incumbent found.
        TimeLimitReachedWithoutSolutionException: if the solving time limit was reached with no incumbent.
    """
    with progress_reporter.step(f"Building the {model_name}") as step:
        model = build_model()
        report_model_size(step, model.statistics)
    with progress_reporter.step(f"Solving the {model_name}") as step:
        try:
            TransformationModelSolver.solve_or_raise(model)
        finally:
            # NB: Reported even when solving raises, since the levels solved are what tells why it did.
            report_solve(step, model.statistics)
    return model


def analyze_solution(progress_reporter: ProgressReporter,
                     build_result: Callable[[], TransformationResult]) -> TransformationResult:
    """
    Build the result of a transformation, reporting it as a step with the conflict it ran into.

    Args:
        progress_reporter: What the step is reported to.
        build_result: Builds the result of the transformation.

    Returns:
        The result of the transformation.
    """
    with progress_reporter.step("Analyzing the solution") as step:
        transformation_result = build_result()
        step.info("Conflict", describe_conflict(transformation_result.conflict))
    return transformation_result


def report_evaluation_verdicts(step: ProgressStep, evaluation: Evaluation):
    """
    Report whether the transformation an Evaluator evaluated is feasible, and when its task would start,
    as details of the step evaluating it.

    Args:
        step: The step evaluating the transformation.
        evaluation: The evaluation of the transformation.
    """
    step.info("Feasible", f"{_as_yes_or_no(evaluation.is_feasible)} "
                          f"(skill: {_as_yes_or_no(evaluation.is_skill_feasible)}, "
                          f"time: {_as_yes_or_no(evaluation.is_time_feasible)})")
    if evaluation.start_time is not None:
        bounds = []
        if evaluation.earliest_start_time_for_upstream is not None:
            bounds.append(f"earliest for upstream: "
                          f"{convert_nb_minutes_to_time_string(evaluation.earliest_start_time_for_upstream)}")
        if evaluation.latest_start_time_for_downstream is not None:
            bounds.append(f"latest for downstream: "
                          f"{convert_nb_minutes_to_time_string(evaluation.latest_start_time_for_downstream)}")
        bounds_str = f" ({', '.join(bounds)})" if bounds else ""
        step.info("Start time", f"{convert_nb_minutes_to_time_string(evaluation.start_time)}{bounds_str}")


def _as_yes_or_no(verdict: Optional[bool]) -> str:
    """
    Word a verdict an evaluation may have left unset.

    Args:
        verdict: The verdict, or None if the evaluation did not reach it.

    Returns:
        "yes", "no" or "unknown".
    """
    if verdict is None:
        return "unknown"
    return "yes" if verdict else "no"
