# Local libraries
from src.importing.solution import import_solution
from src.modeling.solution import Solution

# Global variables
# NB: Paths are relative to the project's root directory, which is where pytest is run from.
INSTANCE_FILE_PATH = "tests/data/instance_test.xlsx"
SOLUTION_FILE_PATH = "tests/data/solution_test.txt"
INSTANCE_WITH_UNAVAILABILITIES_FILE_PATH = "tests/data/instance_with_unavailabilities.json"


def build_solution() -> Solution:
    """Returns the reference solution of the tests' data directory, imported from its .txt file."""
    return import_solution(SOLUTION_FILE_PATH)
