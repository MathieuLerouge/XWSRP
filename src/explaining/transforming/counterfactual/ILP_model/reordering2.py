# Third party libraries
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from src.explaining.transforming.counterfactual.ILP_model.reordering_with_alterations import \
    IPModelForReorderingWithInstanceAlterations
from src.optimization.IP.sequence.basemodel import create_activity_key


#######################################################
# Class IPModelForReordering2aWithInstanceAlterations #
#######################################################

class IPModelForReordering2aWithInstanceAlterations(IPModelForReorderingWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Ord,2a) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} later in their route?"
    """

    #####################
    # Constraints - All #
    #####################

    # Constraints are mostly unchanged
    # Only constraints related to the order of activities in the sequence are changed

    #######################
    # Constraints - Order #
    #######################

    def _add_sequence_order_change_constraints(self):
        """
        Add constraints on the order of activities in the sequence:

        - the order of the activities in the first part of the sequence, before the moving task, remains unchanged
        - the order of the activities in the second part of the sequence, after the moving task, remains unchanged
        except that the moving task must be inserted in that portion

        :return: None
        """
        moving_task_step_index = self._sequence.get_step_index_of(self._pivot_task)
        activities = self._sequence.get_contained_activities()
        # Add constraints that ensure that the order of the activities before the moving task remains unchanged
        for j in range(moving_task_step_index - 1):
            self._GRB_model.addLConstr(
                self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))],
                sense=GRB.EQUAL, rhs=1, name=f"FixedArc[{activities[j]},{activities[j + 1]}]"
            )
        # Add a constraint which ensures that the employee moves from the activity before the moving task to
        # the activity after the moving task
        activity_before_moving_task = activities[moving_task_step_index - 1]
        activity_after_moving_task = activities[moving_task_step_index + 1]
        self._GRB_model.addLConstr(
            self.vars_U[(create_activity_key(activity_before_moving_task),
                         create_activity_key(activity_after_moving_task))],
            sense=GRB.EQUAL, rhs=1, name=f"FixedArc[{activity_before_moving_task},{activity_after_moving_task}]"
        )
        # Add a constraint which ensures that the order of the activities remains the same after the moving task
        # except that the moving task gets moved into this part of the sequence
        self._GRB_model.addLConstr(
            grb.quicksum([self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))]
                          for j in range(moving_task_step_index + 1, len(activities) - 1)]),
            sense=GRB.EQUAL, rhs=len(activities) - moving_task_step_index - 3,
            name=f"InsertionBetweenConsecutiveActivitiesAfterMovingTask"
        )
        self._GRB_model.update()


#######################################################
# Class IPModelForReordering2bWithInstanceAlterations #
#######################################################

class IPModelForReordering2bWithInstanceAlterations(IPModelForReorderingWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Ord,2b) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} earlier in their route?"
    """

    #####################
    # Constraints - All #
    #####################

    # Constraints are mostly unchanged
    # Only constraints related to the order of activities in the sequence are changed

    #######################
    # Constraints - Order #
    #######################

    def _add_sequence_order_change_constraints(self):
        """
        Add constraints on the order of activities in the sequence:

        - the order of the activities in the first part of the sequence, before the moving task, remains unchanged
        except that the moving task must be inserted in that portion
        - the order of the activities in the second part of the sequence, after the moving task, remains unchanged

        :return: None
        """
        moving_task_step_index = self._sequence.get_step_index_of(self._pivot_task)
        activities = self._sequence.get_contained_activities()
        # Add a constraint which ensures that the order of the activities remains the same before the moving task
        # except that the moving task gets moved into this part of the sequence
        self._GRB_model.addLConstr(
            grb.quicksum([self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))]
                          for j in range(moving_task_step_index - 1)]),
            sense=GRB.EQUAL, rhs=moving_task_step_index - 2,
            name=f"InsertionBetweenConsecutiveActivitiesBeforeMovingTask"
        )
        # Add a constraint which ensures that the employee moves from the activity before the moving task to
        # the activity after the moving task
        activity_before_moving_task = activities[moving_task_step_index - 1]
        activity_after_moving_task = activities[moving_task_step_index + 1]
        self._GRB_model.addLConstr(
            self.vars_U[(create_activity_key(activity_before_moving_task),
                         create_activity_key(activity_after_moving_task))],
            sense=GRB.EQUAL, rhs=1, name=f"FixedArc[{activity_before_moving_task},{activity_after_moving_task}]"
        )
        # Add constraints that ensure that the order of the activities after the moving task remains unchanged
        for j in range(moving_task_step_index + 1, len(activities) - 1):
            self._GRB_model.addLConstr(
                self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))],
                sense=GRB.EQUAL, rhs=1, name=f"FixedArc[{activities[j]},{activities[j + 1]}]"
            )
        self._GRB_model.update()


#######################################################
# Class IPModelForReordering2cWithInstanceAlterations #
#######################################################

class IPModelForReordering2cWithInstanceAlterations(IPModelForReorderingWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Ord,2c) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} at another position in their route?"
    """

    #####################
    # Constraints - All #
    #####################

    # Constraints are mostly unchanged
    # Only constraints related to the order of activities in the sequence are changed

    #######################
    # Constraints - Order #
    #######################

    def _add_sequence_order_change_constraints(self):
        """
        Add constraints on the order of activities in the sequence:
        the order of the activities in the first part of the sequence remains unchanged
        except that the moving task must be moved to another position in the sequence

        :return: None
        """
        moving_task_step_index = self._sequence.get_step_index_of(self._pivot_task)
        activities = self._sequence.get_contained_activities()
        # Add a constraint which ensures that the employee moves from the activity before the moving task to
        # the activity after the moving task
        activity_before_moving_task = activities[moving_task_step_index - 1]
        activity_after_moving_task = activities[moving_task_step_index + 1]
        self._GRB_model.addLConstr(
            self.vars_U[(create_activity_key(activity_before_moving_task),
                         create_activity_key(activity_after_moving_task))],
            sense=GRB.EQUAL, rhs=1, name=f"FixedArc[{activity_before_moving_task},{activity_after_moving_task}]"
        )
        # Add a constraint which ensures that the order of the activities remains the same
        # except that the moving task gets moved to another position in the sequence
        self._GRB_model.addLConstr(
            grb.quicksum([self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))]
                          for j in range(moving_task_step_index - 1)]) +
            grb.quicksum([self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))]
                          for j in range(moving_task_step_index + 1, len(activities) - 1)]),
            sense=GRB.EQUAL, rhs=len(activities) - 4, name=f"InsertionBetweenConsecutiveActivitiesAtAnotherPosition"
        )
        self._GRB_model.update()
