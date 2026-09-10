# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.computing.templates.counterfactual.ILP_model.swap_with_alterations import \
    IPModelForSwapWithInstanceAlterations
from src.modeling.task import Task
from src.optimization.heuristics.sequence import SequenceForHeuristics
from src.optimization.milp.subproblems.sequencemodel import create_activity_key


##########################################
# IPModelForSwap1WithInstanceAlterations #
##########################################

class IPModelForSwap1WithInstanceAlterations(IPModelForSwapWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Swp,1) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task1} in place of task {Task2}?"
    """

    def __init__(self, sequence: SequenceForHeuristics, replacing_task: Task, replaced_task: Task,
                 instance_parameter_alteration_bounds: InstanceChanges = None,
                 solving_time_limit: int = None):
        """
        Return an IP model for replacing a given task of the sequence by the replacing task
        while allowing instance parameter alterations

        :param sequence: the sequence to optimize (SequenceForHeuristics)
        :param replacing_task: the replacing task (Task)
        :param replaced_task: the replaced task (Task)
        :param instance_parameter_alteration_bounds: the bounds of instance parameter alterations (InstanceChanges)
        :param solving_time_limit: the solving time limit in seconds (int)
        """
        self._replaced_task = replaced_task
        super().__init__(sequence, replacing_task, instance_parameter_alteration_bounds, solving_time_limit)

    #######################################
    # Getters and setters - Replaced task #
    #######################################

    @property
    def replaced_task(self):
        """
        Return the task replaced by the replacing task

        :return: the replaced task (Task)
        """
        return self._replaced_task

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
    # Only flow and covering constraints are changed

    ######################
    # Constraints - Flow #
    ######################

    def _add_flow_constraints(self):
        """
        Add the flow constraints to the model:

        - the flow starts with a departure activity
        - the flow ends with a comeback activity
        - the flow is conserved at each activity
        - the sequence of activities remains unchanged except that the replaced task is replaced by the replacing task

        :return: None
        """
        # Add original flow constraints:
        # - the flow starts with a departure activity
        # - the flow ends with a comeback activity
        # - the flow is conserved at each activity
        super()._add_flow_constraints()
        # Add new constraints ensuring that the sequence remains unchanged except for the replaced task
        # which is replaced by the replacing task
        activities = self._sequence.get_contained_activities()
        activity_before_replacement = self._sequence.get_activity_before(self._replaced_task)
        for j in range(len(activities) - 1):
            activity_key_1 = create_activity_key(activities[j])
            activity_key_2 = create_activity_key(activities[j + 1])
            if activities[j] != activity_before_replacement and activities[j] != self._replaced_task:
                self._model.add_component(
                    f"FixedArc[{activity_key_1},{activity_key_2}]",
                    pyo.Constraint(expr=(self.vars_U[(activity_key_1, activity_key_2)] == 1))
                )
            else:
                self._model.add_component(
                    f"FixedArc[{activity_key_1},{activity_key_2}]",
                    pyo.Constraint(expr=(self.vars_U[(activity_key_1, activity_key_2)] == 0))
                )
                if activities[j] == activity_before_replacement:
                    self._model.add_component(
                        f"FixedArc[{activity_key_1},{self._pivot_task_key}]",
                        pyo.Constraint(expr=(self.vars_U[(activity_key_1, self._pivot_task_key)] == 1))
                    )
                else:
                    self._model.add_component(
                        f"FixedArc[{self._pivot_task_key},{activity_key_2}]",
                        pyo.Constraint(expr=(self.vars_U[(self._pivot_task_key, activity_key_2)] == 1))
                    )

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):
        """
        Add the covering constraints to the model:

        - the replaced task must not be performed
        - the replacing task must be performed
        - all other tasks must be performed

        :return: None
        """
        replaced_task_key = create_activity_key(self._replaced_task)
        # Constraint ensuring that the replaced task is not performed
        j = replaced_task_key
        self._model.add_component(
            f"TaskCoveringConstraint[{j}]",
            pyo.Constraint(expr=(
                pyo.quicksum([self.vars_U[(j, k)]
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]) == 0
            ))
        )
        # Constraints ensuring that all tasks (including the replacing task) except the replaced task are performed
        for j in self._get_candidate_tasks_keys(including_pivot_task=True):
            if j != replaced_task_key:
                self._model.add_component(
                    f"TaskCoveringConstraint[{j}]",
                    pyo.Constraint(expr=(
                        pyo.quicksum(
                            [self.vars_U[(j, k)]
                             for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                             if k != j]
                        ) == 1
                    ))
                )
