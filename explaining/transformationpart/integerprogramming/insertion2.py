# Third party libraries
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from explaining.explorationpart.instance_changes import InstanceChanges
from explaining.transformationpart.integerprogramming.insertion import IPModelForInsertionAlteringInput
from model.sequence import Sequence
from model.task import Task
from optimization.IP.sequence.basemodel import create_activity_key


# Class IPModelForIns2a
class IPModelForIns2a(IPModelForInsertionAlteringInput):

    def __init__(self, sequence: Sequence, task_to_insert: Task, instance_slacks: InstanceChanges = None):
        self._sequence = sequence
        super().__init__(sequence, task_to_insert, instance_slacks)

    ######################
    # Constraints - Flow #
    ######################

    def _add_flow_constraints(self):
        super()._add_flow_constraints()
        activities = self._sequence.get_contained_activities()
        self._GRB_model.addLConstr(
            grb.quicksum(
                [self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j+1]))]
                 for j in range(len(activities) - 1)]
            ),
            sense=GRB.EQUAL, rhs=len(activities) - 2,
            name=f"InsertionBetweenConsecutiveActivities"
        )
        self._GRB_model.update()
