# Standard library
from os import getcwd, path, walk

# Local library
from src.utils.constants import *


###########
# General #
###########

def has_a_file_extension(file_name: str):
    """
    Check if a file name has an extension

    :param file_name: the name of the file
    :return: True if the file name has an extension, False otherwise
    """
    return f".{file_name.split('.')[-1]}" in POSSIBLE_EXTENSIONS


def get_file_extension(file_name_with_extension: str):
    """
    Get the extension of a file name

    :param file_name_with_extension: the name of the file with its extension
    :return: the extension of the file
    """
    if not has_a_file_extension(file_name_with_extension):
        raise ValueError(f"The file name {file_name_with_extension} has no extension")
    return f".{file_name_with_extension.split('.')[-1]}"


def remove_file_extension(file_name_with_extension: str):
    """
    Remove the extension of a file name

    :param file_name_with_extension: the name of the file with its extension
    :return: the name of the file without its extension
    """
    return file_name_with_extension[:-(len(get_file_extension(file_name_with_extension)))]


#####################
# Project directory #
#####################


def get_project_directory_path():
    """
    Get the (absolute) path of the project directory

    :return: the (absolute) path of the project directory
    """
    current_working_directory = getcwd()
    if "/src" in current_working_directory:
        index = current_working_directory.find("/src")
        return current_working_directory[:index]
    else:
        return current_working_directory


def make_absolute_path_from_relative_one(relative_path: str):
    """
    Make an absolute path (path from root) from a relative path (path from project directory)

    :param relative_path: a relative path
    :return: the absolute path corresponding to the relative path
    """
    return f"{get_project_directory_path()}/{relative_path}"


def make_relative_path_from_absolute_one(absolute_path: str):
    """
    Make a relative path from an absolute path

    :param absolute_path: an absolute path
    :return: the relative path corresponding to the absolute path
    """
    return absolute_path.replace(f"{get_project_directory_path()}/", '')


def get_file_name_from_path(file_path: str, with_extension: bool = True):
    """
    Get the file name from its path

    :param file_path: the path of the file
    :param with_extension: True if the file name must have its extension, False otherwise
    :return: the file name
    """
    file_name = file_path.split('/')[-1]
    if not with_extension:
        if has_a_file_extension(file_name):
            file_name = remove_file_extension(file_name)
    return file_name


def get_default_inputs_directory_path():
    """
    Get the (absolute) path of the default inputs directory

    :return: the (absolute) path of the default inputs directory
    """
    return make_absolute_path_from_relative_one(INPUTS_DIRECTORY_RELATIVE_PATH)


def get_default_outputs_directory_path():
    """
    Get the (absolute) path of the default outputs directory

    :return: the (absolute) path of the default outputs directory
    """
    return make_absolute_path_from_relative_one(OUTPUTS_DIRECTORY_RELATIVE_PATH)


def make_inputs_file_relative_path_from_file_name(file_name_with_extension: str,
                                                  inputs_directory_relative_path: str = None):
    """
    Make a relative path from an inputs file name (with its extension) and its directory relative path
    NB: by default, the inputs directory relative path is the default one

    :param file_name_with_extension: the name of the file with its extension
    :param inputs_directory_relative_path: the relative path of the directory containing the file
    :return: the relative path of the file
    """
    if inputs_directory_relative_path is None:
        inputs_directory_relative_path = INPUTS_DIRECTORY_RELATIVE_PATH
    file_path = f"{inputs_directory_relative_path}/{file_name_with_extension}"
    return file_path


def check_inputs_file_existence(file_name_with_extension: str, inputs_directory_relative_path: str = None):
    """
    Check if an inputs file exists

    :param file_name_with_extension: the name of the file with its extension
    :param inputs_directory_relative_path: the relative path of the directory containing the file
    :return: True if the file exists, False otherwise
    """
    return path.exists(
        make_inputs_file_relative_path_from_file_name(file_name_with_extension, inputs_directory_relative_path)
    )


############
# Instance #
############


