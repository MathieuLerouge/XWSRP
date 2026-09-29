# Third-party library
import pytest

# Local libraries
from src.explaining.interacting.history import History
from src.explaining.modeling.solution import EditableSolution
from src.explaining.processes import get_demo_solution


@pytest.fixture(scope="module")
def stored_solution() -> EditableSolution:
    """The solution the history under test is built around."""
    return EditableSolution.from_solution(get_demo_solution())


@pytest.fixture
def history(stored_solution) -> History:
    """A history holding one solution and the instance it is of."""
    return History(stored_solution)


def test_the_solution_it_was_built_around_is_in_it(history, stored_solution):
    assert stored_solution in history
    assert stored_solution.instance in history


def test_a_solution_it_does_not_hold_is_not_in_it(history, stored_solution):
    other_solution = stored_solution.copy(name="another_solution")
    assert other_solution not in history
    history.store_solution(other_solution)
    assert other_solution in history


def test_asking_whether_it_holds_something_that_is_neither_is_refused(history):
    """
    `in` must raise on a type the history cannot hold, rather than answering.

    The check used to build its TypeError and return it. `in` coerces whatever __contains__ gives back
    with bool(), and an exception instance is truthy, so every wrong-typed object was reported as held.
    """
    with pytest.raises(TypeError):
        _ = "not a solution" in history
    with pytest.raises(TypeError):
        _ = 42 in history
