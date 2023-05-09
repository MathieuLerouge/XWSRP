# Standard libraries
import random

# Local libraries
from src.modeling.instance import Instance
from src.optimization.heuristics.solution import SolutionForHeuristics


########################
# Stochastic heuristic #
########################

def run_stochastic_heuristic(instance: Instance, mute: bool = False):

    # Initialize solution
    solution = SolutionForHeuristics(instance, heuristic_ID='stochastic')

    # Create a dictionary of possible tasks that may be performed by each employee
    possible_tasks_per_employee = {employee: instance.tasks for employee in instance.employees}

    # Initialize step counter and maximum number of steps left
    step_counter = 1
    max_steps_left = instance.nb_tasks

    # While there are still employees with possible tasks to perform
    while len(possible_tasks_per_employee) > 0:

        # Print message every n steps
        n = 20
        if not mute and step_counter % n == 1:
            print(f"Steps: {step_counter} | Max steps left: {max_steps_left}")

        # Select randomly an employee among the ones who may still have tasks to insert
        # according to a probability distribution which for each employee is inversely proportional to
        # the number of possible tasks that could be performed by the employee
        employees = list(possible_tasks_per_employee.keys())
        weights = [1/len(possible_tasks_per_employee[employee]) for employee in employees]
        employee = random.choices(employees, weights=weights, k=1)[0]

        # Examine for each possible task if it can be feasibly inserted in the sequence of the selected employee and
        # compute its best insertion
        possible_tasks = possible_tasks_per_employee[employee]
        examinations = \
            solution.find_best_feasible_insertion_between_consecutive_activities_for_each_task(possible_tasks, employee)
        possible_tasks = [examination.inserted_task for examination in examinations]

        # If none of the possible tasks can be feasibly inserted,
        # then remove the employee from the ones who may still have tasks to insert
        if len(possible_tasks) == 0:
            del possible_tasks_per_employee[employee]

        # Otherwise,
        else:

            # Select randomly a task according to a probability distribution which for each task
            # is inversely proportional to the traveling time increase due to the insertion of the task
            weights = [1 / (examination.travel_time_increase + 0.01) for examination in examinations]
            examination = random.choices(examinations, weights=weights, k=1)[0]
            task = examination.inserted_task

            # Insert the selected task in the sequence of the selected employee
            solution.insert_task_after_activity(task, examination.activity_before_insertion, examination.start_time)

            # Update possible tasks of selected employee
            # In addition, check if the employee has no more possible tasks to insert
            # and update the maximum number of steps left
            possible_tasks.remove(task)
            possible_tasks_per_employee[employee] = possible_tasks
            employees_to_remove = []
            if len(possible_tasks) == 0:
                employees_to_remove.append(employee)
            max_steps_left = len(possible_tasks)

            # Update possible tasks of other employee
            # In addition, check if the employee has no more possible tasks to insert
            # and update the maximum number of steps left
            for other_employee in possible_tasks_per_employee:
                if other_employee != employee:
                    if task in possible_tasks_per_employee[other_employee]:
                        possible_tasks_per_employee[other_employee].remove(task)
                    if len(possible_tasks_per_employee[other_employee]) == 0:
                        employees_to_remove.append(other_employee)
                    else:
                        max_steps_left = max(max_steps_left, len(possible_tasks_per_employee[other_employee]))
            for employee_to_remove in employees_to_remove:
                del possible_tasks_per_employee[employee_to_remove]

        # Update step counter
        step_counter += 1

    return solution
