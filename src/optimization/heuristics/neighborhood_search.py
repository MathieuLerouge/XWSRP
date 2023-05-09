# Standard libraries
import random
import time

# Third-party libraries
import numpy as np

# Local libraries
from main_configuration import NEIGHBORHOOD_SEARCH_POPULATION_SIZE, NEIGHBORHOOD_SEARCH_NB_NEIGHBORS_PER_SOLUTION, \
    NEIGHBORHOOD_SEARCH_PROPORTION_OF_BEST_SOLUTIONS_TO_KEEP, NEIGHBORHOOD_SEARCH_TIME_LIMIT, \
    NEIGHBORHOOD_SEARCH_TIME_BETWEEN_MESSAGES
from src.modeling.employee import Employee
from src.modeling.instance import Instance
from src.modeling.task import Task
from src.optimization.heuristics.solution import SolutionForHeuristics
from src.optimization.heuristics.stochastic import run_stochastic_heuristic

# Global variables
NEIGHBORHOOD_SEARCH_RANDOM_SEED = 42


###########################################
# Neighborhood search - Random selections #
###########################################

def randomly_select_employee_by_favoring_higher_travel_time_vs_working_time_ratio(
        solution: SolutionForHeuristics, employees: list[Employee] = None) -> Employee:
    """
    Randomly select an employee among the given employees according to a probability distribution which,
    for each employee, is proportional to their total travel time divided by their total working duration

    NB: let n be the number of employees, complexity in O(n)

    :param solution: a solution (SolutionForHeuristics)
    :param employees: list of employees to consider (list[Employee]) (if None, all employees are considered)
    :return: the selected employee (Employee)
    """
    if employees is None:
        employees = solution.instance.employees
    weights = [(solution.get_sequence(employee).total_traveling_duration /
                solution.get_sequence(employee).total_working_duration) for employee in employees]
    if np.sum(weights) > 0:
        return random.choices(employees, weights=weights)[0]
    else:
        return random.choice(employees)


def randomly_select_task_in_employee_sequence_by_favoring_higher_travel_time_delta_vs_duration_ratio(
        solution: SolutionForHeuristics, employee: Employee) -> Task:
    """
    Randomly select a task among those performed by the given employee,
    according to a probability distribution which, for each task, is proportional to
    the total travel time decrease that would be obtained by removing the task
    divided by the task duration for each task

    NB: let n be the number of employees, m be the number of tasks and p be the number of steps in an employee sequence;
    worst case complexity in O(p) (a fortiori O(m)) and average complexity in O(m/n)

    :param solution: a solution (SolutionForHeuristics)
    :param employee: an employee (Employee)
    :return: the selected task (Task)
    """
    sequence = solution.get_sequence(employee)
    weights = [(solution.compute_traveling_duration(before, step) +
                solution.compute_traveling_duration(step, after) -
                solution.compute_traveling_duration(before, after)) / step.activity.duration
               for (before, step, after) in zip(sequence[0:-2], sequence[1:-1], sequence[2:])]
    tasks = [step.activity for step in sequence[1:-1]]
    if np.sum(weights) > 0:
        return random.choices([step.activity for step in sequence[1:-1]], weights=weights)[0]
    else:
        return random.choice(tasks)


################################################
# Neighborhood search - Neighboring operations #
################################################

