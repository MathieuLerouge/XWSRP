# Standard library
from os import getcwd, path, walk

# Local library
from src.utils.constants import *


#####################
# Project directory #
#####################


def get_project_directory_path():
    current_working_directory = getcwd()
    if "/src" in current_working_directory:
        index = current_working_directory.find("/src")
        return current_working_directory[:index]
    else:
        return current_working_directory


def get_default_inputs_directory_path():
    return get_project_directory_path() + f"/{INPUTS_DIRECTORY_RELATIVE_PATH}"


def get_default_outputs_directory_path():
    return get_project_directory_path() + f"/{OUTPUTS_DIRECTORY_RELATIVE_PATH}"


############
# Instance #
############


def get_instances_files_paths(directory_path: str = None):
    if directory_path is None:
        directory_path = get_default_inputs_directory_path()
    try:
        _, _, files_names_with_extensions = next(walk(directory_path))
    except StopIteration:
        raise FileNotFoundError(f"There are no instances in the directory {directory_path}")
    instances_files_paths = []
    for file_name_with_extension in files_names_with_extensions:
        if (INSTANCE_FILE_EXTENSION in file_name_with_extension and
                INSTANCE_FILE_NAME_PREFIX == file_name_with_extension[:len(INSTANCE_FILE_NAME_PREFIX)]):
            instance_file_path = directory_path + "/" + file_name_with_extension
            instances_files_paths.append(instance_file_path)
    instances_files_paths.sort()
    return instances_files_paths


def identify_meta_data_in_instance_file_name(instance_file_name: str):
    file_name_without_prefix = instance_file_name.removeprefix(INSTANCE_FILE_NAME_PREFIX)
    words = file_name_without_prefix.split(INSTANCE_VERSION_STRING)
    return {CORE_KEY: words[0], 'version': None if len(words) == 1 else int(words[1])}


def identify_meta_data_in_instance_file_path(instance_file_path: str = None):
    return identify_meta_data_in_instance_file_name(
        instance_file_path.split('/')[-1].removesuffix(INSTANCE_FILE_EXTENSION)
    )


def create_instance_file_name(core: str, version: int = None):
    if version is None:
        version_suffix = ""
    else:
        version_suffix = f"{INSTANCE_VERSION_STRING}{str(version)}"
    return f"{INSTANCE_FILE_NAME_PREFIX}{core}{version_suffix}"


def get_instance_with_version_directory_path(version: int):
    return f"{get_project_directory_path()}/{TEACHING_DATA_DIRECTORY_RELATIVE_PATH}/" \
           f"{INSTANCE_VERSION_STRING}{str(version)}/instances"


def create_instance_file_path(core: str, version: int = None, instance_directory_path: str = None):
    if instance_directory_path is None:
        if version is not None:
            instance_directory_path = get_instance_with_version_directory_path(version)
        else:
            instance_directory_path = get_default_inputs_directory_path()
    return f"{instance_directory_path}/{create_instance_file_name(core, version)}{INSTANCE_FILE_EXTENSION}"


############
# Solution #
############


def get_solution_directory_path_given_version(version: int):
    return f"{get_project_directory_path()}/{TEACHING_DATA_DIRECTORY_RELATIVE_PATH}/" \
           f"{INSTANCE_VERSION_STRING}{str(version)}/solutions"


def get_solutions_files_paths_given_meta_data(core: str, version: int, solutions_directory_path: str = None):
    if solutions_directory_path is None:
        solutions_directory_path = get_solution_directory_path_given_version(version)
    try:
        _, _, files_names_with_extensions = next(walk(solutions_directory_path))
    except StopIteration:
        raise FileNotFoundError(f"There are no corresponding solutions in the directory {solutions_directory_path}")
    solutions_files_paths = []
    core_and_version = core + INSTANCE_VERSION_STRING + str(version)
    for file_name_with_extension in files_names_with_extensions:
        if (SOLUTION_FILE_EXTENSION in file_name_with_extension and
                not(SOLUTION_ANALYSIS_FILE_NAME_SUFFIX in file_name_with_extension) and
                core_and_version in file_name_with_extension):
            solution_file_path = solutions_directory_path + "/" + file_name_with_extension
            solutions_files_paths.append(solution_file_path)
    return solutions_files_paths