def is_an_instance_file_name(file_name_with_extension: str):
    """
    Check if a file name is an instance file name
    NB: the file name must have an extension

    :param file_name_with_extension: the name of the file with its extension
    :return: True if the file name is an instance file name, False otherwise
    """
    if has_a_file_extension(file_name_with_extension) and \
            get_file_extension(file_name_with_extension) in INSTANCE_FILE_POSSIBLE_EXTENSIONS:
        for prefix in INSTANCE_FILE_NAME_POSSIBLE_PREFIXES:
            if prefix == file_name_with_extension[:len(prefix)]:
                return True
    return False


def get_instance_file_name_case_type(file_name: str):
    """
    Get the case type of an instance file name

    :param file_name: the name of the file
    :return: the case type of the instance file name
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
    Remove the prefix of an instance file name

    :param file_name: the name of the file
    :return: the name of the file without its prefix
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
    Check if a instance file name mentions a version

    :param file_name: the name of the instance file
    :return: True if the instance file name mentions a version, False otherwise
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
    Get the version of a instance file name

    :param file_name: the name of the instance file
    :return: the version of the instance file name
    """
    if not is_an_instance_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not an instance file name")
    if not does_instance_file_name_mention_version(file_name):
        raise ValueError(f"The file name {file_name} does not mention a version")
    return int(file_name[file_name.find(INSTANCE_VERSION_SYMBOL) + 1])


def remove_instance_version_from_instance_file_name(file_name: str):
    """
    Remove the version of a instance file name

    :param file_name: the name of the instance file
    :return: the instance file name without the version
    """
    if not is_an_instance_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not an instance file name")
    if not does_instance_file_name_mention_version(file_name):
        raise ValueError(f"The file name {file_name} does not mention a version")
    index = file_name.index(INSTANCE_VERSION_SYMBOL)
    return file_name[:index] + file_name[index + 2:]


def get_core_in_instance_file_name(file_name: str):
    """
    Get the core of a instance file name

    :param file_name: the name of the file
    :return: the core of the instance file name
    """
    if does_instance_file_name_mention_version(file_name):
        file_name = remove_instance_version_from_instance_file_name(file_name)
    file_name = remove_instance_file_name_prefix(file_name)
    if has_a_file_extension(file_name):
        file_name = remove_file_extension(file_name)
    return file_name


def get_instance_name_in_instance_file_name(file_name_with_extension: str):
    """
    Get the instance name from its file name

    :param file_name_with_extension: the name of the file
    :return: the name of the instance file name
    """
    if not is_an_instance_file_name(file_name_with_extension):
        raise ValueError(f"The file name {file_name_with_extension} is not an instance file name")
    if does_instance_file_name_mention_version(file_name_with_extension):
        file_name_with_extension = remove_instance_version_from_instance_file_name(file_name_with_extension)
    if has_a_file_extension(file_name_with_extension):
        file_name_with_extension = remove_file_extension(file_name_with_extension)
    return file_name_with_extension


def get_instance_name_in_instance_file_path(file_path: str):
    """
    Get the instance name from its file path

    :param file_path: the path of the file
    :return: the name of the instance file name
    """
    return get_instance_name_in_instance_file_name(get_file_name_from_path(file_path, with_extension=True))


def identify_meta_data_in_instance_file_name(file_name_with_extension: str):
    """
    Identify the meta data in an instance file name

    :param file_name_with_extension: the name of the instance file with its extension
    :return: the meta data of the instance file
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
    Identify the meta data in an instance file path

    :param file_path: the path of the instance file
    :return: the meta data of the instance file
    """
    return identify_meta_data_in_instance_file_name(file_path.split('/')[-1])