def randomly_remove_performed_task_from_employee_sequence(solution: SolutionForHeuristics):
    """
    Remove a random performed task from a random employee sequence

    - The employee is randomly selected among those who have performed at least one task,
      according to a probability distribution which is proportional to
      the total travel time divided by the total working duration for each employee

    - The task is randomly selected among those performed by the selected employee,
      according to a probability distribution which is proportional, for each task, to
      the total travel time decrease obtained by removing the task divided by the task duration

    NB: let n be the number of employees and m be the number of tasks

    - worst case complexity is in O(max(n,m)) i.e. O(m) if n << m

    - average complexity is in O(max(n,m/n))

    :param solution: the solution to modify (SolutionForHeuristics)
    :return: a pair (solution, success) where
    success is a boolean indicating whether the removal was successful and
    solution is the solution obtained after the removal
    (by default, if success is False, solution is the same as the input solution)
    """
    # For complexity computation:
    # - n is the number of employees
    # - m is the number of tasks
    # - p is the number of steps in an employee sequence
    # Get the list of employees who have performed at least one task
    # NB: O(n)
    working_employees = [employee for employee in solution.instance.employees
                         if len(solution.get_tasks_performed_by(employee)) > 0]
    # If there is no employee who has performed at least one task, return the input solution
    if len(working_employees) == 0:
        return solution, False
    # Otherwise,
    else:
        # Select randomly an employee among those who have performed at least one task
        # NB: O(n)
        employee = \
            randomly_select_employee_by_favoring_higher_travel_time_vs_working_time_ratio(solution, working_employees)
        # Select randomly a task among those performed by the selected employee
        # NB: O(p)
        # NB 2: worst case complexity in O(m)
        # NB 3: average complexity in O(m/n)
        task = \
            randomly_select_task_in_employee_sequence_by_favoring_higher_travel_time_delta_vs_duration_ratio(solution,
                                                                                                             employee)
        # Remove the selected task from the selected employee sequence
        # NB: O(p)
        # NB 2: worst case complexity in O(m)
        # NB 3: average case complexity in O(m/n)
        solution.remove_task(task, tighten_times=False)
        return solution, True


def randomly_insert_non_performed_task_in_employee_sequence(solution: SolutionForHeuristics):
    """
    Insert a random non-performed task in a random employee sequence

    - The task is randomly selected among those not performed by any employee

    - The insertion is randomly selected among all feasible insertions in employee sequences,
      according to a probability distribution which is inversely proportional, for each insertion, to
      the total travel time increase due to this insertion

    NB: let n be the number of employees and m be the number of tasks,
    worst case complexity is in O(max(n,m)) i.e. O(m) if n << m

    :param solution: the solution to modify (SolutionForHeuristics)
    :return: a pair (solution, success) where
    success is a boolean indicating whether the task insertion was successful and
    solution is the solution obtained after inserting the task
    (by default, if success is False, solution is the same as the input solution)
    """
    # For complexity computation:
    # - n is the number of employees
    # - m is the number of tasks
    # - p is the number of steps in an employee sequence
    if solution.nb_non_performed_tasks == 0:
        return solution, False
    else:
        # Select randomly a task among the non-performed ones
        # NB: O(1)
        task = random.choice(solution.non_performed_tasks)
        # Get the list of employees who are skilled-enough to perform the selected task
        # NB: O(n)
        skilled_employees = solution.instance.get_employees_with_skill_level_higher_than(task.skill_level)
        # Get the list of feasible insertions of the selected task for each of these employees
        # NB: O(m)
        feasible_insertions_examinations = []
        for employee in skilled_employees:
            feasible_insertions_examinations.extend(
                solution.find_feasible_insertions_between_consecutive_activities(employee, task)
            )
        # If there is no feasible insertion for any skilled employee, return the input solution
        if len(feasible_insertions_examinations) == 0:
            return solution, False
        # Otherwise,
        else:
            # Select randomly an insertion among the feasible ones,
            # according to a probability distribution which is inversely proportional to
            # the travel time increase due to each insertion of the task in the employee sequence
            # NB: O(m)
            weights = [1 / (examination.travel_time_increase + 1)
                       for examination in feasible_insertions_examinations]
            examination = random.choices(feasible_insertions_examinations, weights=weights)[0]
            # Insert the task in the selected employee sequence
            # NB: O(p)
            # NB 2: worst case complexity in O(m)
            # NB 3: average case complexity in O(m/n)
            solution.insert_task_after_activity(task, examination.activity_before_insertion, examination.start_time,
                                                tighten_times=False)
            return solution, True


