# Standard libraries
from typing import Optional, TypeVar

# Local libraries
from src.explaining.neighborhood.neighborhood import Neighborhood
from src.explaining.neighborhood.operator import (
    SequenceReordering, TaskDeletion, TaskInsertion, TaskRepositioning
)
from src.explaining.neighborhood.primitive import Primitive
from src.explaining.neighborhood.restriction import (
    ForbiddenBackwardSubsequence, ForbiddenSequence, ImmediatePrecedence, Precedence, PrecedenceChain
)
from src.explaining.question.question import ContrastiveQuestion
from src.explaining.question.questions_templates_bank import (
    WHY_NOT_INS_1, WHY_NOT_INS_2A, WHY_NOT_INS_2B, WHY_NOT_INS_2C, WHY_NOT_INS_3,
    WHY_NOT_SWP_1, WHY_NOT_SWP_2A, WHY_NOT_SWP_2B, WHY_NOT_SWP_2C, WHY_NOT_SWP_3,
    WHY_NOT_ORD_LAT_1, WHY_NOT_ORD_EAR_1, WHY_NOT_ORD_LAT_2, WHY_NOT_ORD_EAR_2, WHY_NOT_ORD_2, WHY_NOT_ORD_3
)

# The kind of primitive filter_primitives is asked for, so that it hands back that kind rather than a bare Primitive.
SelectedPrimitive = TypeVar("SelectedPrimitive", bound=Primitive)


##############
# Recognizer #
##############

class Recognizer:
    """
    Stateless collection of static methods recovering, from a Neighborhood alone,
    the contrastive question it is the image of under Mapper.map.

    It is Mapper's inverse, and it is what lets the neighborhood computation pipeline reach the answering layer:
    the recovered question carries the template id the explanation templates are keyed by,
    and the field values they are completed with.

    Unlike TemplateComplianceChecker - which answers by family because it deliberately reads nothing but
    the primitives - a Recognizer reads the Neighborhood's own solution too, which is what tells apart the
    templates naming one candidate from those offering a whole set of them.
    """

    @staticmethod
    def recognize(neighborhood: Neighborhood) -> Optional[ContrastiveQuestion]:
        """
        Return the contrastive question the given neighborhood is the image of, or None if it is the image of none.

        Args:
            neighborhood: The neighborhood to recognize.

        Returns:
            The question whose mapping produces this neighborhood, or None if no template's shape matches.
        """
        recognition = Recognizer.recognize_template(neighborhood)
        if recognition is None:
            return None
        template_id, fields_values = recognition
        return ContrastiveQuestion(neighborhood.solution, template_id, fields_values)

    @staticmethod
    def recognize_template(neighborhood: Neighborhood) -> Optional[tuple[str, list[str]]]:
        """
        Return the template id and field values the given neighborhood is the image of, without building a question.

        Kept apart from recognize() so that callers needing only the template id - TemplateComplianceChecker,
        which reports a family - do not pay for the field-value validation ContrastiveQuestion runs.

        Args:
            neighborhood: The neighborhood to recognize.

        Returns:
            A pair made of the question template's id and the field values completing it,
            or None if no template's shape matches.
        """
        for recognize_shape in _SHAPES:
            recognition = recognize_shape(neighborhood)
            if recognition is not None:
                return recognition
        return None


###########
# Helpers #
###########


def filter_primitives(primitives: list[Primitive], primitive_type: type[SelectedPrimitive]) -> list[SelectedPrimitive]:
    """
    Return the given primitives that are instances of the given type.

    Args:
        primitives: The operators or restrictions to filter.
        primitive_type: The type to keep.

    Returns:
        The kept primitives, in their original order, typed as that same type so that callers can read
        their own fields off them.
    """
    return [primitive for primitive in primitives if isinstance(primitive, primitive_type)]


def are_all_primitives_of_types(primitives: list[Primitive], primitive_types: tuple[type[Primitive], ...]) -> bool:
    """
    Return whether every one of the given primitives is an instance of one of the given types.

    Args:
        primitives: The operators or restrictions to check.
        primitive_types: The types allowed.

    Returns:
        Whether every primitive is allowed.
    """
    return all(isinstance(primitive, primitive_types) for primitive in primitives)


