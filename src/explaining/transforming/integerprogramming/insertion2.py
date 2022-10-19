# Third party libraries
import gurobipy as grb
from gurobipy import GRB

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.transforming.integerprogramming.insertion import IPModelForInsertionAlteringInput
from src.modeling.sequence import Sequence
from src.modeling.task import Task
from src.optimization.IP.sequence.basemodel import create_activity_key


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
