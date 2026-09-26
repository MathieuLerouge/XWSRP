# Standard library
from typing import Optional

# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.computing.templates.counterfactual.milp.swap.base import \
    SwapWithAlterationsBaseModel
from src.modeling.task import Task
from src.optimization.heuristics.sequence import SequenceForHeuristics
from src.optimization.milp.subproblems.sequencemodel import create_activity_key, LEAVING_HOME_KEY, COMING_BACK_HOME_KEY


##############################
# Swap2aWithAlterationsModel #
##############################

class Swap2aWithAlterationsModel(SwapWithAlterationsBaseModel):
    """
    MILP model to compute explanation content for answering (Swp,2a) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} in place of one of their tasks?"
    """

    ######################
    # Decision variables #
    ######################

    # Decision variables are unchanged

    ######################
    # Objective function #
    ######################

    # Objective function is unchanged

    #####################
    # Constraints - All #
    #####################

    # Constraints are mostly unchanged
    # Only the flow constraints are changed

    ######################
    # Constraints - Flow #
    ######################

    def _add_flow_constraints(self):
        """
        Add flow constraints to the model:

        - the flow starts with a departure activity
        - the flow ends with a comeback activity
        - the flow is conserved at each activity
        - the sequence of activities remains unchanged except that one task is replaced by the replacing task
        """
        # Add original flow constraints:
        # - ensuring that the flow starts with a departure activity
        # - ensuring that the flow ends with a comeback activity
        # - ensuring that the flow is conserved at each activity
        super()._add_flow_constraints()
        # Add a new flow constraint which ensures that the sequence of activities remains the same
        # except that one task is replaced by the replacing task
        activities = self._sequence.get_contained_activities()
        self._model.add_component(
            "ReplacementBetweenConsecutiveActivities",
            pyo.Constraint(expr=(
                pyo.quicksum(
                    [self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))]
                     for j in range(len(activities) - 1)]
                ) == len(activities) - 3
            ))
        )


##############################
# Swap2bWithAlterationsModel #
##############################

