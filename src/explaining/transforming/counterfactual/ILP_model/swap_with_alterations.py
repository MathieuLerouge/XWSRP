# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.transforming.counterfactual.ILP_model.transformation_with_alterations import \
    IPModelForTransformationWithInstanceAlterations
from src.modeling.task import Task
from src.optimization.heuristics.sequence import SequenceForHeuristics


#########################################
# IPModelForSwapWithInstanceAlterations #
#########################################

class IPModelForSwapWithInstanceAlterations(IPModelForTransformationWithInstanceAlterations):
    """
    Base IP model to compute explanation content for answering counterfactual question about swap
    """

    def __init__(self, sequence: SequenceForHeuristics, replacing_task: Task,
                 instance_parameter_alteration_bounds: InstanceChanges = None,
                 solving_time_limit: int = None):
        """
        Return an IP model for replacing a task of the sequence by the replacing task
        while allowing instance parameter alterations

        :param sequence: the sequence to optimize (SequenceForHeuristics)
        :param replacing_task: the replacing task (Task)
        :param instance_parameter_alteration_bounds: the bounds of instance parameter alterations (InstanceChanges)
        :param solving_time_limit: the solving time limit in seconds (int)
        """
        super().__init__(sequence, replacing_task, instance_parameter_alteration_bounds, solving_time_limit)

    ########################################
    # Getters and setters - Replacing task #
    ########################################

    @property
    def replacing_task(self):
        """
        Return the replacing task

        :return: the replacing task (Task)
        """
        return self._pivot_task

    @property
    def replacing_task_time_gap(self):
        """
        Return the time gap between backward and forward start times of the replacing task

        :return: the time gap between backward and forward start times of the replacing task (int)
        """
        return self.pivot_task_time_gap

    @property
    def replacing_task_start_time(self):
        """
        Return the start time of the replacing task

        :return: the start time of the replacing task (int)
        """
        return self.pivot_task_start_time

    @property
    def replacing_task_start_time_for_backward(self):
        """
        Return the start time of the replacing task which respects time constraints in backward direction

        :return: the backward start time of the replacing task (int)
        """
        return self.pivot_task_start_time_for_backward

    @property
    def replacing_task_start_time_for_forward(self):
        """
        Return the start time of the replacing task which respects time constraints in forward direction

        :return: the forward start time of the replacing task (int)
        """
        return self.pivot_task_start_time_for_forward

    #######################################
    # Getters and setters - Replaced task #
    #######################################

    @property
    def replaced_task(self):
        """
        Return the task replaced by the replacing task,
        which is deduced from the results of the sequence optimization

        :return: the replaced task (Task)
        """
        for task_key in self._get_candidate_tasks_keys(including_pivot_task=False):
            if not self._is_task_performed_given_key(task_key):
                return self.get_candidate_task_by_key(task_key)
        raise AttributeError("There is no solution sequence stored")

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

    # Constraints are mostly unchanged
    # Only the covering constraints are changed

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):
        """
        Add the covering constraints to the model:

        - the replacing task must be performed
        - all other tasks must be performed at most once
        - there must be as many task performed as there are tasks in the sequence before the transformation

        :return: None
        """
        # Constraint ensuring that the replacing task is performed
        j = self._pivot_task_key
        self._model.add_component(
            f"TaskCoveringConstraint[{j}]",
            pyo.Constraint(expr=(
                pyo.quicksum([self.vars_U[(j, k)]
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]) == 1
            ))
        )
        # Constraints ensuring that all other tasks are performed at most once
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"TaskCoveringConstraint[{j}]",
                pyo.Constraint(expr=(
                    pyo.quicksum([self.vars_U[(j, k)]
                                  for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                                  if k != j]) <= 1
                ))
            )
        # Constraint ensuring that there must be as many task performed as there are tasks in the sequence
        # before the transformation
        self._model.add_component(
            "GeneralCoveringConstraint",
            pyo.Constraint(expr=(
                pyo.quicksum([self.vars_U[(j, k)]
                              for j in self.get_activities_keys(including_departure=True, including_comeback=False)
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]) == self._sequence.nb_steps - 1
            ))
        )
