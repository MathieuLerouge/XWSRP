# Third-party library
import pyomo.environ as pyo

# Local libraries
from src.explaining.modeling.instance_changes import InstanceChanges
from src.explaining.transforming.counterfactual.ILP_model.reordering_with_alterations import \
    IPModelForReorderingWithInstanceAlterations
from src.modeling.task import Task
from src.optimization.heuristics.sequence import SequenceForHeuristics
from src.optimization.milp.subproblems.sequencemodel import create_activity_key


#################################################
# IPModelForReordering1aWithInstanceAlterations #
#################################################

class IPModelForReordering1aWithInstanceAlterations(IPModelForReorderingWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Ord,1a) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} later in their route,
    just after task {Task2}?"
    """

    def __init__(self, sequence: SequenceForHeuristics, moving_task: Task, fixed_task: Task,
                 instance_parameter_alteration_bounds: InstanceChanges = None,
                 solving_time_limit: int = None):
        """
        Return an IP model for moving a task of the sequence after another task of the sequence.
        while allowing instance parameter alterations

        :param sequence: the sequence to optimize (SequenceForHeuristics)
        :param moving_task: the moving task (Task)
        :param fixed_task: the task after which the moving task is moved (Task)
        :param instance_parameter_alteration_bounds: the bounds of instance parameter alterations (InstanceChanges)
        :param solving_time_limit: the solving time limit in seconds (int)
        """
        self._fixed_task = fixed_task
        super().__init__(sequence, moving_task, instance_parameter_alteration_bounds, solving_time_limit)

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
        the order of the activities of the sequence remains unchanged
        except that the moving task must be inserted after the fixed task

        :return: None
        """
        moving_task_step_index = self._sequence.get_step_index_of(self._pivot_task)
        fixed_task_step_index = self._sequence.get_step_index_of(self._fixed_task)
        activities = self._sequence.get_contained_activities()
        # Add constraints that ensure that the order of the activities before the moving task remains unchanged
        for j in range(moving_task_step_index - 1):
            self._model.add_component(
                f"FixedArc[{activities[j]},{activities[j + 1]}]",
                pyo.Constraint(expr=(
                    self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))] == 1
                ))
            )
        # Add a constraint which ensures that the employee moves
        # from the activity before the moving task to the activity after the moving task
        activity_before_moving_task = activities[moving_task_step_index - 1]
        activity_after_moving_task = activities[moving_task_step_index + 1]
        self._model.add_component(
            f"FixedArc[{activity_before_moving_task},{activity_after_moving_task}]",
            pyo.Constraint(expr=(
                self.vars_U[(create_activity_key(activity_before_moving_task),
                             create_activity_key(activity_after_moving_task))] == 1
            ))
        )
        # Add constraints that ensure that the order of the activities
        # after the moving task to the fixed task remains unchanged
        for j in range(moving_task_step_index + 1, fixed_task_step_index):
            self._model.add_component(
                f"FixedArc[{activities[j]},{activities[j + 1]}]",
                pyo.Constraint(expr=(
                    self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))] == 1
                ))
            )
        # Add constraint which ensures that the employee moves from the fixed task to the moving task
        # and from the moving task to the activity after the fixed task
        self._model.add_component(
            f"FixedArc[{self._fixed_task},{self.moving_task}]",
            pyo.Constraint(expr=(
                self.vars_U[(create_activity_key(self._fixed_task), self._moving_task_key)] == 1
            ))
        )
        activity_after_fixed_task = self._sequence.get_activity_after(self._fixed_task)
        self._model.add_component(
            f"FixedArc[{self.moving_task},{activity_after_fixed_task}]",
            pyo.Constraint(expr=(
                self.vars_U[(self._moving_task_key, create_activity_key(activity_after_fixed_task))] == 1
            ))
        )
        # Add constraints that ensure that the order of the activities
        # after the fixed task to the end of the sequence remains unchanged
        for j in range(fixed_task_step_index + 1, len(activities) - 1):
            self._model.add_component(
                f"FixedArc[{activities[j]},{activities[j + 1]}]",
                pyo.Constraint(expr=(
                    self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))] == 1
                ))
            )


