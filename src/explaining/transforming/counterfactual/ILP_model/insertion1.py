# Third-party libraries
from gurobipy import GRB

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.transforming.counterfactual.ILP_model.insertion_with_alterations \
    import IPModelForInsertionWithInstanceAlterations
from src.modeling.activity import Activity
from src.modeling.task import Task
from src.optimization.IP.sequence.basemodel import create_activity_key
from src.optimization.heuristics.sequence import SequenceForHeuristics


#####################################################
# Class IPModelForInsertion1WithInstanceAlterations #
#####################################################

class IPModelForInsertion1WithInstanceAlterations(IPModelForInsertionWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Ins,1) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} just after activity {Activity}?"
    """

    def __init__(self, sequence: SequenceForHeuristics, task_to_insert: Task, activity: Activity,
                 instance_parameter_alteration_bounds: InstanceChanges = None,
                 solving_time_limit: int = None):
        """
        Return an IP model for inserting the given task in the given sequence after the given activity
        while allowing instance parameter alterations

        :param sequence: the sequence to optimize (SequenceForHeuristics)
        :param task_to_insert: the task to insert (Task)
        :param activity: the activity after which the task is inserted (Activity)
        :param instance_parameter_alteration_bounds: the bounds of instance parameter alterations (InstanceChanges)
        :param solving_time_limit: the solving time limit in seconds (int)
        """
        self._activity_before_insertion = activity
        super().__init__(sequence, task_to_insert, instance_parameter_alteration_bounds, solving_time_limit)

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
    # Only flow constraints are changed

    ######################
    # Constraints - Flow #
    ######################

    def _add_flow_constraints(self):
        """
        Add flow constraints to the model:

        - the flow starts with a departure activity
        - the flow ends with a comeback activity
        - the flow is conserved at each activity
        - the sequence of activities remains unchanged except that a task is inserted in the sequence at given position

        :return: None
        """
        # Add original flow constraints:
        # - the flow starts with a departure activity
        # - the flow ends with a comeback activity
        # - the flow is conserved at each activity
        super()._add_flow_constraints()
        # Add new constraints ensuring that the order of the activities in the sequence remains unchanged
        # from start to the activity before insertion and from the activity after insertion to the end
        activities = self._sequence.get_contained_activities()
        for j in range(len(activities) - 1):
            if activities[j] != self._activity_before_insertion:
                self._GRB_model.addLConstr(
                    self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))],
                    sense=GRB.EQUAL, rhs=1, name=f"FixedArc[{activities[j]},{activities[j + 1]}]"
                )
        # Add new constraints ensuring that the task is inserted at the right position
        self._GRB_model.addLConstr(
            self.vars_U[(create_activity_key(self._activity_before_insertion), self._pivot_task_key)],
            sense=GRB.EQUAL, rhs=1, name=f"FixedArc[{self._activity_before_insertion},{self._pivot_task}]"
        )
        activity_after_insertion = self._sequence.get_activity_after(self._activity_before_insertion)
        self._GRB_model.addLConstr(
            self.vars_U[(self._pivot_task_key, create_activity_key(activity_after_insertion))],
            sense=GRB.EQUAL, rhs=1, name=f"FixedArc[{self._pivot_task},{activity_after_insertion}]"
        )
        self._GRB_model.update()
