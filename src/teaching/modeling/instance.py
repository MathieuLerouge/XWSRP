# Local libraries
from src.modeling.instance import Instance
from src.utils.files import get_instance_version_in_instance_file_name, remove_instance_version_from_instance_file_name, \
    remove_instance_file_name_prefix


#############################
# Class InstanceForTeaching #
#############################

class InstanceForTeaching(Instance):

    def __init__(self, name: str):
        super().__init__(name)
        self._version = get_instance_version_in_instance_file_name(name)
        if self._version == 1:
            self.must_cover_all_tasks = True
        elif self._version in [2, 3]:
            self.must_cover_all_tasks = False
        else:
            raise ValueError(f"Given instance has a version {self._version} "
                             f"but its version must be either 1, 2 or 3")

    ###########
    # Version #
    ###########

    @property
    def version(self):
        return self._version

    ########
    # Name #
    ########

    @property
    def core_name(self):
        return remove_instance_file_name_prefix(remove_instance_version_from_instance_file_name(self._name))

    @property
    def core_name_with_version(self):
        if self.version is None:
            return self.core_name
        else:
            return remove_instance_file_name_prefix(self._name)

    @property
    def name_with_version(self):
        return self._name

    @property
    def name_without_version(self):
        return remove_instance_version_from_instance_file_name(self._name)
