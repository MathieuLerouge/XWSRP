# Standard library
from typing import Optional

# Local libraries
from src.explaining.computing.model import NeighborhoodFeasibilityMILP
from src.explaining.computing.templates.infeasibility import Infeasibility, TimeInfeasibility
from src.explaining.computing.templates.transformation import \
    apply_transformation_induced_by_contrastive_or_scenario_question
from src.explaining.modeling.solution import EditableSolution
from src.explaining.neighborhood.templates.mapper import Mapper
from src.explaining.questioning.question import ContrastiveQuestion
from src.modeling.instance import Instance
from src.modeling.solution import Solution
from src.reading.instance import extract_instance_from_file
from src.reading.solution import extract_solution_from_file

# Global variables
_AUSTRIA_INSTANCE_PATH = "src/explaining/instances/InstanceAustria.xlsx"
_AUSTRIA_SOLUTION_PATH = "src/explaining/solutions/SolutionAustria.txt"


def build_austria_instance() -> Instance:
    return extract_instance_from_file(_AUSTRIA_INSTANCE_PATH, True, True, True)


def build_austria_solution() -> Solution:
    return extract_solution_from_file(_AUSTRIA_SOLUTION_PATH, True, True, True)


def gap_from_infeasibility(infeasibility: Optional[Infeasibility]):
    """
    Return the feasibility gap for the given Infeasibility (or None): 0 if feasible, otherwise the
    (earliest upstream) - (latest downstream) quantity.

    Raises:
        AssertionError: if infeasibility is a SkillInfeasibility, which this comparison excludes since
            skill mismatches aren't handled by the neighborhood computation pipeline yet.
    """
    if infeasibility is None:
        return 0
    assert isinstance(infeasibility, TimeInfeasibility), (
        f"Unexpected infeasibility type for a skill-compatible test case: {type(infeasibility)}"
    )
    return (infeasibility.earliest_upstream_feasible_start_time_of_conflicting_task -
            infeasibility.latest_downstream_feasible_start_time_of_conflicting_task)


def get_tailored_computation_pipeline_gap_and_solution(
        solution: Solution, template_id: str, fields_values: list[str]
):
    """
    Return (feasibility gap, support_solution) following the tailored computation pipeline.
    """
    editable_solution = EditableSolution.from_Solution(solution)
    question = ContrastiveQuestion(editable_solution, template_id, fields_values)
    support_solution, infeasibility, _ = apply_transformation_induced_by_contrastive_or_scenario_question(
        editable_solution, question
    )
    return gap_from_infeasibility(infeasibility), support_solution


def get_neighborhood_computation_pipeline_gap_and_solution(
        solution: Solution, template_id: str, fields_values: list[str]
):
    """
    Return (feasibility gap, support_solution) following the neighborhood computation pipeline.
    """
    question = ContrastiveQuestion(solution, template_id, fields_values)
    neighborhood = Mapper.map(question)
    model = NeighborhoodFeasibilityMILP(neighborhood)
    outcome = model.solve(mute=True)
    assert outcome.has_incumbent, "The neighborhood computation pipeline's MILP should be feasible by construction"
    return model.target_feasibility_gap, model.solution


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
