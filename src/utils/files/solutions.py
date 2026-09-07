# Standard library
from os import listdir, path
from typing import Optional

# Local library
from src.utils.constants import *
from src.utils.files.general import *


############
# Solution #
############

def is_a_solution_file_name(file_name: str):
    """
    Check whether a file name is a solution file name (with or without extension).

    Args:
        file_name: The file name (with or without extension).

    Returns:
        Whether the file name is a solution file name.
    """
    for prefix in SOLUTION_FILE_NAME_POSSIBLE_PREFIXES:
        if prefix == file_name[:len(prefix)]:
            return True
    return False


def is_a_solution_file_name_with_extension(file_name_with_extension: str):
    """
    Check if a file name is a solution file name.

    Args:
        file_name_with_extension: The name of the file with its extension.

    Returns:
        True if the file name is a solution file name, False otherwise.
    """
    if (has_a_file_extension(file_name_with_extension)
            and get_file_extension(file_name_with_extension) == SOLUTION_FILE_EXTENSION):
        for prefix in SOLUTION_FILE_NAME_POSSIBLE_PREFIXES:
            if prefix == file_name_with_extension[:len(prefix)]:
                return True
    return False


def get_solution_file_name_case_type(file_name: str):
    """
    Get the case type of solution file name (with or without).

    Args:
        file_name: The name of the solution file (with or without).

    Returns:
        The case type of the solution file name.

    Raises:
        ValueError: If file_name isn't a solution file name, or if its case is neither CamelCase nor
            snake_case.
    """
    if not is_a_solution_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not a solution file name")
    if SOLUTION_NAME_PREFIX in file_name:
        return SNAKE_CASE
    elif SOLUTION_NAME_PREFIX_BIS in file_name:
        return CAMEL_CASE
    else:
        raise ValueError(f"The case of file name {file_name} is neither CamelCase nor snake_case")


def remove_solution_file_name_prefix(file_name: str):
    """
    Remove the prefix of a solution file name (with or without).

    Args:
        file_name: The name of the file (with or without).

    Returns:
        The core of the solution file name.

    Raises:
        ValueError: If file_name isn't a solution file name, or if its case type isn't supported.
    """
    if not is_a_solution_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not a solution file name")
    case_type = get_solution_file_name_case_type(file_name)
    if case_type == SNAKE_CASE:
        return file_name.removeprefix(SOLUTION_NAME_PREFIX)
    elif case_type == CAMEL_CASE:
        return file_name.removeprefix(SOLUTION_NAME_PREFIX_BIS)
    else:
        raise ValueError(f"The case type {case_type} is not supported")


def does_solution_file_name_mention_version(file_name: str):
    """
    Check if a solution file name mentions a version (with or without extension).

    Args:
        file_name: The name of the solution file (with or without extension).

    Returns:
        True if the solution file name mentions a version, False otherwise.

    Raises:
        ValueError: If file_name isn't a solution file name.
    """
    if not is_a_solution_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not a solution file name")
    if INSTANCE_VERSION_SYMBOL in file_name:
        index = file_name.rindex(INSTANCE_VERSION_SYMBOL)
        return file_name[index + len(INSTANCE_VERSION_SYMBOL)].isnumeric()
    else:
        return False


def get_instance_version_in_solution_file_name(file_name: str):
    """
    Get the version of a solution file name (with or without).

    Args:
        file_name: The name of the solution file (with or without).

    Returns:
        The version of the solution file name.

    Raises:
        ValueError: If file_name isn't a solution file name, or if it doesn't mention a version.
    """
    if not is_a_solution_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not a solution file name")
    if not does_solution_file_name_mention_version(file_name):
        raise ValueError(f"The file name {file_name} does not mention a version")
    return int(file_name[file_name.index(INSTANCE_VERSION_SYMBOL) + 1])


def remove_instance_version_from_solution_file_name(file_name: str):
    """
    Remove the version of a solution file name (with or without).

    Args:
        file_name: The name of the solution file (with or without).

    Returns:
        The core of the solution file name.

    Raises:
        ValueError: If file_name isn't a solution file name, or if it doesn't mention a version.
    """
    if not is_a_solution_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not a solution file name")
    if not does_solution_file_name_mention_version(file_name):
        raise ValueError(f"The file name {file_name} does not mention a version")
    index = file_name.index(INSTANCE_VERSION_SYMBOL)
    return file_name[:index] + file_name[index + 2:]


