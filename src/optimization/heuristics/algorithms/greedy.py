# Local libraries
from src.modeling.instance import Instance
from src.optimization.heuristics.evaluator import Evaluator
from src.optimization.heuristics.solution import SolutionForHeuristics
from src.utils.constants import GREEDY_SOLVING_METHOD


####################
# Greedy algorithm #
####################

def run_greedy_algorithm(instance: Instance):

    # Initialize solution
    solution = SolutionForHeuristics(instance, heuristic_id=GREEDY_SOLVING_METHOD)

    # Initialize step counter and maximum number of steps left
    step_counter = 1
    max_steps_left = instance.nb_tasks

    # Start search for inserting tasks
    available_tasks = instance.tasks
    must_search_for_inserting = True
    while must_search_for_inserting:

        # Print message every n steps
        n = 20
        if step_counter % n == 1:
            print(f"Steps: {step_counter} | Max steps left: {max_steps_left}")

        # Find the best task insertion among insertions of any available task and any employee
        evaluation = \
            Evaluator.find_best_insertion_between_consecutive_activities_among_sets(
                solution, available_tasks, instance.employees)

        # If the best task insertion is feasible,
        if evaluation.is_feasible:

            # Insert the selected task in the sequence of the selected employee
            task = evaluation.inserted_task
            solution.insert_task_after_activity(task, evaluation.activity_before_insertion, evaluation.start_time,
                                                tighten_times=False)

            # Update available tasks
            available_tasks.remove(task)

            # If there are no more available tasks, then stop the search
            if not available_tasks:
                must_search_for_inserting = False

        # If the best task insertion is not feasible, then stop the search
        else:
            must_search_for_inserting = False

        # Update step counter
        step_counter += 1
        max_steps_left -= 1

    # Tighten the times of the solution
    solution.tighten_times()
    return solution