def get_solutions_files_paths(directory_path: str = None):
    if directory_path is None:
        directory_path = get_default_inputs_directory_path()
    try:
        _, _, files_names_with_extensions = next(walk(directory_path))
    except StopIteration:
        raise FileNotFoundError(f"There are no solutions in the directory {directory_path}")
    solutions_files_paths = []
    for file_name_with_extension in files_names_with_extensions:
        if (SOLUTION_FILE_EXTENSION in file_name_with_extension and
                SOLUTION_FILE_NAME_PREFIX == file_name_with_extension[:len(SOLUTION_FILE_NAME_PREFIX)] and
                SOLUTION_ANALYSIS_FILE_NAME_SUFFIX not in file_name_with_extension):
            solution_file_path = directory_path + "/" + file_name_with_extension
            solutions_files_paths.append(solution_file_path)
    solutions_files_paths.sort()
    return solutions_files_paths


def identify_meta_data_in_solution_file_name(solution_file_name: str):
    file_name_without_prefix = solution_file_name.removeprefix(SOLUTION_FILE_NAME_PREFIX)
    words = file_name_without_prefix.split(INSTANCE_VERSION_STRING)
    meta_data = {CORE_KEY: None, 'version': None, 'solving method': None}
    if len(words) > 1:
        meta_data[CORE_KEY] = words[0]
        words = words[1].split(SOLUTION_METHOD_STRING)
        meta_data['version'] = int(words[0])
        if len(words) > 1:
            meta_data['solving method'] = int(words[1])
    else:
        words = words[0].split(SOLUTION_METHOD_STRING)
        meta_data[CORE_KEY] = words[0]
        if len(words) > 1:
            meta_data['solving method'] = int(words[1])
    return meta_data


def identify_meta_data_in_solution_file_path(solution_file_path: str):
    return identify_meta_data_in_solution_file_name(
        solution_file_path.split('/')[-1].removesuffix(SOLUTION_FILE_EXTENSION)
    )


#########################
# Instance and solution #
#########################


def find_instance_file_path_corresponding_to_solution(solution_file_path: str, instance_directory_path: str = None):
    meta_data = identify_meta_data_in_solution_file_path(solution_file_path)
    core, version = meta_data[CORE_KEY], meta_data['version']
    if instance_directory_path is not None:
        instance_file_path = create_instance_file_path(core, version, instance_directory_path)
        if path.exists(instance_file_path):
            return instance_file_path
        else:
            raise FileExistsError(f"{instance_file_path} does not exist")
    else:
        solution_folder_path = solution_file_path[:solution_file_path.rindex('/')]
        instance_folder_path = solution_folder_path
        instance_file_possible_path_1 = create_instance_file_path(core, version, instance_folder_path)
        if path.exists(instance_file_possible_path_1):
            return instance_file_possible_path_1
        if "solutions" in solution_file_path:
            instance_folder_path = solution_folder_path.replace("solutions", "instances")
        instance_file_possible_path_2 = create_instance_file_path(core, version, instance_folder_path)
        if path.exists(instance_file_possible_path_2):
            return instance_file_possible_path_2
        if version is not None:
            instance_folder_path = create_instance_file_path(core, version)
        instance_file_possible_path_3 = create_instance_file_path(core, version, instance_folder_path)
        if path.exists(instance_file_possible_path_3):
            return instance_file_possible_path_3
        instance_file_possible_paths = {instance_file_possible_path_1, instance_file_possible_path_2,
                                        instance_file_possible_path_3}
        raise FileExistsError(f"None of the following possible files exist: {instance_file_possible_paths}")


if __name__ == '__main__':
    instance_file_path_ex = get_instances_files_paths()[0]
    print(instance_file_path_ex)
    instance_meta_data_ex = identify_meta_data_in_instance_file_path(instance_file_path_ex)
    print(instance_meta_data_ex)
    print(create_instance_file_path(instance_meta_data_ex[CORE_KEY], instance_meta_data_ex['version']))
    print()
    solution_file_path_ex = get_solutions_files_paths()[0]
    print(solution_file_path_ex)
    solution_meta_data_ex = identify_meta_data_in_solution_file_path(solution_file_path_ex)
    print(solution_meta_data_ex)
    print()
    print(find_instance_file_path_corresponding_to_solution(solution_file_path_ex))