def create_instance_file_name(core: str, version: int = None, case_type: str = SNAKE_CASE):
    """
    Create an instance file name from its core, its version and its case type

    :param core: the core of the instance file name
    :param version: the version of the instance file name
    :param case_type: the case type of the instance file name
    :return: the instance file name
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


def create_instance_file_path(core: str, version: int = None, case_type: str = SNAKE_CASE,
                              instance_file_extension: str = INSTANCE_FILE_EXTENSION,
                              instance_directory_relative_path: str = None):
    """
    Create an instance file path from its core, its version, its case type, its extension and its directory
    NB: if a version is specified, it is assumed that the instance file is located in the directory containing instances
    of this version, otherwise it is assumed that the instance file is located in the default inputs directory

    :param core: the core of the instance file name
    :param version: the version of the instance if any
    :param case_type: the case type of the instance file name (snake case or camel case, default is snake case)
    :param instance_file_extension: the extension of the instance file (default is .xlsx)
    :param instance_directory_relative_path: the relative path of the directory containing the instance file
    :return: the path of the instance file
    """
    if instance_directory_relative_path is None:
        if version is not None:
            instance_directory_path = get_path_of_directory_of_instances_of_given_version(version)
        else:
            instance_directory_path = get_default_inputs_directory_path()
    else:
        instance_directory_path = make_absolute_path_from_relative_one(instance_directory_relative_path)
    return f"{instance_directory_path}/{create_instance_file_name(core, version, case_type)}{instance_file_extension}"


def get_paths_of_instances_files_in_given_directory(instances_directory_relative_path: str = None):
    """
    Get the paths of all the instance files in a directory
    NB: by default, the instances directory is the default inputs directory

    :param instances_directory_relative_path: the relative path of the directory containing the instance files
    :return: the paths of all the instance files in the directory
    """
    if instances_directory_relative_path is None:
        instances_directory_path = get_default_inputs_directory_path()
    else:
        instances_directory_path = make_absolute_path_from_relative_one(instances_directory_relative_path)
    try:
        _, _, files_names_with_extensions = next(walk(instances_directory_path))
    except StopIteration:
        raise FileNotFoundError(f"There are no instances in the directory {instances_directory_path}")
    instances_files_paths = []
    for file_name in files_names_with_extensions:
        if is_an_instance_file_name(file_name):
            instance_file_path = instances_directory_path + "/" + file_name
            instances_files_paths.append(instance_file_path)
    instances_files_paths.sort()
    return instances_files_paths


def get_path_of_directory_of_instances_of_given_version(version: int, absolute_path: bool = True):
    """
    Get the (absolute) path of the directory containing the instances with a specific version

    :param version: the version of the instances
    :param absolute_path: whether the path should be absolute or not
    :return: the path of the directory containing the instances with a specific version
    """
    path_first_art = f"{get_project_directory_path()}/" if absolute_path else ''
    return f"{path_first_art}{TEACHING_DATA_DIRECTORY_RELATIVE_PATH}/" \
           f"{INSTANCE_VERSION_SYMBOL}{str(version)}/instances"


############
# Solution #
############


def is_a_solution_file_name(file_name_with_extension: str):
    """
    Check if a file name is a solution file name

    :param file_name_with_extension: the name of the file with its extension
    :return: True if the file name is a solution file name, False otherwise
    """
    if has_a_file_extension(file_name_with_extension) and \
            get_file_extension(file_name_with_extension) == SOLUTION_FILE_EXTENSION:
        for prefix in SOLUTION_FILE_NAME_POSSIBLE_PREFIXES:
            if prefix == file_name_with_extension[:len(prefix)]:
                return True
    return False


def get_solution_file_name_case_type(file_name: str):
    """
    Get the case type of a solution file name

    :param file_name: the name of the solution file
    :return: the case type of the solution file name
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
    Remove the prefix of a solution file name

    :param file_name: the name of the file
    :return: the core of the solution file name
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
    Check if a solution file name mentions a version

    :param file_name: the name of the solution file
    :return: True if the solution file name mentions a version, False otherwise
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
    Get the version of a solution file name

    :param file_name: the name of the solution file
    :return: the version of the solution file name
    """
    if not is_a_solution_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not a solution file name")
    if not does_solution_file_name_mention_version(file_name):
        raise ValueError(f"The file name {file_name} does not mention a version")
    return int(file_name[file_name.index(INSTANCE_VERSION_SYMBOL) + 1])


def remove_instance_version_from_solution_file_name(file_name: str):
    """
    Remove the version of a solution file name

    :param file_name: the name of the solution file
    :return: the core of the solution file name
    """
    if not is_a_solution_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not a solution file name")
    if not does_solution_file_name_mention_version(file_name):
        raise ValueError(f"The file name {file_name} does not mention a version")
    index = file_name.index(INSTANCE_VERSION_SYMBOL)
    return file_name[:index] + file_name[index + 2:]


def does_solution_file_name_mention_solving_method(file_name: str):
    """
    Check if a solution file name mentions a solving method

    :param file_name: the name of the file
    :return: True if the solution file name mentions a solving method, False otherwise
    """
    if not is_a_solution_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not a solution file name")
    return SOLUTION_SOLVING_METHOD_SYMBOL in file_name


def get_solving_method_solution_file_name(file_name: str):
    """
    Get the solving method mentioned in a solution file name

    :param file_name: the name of the file
    :return: the solving method mentioned in the solution file name
    """
    if not does_solution_file_name_mention_solving_method(file_name):
        raise ValueError(f"The file name {file_name} does not mention a solving method")
    if does_solution_file_name_mention_solving_parameters(file_name):
        file_name = remove_solving_parameters_from_solution_file_name(file_name)
    return file_name.split(SOLUTION_SOLVING_METHOD_SYMBOL)[1].split(SOLUTION_FILE_EXTENSION)[0]


def remove_solving_method_from_solution_file_name(file_name: str):
    """
    Remove the solving method from a solution file name

    :param file_name: the name of the file
    :return: the solution file name without the solving method
    """
    if not does_solution_file_name_mention_solving_method(file_name):
        raise ValueError(f"The file name {file_name} does not mention a solving method")
    return file_name.replace(SOLUTION_SOLVING_METHOD_SYMBOL + get_solving_method_solution_file_name(file_name), "")


def does_solution_file_name_mention_solving_parameters(file_name: str):
    """
    Check if a solution file name mentions solving parameters

    :param file_name: the name of the file
    :return: True if the solution file name mentions solving parameters, False otherwise
    """
    if not is_a_solution_file_name(file_name):
        raise ValueError(f"The file name {file_name} is not a solution file name")
    if SOLUTION_SOLVING_PARAMETERS_LEFT_SYMBOL in file_name and SOLUTION_SOLVING_PARAMETERS_RIGHT_SYMBOL in file_name:
        index_left = file_name.rindex(SOLUTION_SOLVING_PARAMETERS_LEFT_SYMBOL)
        index_right = file_name.rindex(SOLUTION_SOLVING_PARAMETERS_RIGHT_SYMBOL)
        if SOLUTION_SOLVING_PARAMETERS_SEPARATOR_SYMBOL in file_name[index_left + 1:index_right]:
            return True
    return False


def get_solving_parameters_solution_file_name(file_name: str):
    """
    Get the solving parameters mentioned in a solution file name

    :param file_name: the name of the file
    :return: the solving parameters mentioned in the solution file name
    """
    if not does_solution_file_name_mention_solving_parameters(file_name):
        raise ValueError(f"The file name {file_name} does not mention solving parameters")
    index_left = file_name.rindex(SOLUTION_SOLVING_PARAMETERS_LEFT_SYMBOL)
    index_right = file_name.rindex(SOLUTION_SOLVING_PARAMETERS_RIGHT_SYMBOL)
    return file_name[index_left + 1:index_right].split(SOLUTION_SOLVING_PARAMETERS_SEPARATOR_SYMBOL)


def remove_solving_parameters_from_solution_file_name(file_name: str):
    """
    Remove the solving parameters from a solution file name

    :param file_name: the name of the file
    :return: the solution file name without the solving parameters
    """
    if not does_solution_file_name_mention_solving_parameters(file_name):
        raise ValueError(f"The file name {file_name} does not mention solving parameters")
    index_left = file_name.rindex(SOLUTION_SOLVING_PARAMETERS_LEFT_SYMBOL)
    index_right = file_name.rindex(SOLUTION_SOLVING_PARAMETERS_RIGHT_SYMBOL)
    return file_name[:index_left] + file_name[index_right + 1:]


def get_core_in_solution_file_name(file_name: str):
    """
    Get the core of a solution file name

    :param file_name: the name of the file
    :return: the core of the solution file name
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
    Identify the meta data in a solution file name
    
    :param file_name_with_extension: the name of the solution file with its extension
    :return: a dictionary containing the meta data of the solution file name
    """
    core = get_core_in_solution_file_name(file_name_with_extension)
    case_type = get_solution_file_name_case_type(file_name_with_extension)
    if does_solution_file_name_mention_version(file_name_with_extension):
        version = get_instance_version_in_solution_file_name(file_name_with_extension)
    else:
        version = None
    if does_solution_file_name_mention_solving_method(file_name_with_extension):
        solving_method = get_solving_method_solution_file_name(file_name_with_extension)
    else:
        solving_method = None
    if does_solution_file_name_mention_solving_parameters(file_name_with_extension):
        solving_parameters = get_solving_parameters_solution_file_name(file_name_with_extension)
    else:
        solving_parameters = None
    meta_data = {META_DATA_CORE_KEY: core, META_DATA_CASE_KEY: case_type, META_DATA_VERSION_KEY: version,
                 META_DATA_SOLVING_METHOD_KEY: solving_method, META_DATA_SOLVING_PARAMETERS_KEY: solving_parameters}
    return meta_data


def identify_meta_data_in_solution_file_path(solution_file_path: str):
    """
    Identify the meta data of a solution file path

    :param solution_file_path: the path of the solution file
    :return: the meta data of the solution file path
    """
    return identify_meta_data_in_solution_file_name(solution_file_path.split('/')[-1])


def get_paths_of_solutions_files_in_given_directory(solutions_directory_relative_path: str = None):
    """
    Get the paths of the solution files in a given directory
    NB: if the directory containing the solutions is not specified, the default inputs directory is used

    :param solutions_directory_relative_path: the relative path of the directory containing the solution files
    :return: the paths of the solution files in a given directory
    """
    if solutions_directory_relative_path is None:
        directory_path = get_default_inputs_directory_path()
    else:
        directory_path = make_absolute_path_from_relative_one(solutions_directory_relative_path)
    try:
        _, _, files_names_with_extensions = next(walk(directory_path))
    except StopIteration:
        raise FileNotFoundError(f"There are no solutions in the directory {directory_path}")
    solutions_files_paths = []
    for file_name_with_extension in files_names_with_extensions:
        if is_a_solution_file_name(file_name_with_extension):
            solutions_files_paths.append(f"{directory_path}/{file_name_with_extension}")
    solutions_files_paths.sort()
    return solutions_files_paths


def get_solutions_files_paths_given_meta_data(core: str, version: int = None, case_type: str = None,
                                              solutions_directory_relative_path: str = None):
    """
    Get the paths of the solution files satisfying given meta data

    :param core: the core of the solution file name
    :param version: the version of the solution file name if any
    :param case_type: the case type of the solution file name (snake case or camel case)
    :param solutions_directory_relative_path: the relative path of the directory containing the solution files
    :return: the paths of the solution files satisfying given meta data
    """
    if solutions_directory_relative_path is None:
        if version is not None:
            solutions_directory_path = get_directory_of_solutions_of_given_version(version)
        else:
            solutions_directory_path = get_default_outputs_directory_path()
    else:
        solutions_directory_path = make_absolute_path_from_relative_one(solutions_directory_relative_path)
    try:
        _, _, files_names_with_extensions = next(walk(solutions_directory_path))
    except StopIteration:
        raise FileNotFoundError(f"There are no corresponding solutions in the directory {solutions_directory_path}")
    solutions_files_paths = []
    extended_core = core
    if version is not None:
        extended_core += f"{INSTANCE_VERSION_SYMBOL}{str(version)}"
    for file_name in files_names_with_extensions:
        if is_a_solution_file_name(file_name) and extended_core in file_name:
            if case_type is None or case_type == get_solution_file_name_case_type(file_name):
                solutions_files_paths.append(f"{solutions_directory_path}/{file_name}")
    return solutions_files_paths


def get_directory_of_solutions_of_given_version(version: int, absolute_path: bool = True):
    """
    Get the path of the directory containing the solutions with a specific version

    :param version: the version of the solutions
    :param absolute_path: whether the path should be absolute or not
    :return: the path of the directory containing the solutions with a specific version
    """
    path_first_part = f"{get_default_outputs_directory_path()}/" if absolute_path else ""
    return f"{path_first_part}{TEACHING_DATA_DIRECTORY_RELATIVE_PATH}/" \
           f"{INSTANCE_VERSION_SYMBOL}{str(version)}/solutions"


def get_demo_solution_path():
    return f"{get_project_directory_path()}/data/demo/solutions/solution_demo.txt"


#########################
# Instance and solution #
#########################


def find_instance_file_path_corresponding_to_solution(solution_file_path: str,
                                                      instance_directory_relative_path: str = None):
    """
    Find the path of the instance file corresponding to a solution file

    :param solution_file_path: the path of the solution file
    :param instance_directory_relative_path: the relative path of the directory containing the instance files
    :return: the path of the instance file corresponding to a solution file
    """
    meta_data = identify_meta_data_in_solution_file_path(solution_file_path)
    core, case_type, version = \
        meta_data[META_DATA_CORE_KEY], meta_data[META_DATA_CASE_KEY], meta_data[META_DATA_VERSION_KEY]
    if instance_directory_relative_path is not None:
        instance_file_path = create_instance_file_path(core, version, case_type, instance_directory_relative_path)
        if path.exists(instance_file_path):
            return instance_file_path
        else:
            raise FileExistsError(f"{instance_file_path} does not exist")
    else:
        solution_directory_path = solution_file_path[:solution_file_path.rindex('/')]
        instance_directory_relative_path = make_relative_path_from_absolute_one(solution_directory_path)
        instance_file_possible_path_1 = \
            create_instance_file_path(core, version, case_type,
                                      instance_directory_relative_path=instance_directory_relative_path)
        if path.exists(instance_file_possible_path_1):
            return instance_file_possible_path_1
        if "solutions" in solution_file_path:
            instance_directory_relative_path = \
                make_relative_path_from_absolute_one(solution_directory_path.replace("solutions", "instances"))
        instance_file_possible_path_2 = \
            create_instance_file_path(core, version, case_type,
                                      instance_directory_relative_path=instance_directory_relative_path)
        if path.exists(instance_file_possible_path_2):
            return instance_file_possible_path_2
        if version is not None:
            instance_directory_relative_path = \
                get_path_of_directory_of_instances_of_given_version(version, absolute_path=False)
        instance_file_possible_path_3 = \
            create_instance_file_path(core, version, case_type,
                                      instance_directory_relative_path=instance_directory_relative_path)
        if path.exists(instance_file_possible_path_3):
            return instance_file_possible_path_3
        instance_file_possible_paths = list({instance_file_possible_path_1, instance_file_possible_path_2,
                                             instance_file_possible_path_3})
        if len(instance_file_possible_paths) == 1:
            raise FileExistsError(f"{instance_file_possible_paths[0]} does not exist")
        else:
            raise FileExistsError(f"{instance_file_possible_paths} do not exist")


if __name__ == '__main__':
    print("Project directory:", get_project_directory_path())
    print("Default inputs directory:", get_default_inputs_directory_path())
    print("Default outputs directory:", get_default_outputs_directory_path())
    print()
    instance_file_path_ex = get_paths_of_instances_files_in_given_directory()[0]
    print("Path of an instance in default inputs directory:", instance_file_path_ex)
    instance_file_name_with_extension = get_file_name_from_path(instance_file_path_ex, with_extension=True)
    print("Instance file name (with extension):", instance_file_name_with_extension)
    print("Name of this instance:", get_instance_name_in_instance_file_name(instance_file_name_with_extension))
    instance_file_extension_ex = get_file_extension(instance_file_path_ex)
    print("Extension of this instance:", instance_file_extension_ex)
    instance_meta_data_ex = identify_meta_data_in_instance_file_path(instance_file_path_ex)
    print("Meta data of this instance:", instance_meta_data_ex)
    print("Path of same instance built from meta data:",
          create_instance_file_path(instance_meta_data_ex[META_DATA_CORE_KEY],
                                    instance_meta_data_ex[META_DATA_VERSION_KEY],
                                    instance_meta_data_ex[META_DATA_CASE_KEY],
                                    instance_file_extension_ex)
          )
    print()
    solution_file_path_ex = get_paths_of_solutions_files_in_given_directory()[0]
    print("Path of a solution in default inputs directory:", solution_file_path_ex)
    solution_file_extension_ex = get_file_extension(solution_file_path_ex)
    print("Extension of this solution:", solution_file_extension_ex)
    solution_meta_data_ex = identify_meta_data_in_solution_file_path(solution_file_path_ex)
    print("Meta data of this solution:", solution_meta_data_ex)
    print("Path of instance corresponding to this solution (automated search):",
          find_instance_file_path_corresponding_to_solution(solution_file_path_ex))
    print()
    path_of_directory_of_v1_instances = get_path_of_directory_of_instances_of_given_version(1)
    print("Path of directory of v1 instances:", path_of_directory_of_v1_instances)
    v1_instance_file_path_ex = \
        get_paths_of_instances_files_in_given_directory(
              make_relative_path_from_absolute_one(path_of_directory_of_v1_instances)
        )[0]
    print("Path of an instance in directory of v1 instances:", v1_instance_file_path_ex)
    v1_instance_file_name_with_extension = get_file_name_from_path(v1_instance_file_path_ex, with_extension=True)
    print("Instance file name (with extension):", v1_instance_file_name_with_extension)
    print("Name of this instance:", get_instance_name_in_instance_file_name(v1_instance_file_name_with_extension))
    v1_instance_meta_data_ex = identify_meta_data_in_instance_file_path(v1_instance_file_path_ex)
    print("Meta data of this instance:", v1_instance_meta_data_ex)
    print("Path of same instance built from meta data:",
          create_instance_file_path(v1_instance_meta_data_ex[META_DATA_CORE_KEY],
                                    v1_instance_meta_data_ex[META_DATA_VERSION_KEY],
                                    v1_instance_meta_data_ex[META_DATA_CASE_KEY])
          )
    print()
    print("Path of directory of v1 solutions:", get_directory_of_solutions_of_given_version(1))
    relative_path_of_directory_of_v1_solutions = get_directory_of_solutions_of_given_version(1, False)
    print("Relative path of directory of v1 solutions:", relative_path_of_directory_of_v1_solutions)
    v1_solution_file_path_ex = \
        get_paths_of_solutions_files_in_given_directory(relative_path_of_directory_of_v1_solutions)[0]
    print("Path of a solution in directory of v1 solutions:", v1_solution_file_path_ex)
    v1_solution_meta_data_ex = identify_meta_data_in_solution_file_path(v1_solution_file_path_ex)
    print("Meta data of this solution:", v1_solution_meta_data_ex)
    print("Path of instance corresponding to this solution (automated search):",
          find_instance_file_path_corresponding_to_solution(v1_solution_file_path_ex))
    print()
    demo_solution_path = get_demo_solution_path()
    print("Path of demo solution:", demo_solution_path)
    print("Path of instance corresponding to this solution (automated search):",
          find_instance_file_path_corresponding_to_solution(demo_solution_path))
