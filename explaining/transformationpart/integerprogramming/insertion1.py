# Third-party libraries
from gurobipy import GRB

# Local libraries
from explaining.explorationpart.instance_changes import InstanceChanges
from explaining.transformationpart.integerprogramming.insertion import IPModelForInsertionAlteringInput
from model.activity import Activity
from model.sequence import Sequence
from model.task import Task
from optimization.IP.sequence.basemodel import create_activity_key


# Class IPModelForIns1
class IPModelForIns1(IPModelForInsertionAlteringInput):

    def __init__(self, sequence: Sequence, task_to_insert: Task, activity: Activity,
                 instance_slacks: InstanceChanges = None):
        self._activity_before_insertion = activity
        self._sequence = sequence
        super().__init__(sequence, task_to_insert, instance_slacks)

    ######################
    # Constraints - Flow #
    ######################

    def _add_flow_constraints(self):
        super()._add_flow_constraints()
        activities = self._sequence.get_contained_activities()
        for j in range(len(activities) - 1):
            if activities[j] != self._activity_before_insertion:
                self._GRB_model.addLConstr(
                    self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))],
                    sense=GRB.EQUAL, rhs=1, name=f"FixedArc[{activities[j]},{activities[j + 1]}]"
                )
        self._GRB_model.update()