def randomly_replace_performed_task_by_non_performed_one(solution: SolutionForHeuristics):
    """
    Replace a random performed task of a random employee sequence by a random non-performed one

    - The employee is randomly selected among those who have performed at least one task,
      according to a probability distribution which is proportional, for each employee, to
      the total travel time divided by the total working duration

    - The replaced task is randomly selected among those performed by the selected employee,
      according to a probability distribution which is proportional, for each task, to
      the total travel time decrease obtained by removing the task divided by the task duration

    - The replacing task is randomly selected among those not performed by any employee,
      according to a probability distribution which is proportional, for each task, to the duration divided by
      the total travel time increase due to inserting the task in the employee sequence

    NB: let n be the number of employees and m be the number of tasks,
    worst case complexity is in O(max(n,m)) i.e. O(m) if n << m

    :param solution: the solution to modify (SolutionForHeuristics)
    :return: a pair (solution, success) where
    success is a boolean indicating whether the task replacement was successful and
    solution is the solution obtained after replacing the task
    (by default, if success is False, solution is the same as the input solution)
    """
    # For complexity computation:
    # - n is the number of employees
    # - m is the number of tasks
    # - p is the number of steps in an employee sequence
    # Get the list of employees who have performed at least one task
    # NB: O(n)
    working_employees = [employee for employee in solution.instance.employees
                         if len(solution.get_tasks_performed_by(employee)) > 0]
    # If there is no employee who has performed at least one task, return the input solution
    if len(working_employees) == 0:
        return solution, False
    # Otherwise,
    else:
        # Select randomly an employee among those who have performed at least one task
        # NB: O(n)
        employee = \
            randomly_select_employee_by_favoring_higher_travel_time_vs_working_time_ratio(solution, working_employees)
        # Select randomly a task among those performed by the selected employee
        # NB: O(p)
        # NB 2: worst case complexity in O(m)
        # NB 3: average complexity in O(m/n)
        replaced_task = \
            randomly_select_task_in_employee_sequence_by_favoring_higher_travel_time_delta_vs_duration_ratio(solution,
                                                                                                             employee)
        # Get the list of non performed tasks such that the employee is skilled-enough to perform them
        # NB: O(m)
        possible_replacing_tasks = \
            [task for task in solution.non_performed_tasks if employee.is_capable_of_performing(task)]
        # Get the list of feasible replacements of the selected task by each of the possible tasks
        # NB: O(m)
        examinations = \
            solution.find_feasible_replacements_of_task_given_various_replacing_tasks(employee, replaced_task,
                                                                                      possible_replacing_tasks)
        # If there is no feasible replacement, return the input solution
        if len(examinations) == 0:
            return solution, False
        # Otherwise,
        else:
            # Select randomly a replacement among the feasible ones,
            # according to a probability distribution which is proportional, for each replacement, to 
            # the duration of the replacing task divided by
            # the travel time increase due to each replacement of the task in the employee sequence
            # NB: O(m)
            weights = [(examination.replacing_task.duration / (examination.travel_time_increase + 1)
                        if examination.travel_time_increase >= 0 else
                        examination.replacing_task.duration - examination.travel_time_increase)
                       for examination in examinations]
            examination = random.choices(examinations, weights=weights)[0]
            # Replace the task in the selected employee sequence
            # NB: O(p)
            # NB 2: worst case complexity in O(m)
            # NB 3: average case complexity in O(m/n)
            solution.replace_task_by_another(replaced_task, examination.replacing_task, examination.start_time,
                                             tighten_times=False)
            return solution, True


# TODO: other replacement strategies
# random non performed task
# employees skilled enough to perform the task
# feasible replacements of any task by selected non performed task


