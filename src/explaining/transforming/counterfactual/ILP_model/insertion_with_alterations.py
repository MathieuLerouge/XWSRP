# Third party libraries
from gurobipy import GRB

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.modeling.task import Task
from src.explaining.transforming.counterfactual.ILP_model.transformation_with_alterations import \
    IPModelForTransformationWithInstanceAlterations
from src.optimization.heuristics.sequence import SequenceForHeuristics


####################################################
# Class IPModelForInsertionWithInstanceAlterations #
####################################################

class IPModelForInsertionWithInstanceAlterations(IPModelForTransformationWithInstanceAlterations):
    """
    Base IP model to compute explanation content for answering counterfactual question about insertion
    """

    def __init__(self, sequence: SequenceForHeuristics, task_to_insert: Task,
                 instance_parameter_alteration_bounds: InstanceChanges = None,
                 solving_time_limit: int = None):
        """
        Return an IP model for inserting a task in the sequence while allowing instance parameter alterations

        :param sequence: the sequence to optimize (SequenceForHeuristics)
        :param task_to_insert: the task to insert (Task)
        :param instance_parameter_alteration_bounds: the bounds of instance parameter alterations (InstanceChanges)
        :param solving_time_limit: the solving time limit in seconds (int)
        """
        super().__init__(sequence, task_to_insert, instance_parameter_alteration_bounds, solving_time_limit)

    #######################################
    # Getters and setters - Entering task #
    #######################################

    @property
    def task_to_insert(self):
        """
        Return the task to insert

        :return: the task to insert (Task)
        """
        return self._pivot_task

    @property
    def task_to_insert_time_gap(self):
        """
        Return the time gap between backward and forward start times of the task to insert

        :return: the time gap between backward and forward start times of the task to insert (int)
        """
        return self.pivot_task_time_gap

    @property
    def task_to_insert_start_time(self):
        """
        Return the start time of the task to insert

        :return: the start time of the task to insert (int)
        """
        return self.pivot_task_start_time

    @property
    def task_to_insert_start_time_for_backward(self):
        """
        Return the start time of the task to insert which respects time constraints in backward direction

        :return: the backward start time of the task to insert (int)
        """
        return self.pivot_task_start_time_for_backward

    @property
    def task_to_insert_start_time_for_forward(self):
        """
        Return the start time of the task to insert which respects time constraints in forward direction

        :return: the forward start time of the task to insert (int)
        """
        return self.pivot_task_start_time_for_forward

    ######################
    # Decision variables #
    ######################

    # Decision variables are unchanged

    ######################
    # Objective function #
    ######################

    def _add_objective_function(self):
        """
        Add the objective function to the model, which minimizes according to a lexicographic order:

        - the time gap between backward and forward start times of the replacing task
        - the total sum of task duration alterations
        - the largest time alteration
        - the number of instance parameter alterations
        - the total traveling time

        :return: None
        """
        self._build_key_expressions()
        self._GRB_model.ModelSense = GRB.MINIMIZE
        objectives = [self._time_gap_expression,
                      self._total_altered_task_duration_expression, self.var_D_max, self._nb_alterations_expression,
                      self._total_traveling_time_expression]
        for index, objective in enumerate(objectives):
            self._GRB_model.setObjectiveN(objective, index, len(objectives) - 1 - index)
        self._GRB_model.update()

    #####################
    # Constraints - All #
    #####################

    # Constraints are unchanged
