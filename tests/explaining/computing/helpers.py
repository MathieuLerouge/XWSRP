# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.conflict.conflict import Conflict, TimeConflict
from src.explaining.computing.conflict.extractor import ConflictExtractor
from src.explaining.computing.model import NeighborhoodModel
from src.explaining.computing.templates.dispatch import TransformationDispatcher
from src.explaining.modeling.solution import EditableSolution
from src.explaining.neighborhood.templates.mapper import Mapper
from src.explaining.questioning.question import ContrastiveQuestion
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.importing.instance import extract_instance_from_file
from src.importing.solution import import_solution

# Global variables
_AUSTRIA_INSTANCE_PATH = "src/explaining/instances/InstanceAustria.xlsx"
_AUSTRIA_SOLUTION_PATH = "src/explaining/solutions/SolutionAustria.txt"


def build_austria_instance() -> Instance:
    return extract_instance_from_file(_AUSTRIA_INSTANCE_PATH, True, True, True)


def build_austria_solution() -> Solution:
    return import_solution(_AUSTRIA_SOLUTION_PATH, True, True, True)


def gap_from_conflict(conflict: Optional[Conflict]):
    """
    Return the feasibility gap for the given Conflict (or None): 0 if feasible,
    otherwise the (earliest upstream) - (latest downstream) quantity.

    Raises:
        AssertionError: if conflict is a SkillConflict, which has no gap to measure at all
            - the two pipelines compare their skill conflicts by pairing rather than by gap.
    """
    if conflict is None:
        return 0
    assert isinstance(conflict, TimeConflict), (
        f"Unexpected conflict type for a skill-compatible test case: {type(conflict)}"
    )
    return (conflict.earliest_upstream_feasible_start_time_of_conflicting_task -
            conflict.latest_downstream_feasible_start_time_of_conflicting_task)


def get_tailored_computation_pipeline_gap_and_solution(
        solution: Solution, template_id: str, fields_values: list[str]
):
    """
    Return (feasibility gap, support_solution, conflict) following the tailored computation pipeline.
    """
    editable_solution = EditableSolution.from_solution(solution)
    question = ContrastiveQuestion(editable_solution, template_id, fields_values)
    result = TransformationDispatcher.handle_contrastive_or_scenario_question(editable_solution, question)
    return gap_from_conflict(result.conflict), result.support_solution, result.conflict


def get_neighborhood_computation_pipeline_gap_and_solution(
        solution: Solution, template_id: str, fields_values: list[str]
):
    """
    Return (feasibility gap, support_solution, conflict) following the neighborhood computation pipeline.

    The gap and the support solution are both None when the neighborhood is blocked by a skill conflict:
    the MILP is never built for it, since no arrangement of it exists to search in the first place.
    """
    question = ContrastiveQuestion(solution, template_id, fields_values)
    neighborhood = Mapper.map(question)
    skill_conflict = ConflictExtractor.extract_from_neighborhood(neighborhood)
    if skill_conflict is not None:
        return None, None, skill_conflict
    model = NeighborhoodModel(neighborhood)
    outcome = model.solve(mute=True)
    assert outcome.has_incumbent, "The neighborhood computation pipeline's MILP should be feasible by construction"
    return model.feasibility_shortfall, model.solution, ConflictExtractor.extract_from_solved_model(model)


def assert_same_conflict(tailored_conflict: Optional[Conflict],
                              neighborhood_conflict: Optional[Conflict]):
    """
    Assert both pipelines describe the same conflict, field for field.
    Only meaningful once the two gaps are known to be equal:
    when the neighborhood pipeline's MILP finds a  better arrangement than the tailored pipeline's heuristic
    (a strictly smaller gap, which assert_parity_over_random_samples explicitly allows),
    the two are describing different arrangements and have no reason to agree on anything but the fact that neither fits.
    """
    assert (tailored_conflict is None) == (neighborhood_conflict is None), (
        f"One pipeline reports a conflict and the other does not: "
        f"tailored={tailored_conflict}, neighborhood={neighborhood_conflict}"
    )
    if tailored_conflict is None:
        return
    assert tailored_conflict.to_dict() == neighborhood_conflict.to_dict(), (
        f"Conflicts differ: tailored={tailored_conflict.to_dict()}, "
        f"neighborhood={neighborhood_conflict.to_dict()}"
    )


def assert_same_kpis(solution_1: Solution, solution_2: Solution):
    """
    Assert two feasible support solutions agree on task performance/assignee and total KPIs.

    NB: solution_1 and solution_2 are assumed to relate to the same instance.
    """
    solution_1.compute_kpis()
    solution_2.compute_kpis()
    for task in solution_1.instance.tasks:
        performed_1 = solution_1.get_task_performance_status(task)
        assert performed_1 == solution_2.get_task_performance_status(task), f"{task.name} performance status differs"
        if performed_1:
            assert solution_1.get_task_assignee(task) == solution_2.get_task_assignee(task), \
                f"{task.name} assignee differs"
    assert solution_1.total_working_duration == solution_2.total_working_duration
    assert solution_1.total_traveling_duration == solution_2.total_traveling_duration


def assert_at_least_as_good_kpis(tailored_solution: Solution, neighborhood_solution: Solution):
    """
    Assert the neighborhood pipeline's solution is lexicographically at least as good as the tailored
    pipeline's: never a higher total working duration, and (once that ties) never a higher total
    traveling duration either.

    Unlike assert_same_kpis, this doesn't require the two pipelines to have picked the exact same tasks:
    for candidate-set questions (e.g. (Swp,2a)/(2b)/(2c), where the outgoing/incoming task isn't named),
    the neighborhood pipeline's exhaustive MILP search can legitimately find a strictly better-optimized
    swap than the tailored pipeline's heuristic, not just an equally good one.

    NB: tailored_solution and neighborhood_solution are assumed to relate to the same instance.
    """
    tailored_solution.compute_kpis()
    neighborhood_solution.compute_kpis()
    assert neighborhood_solution.total_working_duration <= tailored_solution.total_working_duration, \
        "neighborhood pipeline's total working duration exceeds the tailored pipeline's"
    if neighborhood_solution.total_working_duration == tailored_solution.total_working_duration:
        assert neighborhood_solution.total_traveling_duration <= tailored_solution.total_traveling_duration, \
            "neighborhood pipeline's total traveling duration exceeds the tailored pipeline's"