def randomly_reassign_task_from_employee_sequence_to_another(solution: SolutionForHeuristics):
    """
    Reassign a random task of a random employee sequence to another random employee sequence

    :param solution: the solution to modify (SolutionForHeuristics)
    :return: a pair (solution, success) where
    success is a boolean indicating whether reassigning the task was successful and
    solution is the solution obtained after reassigning the task
    (by default, if success is False, solution is the same as the input solution)
    """
    # For complexity computation:
    # - n is the number of employees
    # - m is the number of tasks
    # - p is the number of steps in an employee sequence
    # Get the list of employees who have performed at least one task
    # NB: O(n)
    working_employees = [employee for employee in solution.instance.employees
                         if len(solution.get_tasks_performed_by(employee)) > 0]
    # If there is no employee who has performed at least one task, return the input solution
    if len(working_employees) == 0:
        return solution, False
    # Otherwise,
    else:
        # Select randomly an employee among those who have performed at least one task
        # NB: O(n)
        stolen_employee = \
            randomly_select_employee_by_favoring_higher_travel_time_vs_working_time_ratio(solution, working_employees)
        # Select randomly a task among those performed by the selected employee
        # NB: O(p)
        # NB 2: worst case complexity in O(m)
        # NB 3: average complexity in O(m/n)
        moving_task = \
            randomly_select_task_in_employee_sequence_by_favoring_higher_travel_time_delta_vs_duration_ratio(
                solution, stolen_employee
            )
        # Get the list of employees who are skilled-enough to perform the selected task and are not the first employee
        # NB: O(n)
        skilled_employees = [employee for employee in solution.instance.employees
                             if employee != stolen_employee and employee.skill_level >= moving_task.skill_level]
        # Get the list of feasible reassignments of the selected task for each of these employees
        # NB: O(m)
        examinations = []
        for employee in skilled_employees:
            examinations.extend(
                solution.find_feasible_reassignments(stolen_employee, moving_task, employee)
            )
        # If there is no feasible reassignment for any skilled employee, return the input solution
        if len(examinations) == 0:
            return solution, False
        # Otherwise,
        else:
            # Select randomly a reassignment among the feasible ones,
            # according to a probability distribution which is inversely proportional to
            # the travel time increase due to each reassignment of the task in the employee sequence
            # NB: O(m)
            weights = [(1 / (examination.travel_time_increase + 1) if examination.travel_time_increase >= 0 else
                        -examination.travel_time_increase)
                       for examination in examinations]
            examination = random.choices(examinations, weights=weights)[0]
            # Insert the task in the selected employee sequence
            # NB: O(p)
            # NB 2: worst case complexity in O(m)
            # NB 3: average case complexity in O(m/n)
            solution.reassign_task_after_activity(moving_task, examination.activity_before_reassignment,
                                                  examination.start_time, tighten_times=False)
            return solution, True


def randomly_reorder_task_in_employee_sequence(solution: SolutionForHeuristics):
    # Get the list of employees who have performed at least two tasks
    working_employees = [employee for employee in solution.instance.employees
                         if len(solution.get_tasks_performed_by(employee)) > 1]
    # If there is no employee who has performed at least two tasks, return the input solution
    if len(working_employees) == 0:
        return solution, False
    # Otherwise,
    else:
        # Select randomly an employee among those who have performed at least two tasks
        # NB: O(n)
        employee = \
            randomly_select_employee_by_favoring_higher_travel_time_vs_working_time_ratio(solution, working_employees)
        # Select randomly a task among those performed by the selected employee
        # NB: O(p)
        sequence = solution.get_sequence(employee)
        weights = [(solution.compute_traveling_duration(before, step) +
                    solution.compute_traveling_duration(step, after) -
                    solution.compute_traveling_duration(before, after))
                   for (before, step, after) in zip(sequence[0:-2], sequence[1:-1], sequence[2:])]
        tasks = [step.activity for step in sequence[1:-1]]
        if np.sum(weights) > 0:
            task = random.choices([step.activity for step in sequence[1:-1]], weights=weights)[0]
        else:
            task = random.choice(tasks)
        # Get the list of feasible reorders of the selected task
        # NB: O(m)
        examinations = solution.find_task_feasible_reorders(employee, task)
        # If there is no feasible reorder for any skilled employee, return the input solution
        if len(examinations) == 0:
            return solution, False
        # Otherwise,
        else:
            # Select randomly a reorder among the feasible ones,
            # according to a probability distribution which is inversely proportional to
            # the travel time increase due to each reorder of the task in the employee sequence
            # NB: O(m)
            weights = [(1 / (examination.travel_time_increase + 1) if examination.travel_time_increase >= 0 else
                        -examination.travel_time_increase)
                       for examination in examinations]
            examination = random.choices(examinations, weights=weights)[0]
            # Insert the task in the selected employee sequence
            # NB: O(p)
            # NB 2: worst case complexity in O(m)
            # NB 3: average case complexity in O(m/n)
            solution.shift_task_in_sequence_after_activity(task, examination.activity_before, examination.start_time,
                                                           tighten_times=False)
            return solution, True


