# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.transforming.integerprogramming.insertion import IPModelForInsertionAlteringInput
from src.modeling.sequence import Sequence
from src.modeling.task import Task


# Class IPModelForIns3
class IPModelForIns3(IPModelForInsertionAlteringInput):

    def __init__(self, sequence: Sequence, task_to_insert: Task, instance_slacks: InstanceChanges = None):
        super().__init__(sequence, task_to_insert, instance_slacks)