def _get_lone_operator(
        neighborhood: Neighborhood, operator_type: type[SelectedPrimitive]
) -> Optional[SelectedPrimitive]:
    """
    Return the neighborhood's single operator when it is of the given type, or None otherwise.

    Args:
        neighborhood: The neighborhood to read the operator off.
        operator_type: The type the lone operator must have.

    Returns:
        The operator, or None if the neighborhood carries anything but exactly one operator of that type.
    """
    operators = neighborhood.operators
    if len(operators) != 1 or not isinstance(operators[0], operator_type):
        return None
    return operators[0]


def _targets_all_employees(candidate_employees: frozenset, neighborhood: Neighborhood) -> bool:
    """
    Return whether an operator's candidate employees are exactly all the employees of the instance.

    Args:
        candidate_employees: The operator's candidate employees.
        neighborhood: The neighborhood whose instance the employees are compared against.

    Returns:
        Whether the operator is the "any employee" kind.
    """
    employees = neighborhood.solution.instance.employees
    return len(candidate_employees) > 1 and candidate_employees == frozenset(employees)


def _targets_all_non_performed_tasks(candidate_tasks: frozenset, neighborhood: Neighborhood) -> bool:
    """
    Return whether an insertion's candidate tasks are exactly the solution's non-performed tasks.

    Args:
        candidate_tasks: The insertion's candidate tasks.
        neighborhood: The neighborhood whose solution the tasks are compared against.

    Returns:
        Whether the insertion is the "any non-performed task" kind.
    """
    non_performed_tasks = neighborhood.solution.non_performed_tasks
    return len(non_performed_tasks) > 0 and candidate_tasks == frozenset(non_performed_tasks)


def _get_lone_task_name(tasks: frozenset) -> Optional[str]:
    """Return the name of the single task of the given set, or None if it does not hold exactly one."""
    if len(tasks) != 1:
        return None
    return next(iter(tasks)).name


def _get_lone_employee_name(employees: frozenset) -> Optional[str]:
    """Return the name of the single employee of the given set, or None if it does not hold exactly one."""
    if len(employees) != 1:
        return None
    return next(iter(employees)).name


def _recognize_insertion_shape(neighborhood: Neighborhood) -> Optional[tuple[str, list[str]]]:
    """
    Return the (Ins,*) template the given neighborhood is the image of, or None if it is the image of none.

    The five templates are told apart by, in order: whether an insertion point is pinned ((Ins,1)),
    whether several employees are offered ((Ins,2c)), whether the rest of the order is kept at all ((Ins,3)),
    and whether the candidate tasks are the whole set of non-performed ones ((Ins,2b)) or a single named
    task ((Ins,2a)). The last two coincide on a solution with exactly one non-performed task, in which case
    (Ins,2b) is the reading reported.

    Args:
        neighborhood: The neighborhood to recognize.

    Returns:
        A pair made of the template id and its field values, or None.
    """
    insertion = _get_lone_operator(neighborhood, TaskInsertion)
    if insertion is None:
        return None
    restrictions = neighborhood.restrictions
    if not are_all_primitives_of_types(restrictions, (PrecedenceChain, ImmediatePrecedence)):
        return None
    candidate_employees, candidate_tasks = insertion.candidate_employees, insertion.candidate_tasks
    precedence_chains = filter_primitives(restrictions, PrecedenceChain)
    immediate_precedences = filter_primitives(restrictions, ImmediatePrecedence)
    employee_name = _get_lone_employee_name(candidate_employees)
    task_name = _get_lone_task_name(candidate_tasks)

    # (Ins,1): one pinned insertion point, so one named employee and one named task.
    if immediate_precedences:
        if len(immediate_precedences) != 1 or len(precedence_chains) != 1:
            return None
        if employee_name is None or task_name is None:
            return None
        immediate_precedence = immediate_precedences[0]
        if immediate_precedence.successor not in candidate_tasks:
            return None
        return WHY_NOT_INS_1, [employee_name, task_name, immediate_precedence.predecessor.name]

    # (Ins,2c): any employee, one named task, every employee's own order kept.
    if _targets_all_employees(candidate_employees, neighborhood):
        if task_name is None or len(precedence_chains) != len(candidate_employees):
            return None
        return WHY_NOT_INS_2C, [task_name]

    if employee_name is None:
        return None

    # (Ins,3): the order of the employee's other tasks left free too.
    if not restrictions:
        if task_name is None:
            return None
        return WHY_NOT_INS_3, [employee_name, task_name]

    if len(precedence_chains) != 1:
        return None
    # (Ins,2b) before (Ins,2a): see the docstring's note on the one-non-performed-task tie.
    if _targets_all_non_performed_tasks(candidate_tasks, neighborhood):
        return WHY_NOT_INS_2B, [employee_name]
    if task_name is None:
        return None
    return WHY_NOT_INS_2A, [employee_name, task_name]


