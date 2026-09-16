# Third-party library
import pytest
from instructor import Mode

# Local libraries
from src.explaining.neighborhood.llm.exceptions import NeighborhoodExtractionError
from src.explaining.neighborhood.llm.extractor import Extractor
from src.explaining.neighborhood.operator import (
    SequenceReordering, TaskDeletion, TaskInsertion, TaskRepositioning
)
from src.explaining.neighborhood.restriction import (
    ForbiddenBackwardSubsequence, ForbiddenSequence, ImmediatePrecedence, Precedence, PrecedenceChain
)
from tests.explaining.neighborhood.helpers import build_solution_with_task_performances
from tests.modeling.helpers import build_instance

# Real-model quality checks: one free-text question per row of neighborhood/README.md section 4's
# (Ins,*)/(Swp,*)/(Ord,*) tables, phrased the way an end-user actually would rather than the
# tailored QuestionTemplate's exact wording - the point of this pipeline is to cover phrasings the
# fixed catalogue can't. Run against a free, local Ollama model (see the root README) rather than
# main_configuration.EXTRACTOR_MODEL, so these tests don't silently start hitting a paid provider
# if that configuration ever changes. Assertions check operator/restriction kinds present, not
# full object equality, since the LLM may reasonably phrase equivalent candidate sets differently;
# some run-to-run variance is expected from a small local model - see PR 9's marker.
_MODEL = "ollama/qwen2.5:7b"
_MODE = Mode.MD_JSON


@pytest.fixture(scope="module")
def instance():
    return build_instance()


@pytest.fixture(scope="module")
def solution(instance):
    # Valentin performs T1, T2, T3, T4 in order; Ambre performs T6, T7 in order;
    # T5, T8-T14 are left non-performed.
    return build_solution_with_task_performances(instance, "solution", {
        "T1": ("Valentin", 480), "T2": ("Valentin", 560), "T3": ("Valentin", 640), "T4": ("Valentin", 720),
        "T6": ("Ambre", 480), "T7": ("Ambre", 560),
    })


@pytest.fixture
def extractor(solution):
    return Extractor(solution, _MODEL, mode=_MODE)


def _operator_types(neighborhood):
    return {type(operator) for operator in neighborhood.operators}


def _restriction_types(neighborhood):
    return {type(restriction) for restriction in neighborhood.restrictions}


############
# (Ins,1) #
############

def test_ins_1(extractor, instance):
    neighborhood = extractor.extract("Why doesn't Valentin do task T5 right after task T3?")
    operator_types = _operator_types(neighborhood)
    assert TaskInsertion in operator_types
    task_insertion = next(o for o in neighborhood.operators if isinstance(o, TaskInsertion))
    assert instance.get_task_by_name("T5") in task_insertion.candidate_tasks
    assert ImmediatePrecedence in _restriction_types(neighborhood)


#############
# (Ins,2a) #
#############

def test_ins_2a(extractor, instance):
    neighborhood = extractor.extract("Why isn't Valentin performing task T5 at some point in his day?")
    task_insertion = next(o for o in neighborhood.operators if isinstance(o, TaskInsertion))
    assert instance.get_task_by_name("T5") in task_insertion.candidate_tasks
    assert PrecedenceChain in _restriction_types(neighborhood)


#############
# (Ins,2b) #
#############

def test_ins_2b(extractor, instance):
    neighborhood = extractor.extract(
        "Why doesn't Valentin do any of the tasks he currently isn't assigned, at some point in his day?"
    )
    task_insertion = next(o for o in neighborhood.operators if isinstance(o, TaskInsertion))
    valentin_tasks = {instance.get_task_by_name(name) for name in ["T1", "T2", "T3", "T4"]}
    assert len(task_insertion.candidate_tasks) > 0
    assert task_insertion.candidate_tasks.isdisjoint(valentin_tasks)


#############
# (Ins,2c) #
#############

def test_ins_2c(extractor, instance):
    neighborhood = extractor.extract("Why isn't task T5 performed by anyone at some point in the day?")
    task_insertion = next(o for o in neighborhood.operators if isinstance(o, TaskInsertion))
    assert instance.get_task_by_name("T5") in task_insertion.candidate_tasks
    assert len(task_insertion.candidate_employees) >= 1


############
# (Ins,3) #
############

def test_ins_3(extractor, instance):
    neighborhood = extractor.extract(
        "Why doesn't Valentin do task T5 in addition to his current tasks, even if it means changing their order?"
    )
    task_insertion = next(o for o in neighborhood.operators if isinstance(o, TaskInsertion))
    assert instance.get_task_by_name("T5") in task_insertion.candidate_tasks


############
# (Swp,1) #
############

def test_swp_1(extractor, instance):
    neighborhood = extractor.extract("Why isn't Valentin performing task T5 instead of task T2?")
    operator_types = _operator_types(neighborhood)
    assert TaskInsertion in operator_types and TaskDeletion in operator_types
    task_insertion = next(o for o in neighborhood.operators if isinstance(o, TaskInsertion))
    task_deletion = next(o for o in neighborhood.operators if isinstance(o, TaskDeletion))
    assert instance.get_task_by_name("T5") in task_insertion.candidate_tasks
    assert instance.get_task_by_name("T2") in task_deletion.candidate_tasks


#############
# (Swp,2a) #
#############

