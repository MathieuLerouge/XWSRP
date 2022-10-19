# Local libraries
from explaining.explorationpart.instance_changes import InstanceChanges
from explaining.transformationpart.integerprogramming.insertion import IPModelForInsertionAlteringInput
from model.sequence import Sequence
from model.task import Task


# Class IPModelForIns3
class IPModelForIns3(IPModelForInsertionAlteringInput):

    def __init__(self, sequence: Sequence, task_to_insert: Task, instance_slacks: InstanceChanges = None):
        super().__init__(sequence, task_to_insert, instance_slacks)
