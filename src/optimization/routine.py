#! /usr/bin/env python3
# coding: utf-8


# Local libraries
from src.checking.feasibility import check_feasibility
from src.drawing.figuresmanager import FiguresManager
from src.reading.instance import extract_instance_from_file
from src.optimization.IP.WSRPmodel import WSRPIPModel
from src.utils.display import print_title_frame
from src.utils.files import get_instances_files_paths
from src.writing.analysis import write_solution_analysis
from src.writing.solution import write_solution


# Optimization routine function
def apply_optimization_routine(solving_time_limit_in_seconds: int = 3600):
    instances_files_names = get_instances_files_paths()
    for instance_file_name in instances_files_names:
        instance = extract_instance_from_file(instance_file_name)
        print("")
        print_title_frame("Optimization of " + instance.name)
        print("")
        model = WSRPIPModel(instance=instance)
        print(f"IP model version {model.version}")
        model.update()
        model.solving_time_limit = solving_time_limit_in_seconds
        model.optimize(mute=True)
        solution = model.solution
        if check_feasibility(solution, covering=(model.version == 1))[0]:
            raise Exception("The solution given by the optimization is not feasible")
        solution.compute_KPIs()
        write_solution(solution)
        write_solution_analysis(solution)
        figures_manager = FiguresManager(solution)
        figures_manager.save_figures()
        print("")


# Main
def main():
    apply_optimization_routine(120)


if __name__ == '__main__':
    main()