def does_solution_file_name_mention_solving_method(file_name: str):
    """
    Check if a solution file name mentions a solving method (with or without extension).

    Args:
        file_name: The name of the file (with or without extension).

    Returns:
        True if the solution file name mentions a solving method, False otherwise.

    Raises:
        ValueError: If file_name isn't a solution file name, or if its case type isn't supported.
    """
    if not is_a_solution_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not a solution file name")
    case_type = get_solution_file_name_case_type(file_name)
    if case_type == SNAKE_CASE:
        return SOLUTION_SOLVING_METHOD_SYMBOL in file_name
    elif case_type == CAMEL_CASE:
        return SOLUTION_SOLVING_METHOD_SYMBOL_BIS in file_name
    else:
        raise ValueError(f"The case type {case_type} is not supported")


def does_solution_file_path_mention_solving_method(file_path: str):
    """
    Check if a solution file path mentions a solving method (with or without extension).

    Args:
        file_path: The path of the file (with or without extension).

    Returns:
        True if the solution file path mentions a solving method, False otherwise.
    """
    return does_solution_file_name_mention_solving_method(file_path.split('/')[-1])


def get_solving_method_in_solution_file_name(file_name: str):
    """
    Get the solving method mentioned in a solution file name.

    Args:
        file_name: The name of the file.

    Returns:
        The solving method mentioned in the solution file name.

    Raises:
        ValueError: If file_name doesn't mention a solving method, or if its case type isn't supported.
    """
    if not does_solution_file_name_mention_solving_method(file_name):
        raise ValueError(f"The file name {file_name} does not mention a solving method")
    if does_solution_file_name_mention_solving_parameters(file_name):
        file_name = remove_solving_parameters_from_solution_file_name(file_name)
    case_type = get_solution_file_name_case_type(file_name)
    if case_type == SNAKE_CASE:
        return file_name.split(f"_{SOLUTION_SOLVING_METHOD_SYMBOL}_")[1].split(SOLUTION_FILE_EXTENSION)[0]
    elif case_type == CAMEL_CASE:
        return file_name.split(SOLUTION_SOLVING_METHOD_SYMBOL_BIS)[1].split(SOLUTION_FILE_EXTENSION)[0]
    else:
        raise ValueError(f"The case type {case_type} is not supported")


def get_solving_method_in_solution_file_path(file_path: str):
    """
    Get the solving method mentioned in a solution file path.

    Args:
        file_path: The path of the file.

    Returns:
        The solving method mentioned in the solution file path.
    """
    return get_solving_method_in_solution_file_name(file_path.split('/')[-1])


def remove_solving_method_from_solution_file_name(file_name: str):
    """
    Remove the solving method from a solution file name.

    Args:
        file_name: The name of the file.

    Returns:
        The solution file name without the solving method.

    Raises:
        ValueError: If file_name doesn't mention a solving method, or if its case type isn't supported.
    """
    if not does_solution_file_name_mention_solving_method(file_name):
        raise ValueError(f"The file name {file_name} does not mention a solving method")
    solving_method = get_solving_method_in_solution_file_name(file_name)
    case_type = get_solution_file_name_case_type(file_name)
    if case_type == SNAKE_CASE:
        return file_name.replace(f"_{SOLUTION_SOLVING_METHOD_SYMBOL}_{solving_method}", "")
    elif case_type == CAMEL_CASE:
        return file_name.replace(f"{SOLUTION_SOLVING_METHOD_SYMBOL_BIS}{solving_method}", "")
    else:
        raise ValueError(f"The case type {case_type} is not supported")


