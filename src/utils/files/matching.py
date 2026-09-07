# Standard library
from typing import Optional

# Local library
from src.utils.files.instances import *
from src.utils.files.solutions import *


#########################
# Instance and solution #
#########################

def find_instance_file_path_corresponding_to_solution(solution_file_path: str,
                                                      instance_directory_relative_path: Optional[str] = None):
    """
    Find the path of the instance file corresponding to a solution file.

    Args:
        solution_file_path: The path of the solution file.
        instance_directory_relative_path: The relative path of the directory containing the instance files.

    Returns:
        The path of the instance file corresponding to a solution file.

    Raises:
        FileExistsError: If none of the candidate instance file paths built from the solution's metadata
            exist on disk.
    """
    meta_data = identify_meta_data_in_solution_file_path(solution_file_path)
    core, case_type, version = (
        meta_data[META_DATA_CORE_KEY], meta_data[META_DATA_CASE_KEY], meta_data[META_DATA_VERSION_KEY]
    )
    if instance_directory_relative_path is not None:
        instance_file_paths = create_instance_file_paths_with_various_extensions(
            core, version, case_type, instance_directory_relative_path
        )
        for instance_file_path in instance_file_paths:
            if path.exists(instance_file_path):
                return instance_file_path
        raise FileExistsError(f"{instance_file_paths} do not exist")
    else:
        solution_directory_path = solution_file_path[:solution_file_path.rindex('/')]
        instance_directory_relative_path = make_relative_path_from_absolute_one(solution_directory_path)
        instance_file_possible_paths_1 = create_instance_file_paths_with_various_extensions(
            core, version, case_type, instance_directory_relative_path
        )
        for instance_file_possible_path_1 in instance_file_possible_paths_1:
            if path.exists(instance_file_possible_path_1):
                return instance_file_possible_path_1
        if "solutions" in solution_file_path:
            instance_directory_relative_path = make_relative_path_from_absolute_one(
                solution_directory_path.replace("solutions", "instances")
            )
        instance_file_possible_paths_2 = create_instance_file_paths_with_various_extensions(
            core, version, case_type, instance_directory_relative_path
        )
        for instance_file_possible_path_2 in instance_file_possible_paths_2:
            if path.exists(instance_file_possible_path_2):
                return instance_file_possible_path_2
        if version is not None:
            instance_directory_relative_path = get_path_of_directory_of_instances_of_given_version(
                version, absolute_path=False
            )
        instance_file_possible_paths_3 = create_instance_file_paths_with_various_extensions(
            core, version, case_type, instance_directory_relative_path
        )
        for instance_file_possible_path_3 in instance_file_possible_paths_3:
            if path.exists(instance_file_possible_path_3):
                return instance_file_possible_path_3
        instance_file_possible_paths = list(
            set(instance_file_possible_paths_1 + instance_file_possible_paths_2 + instance_file_possible_paths_3)
        )
        if len(instance_file_possible_paths) == 1:
            raise FileExistsError(f"{instance_file_possible_paths[0]} does not exist")
        else:
            raise FileExistsError(f"{instance_file_possible_paths} do not exist")
