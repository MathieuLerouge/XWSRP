# Third party libraries
from matplotlib import pyplot as plt

# Local libraries
from src.drawing.constants import *
from src.drawing.KPIs import create_KPIs_figure
from src.drawing.routes import create_routes_figure
from src.drawing.schedules import create_schedules_figure
from src.modeling.solution import Solution
from src.utils.constants import DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
from src.utils.files import make_absolute_path_from_relative_one


###########
# Figures #
###########


def create_figure_id(solution: Solution, figure_key: str):
    """
    Create a figure id from the solution name and the figure key.

    :param solution: solution (Solution)
    :param figure_key: figure key (str)
    :return: figure id (str)
    """
    return solution.name + figure_key


def create_figure(solution: Solution, figure_key: str, for_UI: bool = False):
    """
    Create a figure from the solution and the figure key.

    :param solution: solution (Solution)
    :param figure_key: figure key (str)
    :param for_UI: if True, the figure is created for the UI (bool)
    :return: figure (Figure)
    """
    figure_id = create_figure_id(solution, figure_key)
    if figure_key == ROUTES_FIGURE_KEY:
        return create_routes_figure(solution, figure_id, for_UI=for_UI)
    elif figure_key == SCHEDULES_FIGURE_KEY:
        return create_schedules_figure(solution, figure_id, for_UI=for_UI)
    elif figure_key == KPIS_FIGURE_KEY:
        return create_KPIs_figure(solution, figure_id, for_UI=for_UI)
    else:
        raise ValueError(f"Wrong figure key {figure_key} for figure")


def create_figure_file_path(solution: Solution, figure_key: str, outputs_directory_relative_path: str = None):
    """
    Create a figure file path from the solution name and the figure key.
    If no outputs directory relative path is provided,
    the default one is used the path of the default outputs directory.

    :param solution: solution (Solution)
    :param figure_key: figure key (str)
    :param outputs_directory_relative_path: outputs directory relative path (str)
    :return: figure file path (str)
    """
    if outputs_directory_relative_path is None:
        outputs_directory_relative_path = DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH
    if solution.instance.name_case_type_is_snake_case:
        figure_file_name_with_extension = f"{solution.name}_{figure_key}.png"
    elif solution.instance.name_case_type_is_camel_case:
        figure_keys_bis = {ROUTES_FIGURE_KEY: ROUTES_FIGURE_KEY_BIS, SCHEDULES_FIGURE_KEY: SCHEDULES_FIGURE_KEY_BIS,
                           KPIS_FIGURE_KEY: KPIS_FIGURE_KEY_BIS}
        figure_file_name_with_extension = f"{solution.name}{figure_keys_bis[figure_key]}.png"
    else:
        raise ValueError(f"Wrong case type {solution.instance.name_case_type}")
    return make_absolute_path_from_relative_one(f"{outputs_directory_relative_path}/{figure_file_name_with_extension}")


##################
# FiguresManager #
##################