def does_solution_file_name_mention_solving_parameters(file_name: str):
    """
    Check if a solution file name (with or without) mentions solving parameters.

    Args:
        file_name: The name of the file (with or without).

    Returns:
        True if the solution file name mentions solving parameters, False otherwise.

    Raises:
        ValueError: If file_name isn't a solution file name.
    """
    if not is_a_solution_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not a solution file name")
    if SOLUTION_SOLVING_PARAMETERS_LEFT_SYMBOL in file_name and SOLUTION_SOLVING_PARAMETERS_RIGHT_SYMBOL in file_name:
        index_left = file_name.rindex(SOLUTION_SOLVING_PARAMETERS_LEFT_SYMBOL)
        index_right = file_name.rindex(SOLUTION_SOLVING_PARAMETERS_RIGHT_SYMBOL)
        if SOLUTION_SOLVING_PARAMETERS_SEPARATOR_SYMBOL in file_name[index_left + 1:index_right]:
            return True
    return False


def get_solving_parameters_in_solution_file_name(file_name: str):
    """
    Get the solving parameters mentioned in a solution file name.

    Args:
        file_name: The name of the file.

    Returns:
        The solving parameters mentioned in the solution file name.

    Raises:
        ValueError: If file_name doesn't mention solving parameters.
    """
    if not does_solution_file_name_mention_solving_parameters(file_name):
        raise ValueError(f"The file name {file_name} does not mention solving parameters")
    index_left = file_name.rindex(SOLUTION_SOLVING_PARAMETERS_LEFT_SYMBOL)
    index_right = file_name.rindex(SOLUTION_SOLVING_PARAMETERS_RIGHT_SYMBOL)
    return file_name[index_left + 1:index_right].split(SOLUTION_SOLVING_PARAMETERS_SEPARATOR_SYMBOL)


def remove_solving_parameters_from_solution_file_name(file_name: str):
    """
    Remove the solving parameters from a solution file name.

    Args:
        file_name: The name of the file.

    Returns:
        The solution file name without the solving parameters.

    Raises:
        ValueError: If file_name doesn't mention solving parameters.
    """
    if not does_solution_file_name_mention_solving_parameters(file_name):
        raise ValueError(f"The file name {file_name} does not mention solving parameters")
    index_left = file_name.rindex(SOLUTION_SOLVING_PARAMETERS_LEFT_SYMBOL)
    index_right = file_name.rindex(SOLUTION_SOLVING_PARAMETERS_RIGHT_SYMBOL)
    return file_name[:index_left] + file_name[index_right + 1:]


def get_core_in_solution_file_name(file_name: str):
    """
    Get the core of a solution file name.

    Args:
        file_name: The name of the file.

    Returns:
        The core of the solution file name.
    """
    if does_solution_file_name_mention_version(file_name):
        file_name = remove_instance_version_from_solution_file_name(file_name)
    if does_solution_file_name_mention_solving_method(file_name):
        file_name = remove_solving_method_from_solution_file_name(file_name)
    if does_solution_file_name_mention_solving_parameters(file_name):
        file_name = remove_solving_parameters_from_solution_file_name(file_name)
    file_name = remove_solution_file_name_prefix(file_name)
    if has_a_file_extension(file_name):
        file_name = remove_file_extension(file_name)
    return file_name


def identify_meta_data_in_solution_file_name(file_name_with_extension: str):
    """
    Identify the metadata in a solution file name.

    Args:
        file_name_with_extension: The name of the solution file with its extension.

    Returns:
        A dictionary containing the metadata of the solution file name.
    """
    core = get_core_in_solution_file_name(file_name_with_extension)
    case_type = get_solution_file_name_case_type(file_name_with_extension)
    if does_solution_file_name_mention_version(file_name_with_extension):
        version = get_instance_version_in_solution_file_name(file_name_with_extension)
    else:
        version = None
    if does_solution_file_name_mention_solving_method(file_name_with_extension):
        solving_method = get_solving_method_in_solution_file_name(file_name_with_extension)
    else:
        solving_method = None
    if does_solution_file_name_mention_solving_parameters(file_name_with_extension):
        solving_parameters = get_solving_parameters_in_solution_file_name(file_name_with_extension)
    else:
        solving_parameters = None
    meta_data = {META_DATA_CORE_KEY: core, META_DATA_CASE_KEY: case_type, META_DATA_VERSION_KEY: version,
                 META_DATA_SOLVING_METHOD_KEY: solving_method, META_DATA_SOLVING_PARAMETERS_KEY: solving_parameters}
    return meta_data


