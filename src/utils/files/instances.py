# Standard library
from os import listdir, path
from typing import Optional

# Local library
from src.utils.constants import *
from src.utils.files.general import *


############
# Instance #
############

def is_an_instance_file_name(file_name: str):
    """
    Check if a file name is an instance file name (with or without extension).

    Args:
        file_name: The name of the file (with or without extension).

    Returns:
        True if the file name is an instance file name, False otherwise.
    """
    for prefix in INSTANCE_FILE_NAME_POSSIBLE_PREFIXES:
        if prefix == file_name[:len(prefix)]:
            return True
    return False


def is_an_instance_file_name_with_extension(file_name_with_extension: str):
    """
    Check if a file name is an instance file name.

    NB: the file name must have an extension.

    Args:
        file_name_with_extension: The name of the file with its extension.

    Returns:
        True if the file name is an instance file name, False otherwise.

    Raises:
        ValueError: If file_name_with_extension has no extension.
    """
    if not has_a_file_extension(file_name_with_extension):
        raise ValueError(f"The file name {file_name_with_extension} has no extension")
    if get_file_extension(file_name_with_extension) in INSTANCE_FILE_POSSIBLE_EXTENSIONS:
        for prefix in INSTANCE_FILE_NAME_POSSIBLE_PREFIXES:
            if prefix == file_name_with_extension[:len(prefix)]:
                return True
    return False


def get_instance_file_name_case_type(file_name: str):
    """
    Get the case type of instance file name (with or without extension).

    Args:
        file_name: The name of the file (with or without extension).

    Returns:
        The case type of the instance file name.

    Raises:
        ValueError: If file_name isn't an instance file name, or if its case is neither CamelCase nor
            snake_case.
    """
    if not is_an_instance_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not an instance file name")
    if INSTANCE_NAME_PREFIX in file_name:
        return SNAKE_CASE
    elif INSTANCE_NAME_PREFIX_BIS in file_name:
        return CAMEL_CASE
    else:
        raise ValueError(f"The case of thr file name {file_name} is neither CamelCase nor snake_case")


def remove_instance_file_name_prefix(file_name: str):
    """
    Remove the prefix of an instance file name (with or without extension).

    Args:
        file_name: The name of the file (with or without extension).

    Returns:
        The name of the file without its prefix.

    Raises:
        ValueError: If file_name isn't an instance file name, or if its case type isn't supported.
    """
    if not is_an_instance_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not an instance file name")
    case_type = get_instance_file_name_case_type(file_name)
    if case_type == SNAKE_CASE:
        return file_name[len(INSTANCE_NAME_PREFIX):]
    elif case_type == CAMEL_CASE:
        return file_name[len(INSTANCE_NAME_PREFIX_BIS):]
    else:
        raise ValueError(f"The case type {case_type} is not supported")


def does_instance_file_name_mention_version(file_name: str):
    """
    Check if an instance file name mentions a version.

    Args:
        file_name: The name of the instance file.

    Returns:
        True if the instance file name mentions a version, False otherwise.

    Raises:
        ValueError: If file_name isn't an instance file name.
    """
    if not is_an_instance_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not an instance file name")
    if INSTANCE_VERSION_SYMBOL in file_name:
        index = file_name.rindex(INSTANCE_VERSION_SYMBOL)
        return file_name[index + len(INSTANCE_VERSION_SYMBOL)].isnumeric()
    else:
        return False


def get_instance_version_in_instance_file_name(file_name: str):
    """
    Get the version of an instance file name (with or without extension).

    Args:
        file_name: The name of the instance file (with or without extension).

    Returns:
        The version of the instance file name.

    Raises:
        ValueError: If file_name isn't an instance file name, or if it doesn't mention a version.
    """
    if not is_an_instance_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not an instance file name")
    if not does_instance_file_name_mention_version(file_name):
        raise ValueError(f"The file name {file_name} does not mention a version")
    return int(file_name[file_name.find(INSTANCE_VERSION_SYMBOL) + 1])


def remove_instance_version_from_instance_file_name(file_name: str):
    """
    Remove the version of an instance file name (with or without extension).

    Args:
        file_name: The name of the instance file (with or without extension).

    Returns:
        The instance file name without the version.

    Raises:
        ValueError: If file_name isn't an instance file name, or if it doesn't mention a version.
    """
    if not is_an_instance_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not an instance file name")
    if not does_instance_file_name_mention_version(file_name):
        raise ValueError(f"The file name {file_name} does not mention a version")
    index = file_name.index(INSTANCE_VERSION_SYMBOL)
    return file_name[:index] + file_name[index + 2:]


def get_core_in_instance_file_name(file_name: str):
    """
    Get the core of an instance file name.

    Args:
        file_name: The name of the file.

    Returns:
        The core of the instance file name.
    """
    if does_instance_file_name_mention_version(file_name):
        file_name = remove_instance_version_from_instance_file_name(file_name)
    file_name = remove_instance_file_name_prefix(file_name)
    if has_a_file_extension(file_name):
        file_name = remove_file_extension(file_name)
    return file_name


def get_instance_name_in_instance_file_name(file_name: str):
    """
    Get the instance name from its file name (with or without extension).

    Args:
        file_name: The name of the file (with or without extension).

    Returns:
        The name of the instance file name.

    Raises:
        ValueError: If file_name isn't an instance file name.
    """
    if not is_an_instance_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not an instance file name")
    if has_a_file_extension(file_name):
        file_name = remove_file_extension(file_name)
    return file_name


def get_instance_name_in_instance_file_path(file_path: str):
    """
    Get the instance name from its file path.

    Args:
        file_path: The path of the file.

    Returns:
        The name of the instance file name.
    """
    return get_instance_name_in_instance_file_name(get_file_name_from_path(file_path, with_extension=True))