class Swap2bWithAlterationsModel(SwapWithAlterationsBaseModel):
    """
    MILP model to compute explanation content for answering (Swp,2b) counterfactual question:
    "How to make possible that employee {Employee} performs any non-performed task in place of one of their tasks?"
    """

    def __init__(self, sequence: SequenceForHeuristics, non_performed_tasks: list[Task],
                 instance_parameter_alteration_bounds: Optional[InstanceChanges] = None,
                 solving_time_limit: Optional[int] = None):
        """
        Return a MILP model for swapping a non-performed task in a sequence.

        Args:
            sequence: The sequence to optimize.
            non_performed_tasks: The non performed task.
            instance_parameter_alteration_bounds: The bounds of instance parameter alterations.
            solving_time_limit: The solving time limit in seconds.
        """
        self._non_performed_tasks = non_performed_tasks
        super().__init__(sequence, None, instance_parameter_alteration_bounds, solving_time_limit)
        if solving_time_limit is not None:
            self.solving_time_limit = solving_time_limit

    def _compute_candidate_tasks(self):
        """
        Compute the candidate tasks i.e. the tasks that can be part of the employee's sequence

        Returns:
            The list of candidate tasks.
        """
        return self._sequence.get_contained_tasks() + [task for task in self._non_performed_tasks]

    #########################################
    # Getters and setters - Candidate tasks #
    #########################################

    def _get_candidate_tasks_keys(self, including_pivot_task: bool = True):
        """
        Return the list of candidate tasks keys i.e. the keys of the tasks that can be part of the employee's sequence

        Returns:
            The list of candidate tasks keys.
        """
        if including_pivot_task:
            return [task.name for task in self.candidate_tasks]
        else:
            return [task.name for task in self.candidate_tasks if task not in self._non_performed_tasks]

    ######################
    # Decision variables #
    ######################

    # Decision variables are unchanged

    ######################
    # Objective function #
    ######################

    # Objective function is unchanged

    #####################
    # Constraints - All #
    #####################

    # Constraints are mostly unchanged
    # Only the flow and covering constraints are changed

    ######################
    # Constraints - Flow #
    ######################

    def _add_flow_constraints(self):
        """
        Add flow constraints to the model:

        - the flow starts with a departure activity
        - the flow ends with a comeback activity
        - the flow is conserved at each activity
        - the sequence of activities remains unchanged except that a task is inserted in the sequence
        """
        # Add original flow constraints:
        # - ensuring that the flow starts with a departure activity
        # - ensuring that the flow ends with a comeback activity
        # - ensuring that the flow is conserved at each activity
        super()._add_flow_constraints()
        # Add a new flow constraint which ensures that the sequence of activities remains the same
        # except that a task is inserted in the sequence
        activities = self._sequence.get_contained_activities()
        self._model.add_component(
            "SwapBetweenConsecutiveActivities",
            pyo.Constraint(expr=(
                pyo.quicksum(
                    [self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))]
                     for j in range(len(activities) - 1)]
                ) == len(activities) - 3
            ))
        )

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):
        """
        Add the covering constraints to the model.
        """
        activities = self._sequence.get_contained_activities()
        self._model.add_component(
            "PerformedTaskCoveringConstraint",
            pyo.Constraint(expr=(
                pyo.quicksum([self.vars_U[(j, k)]
                              for j in self._get_candidate_tasks_keys(including_pivot_task=False)
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]) == len(activities) - 3
            ))
        )
        self._model.add_component(
            "TaskCoveringConstraintPotentialPivots",
            pyo.Constraint(expr=(
                pyo.quicksum([self.vars_U[(create_activity_key(task), k)]
                              for task in self._non_performed_tasks
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != create_activity_key(task)]) == 1
            ))
        )

    #############################
    # Constraints - Time window #
    #############################

    def _add_time_window_constraints(self):
        """
        Add the time window constraints to the model.
        """
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"TimeWindowLBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_lb +
                    (self.vars_D_LB_t[j] if self.vars_X_LB_t[j] is not None else 0) >= 0
                ))
            )
            self._model.add_component(
                f"TimeWindowUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                    (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) -
                    self.get_candidate_task_by_key(j).end_time_ub -
                    (self.vars_D_UB_t[j] if self.vars_X_UB_t[j] is not None else 0) <= 0
                ))
            )
        for task in self._non_performed_tasks:
            j = create_activity_key(task)
            self._model.add_component(
                f"TimeWindowLBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.var_T_backward -
                    self._task_performances_expressions[j] * self.get_candidate_task_by_key(j).start_time_lb +
                    (self.vars_D_LB_t[j] if self.vars_X_LB_t[j] is not None else 0) >= 0
                ))
            )
            self._model.add_component(
                f"TimeWindowUBConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.var_T_forward + self.get_candidate_task_by_key(j).duration -
                    (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) -
                    self._task_performances_expressions[j] * self.get_candidate_task_by_key(j).end_time_ub -
                    (self.vars_D_UB_t[j] if self.vars_X_UB_t[j] is not None else 0) -
                    (1 - self._task_performances_expressions[j]) * (24 * 60) <= 0
                ))
            )

    ################################
    # Constraints - Sequence times #
    ################################

    def _add_sequence_times_constraints(self):
        """
        Add the sequence times constraints to the model.
        """
        # Add departure-to-first-task time sequence constraints
        for k in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"SequenceDepartureToTaskConstraint[{k}]",
                pyo.Constraint(expr=(
                    self.vars_T[k] - self.get_traveling_duration(LEAVING_HOME_KEY, k) - self.employee.start_time_lb +
                    (self.var_D_LB_e if self.var_X_LB_e is not None else 0) >= 0
                ))
            )
        for task in self._non_performed_tasks:
            k = create_activity_key(task)
            self._model.add_component(
                f"SequenceDepartureToTaskConstraint[{k}]",
                pyo.Constraint(expr=(
                    self.var_T_backward -
                    self._task_performances_expressions[k] * self.get_traveling_duration(LEAVING_HOME_KEY, k) -
                    self.employee.start_time_lb +
                    (self.var_D_LB_e if self.var_X_LB_e is not None else 0) >= 0
                ))
            )
        # Add last-task-to-comeback time sequence constraints
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._model.add_component(
                f"SequenceTaskToComebackConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                    (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                    self.get_traveling_duration(j, COMING_BACK_HOME_KEY) - self.employee.end_time_ub -
                    (self.var_D_UB_e if self.var_X_UB_e is not None else 0) <= 0
                ))
            )
        for task in self._non_performed_tasks:
            j = create_activity_key(task)
            self._model.add_component(
                f"SequenceTaskToComebackConstraint[{j}]",
                pyo.Constraint(expr=(
                    self.var_T_forward + self.get_candidate_task_by_key(j).duration -
                    (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                    self._task_performances_expressions[j] * self.get_traveling_duration(j, COMING_BACK_HOME_KEY) -
                    self.employee.end_time_ub -
                    (self.var_D_UB_e if self.var_X_UB_e is not None else 0) <= 0
                ))
            )
        # Add task-to-task time sequence constraints
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            for k in self._get_candidate_tasks_keys(including_pivot_task=False):
                if k != j:
                    self._model.add_component(
                        f"SequenceTaskToTaskConstraint[{j, k}]",
                        pyo.Constraint(expr=(
                            self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                            (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                            self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.vars_T[k] -
                            (1 - self.vars_U[(j, k)]) * 24 * 60 <= 0
                        ))
                    )
        for task in self._non_performed_tasks:
            j = create_activity_key(task)
            for k in self._get_candidate_tasks_keys(including_pivot_task=False):
                if k != j:
                    self._model.add_component(
                        f"SequenceTaskToTaskConstraint[{j, k}]",
                        pyo.Constraint(expr=(
                            self.var_T_forward + self.get_candidate_task_by_key(j).duration -
                            (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                            self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.vars_T[k] -
                            (1 - self.vars_U[(j, k)]) * 24 * 60 <= 0
                        ))
                    )
        for task in self._non_performed_tasks:
            k = create_activity_key(task)
            for j in self._get_candidate_tasks_keys(including_pivot_task=False):
                if k != j:
                    self._model.add_component(
                        f"SequenceTaskToTaskConstraint[{j, k}]",
                        pyo.Constraint(expr=(
                            self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                            (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                            self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.var_T_backward -
                            (1 - self.vars_U[(j, k)]) * 24 * 60 <= 0
                        ))
                    )

    ###################################################
    # Data extraction from MILP solving results - All #
    ###################################################

    def _extract_data_from_milp_solving(self):
        """
        Extract all the data from the results obtained by solving the Integer Program
        """
        for task in self._non_performed_tasks:
            if self.is_task_performed(task):
                self._pivot_task = task
        self._extract_support_instance_alterations_from_milp_solving()
        self._extract_support_instance_from_milp_solving()
        self._extract_sequence_from_milp_solving()