#################################################
# IPModelForReordering1bWithInstanceAlterations #
#################################################

class IPModelForReordering1bWithInstanceAlterations(IPModelForReorderingWithInstanceAlterations):
    """
    IP model to compute explanation content for answering (Ord,1b) counterfactual question:
    "How to make possible that employee {Employee} performs task {Task} earlier in their route,
    just before task {Task2}?"
    """

    def __init__(self, sequence: SequenceForHeuristics, moving_task: Task, fixed_task: Task,
                 instance_parameter_alteration_bounds: InstanceChanges = None,
                 solving_time_limit: int = None):
        """
        Return an IP model for moving a task of the sequence after another task of the sequence.
        while allowing instance parameter alterations

        :param sequence: the sequence to optimize (SequenceForHeuristics)
        :param moving_task: the moving task (Task)
        :param fixed_task: the task before which the moving task is moved (Task)
        :param instance_parameter_alteration_bounds: the bounds of instance parameter alterations (InstanceChanges)
        :param solving_time_limit: the solving time limit in seconds (int)
        """
        self._fixed_task = fixed_task
        super().__init__(sequence, moving_task, instance_parameter_alteration_bounds, solving_time_limit)

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
        the order of the activities of the sequence remains unchanged
        except that the moving task must be inserted before the fixed task

        :return: None
        """
        moving_task_step_index = self._sequence.get_step_index_of(self._pivot_task)
        fixed_task_step_index = self._sequence.get_step_index_of(self._fixed_task)
        activities = self._sequence.get_contained_activities()
        # Add constraints that ensure that the order of the activities before the fixed task remains unchanged
        for j in range(fixed_task_step_index - 1):
            self._model.add_component(
                f"FixedArc[{activities[j]},{activities[j + 1]}]",
                pyo.Constraint(expr=(
                    self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))] == 1
                ))
            )
        # Add a constraint which ensures that the employee moves
        # from the activity before the fixed task to the moving task
        # and from the moving task to the fixed task
        activity_before_fixed_task = activities[fixed_task_step_index - 1]
        self._model.add_component(
            f"FixedArc[{activity_before_fixed_task},{self.moving_task}]",
            pyo.Constraint(expr=(
                self.vars_U[(create_activity_key(activity_before_fixed_task), self._moving_task_key)] == 1
            ))
        )
        self._model.add_component(
            f"FixedArc[{self.moving_task},{self._fixed_task}]",
            pyo.Constraint(expr=(
                self.vars_U[(self._moving_task_key, create_activity_key(self._fixed_task))] == 1
            ))
        )
        # Add constraints that ensure that the order of the activities
        # from the fixed task to before the moving task remains unchanged
        for j in range(fixed_task_step_index, moving_task_step_index - 1):
            self._model.add_component(
                f"FixedArc[{activities[j]},{activities[j + 1]}]",
                pyo.Constraint(expr=(
                    self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))] == 1
                ))
            )
        # Add a constraint which ensures that the employee moves
        # from the activity before the moving task to the activity after the moving task
        activity_before_moving_task = activities[moving_task_step_index - 1]
        activity_after_moving_task = activities[moving_task_step_index + 1]
        self._model.add_component(
            f"FixedArc[{activity_before_moving_task},{activity_after_moving_task}]",
            pyo.Constraint(expr=(
                self.vars_U[(create_activity_key(activity_before_moving_task),
                             create_activity_key(activity_after_moving_task))] == 1
            ))
        )
        # Add constraints that ensure that the order of the activities
        # after the moving task to the end of the sequence remains unchanged
        for j in range(moving_task_step_index + 1, len(activities) - 1):
            self._model.add_component(
                f"FixedArc[{activities[j]},{activities[j + 1]}]",
                pyo.Constraint(expr=(
                    self.vars_U[(create_activity_key(activities[j]), create_activity_key(activities[j + 1]))] == 1
                ))
            )