def identify_meta_data_in_instance_file_name(file_name_with_extension: str):
    """
    Identify the metadata in an instance file name.

    Args:
        file_name_with_extension: The name of the instance file with its extension.

    Returns:
        The metadata of the instance file.
    """
    core = get_core_in_instance_file_name(file_name_with_extension)
    case_type = get_instance_file_name_case_type(file_name_with_extension)
    if does_instance_file_name_mention_version(file_name_with_extension):
        version = get_instance_version_in_instance_file_name(file_name_with_extension)
    else:
        version = None
    return {META_DATA_CORE_KEY: core, META_DATA_CASE_KEY: case_type, META_DATA_VERSION_KEY: version}


def identify_meta_data_in_instance_file_path(file_path: str):
    """
    Identify the metadata in an instance file path.

    Args:
        file_path: The path of the instance file.

    Returns:
        The metadata of the instance file.
    """
    return identify_meta_data_in_instance_file_name(file_path.split('/')[-1])


def create_instance_file_name(core: str, version: Optional[int] = None, case_type: str = SNAKE_CASE):
    """
    Create an instance file name from its core, its version and its case type.

    Args:
        core: The core of the instance file name.
        version: The version of the instance file name.
        case_type: The case type of the instance file name.

    Returns:
        The instance file name.

    Raises:
        ValueError: If case_type isn't supported.
    """
    if version is None:
        version_suffix = ""
    else:
        version_suffix = f"{INSTANCE_VERSION_SYMBOL}{str(version)}"
    if case_type == SNAKE_CASE:
        instance_file_name_prefix = INSTANCE_NAME_PREFIX
    elif case_type == CAMEL_CASE:
        instance_file_name_prefix = INSTANCE_NAME_PREFIX_BIS
    else:
        raise ValueError(f"The case type {case_type} is not supported")
    return f"{instance_file_name_prefix}{core}{version_suffix}"


def create_instance_file_path(core: str, version: Optional[int] = None, case_type: str = SNAKE_CASE,
                              instance_file_extension: str = INSTANCE_FILE_EXTENSION,
                              instance_directory_relative_path: Optional[str] = None):
    """
    Create an instance file path from its core, its version, its case type, its extension and its directory.

    NB: if a version is specified, it is assumed that the instance file is located in the directory containing
    instances of this version, otherwise it is assumed that the instance file is located in the default inputs
    directory.

    Args:
        core: The core of the instance file name.
        version: The version of the instance if any.
        case_type: The case type of the instance file name (snake case or camel case, default is snake case).
        instance_file_extension: The extension of the instance file (default is .xlsx).
        instance_directory_relative_path: The relative path of the directory containing the instance file.

    Returns:
        The path of the instance file.
    """
    if instance_directory_relative_path is None:
        if version is not None:
            instance_directory_path = get_path_of_directory_of_instances_of_given_version(version)
        else:
            instance_directory_path = get_default_inputs_directory_path()
    else:
        instance_directory_path = make_absolute_path_from_relative_one(instance_directory_relative_path)
    return f"{instance_directory_path}/{create_instance_file_name(core, version, case_type)}{instance_file_extension}"


def create_instance_file_paths_with_various_extensions(core: str, version: Optional[int] = None,
                                                       case_type: str = SNAKE_CASE,
                                                       instance_directory_relative_path: Optional[str] = None):
    """
    Create the instance file paths for a given core, version and case type, one per possible extension.

    Args:
        core: The core of the instance file name.
        version: The version of the instance if any.
        case_type: The case type of the instance file name (snake case or camel case, default is snake case).
        instance_directory_relative_path: The relative path of the directory containing the instance file.

    Returns:
        The list of instance file paths, one per possible instance file extension.
    """
    return [create_instance_file_path(core, version, case_type, extension, instance_directory_relative_path)
            for extension in INSTANCE_FILE_POSSIBLE_EXTENSIONS]


def get_paths_of_instances_files_in_given_directory(instances_directory_relative_path: Optional[str] = None):
    """
    Get the paths of all the instance files in a directory.

    NB: by default, the instances directory is the default inputs directory.

    Args:
        instances_directory_relative_path: The relative path of the directory containing the instance files.

    Returns:
        The paths of all the instance files in the directory.

    Raises:
        FileNotFoundError: If the instances directory doesn't exist.
    """
    if instances_directory_relative_path is None:
        instances_directory_path = get_default_inputs_directory_path()
    else:
        instances_directory_path = make_absolute_path_from_relative_one(instances_directory_relative_path)
    try:
        entries = listdir(instances_directory_path)
    except (FileNotFoundError, NotADirectoryError):
        raise FileNotFoundError(f"There are no instances in the directory {instances_directory_path}")
    files_names_with_extensions = [
        entry for entry in entries if path.isfile(path.join(instances_directory_path, entry))
    ]
    instances_files_paths = []
    for file_name in files_names_with_extensions:
        if is_an_instance_file_name_with_extension(file_name):
            instance_file_path = instances_directory_path + "/" + file_name
            instances_files_paths.append(instance_file_path)
    instances_files_paths.sort()
    return instances_files_paths


def get_path_of_directory_of_instances_of_given_version(version: int, absolute_path: bool = True):
    """
    Get the (absolute) path of the directory containing the instances with a specific version.

    Args:
        version: The version of the instances.
        absolute_path: Whether the path should be absolute or not.

    Returns:
        The path of the directory containing the instances with a specific version.
    """
    path_first_art = f"{get_project_directory_path()}/" if absolute_path else ''
    return (f"{path_first_art}{TEACHING_DATA_DIRECTORY_RELATIVE_PATH}/"
            f"{INSTANCE_VERSION_SYMBOL}{str(version)}/instances")
