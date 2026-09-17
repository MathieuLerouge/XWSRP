# Local libraries
from src.feasibility.violation.violation import Violation


def test_violation_repr_returns_its_text():
    class DummyViolation(Violation):
        @property
        def text(self):
            return "dummy violation text"

    assert repr(DummyViolation()) == "dummy violation text"