def identify_meta_data_in_solution_file_path(solution_file_path: str):
    """
    Identify the metadata of a solution file path.

    Args:
        solution_file_path: The path of the solution file.

    Returns:
        The metadata of the solution file path.
    """
    return identify_meta_data_in_solution_file_name(solution_file_path.split('/')[-1])


def get_paths_of_solutions_files_in_given_directory(solutions_directory_relative_path: Optional[str] = None):
    """
    Get the paths of the solution files in a given directory.

    NB: if the directory containing the solutions is not specified, the default inputs directory is used.

    Args:
        solutions_directory_relative_path: The relative path of the directory containing the solution files.

    Returns:
        The paths of the solution files in a given directory.

    Raises:
        FileNotFoundError: If the solutions directory doesn't exist.
    """
    if solutions_directory_relative_path is None:
        directory_path = get_default_inputs_directory_path()
    else:
        directory_path = make_absolute_path_from_relative_one(solutions_directory_relative_path)
    try:
        entries = listdir(directory_path)
    except (FileNotFoundError, NotADirectoryError):
        raise FileNotFoundError(f"There are no solutions in the directory {directory_path}")
    files_names_with_extensions = [entry for entry in entries if path.isfile(path.join(directory_path, entry))]
    solutions_files_paths = []
    for file_name_with_extension in files_names_with_extensions:
        if is_a_solution_file_name_with_extension(file_name_with_extension):
            solutions_files_paths.append(f"{directory_path}/{file_name_with_extension}")
    solutions_files_paths.sort()
    return solutions_files_paths


def get_solutions_files_paths_given_meta_data(core: str, version: Optional[int] = None,
                                              case_type: Optional[str] = None,
                                              solutions_directory_relative_path: Optional[str] = None):
    """
    Get the paths of the solution files satisfying given metadata.

    Args:
        core: The core of the solution file name.
        version: The version of the solution file name if any.
        case_type: The case type of the solution file name (snake case or camel case).
        solutions_directory_relative_path: The relative path of the directory containing the solution files.

    Returns:
        The paths of the solution files satisfying given metadata.

    Raises:
        FileNotFoundError: If the solutions directory doesn't exist.
    """
    if solutions_directory_relative_path is None:
        if version is not None:
            solutions_directory_path = get_directory_of_solutions_of_given_version(version)
        else:
            solutions_directory_path = get_default_outputs_directory_path()
    else:
        solutions_directory_path = make_absolute_path_from_relative_one(solutions_directory_relative_path)
    try:
        entries = listdir(solutions_directory_path)
    except (FileNotFoundError, NotADirectoryError):
        raise FileNotFoundError(f"There are no corresponding solutions in the directory {solutions_directory_path}")
    files_names_with_extensions = [
        entry for entry in entries if path.isfile(path.join(solutions_directory_path, entry))
    ]
    solutions_files_paths = []
    extended_core = core
    if version is not None:
        extended_core += f"{INSTANCE_VERSION_SYMBOL}{str(version)}"
    for file_name in files_names_with_extensions:
        if is_a_solution_file_name_with_extension(file_name) and extended_core in file_name:
            if case_type is None or case_type == get_solution_file_name_case_type(file_name):
                solutions_files_paths.append(f"{solutions_directory_path}/{file_name}")
    return solutions_files_paths


def get_directory_of_solutions_of_given_version(version: int, absolute_path: bool = True):
    """
    Get the path of the directory containing the solutions with a specific version.

    Args:
        version: The version of the solutions.
        absolute_path: Whether the path should be absolute or not.

    Returns:
        The path of the directory containing the solutions with a specific version.
    """
    path_first_part = f"{get_default_outputs_directory_path()}/" if absolute_path else ""
    return (f"{path_first_part}{TEACHING_DATA_DIRECTORY_RELATIVE_PATH}/"
            f"{INSTANCE_VERSION_SYMBOL}{str(version)}/solutions")


def get_demo_solution_path():
    """Get the (absolute) path of the demo solution file."""
    return f"{get_project_directory_path()}/data/demo/solutions/solution_demo.txt"