def _recognize_swap_shape(neighborhood: Neighborhood) -> Optional[tuple[str, list[str]]]:
    """
    Return the (Swp,*) template the given neighborhood is the image of, or None if it is the image of none.

    Every (Swp,*) neighborhood pairs a one-task TaskDeletion with a TaskInsertion over the same employees.
    They are told apart by how the surviving order is kept - a PrecedenceChain leaving out one named
    outgoing task ((Swp,1)), a ForbiddenBackwardSubsequence when the outgoing task is the solver's to pick
    ((Swp,2*)), or nothing at all ((Swp,3)) - and then the same employee/task cardinalities the (Ins,*)
    templates use, with the same (Swp,2b)-over-(Swp,2a) tie resolution.

    Args:
        neighborhood: The neighborhood to recognize.

    Returns:
        A pair made of the template id and its field values, or None.
    """
    operators = neighborhood.operators
    if len(operators) != 2:
        return None
    deletions = filter_primitives(operators, TaskDeletion)
    insertions = filter_primitives(operators, TaskInsertion)
    if len(deletions) != 1 or len(insertions) != 1:
        return None
    deletion, insertion = deletions[0], insertions[0]
    if deletion.min_nb_removals != 1 or deletion.max_nb_removals != 1:
        return None
    candidate_employees, candidate_tasks = insertion.candidate_employees, insertion.candidate_tasks
    if deletion.freed_employees != candidate_employees or len(deletion.candidate_tasks) == 0:
        return None
    restrictions = neighborhood.restrictions
    if not are_all_primitives_of_types(restrictions, (PrecedenceChain, ForbiddenBackwardSubsequence)):
        return None
    precedence_chains = filter_primitives(restrictions, PrecedenceChain)
    forbidden_backward_subsequences = filter_primitives(restrictions, ForbiddenBackwardSubsequence)
    employee_name = _get_lone_employee_name(candidate_employees)
    task_name = _get_lone_task_name(candidate_tasks)

    # (Swp,3): the order of the employee's other tasks left free too.
    if not restrictions:
        if employee_name is None or task_name is None:
            return None
        return WHY_NOT_SWP_3, [employee_name, task_name]

    # A template fixes the surviving tasks' order with one mechanism or the other, never with both.
    if precedence_chains and forbidden_backward_subsequences:
        return None

    # (Swp,1): the outgoing task is named, so it is the one left out of the order kept fixed.
    if precedence_chains:
        outgoing_task_name = _get_lone_task_name(deletion.candidate_tasks)
        if len(precedence_chains) != 1 or employee_name is None or task_name is None:
            return None
        if outgoing_task_name is None or outgoing_task_name in [task.name for task in precedence_chains[0].tasks]:
            return None
        return WHY_NOT_SWP_1, [employee_name, task_name, outgoing_task_name]

    if not all(restriction.employee in deletion.freed_employees
               for restriction in forbidden_backward_subsequences):
        return None

    # (Swp,2c): any employee, one named incoming task, any currently-performed task on the way out.
    if _targets_all_employees(candidate_employees, neighborhood):
        if task_name is None or len(forbidden_backward_subsequences) != len(candidate_employees):
            return None
        return WHY_NOT_SWP_2C, [task_name]

    if employee_name is None or len(forbidden_backward_subsequences) != 1:
        return None
    # (Swp,2b) before (Swp,2a): see the docstring's note on the one-non-performed-task tie.
    if _targets_all_non_performed_tasks(candidate_tasks, neighborhood):
        return WHY_NOT_SWP_2B, [employee_name]
    if task_name is None:
        return None
    return WHY_NOT_SWP_2A, [employee_name, task_name]