def test_swp_2a(extractor, instance):
    neighborhood = extractor.extract("Why isn't Valentin performing task T5 rather than one of his current tasks?")
    operator_types = _operator_types(neighborhood)
    assert TaskInsertion in operator_types and TaskDeletion in operator_types
    task_insertion = next(o for o in neighborhood.operators if isinstance(o, TaskInsertion))
    task_deletion = next(o for o in neighborhood.operators if isinstance(o, TaskDeletion))
    assert instance.get_task_by_name("T5") in task_insertion.candidate_tasks
    assert len(task_deletion.candidate_tasks) > 0


#############
# (Swp,2b) #
#############

def test_swp_2b(extractor, instance):
    neighborhood = extractor.extract(
        "Why doesn't Valentin do one of his non-performed tasks rather than one of his current tasks?"
    )
    operator_types = _operator_types(neighborhood)
    assert TaskInsertion in operator_types and TaskDeletion in operator_types
    task_insertion = next(o for o in neighborhood.operators if isinstance(o, TaskInsertion))
    task_deletion = next(o for o in neighborhood.operators if isinstance(o, TaskDeletion))
    valentin_tasks = {instance.get_task_by_name(name) for name in ["T1", "T2", "T3", "T4"]}
    assert task_insertion.candidate_tasks.isdisjoint(valentin_tasks)
    assert len(task_deletion.candidate_tasks) > 0


#############
# (Swp,2c) #
#############

def test_swp_2c(extractor, instance):
    neighborhood = extractor.extract("Why isn't task T5 performed by someone rather than one of their current tasks?")
    operator_types = _operator_types(neighborhood)
    assert TaskInsertion in operator_types and TaskDeletion in operator_types
    task_insertion = next(o for o in neighborhood.operators if isinstance(o, TaskInsertion))
    task_deletion = next(o for o in neighborhood.operators if isinstance(o, TaskDeletion))
    assert instance.get_task_by_name("T5") in task_insertion.candidate_tasks
    assert len(task_deletion.candidate_tasks) > 0


############
# (Swp,3) #
############

def test_swp_3(extractor, instance):
    neighborhood = extractor.extract(
        "Why isn't Valentin performing task T5 rather than one of his current tasks, "
        "even if it means changing the order of his day?"
    )
    operator_types = _operator_types(neighborhood)
    assert TaskInsertion in operator_types and TaskDeletion in operator_types
    task_insertion = next(o for o in neighborhood.operators if isinstance(o, TaskInsertion))
    assert instance.get_task_by_name("T5") in task_insertion.candidate_tasks


#############
# (Ord,1a) #
#############

def test_ord_1a(extractor, instance):
    neighborhood = extractor.extract("Why isn't Valentin performing task T2 later in his day, right after task T3?")
    assert TaskRepositioning in _operator_types(neighborhood)
    task_repositioning = next(o for o in neighborhood.operators if isinstance(o, TaskRepositioning))
    assert task_repositioning.target_task == instance.get_task_by_name("T2")
    assert ImmediatePrecedence in _restriction_types(neighborhood)


#############
# (Ord,1b) #
#############

def test_ord_1b(extractor, instance):
    neighborhood = extractor.extract("Why isn't Valentin performing task T3 earlier in his day, right before task T2?")
    assert TaskRepositioning in _operator_types(neighborhood)
    task_repositioning = next(o for o in neighborhood.operators if isinstance(o, TaskRepositioning))
    assert task_repositioning.target_task == instance.get_task_by_name("T3")
    assert ImmediatePrecedence in _restriction_types(neighborhood)


#############
# (Ord,2a) #
#############

def test_ord_2a(extractor, instance):
    neighborhood = extractor.extract("Why isn't Valentin performing task T2 at a later stage of his day?")
    assert TaskRepositioning in _operator_types(neighborhood)
    task_repositioning = next(o for o in neighborhood.operators if isinstance(o, TaskRepositioning))
    assert task_repositioning.target_task == instance.get_task_by_name("T2")
    assert Precedence in _restriction_types(neighborhood)


#############
# (Ord,2b) #
#############

def test_ord_2b(extractor, instance):
    neighborhood = extractor.extract("Why isn't Valentin performing task T3 at an earlier stage of his day?")
    assert TaskRepositioning in _operator_types(neighborhood)
    task_repositioning = next(o for o in neighborhood.operators if isinstance(o, TaskRepositioning))
    assert task_repositioning.target_task == instance.get_task_by_name("T3")
    assert Precedence in _restriction_types(neighborhood)


#############
# (Ord,2c) #
#############

def test_ord_2c(extractor, instance):
    neighborhood = extractor.extract("Why isn't Valentin performing task T2 at any other stage of his day?")
    assert TaskRepositioning in _operator_types(neighborhood)
    task_repositioning = next(o for o in neighborhood.operators if isinstance(o, TaskRepositioning))
    assert task_repositioning.target_task == instance.get_task_by_name("T2")
    assert ForbiddenSequence in _restriction_types(neighborhood)


############
# (Ord,3) #
############

def test_ord_3(extractor, instance):
    neighborhood = extractor.extract("Why can't Ambre's route be done in a different order?")
    assert SequenceReordering in _operator_types(neighborhood)
    sequence_reordering = next(o for o in neighborhood.operators if isinstance(o, SequenceReordering))
    assert sequence_reordering.employee == instance.get_employee_by_name("Ambre")
    assert ForbiddenSequence in _restriction_types(neighborhood)


######################
# Not coverable yet #
######################

def test_task_relocation_shaped_question_is_not_coverable(extractor):
    with pytest.raises(NeighborhoodExtractionError):
        extractor.extract("Why isn't task T2 moved from Valentin to Ambre?")
