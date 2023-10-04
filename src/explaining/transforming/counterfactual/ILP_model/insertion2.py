# Third party libraries
import gurobipy as grb
from gurobipy import GRB

from src.explaining.modeling.instance_changes import InstanceChanges
# Local libraries
from src.explaining.transforming.counterfactual.ILP_model.insertion_with_alterations \
    import IPModelForInsertionWithInstanceAlterations
from src.modeling.task import Task
from src.optimization.IP.sequence.basemodel import create_activity_key, LEAVING_HOME_KEY, COMING_BACK_HOME_KEY
from src.optimization.heuristics.sequence import SequenceForHeuristics


######################################################
# Class IPModelForInsertion2aWithInstanceAlterations #
######################################################

class IPModelForInsertion2aWithInstanceAlterations(IPModelForInsertionWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Ins,2a) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task}
    between two consecutive activities of their route?"
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
        - the sequence of activities remains unchanged except that a task is inserted in the sequence

        :return: None
        """
        # Add original flow constraints:
        # - ensuring that the flow starts with a departure activity
        # - ensuring that the flow ends with a comeback activity
        # - ensuring that the flow is conserved at each activity
        super()._add_flow_constraints()
        # Add a new flow constraint which ensures that the sequence of activities remains the same
        # except that a task is inserted in the sequence
        activities = self._sequence.get_contained_activities()
        self._GRB_model.addLConstr(
            grb.quicksum([self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))]
                          for j in range(len(activities) - 1)]),
            sense=GRB.EQUAL, rhs=len(activities) - 2, name=f"InsertionBetweenConsecutiveActivities"
        )
        self._GRB_model.update()


######################################################
# Class IPModelForInsertion2bWithInstanceAlterations #
######################################################

class IPModelForInsertion2bWithInstanceAlterations(IPModelForInsertionWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Ins,2b) counterfactual question:
    "How to make possible that employee {Employee} performs any non-performed task
    between two consecutive activities of their planning?"
    """

    def __init__(self, sequence: SequenceForHeuristics, non_performed_tasks: list[Task],
                 instance_parameter_alteration_bounds: InstanceChanges = None,
                 solving_time_limit: int = None):
        """
        Return an IP model for inserting a non-performed task in a sequence.

        :param sequence: the sequence to optimize (SequenceForHeuristics)
        :param non_performed_tasks: the non performed task (list[Task])
        :param instance_parameter_alteration_bounds: the bounds of instance parameter alterations (InstanceChanges)
        :param solving_time_limit: the solving time limit in seconds (int)
        """
        self._non_performed_tasks = non_performed_tasks
        super().__init__(sequence, None, instance_parameter_alteration_bounds, solving_time_limit)
        if solving_time_limit is not None:
            self.solving_time_limit = solving_time_limit

    def _compute_candidate_tasks(self):
        """
        Compute the candidate tasks i.e. the tasks that can be part of the employee's sequence

        :return: the list of candidate tasks (List[Task])
        """
        return self._sequence.get_contained_tasks() + [task for task in self._non_performed_tasks]

    #########################################
    # Getters and setters - Candidate tasks #
    #########################################

    def _get_candidate_tasks_keys(self, including_pivot_task: bool = True):
        """
        Return the list of candidate tasks keys i.e. the keys of the tasks that can be part of the employee's sequence

        :return: the list of candidate tasks keys (List[str])
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

        :return: None
        """
        # Add original flow constraints:
        # - ensuring that the flow starts with a departure activity
        # - ensuring that the flow ends with a comeback activity
        # - ensuring that the flow is conserved at each activity
        super()._add_flow_constraints()
        # Add a new flow constraint which ensures that the sequence of activities remains the same
        # except that a task is inserted in the sequence
        activities = self._sequence.get_contained_activities()
        self._GRB_model.addLConstr(
            grb.quicksum([self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))]
                          for j in range(len(activities) - 1)]),
            sense=GRB.EQUAL, rhs=len(activities) - 2, name=f"InsertionBetweenConsecutiveActivities"
        )
        self._GRB_model.update()

    ##########################
    # Constraints - Covering #
    ##########################

    def _add_covering_constraints(self):
        """
        Add the covering constraints to the model.

        :return: None
        """
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._GRB_model.addLConstr(
                grb.quicksum([self.vars_U[(j, k)]
                              for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                              if k != j]),
                sense=GRB.EQUAL, rhs=1, name=f"TaskCoveringConstraint[{j}]"
            )
        self._GRB_model.addLConstr(
            grb.quicksum([self.vars_U[(create_activity_key(task), k)]
                          for task in self._non_performed_tasks
                          for k in self.get_activities_keys(including_departure=False, including_comeback=True)
                          if k != create_activity_key(task)]),
            sense=GRB.EQUAL, rhs=1, name=f"TaskCoveringConstraintPotentialPivots"
        )

    #############################
    # Constraints - Time window #
    #############################

    def _add_time_window_constraints(self):
        """
        Add the time window constraints to the model.

        :return: None
        """
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] - self.get_candidate_task_by_key(j).start_time_LB +
                (self.vars_D_LB_t[j] if self.vars_X_LB_t[j] is not None else 0),
                sense=GRB.GREATER_EQUAL, rhs=0, name=f"TimeWindowLBConstraint[{j}]"
            )
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) -
                self.get_candidate_task_by_key(j).end_time_UB -
                (self.vars_D_UB_t[j] if self.vars_X_UB_t[j] is not None else 0),
                sense=GRB.LESS_EQUAL, rhs=0, name=f"TimeWindowUBConstraint[{j}]"
            )
        for task in self._non_performed_tasks:
            j = create_activity_key(task)
            self._GRB_model.addLConstr(
                self.var_T_backward -
                self._task_performances_expressions[j]*self.get_candidate_task_by_key(j).start_time_LB +
                (self.vars_D_LB_t[j] if self.vars_X_LB_t[j] is not None else 0),
                sense=GRB.GREATER_EQUAL, rhs=0, name=f"TimeWindowLBConstraint[{j}]"
            )
            self._GRB_model.addLConstr(
                self.var_T_forward + self.get_candidate_task_by_key(j).duration -
                (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) -
                self._task_performances_expressions[j]*self.get_candidate_task_by_key(j).end_time_UB -
                (self.vars_D_UB_t[j] if self.vars_X_UB_t[j] is not None else 0) -
                (1 - self._task_performances_expressions[j])*(24*60),
                sense=GRB.LESS_EQUAL, rhs=0, name=f"TimeWindowUBConstraint[{j}]"
            )

    ################################
    # Constraints - Sequence times #
    ################################

    def _add_sequence_times_constraints(self):
        """
        Add the sequence times constraints to the model.

        :return: None
        """
        # Add departure-to-first-task time sequence constraints
        for k in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[k] - self.get_traveling_duration(LEAVING_HOME_KEY, k) - self.employee.start_time_LB +
                (self.var_D_LB_e if self.var_X_LB_e is not None else 0),
                sense=GRB.GREATER_EQUAL, rhs=0, name=f"SequenceDepartureToTaskConstraint[{k}]"
            )
        for task in self._non_performed_tasks:
            k = create_activity_key(task)
            self._GRB_model.addLConstr(
                self.var_T_backward -
                self._task_performances_expressions[k]*self.get_traveling_duration(LEAVING_HOME_KEY, k) -
                self.employee.start_time_LB +
                (self.var_D_LB_e if self.var_X_LB_e is not None else 0),
                sense=GRB.GREATER_EQUAL, rhs=0, name=f"SequenceDepartureToTaskConstraint[{k}]"
            )
        # Add last-task-to-comeback time sequence constraints
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            self._GRB_model.addLConstr(
                self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                self.get_traveling_duration(j, COMING_BACK_HOME_KEY) - self.employee.end_time_UB -
                (self.var_D_UB_e if self.var_X_UB_e is not None else 0),
                sense=GRB.LESS_EQUAL, rhs=0, name=f"SequenceTaskToComebackConstraint[{j}]"
            )
        for task in self._non_performed_tasks:
            j = create_activity_key(task)
            self._GRB_model.addLConstr(
                self.var_T_forward + self.get_candidate_task_by_key(j).duration -
                (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                self._task_performances_expressions[j]*self.get_traveling_duration(j, COMING_BACK_HOME_KEY) -
                self.employee.end_time_UB -
                (self.var_D_UB_e if self.var_X_UB_e is not None else 0),
                sense=GRB.LESS_EQUAL, rhs=0, name=f"SequenceTaskToComebackConstraint[{j}]"
            )
        # Add task-to-task time sequence constraints
        for j in self._get_candidate_tasks_keys(including_pivot_task=False):
            for k in self._get_candidate_tasks_keys(including_pivot_task=False):
                if k != j:
                    self._GRB_model.addLConstr(
                        self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                        (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.vars_T[k] -
                        (1 - self.vars_U[(j, k)]) * 24 * 60,
                        sense=GRB.LESS_EQUAL, rhs=0, name=f"SequenceTaskToTaskConstraint[{j, k}]"
                    )
        for task in self._non_performed_tasks:
            j = create_activity_key(task)
            for k in self._get_candidate_tasks_keys(including_pivot_task=False):
                if k != j:
                    self._GRB_model.addLConstr(
                        self.var_T_forward + self.get_candidate_task_by_key(j).duration -
                        (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.vars_T[k] -
                        (1 - self.vars_U[(j, k)]) * 24 * 60,
                        sense=GRB.LESS_EQUAL, rhs=0, name=f"SequenceTaskToTaskConstraint[{j, k}]"
                    )
        for task in self._non_performed_tasks:
            k = create_activity_key(task)
            for j in self._get_candidate_tasks_keys(including_pivot_task=False):
                if k != j:
                    self._GRB_model.addLConstr(
                        self.vars_T[j] + self.get_candidate_task_by_key(j).duration -
                        (self.vars_D_dt_t[j] if self.vars_X_dt_t[j] is not None else 0) +
                        self.vars_U[(j, k)] * self.get_traveling_duration(j, k) - self.var_T_backward -
                        (1 - self.vars_U[(j, k)]) * 24 * 60,
                        sense=GRB.LESS_EQUAL, rhs=0, name=f"SequenceTaskToTaskConstraint[{j, k}]"
                    )

    #################################################
    # Data extraction from IP solving results - All #
    #################################################

    def _extract_data_from_IP_solving(self):
        """
        Extract all the data from the results obtained by solving the Integer Program

        :return: None
        """
        for task in self._non_performed_tasks:
            if self.is_task_performed(task):
                self._pivot_task = task
        self._extract_support_instance_alterations_from_IP_solving()
        self._extract_support_instance_from_IP_solving()
        self._extract_sequence_from_IP_solving()
