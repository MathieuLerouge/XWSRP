# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.computing.templates.counterfactual.ILP_model.transformation_with_alterations import \
    IPModelForTransformationWithInstanceAlterations
from src.modeling.task import Task
from src.optimization.heuristics.sequence import SequenceForHeuristics
from src.optimization.milp.subproblems.sequencemodel import create_activity_key


###############################################
# IPModelForReorderingWithInstanceAlterations #
###############################################

class IPModelForReorderingWithInstanceAlterations(IPModelForTransformationWithInstanceAlterations):
    """
    Base IP model to compute explanation content for answering counterfactual question about reordering
    """

    def __init__(self, sequence: SequenceForHeuristics, moving_task: Task,
                 instance_parameter_alteration_bounds: InstanceChanges = None,
                 solving_time_limit: int = None):
        """
        Return an IP model for moving a task of the sequence at another position
        while allowing instance parameter alterations

        :param sequence: the sequence to optimize (SequenceForHeuristics)
        :param moving_task: the moving task (Task)
        :param instance_parameter_alteration_bounds: the bounds of instance parameter alterations (InstanceChanges)
        :param solving_time_limit: the solving time limit in seconds (int)
        """
        super().__init__(sequence, moving_task, instance_parameter_alteration_bounds, solving_time_limit)

    def _compute_candidate_tasks(self):
        """
        Compute the candidate tasks i.e. the tasks that are part of the employee's sequence

        :return: the list of candidate tasks (List[Task])
        """
        return self._sequence.get_contained_tasks()

    #####################################
    # Getters and setters - Moving task #
    #####################################

    @property
    def moving_task(self):
        """
        Return the moving task

        :return: the moving task (Task)
        """
        return self._pivot_task

    @property
    def _moving_task_key(self):
        """
        Return the key of the moving task

        :return: the key of the moving task (str)
        """
        return self._pivot_task_key

    @property
    def moving_task_time_gap(self):
        """
        Return the time gap between backward and forward start times of the moving task

        :return: the time gap between backward and forward start times of the moving task (int)
        """
        return self.pivot_task_time_gap

    @property
    def moving_task_start_time(self):
        """
        Return the start time of the moving task

        :return: the start time of the moving task (int)
        """
        return self.pivot_task_start_time

    @property
    def moving_task_start_time_for_backward(self):
        """
        Return the start time of the moving task which respects time constraints in backward direction

        :return: the backward start time of the moving task (int)
        """
        return self.pivot_task_start_time_for_backward

    @property
    def moving_task_start_time_for_forward(self):
        """
        Return the start time of the moving task which respects time constraints in forward direction

        :return: the forward start time of the moving task (int)
        """
        return self.pivot_task_start_time_for_forward

    ######################
    # Decision variables #
    ######################

    # Decision variables are unchanged

    ######################
    # Objective function #
    ######################

    # Objective function is unchanged (lexicographic, see the base class)

    #####################
    # Constraints - All #
    #####################

    def _add_constraints(self):
        """
        Add all constraints to the model including:

        - covering constraints
        - flow constraints
        - time window constraints
        - sequence times constraints
        - split time constraints
        - instance parameter alterations bounds constraints
        - sequence order change constraint
        - (no skill constraints)

        :return: None
        """
        super()._add_constraints()
        self._add_sequence_order_change_constraints()

    #######################
    # Constraints - Order #
    #######################

    def _add_sequence_order_change_constraints(self):
        """
        Add the constraints ensuring that the order of activities in the sequence changes

        :return: None
        """
        sequence = self._sequence
        self._model.add_component(
            "SequenceOrderConstraint",
            pyo.Constraint(expr=(
                pyo.quicksum([self.vars_U[(create_activity_key(sequence[j].activity),
                                           create_activity_key(sequence[j + 1].activity))]
                              for j in range(sequence.nb_steps - 1)]) <= sequence.nb_steps - 3
            ))
        )
