# Standard library
from os import walk, path

# Local library
from src.utils.constants import *


############
# Instance #
############

def get_instances_files_names(instances_directory: str = None):
    if instances_directory is None:
        instances_directory = INPUTS_DIRECTORY
    try:
        _, _, files_names = next(walk(instances_directory))
    except StopIteration:
        raise FileNotFoundError(f"There are no instances in the directory {instances_directory}")
    instances_files_names = []
    for file_name in files_names:
        if INSTANCE_FILENAME_EXTENSION in file_name and INSTANCE_FILENAME_PREFIX in file_name:
            extended_file_name = instances_directory + "/" + file_name
            instances_files_names.append(extended_file_name)
    instances_files_names.sort()
    return instances_files_names


def extract_data_from_instance_filename(instance_filename: str = None, ignore_version: bool = False):
    if not ignore_version and not (INSTANCE_VERSION_STRING in instance_filename):
        raise ValueError(f"The given instance filename {instance_filename} is incorrect, "
                         f"it does not contain {INSTANCE_VERSION_STRING} to signal the instance version")
    words = instance_filename.split('/')[-1].\
        removeprefix(INSTANCE_FILENAME_PREFIX).\
        removesuffix(INSTANCE_FILENAME_EXTENSION).\
        split(INSTANCE_VERSION_STRING)
    region_name = words[0]
    if ignore_version:
        instance_version = None
    else:
        instance_version = int(words[1])
    return region_name, instance_version


def create_instance_filename(region_name: str, instance_version: int = None, instance_directory: str = None):
    if instance_directory is None:
        instance_directory = (INSTANCES_SETS_DIRECTORY + "/" +
                              INSTANCE_SET_NAME_PREFIX + INSTANCE_VERSION_STRING + str(instance_version))
    if instance_version is None:
        instance_version_id = ""
    else:
        instance_version_id = INSTANCE_VERSION_STRING + str(instance_version)
    return (instance_directory + "/" + INSTANCE_FILENAME_PREFIX + region_name +
            instance_version_id + INSTANCE_FILENAME_EXTENSION)


############
# Solution #
############

def get_solutions_files_names(solutions_directory: str = None):
    if solutions_directory is None:
        solutions_directory = INPUTS_DIRECTORY
    try:
        _, _, files_names = next(walk(solutions_directory))
    except StopIteration:
        raise FileNotFoundError(f"There are no solutions in the directory {solutions_directory}")
    solutions_files_names = []
    for file_name in files_names:
        if (SOLUTION_FILENAME_EXTENSION in file_name and
                SOLUTION_FILENAME_PREFIX in file_name and
                not (SOLUTION_ANALYSIS_FILENAME_SUFFIX in file_name)):
            extended_file_name = solutions_directory + "/" + file_name
            solutions_files_names.append(extended_file_name)
    solutions_files_names.sort()
    return solutions_files_names


def extract_data_from_solution_filename(solution_filename: str,
                                        ignore_instance_version: bool = False, ignore_solving_method: bool = False):
    if not ignore_solving_method and not (SOLUTION_METHOD_STRING in solution_filename):
        raise ValueError(f"The given solution filename {solution_filename} is incorrect, "
                         f"it does not contain {SOLUTION_METHOD_STRING} to signal the solving method")
    words = solution_filename.split('/')[-1].\
        removeprefix(SOLUTION_FILENAME_PREFIX). \
        removesuffix(SOLUTION_FILENAME_EXTENSION). \
        split(SOLUTION_METHOD_STRING)
    if ignore_solving_method:
        solving_method_id = None
    else:
        solving_method_id = words[-1]

    if not ignore_instance_version and not (INSTANCE_VERSION_STRING in words[0]):
        raise ValueError(f"The given solution filename {solution_filename} is incorrect, "
                         f"it does not contain {INSTANCE_VERSION_STRING} to signal the instance version")
    words = words[0].split(INSTANCE_VERSION_STRING)
    if ignore_instance_version:
        instance_version = None
    else:
        instance_version = int(words[1])
    region_name = words[0]
    return region_name, instance_version, solving_method_id


#########################
# Instance and solution #
#########################

def find_specific_solutions_files_names(instance_version: int, region_name: str, solutions_directory: str = None):
    if solutions_directory is None:
        solutions_directory = (SOLUTIONS_SETS_DIRECTORY + "/" +
                               INSTANCE_SET_NAME_PREFIX + INSTANCE_VERSION_STRING + str(instance_version))
    try:
        _, _, files_names = next(walk(solutions_directory))
    except StopIteration:
        raise FileNotFoundError(f"There are no corresponding solutions in the directory {solutions_directory}")
    solutions_files_names = []
    extended_region_name = region_name + INSTANCE_VERSION_STRING + str(instance_version)
    for file_name in files_names:
        if (SOLUTION_FILENAME_EXTENSION in file_name and not(SOLUTION_ANALYSIS_FILENAME_SUFFIX in file_name) and
                extended_region_name in file_name):
            extended_file_name = solutions_directory + "/" + file_name
            solutions_files_names.append(extended_file_name)
    return solutions_files_names


def find_instance_filename_corresponding_to_solution(solution_filename: str = None, instance_directory: str = None,
                                                     ignore_instance_version: bool = False,
                                                     ignore_solving_method: bool = False):
    region_name, instance_version, _ = extract_data_from_solution_filename(
        solution_filename, ignore_instance_version, ignore_solving_method
    )
    if instance_directory is None:
        instance_directory = INPUTS_DIRECTORY
    instance_file_name_1 = create_instance_filename(region_name, instance_version, instance_directory)
    instance_file_name_2_1 = create_instance_filename(region_name, instance_version, INPUTS_DIRECTORY)
    instance_file_name_2_2 = create_instance_filename(region_name, instance_version)
    if path.exists(instance_file_name_1):
        return instance_file_name_1
    elif path.exists(instance_file_name_2_1):
        return instance_file_name_2_1
    elif path.exists(instance_file_name_2_2):
        return instance_file_name_2_2
    else:
        raise FileExistsError(f"Neither {instance_file_name_1}, nor {instance_file_name_2_1}, "
                              f"nor {instance_file_name_2_2} exist")