#############################################
# Neighborhood search - Auxiliary functions #
#############################################


def sort_population(population: list[SolutionForHeuristics]):
    population.sort(key=lambda s: (s.total_working_duration, -s.total_traveling_duration), reverse=True)
    return population


def shuffle_solution(solution: SolutionForHeuristics, nb_iterations: int = 10):
    for _ in range(nb_iterations):
        neighboring_function_label = random.choice(list(NEIGHBORING_FUNCTIONS.keys()))
        neighboring_function = NEIGHBORING_FUNCTIONS[neighboring_function_label]
        solution, _ = neighboring_function(solution)
    return solution


def initialize_solution_population(instance: Instance, solution: SolutionForHeuristics = None):
    population = []
    nb_steps_between_messages = max(np.ceil(.2 * NEIGHBORHOOD_SEARCH_POPULATION_SIZE), 2)
    if solution is not None:
        nb_best = int(np.ceil(NEIGHBORHOOD_SEARCH_POPULATION_SIZE *
                              NEIGHBORHOOD_SEARCH_PROPORTION_OF_BEST_SOLUTIONS_TO_KEEP))
        for i in range(1, nb_best + 1):
            if i % nb_steps_between_messages == 1:
                print(f"Preparing initial solution: {i}")
            if i == 1:
                population.append(SolutionForHeuristics.from_SolutionOpti(solution, 'neighborhood_search'))
            else:
                solution_copy = SolutionForHeuristics.from_SolutionOpti(solution, 'neighborhood_search')
                population.append(shuffle_solution(solution_copy))
    for i in range(len(population) + 1, NEIGHBORHOOD_SEARCH_POPULATION_SIZE + 1):
        if i % nb_steps_between_messages == 1:
            print(f"Preparing initial solution: {i}")
        stochastic_solution = run_stochastic_heuristic(instance, mute=True)
        population.append(SolutionForHeuristics.from_SolutionOpti(stochastic_solution, 'neighborhood_search'))
    sort_population(population)
    return population


NEIGHBORING_FUNCTIONS = dict(
    removing=randomly_remove_performed_task_from_employee_sequence,
    inserting=randomly_insert_non_performed_task_in_employee_sequence,
    replacing=randomly_replace_performed_task_by_non_performed_one,
    reassigning=randomly_reassign_task_from_employee_sequence_to_another,
    reordering=randomly_reorder_task_in_employee_sequence
)


def compute_weights_distribution_for_neighboring_functions(neighboring_successes_counters: dict[str, (int, int)]):
    weights = dict()
    for neighboring_function_name, (successes, attempts) in neighboring_successes_counters.items():
        successes = max(successes, 1)
        attempts = max(attempts, 1)
        weights[neighboring_function_name] = successes / attempts
    total_weight = sum([weight for weight in weights.values()])
    weights['removing'] = (total_weight - weights['removing']) / (len(NEIGHBORING_FUNCTIONS) - 1)
    return weights


def create_neighboring_pool(solution: SolutionForHeuristics, neighboring_successes_counters: dict[str, (int, int)],
                            pool_size: int, neighboring_failure_limit: int = None):
    if neighboring_failure_limit is None:
        neighboring_failure_limit = 2 * pool_size
    pool = []
    nb_neighboring_failures = 0
    while len(pool) < pool_size and nb_neighboring_failures < neighboring_failure_limit:
        # neighboring_function_label = random.choice(list(NEIGHBORING_FUNCTIONS.keys()))
        weights = compute_weights_distribution_for_neighboring_functions(neighboring_successes_counters)
        if solution.nb_non_performed_tasks == 0:
            weights['inserting'] = 0
        neighboring_function_label = \
            random.choices(list(NEIGHBORING_FUNCTIONS.keys()), weights=list(weights.values()))[0]
        neighboring_function = NEIGHBORING_FUNCTIONS[neighboring_function_label]
        neighboring_successes_counters[neighboring_function_label][1] += 1
        neighboring_solution, neighboring_success = neighboring_function(solution.copy(solution.name))
        if neighboring_success:
            pool.append(neighboring_solution)
            neighboring_successes_counters[neighboring_function_label][0] += 1
        else:
            nb_neighboring_failures += 1
    for _ in range(pool_size - len(pool)):
        pool.append(solution.copy(solution.name))
    return pool


