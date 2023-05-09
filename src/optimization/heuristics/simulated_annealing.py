# Standard libraries
import math
import random

# Third party library
import matplotlib.pyplot as plt

# Local libraries
from src.drawing.routes import create_routes_figure
from src.drawing.schedules import create_schedules_figure
from src.optimization.heuristics.greedy import run_greedy_algorithm
from src.optimization.heuristics.solution import SolutionForHeuristics
from src.reading.instance import extract_instance_from_file
from src.utils.files import get_project_directory_path
from src.writing.solution import write_solution


def run_simulated_annealing(solution: SolutionForHeuristics):

    def _insert_random_non_performed_task(_solution: SolutionForHeuristics):
        """
        Insert a random non-performed task in a random employee's sequence
        Assumption: there are non-performed tasks
        :param _solution: a solution
        :return: a pair (solution, success) where success is a boolean indicating whether the insertion was successful
        and solution is the solution after the insertion (or the original solution if the insertion was not successful)
        """
        task = random.choice(_solution.non_performed_tasks)
        employee = random.choice(_solution.instance.get_employees_with_skill_level_higher_than(task.skill_level))
        examination = _solution.find_best_insertion_between_consecutive_activities(employee, task)
        if examination.is_feasible:
            activity = examination.activity_before_insertion
            _solution.insert_task_after_activity(task, activity, examination.start_time, tighten_times=True)
            return _solution, True
        else:
            return _solution, False

    def _transfer_random_performed_task_from_employee_to_another(_solution: SolutionForHeuristics):
        """
        Transfer a random performed task of an employee's sequence to another employee
        Assumption: there are performed tasks
        """
        task = random.choice(solution.performed_tasks)
        employee = random.choice(_solution.instance.get_employees_with_skill_level_higher_than(task.skill_level))
        examination = _solution.find_best_insertion_between_consecutive_activities(employee, task)
        if examination.is_feasible:
            activity = examination.activity_before_insertion
            _solution.insert_task_after_activity(task, activity, examination.start_time, tighten_times=True)
            return _solution, True
        else:
            return _solution, False

    def _remove_random_performed_task(_solution: SolutionForHeuristics):
        """
        Remove a random performed task from an employee's sequence
        :param _solution: a solution
        :return: a pair (solution, success) where success is a boolean indicating whether the removal was successful
        and solution is the solution after the removal (or the original solution if the removal was not successful)
        """
        _solution.remove_task(random.choice(_solution.performed_tasks))
        return _solution, True

    moves = [_insert_random_non_performed_task, _transfer_random_performed_task_from_employee_to_another,
             _remove_random_performed_task]
    moves_if_no_performed_tasks, moves_if_all_tasks_performed = moves.copy(), moves.copy()
    moves_if_no_performed_tasks.remove(_transfer_random_performed_task_from_employee_to_another)
    moves_if_no_performed_tasks.remove(_remove_random_performed_task)
    moves_if_all_tasks_performed.remove(_insert_random_non_performed_task)

    def _apply_random_move(_solution: SolutionForHeuristics):
        if _solution.nb_performed_tasks == 0:
            return random.choice(moves_if_no_performed_tasks)(_solution)
        elif _solution.nb_non_performed_tasks == 0:
            return random.choice(moves_if_all_tasks_performed)(_solution)
        else:
            return random.choice(moves)(_solution)

    def _compute_energy(_solution: SolutionForHeuristics):
        return _solution.total_traveling_duration - 10*_solution.total_working_duration

    def _compute_probability(_energy_variation: float, _temperature: float):
        assert _energy_variation > 0
        return math.exp(-_energy_variation/_temperature)

    nb_epochs = 10
    initial_temperature = 3000
    cooling_rate = 0.0005
    best_solution = solution
    print(f"Before optimization, best solution has objective values: "
          f"{best_solution.total_working_duration, best_solution.total_traveling_duration}")
    for epoch in range(nb_epochs):
        print("Epoch", epoch)
        temperature = initial_temperature
        while temperature > 1:
            new_solution, success = _apply_random_move(solution.copy(solution.name))
            if success:
                energy_variation = _compute_energy(new_solution) - _compute_energy(solution)
                if energy_variation <= 0:
                    solution = new_solution
                    if _compute_energy(solution) < _compute_energy(best_solution):
                        best_solution = solution
                else:
                    probability = _compute_probability(energy_variation, temperature)
                    if random.random() < probability:
                        solution = new_solution
            temperature = temperature * (1 - cooling_rate)
            # print(f"At temperature {temperature}, solution has energy {_compute_energy(solution)} "
            #       f"while best solution has energy {_compute_energy(best_solution)}")
        solution = best_solution
        print(f"At epoch {epoch}, best solution has objective values: "
              f"{best_solution.total_working_duration, best_solution.total_traveling_duration}")
    return best_solution


if __name__ == "__main__":
    instance_path_example = f"{get_project_directory_path()}/data/DB/instances/instance_Exeter20180803.json"
    instance_example = extract_instance_from_file(instance_path_example, True, True, True)
    solution_example = run_greedy_algorithm(instance_example)
    write_solution(solution_example, f"{get_project_directory_path()}/data/DB/solutions")
    print(solution_example.nb_performed_tasks, solution_example.total_working_duration,
          solution_example.total_traveling_duration)
    create_schedules_figure(solution_example)
    create_routes_figure(solution_example)
    plt.show()
    # solution_example = run_simulated_annealing(solution_example)
    # print(solution_example.nb_performed_tasks, solution_example.total_working_duration,
    #       solution_example.total_traveling_duration)
    # create_schedules_figure(solution_example)
    # plt.show()