class FiguresManager:

    def __init__(self, solution: Solution = None, solutions: list[Solution] = None):
        self._main_solution = None
        self._stored_solutions_figures = dict()
        if solution is not None:
            self._main_solution = solution
            self.store_solution(solution)
        if solutions is not None:
            self.store_solutions(solutions)

    @property
    def main_solution(self):
        if self._main_solution is None:
            raise AttributeError("There is not any stored solution")
        return self._main_solution

    @main_solution.setter
    def main_solution(self, solution: Solution):
        if self.has_any_stored_solution:
            if self._main_solution != solution:
                self._main_solution = solution
                self._store_solution_if_new(solution)
        else:
            self._main_solution = solution
            self._store_new_solution(solution)

    @property
    def has_any_stored_solution(self):
        return self._main_solution is not None

    ###############################
    # Storing solutions - Private #
    ###############################

    def _store_new_solution(self, solution: Solution):
        self._stored_solutions_figures[solution] = dict()

    def _store_solution_if_new(self, solution: Solution):
        if not self.stored_solutions_contain(solution):
            self._store_new_solution(solution)

    ##############################
    # Storing solutions - Public #
    ##############################

    def stored_solutions_contain(self, solution: Solution):
        return solution in self._stored_solutions_figures.keys()

    def store_solution(self, solution: Solution):
        if not self.has_any_stored_solution:
            self._main_solution = solution
            self._store_new_solution(solution)
        else:
            self._store_solution_if_new(solution)

    def store_solutions(self, solutions):
        for solution in solutions:
            self.store_solution(solution)

    def delete_solution(self, solution: Solution):
        if self.stored_solutions_contain(solution):
            self.delete_figures(solution)
            del self._stored_solutions_figures[solution]
            if self.main_solution == solution:
                if bool(self._stored_solutions_figures):
                    self._main_solution = next(iter(self._stored_solutions_figures))
                else:
                    self._main_solution = None

    ##############################
    # Managing figures - Private #
    ##############################

    def _has_figure(self, solution: Solution, figure_key: str):
        return figure_key in self._stored_solutions_figures[solution].keys()

    #############################
    # Managing figures - Public #
    #############################

    def has_figure(self, solution: Solution, figure_key: str):
        if self.stored_solutions_contain(solution):
            return self._has_figure(solution, figure_key)
        else:
            return False

    def has_figures(self, solution: Solution = None):
        if solution is None:
            solution = self.main_solution
        booleans = dict([(figure_key, False) for figure_key in FIGURES_KEYS])
        if self.stored_solutions_contain(solution):
            for figure_key in FIGURES_KEYS:
                booleans[figure_key] = self._has_figure(solution, figure_key)
        return booleans

    def store_solution_figure(self, solution: Solution, figure_key: str, for_UI: bool = False):
        self.store_solution(solution)
        if not self.has_figure(solution, figure_key):
            self._stored_solutions_figures[solution][figure_key] = create_figure(solution, figure_key, for_UI)

    def store_solution_figures(self, solution: Solution = None, for_UI: bool = False):
        if solution is None:
            solution = self.main_solution
        for figure_key in FIGURES_KEYS:
            self.store_solution_figure(solution, figure_key, for_UI)

    def get_solution_figure(self, solution: Solution, figure_key: str, for_UI: bool = False,
                            store_figure: bool = False):
        if self.has_figure(solution, figure_key):
            figure = self._stored_solutions_figures[solution][figure_key]
        elif store_figure:
            self.store_solution_figure(solution, figure_key, for_UI)
            figure = self._stored_solutions_figures[solution][figure_key]
        else:
            figure = create_figure(solution, figure_key, for_UI)
        return figure

    def get_solution_figures(self, solution: Solution = None, for_UI: bool = False,
                             store_figures: bool = False):
        if solution is None:
            solution = self.main_solution
        return dict([
            (figure_key, self.get_solution_figure(solution, figure_key, for_UI, store_figures))
            for figure_key in FIGURES_KEYS
        ])

    def show_figure(self, solution: Solution, figure_key: str):
        plt.close('all')
        plt.figure(self.get_solution_figure(solution, figure_key, False, False))
        plt.show(block=True)

    def show_figures(self, solution: Solution = None):
        plt.close('all')
        if solution is None:
            solution = self.main_solution
        for figure_key in FIGURES_KEYS:
            plt.figure(self.get_solution_figure(solution, figure_key, False, False))
        plt.show(block=True)

    def save_figure_as_file(self, solution: Solution, figure_key: str, output_directory: str = None):
        plt.figure(self.get_solution_figure(solution, figure_key, False, False))
        plt.savefig(create_figure_file_path(solution, figure_key, output_directory), dpi=FIGURE_DPI_FOR_SAVING)

    def save_figures(self, solution: Solution = None, output_directory: str = None):
        if solution is None:
            solution = self.main_solution
        for figure_key in FIGURES_KEYS:
            self.save_figure_as_file(solution, figure_key, output_directory)

    def delete_figures(self, solution: Solution):
        if self.stored_solutions_contain(solution):
            booleans = self.has_figures(solution)
            for figure_key, boolean in booleans.items():
                if boolean:
                    figure = self._stored_solutions_figures[solution][figure_key]
                    figure.clf()
                    plt.close(figure)
            self._stored_solutions_figures[solution] = dict()