#######################################
# Neighborhood search - Main function #
#######################################

def run_neighborhood_search(instance: Instance, solution: SolutionForHeuristics = None):

    # Initialize random seed
    if NEIGHBORHOOD_SEARCH_RANDOM_SEED is not None:
        random.seed(NEIGHBORHOOD_SEARCH_RANDOM_SEED)

    # Generate an initial population of solutions
    print("1. Preparing initial population")
    initialization_start_time = time.time()
    population = initialize_solution_population(instance, solution)
    initialization_time = int(np.ceil(time.time() - initialization_start_time))
    print(f"Initialization time: {initialization_time}s = {initialization_time // 60}min {initialization_time % 60}s")
    print("Preparing initial population: done")
    print("")

    # Run the neighborhood search
    print("2. Running neighborhood search")
    generation_counter = 1
    neighboring_successes_counters = {label: [0, 0] for label in NEIGHBORING_FUNCTIONS.keys()}
    neighborhood_search_start_time = time.time()
    neighborhood_search_time = 0
    messages_counter = 0
    while neighborhood_search_time < NEIGHBORHOOD_SEARCH_TIME_LIMIT:

        # Print message
        n = neighborhood_search_time // NEIGHBORHOOD_SEARCH_TIME_BETWEEN_MESSAGES
        if n > messages_counter:
            messages_counter = n
            best_solution = population[0]
            worst_solution = population[-1]
            print(f"Generation: {generation_counter} | "
                  f"Best solution objective values: "
                  f"({best_solution.total_working_duration}, {best_solution.total_traveling_duration}) | "
                  f"Worst solution objective values: "
                  f"({worst_solution.total_working_duration}, {worst_solution.total_traveling_duration})")

        # Initialize the neighboring population with solutions from the current population
        neighboring_population = [solution.copy(solution.name) for solution in population]

        # Create a pool of neighboring solutions for each solution of the current population
        # and add it them to the neighboring population
        for solution in population:
            pool = create_neighboring_pool(solution, neighboring_successes_counters,
                                           NEIGHBORHOOD_SEARCH_NB_NEIGHBORS_PER_SOLUTION)
            neighboring_population.extend(pool)

        # Sort the neighboring population
        neighboring_population = sort_population(neighboring_population)

        # Create a new population from the neighboring one
        # first, by selecting a fixed proportion of the best solutions of the neighboring population
        # second, by completing the new population with solutions randomly selected
        # among remaining solutions of the neighboring population
        # - Select a fixed proportion of the best solutions
        nb_best_solutions_to_keep = int(
            NEIGHBORHOOD_SEARCH_PROPORTION_OF_BEST_SOLUTIONS_TO_KEEP * NEIGHBORHOOD_SEARCH_POPULATION_SIZE)
        population = neighboring_population[:nb_best_solutions_to_keep]
        # - Complete with random solutions from remaining ones
        remaining_solutions = neighboring_population[nb_best_solutions_to_keep:]
        nb_remaining_solutions_to_add = NEIGHBORHOOD_SEARCH_POPULATION_SIZE - len(population)
        population.extend(random.choices(remaining_solutions, k=nb_remaining_solutions_to_add))

        # Update neighborhood search time
        neighborhood_search_time = int(np.ceil(time.time() - neighborhood_search_start_time))
        generation_counter += 1

    # Return the best solution found
    for neighboring_function_label in NEIGHBORING_FUNCTIONS.keys():
        successes, attempts = neighboring_successes_counters[neighboring_function_label]
        print(f"Neighboring function '{neighboring_function_label}': {successes} successes / {attempts} attempts")
    print(f"Neighboring search time: {neighborhood_search_time}s = "
          f"{neighborhood_search_time // 60}min {neighborhood_search_time % 60}s")
    print("Neighborhood search: done")
    print("")
    population = sort_population(population)
    best_solution = population[0]
    best_solution.tighten_times()
    return best_solution