def _recognize_repositioning_shape(neighborhood: Neighborhood) -> Optional[tuple[str, list[str]]]:
    """
    Return the (Ord,1*)/(Ord,2*) template the given neighborhood is the image of, or None if it is none.

    All five free a single task's position and keep every other task where it was. They are told apart by
    the one further restriction saying where the target may not stay: an ImmediatePrecedence pinning it
    next to a named task ((Ord,1a)/(Ord,1b)), a Precedence pushing it past its current neighbor
    ((Ord,2a)/(Ord,2b)), or a ForbiddenSequence ruling out its current spot only ((Ord,2c)).
    Within each pair, which side of the restriction the target sits on is what says later from earlier.

    Args:
        neighborhood: The neighborhood to recognize.

    Returns:
        A pair made of the template id and its field values, or None.
    """
    repositioning = _get_lone_operator(neighborhood, TaskRepositioning)
    if repositioning is None:
        return None
    restrictions = neighborhood.restrictions
    if not are_all_primitives_of_types(restrictions, (PrecedenceChain, ImmediatePrecedence, Precedence, ForbiddenSequence)):
        return None
    precedence_chains = filter_primitives(restrictions, PrecedenceChain)
    if len(precedence_chains) != 1:
        return None
    target_task = repositioning.target_task
    # The repositioned task is the one task whose place is up for grabs, so it is left out of the chain
    # keeping every other task of the employee's sequence where it was.
    if target_task in precedence_chains[0].tasks:
        return None
    immediate_precedences = filter_primitives(restrictions, ImmediatePrecedence)
    precedences = filter_primitives(restrictions, Precedence)
    forbidden_sequences = filter_primitives(restrictions, ForbiddenSequence)
    if len(immediate_precedences) + len(precedences) + len(forbidden_sequences) != 1:
        return None
    employee_name, target_task_name = repositioning.employee.name, target_task.name

    if immediate_precedences:
        immediate_precedence = immediate_precedences[0]
        if immediate_precedence.successor == target_task:
            return WHY_NOT_ORD_LAT_1, [employee_name, target_task_name, immediate_precedence.predecessor.name]
        if immediate_precedence.predecessor == target_task:
            return WHY_NOT_ORD_EAR_1, [employee_name, target_task_name, immediate_precedence.successor.name]
        return None

    if precedences:
        precedence = precedences[0]
        # (Ord,2a) pushes the target past its current successor, i.e. Precedence(next_task, target).
        if precedence.successor == target_task:
            return WHY_NOT_ORD_LAT_2, [employee_name, target_task_name]
        if precedence.predecessor == target_task:
            return WHY_NOT_ORD_EAR_2, [employee_name, target_task_name]
        return None

    forbidden_sequence = forbidden_sequences[0]
    if forbidden_sequence.employee != repositioning.employee or target_task not in forbidden_sequence.activities:
        return None
    return WHY_NOT_ORD_2, [employee_name, target_task_name]


def _recognize_reordering_shape(neighborhood: Neighborhood) -> Optional[tuple[str, list[str]]]:
    """
    Return (Ord,3) when the given neighborhood is its image, or None otherwise:
    a lone SequenceReordering, with the employee's own original sequence forbidden
    so the solver cannot answer with it unchanged.

    Args:
        neighborhood: The neighborhood to recognize.

    Returns:
        A pair made of the template id and its field values, or None.
    """
    reordering = _get_lone_operator(neighborhood, SequenceReordering)
    if reordering is None:
        return None
    restrictions = neighborhood.restrictions
    if len(restrictions) != 1 or not isinstance(restrictions[0], ForbiddenSequence):
        return None
    if restrictions[0].employee != reordering.employee:
        return None
    return WHY_NOT_ORD_3, [reordering.employee.name]


# The shapes the tailored pipeline's question catalogue produces, each recovering the question it came from.
_SHAPES = (
    _recognize_insertion_shape,
    _recognize_swap_shape,
    _recognize_repositioning_shape,
    _recognize_reordering_shape,
)
