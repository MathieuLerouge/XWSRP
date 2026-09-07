# Standard library
from os import getcwd, path
from pathlib import PurePosixPath
from typing import Optional

# Local library
from src.utils.constants import DEFAULT_INPUTS_DIRECTORY_RELATIVE_PATH, DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH, \
    POSSIBLE_EXTENSIONS


###########
# General #
###########

def has_a_file_extension(file_name: str):
    """
    Check if a file name has an extension.

    Args:
        file_name: The name of the file.

    Returns:
        True if the file name has an extension, False otherwise.
    """
    return f".{file_name.split('.')[-1]}" in POSSIBLE_EXTENSIONS


def get_file_extension(file_name_with_extension: str):
    """
    Get the extension of a file name.

    Args:
        file_name_with_extension: The name of the file with its extension.

    Returns:
        The extension of the file.

    Raises:
        ValueError: If file_name_with_extension has no extension.
    """
    if not has_a_file_extension(file_name_with_extension):
        raise ValueError(f"The file name {file_name_with_extension} has no extension")
    return f".{file_name_with_extension.split('.')[-1]}"


def remove_file_extension(file_name_with_extension: str):
    """
    Remove the extension of a file name.

    Args:
        file_name_with_extension: The name of the file with its extension.

    Returns:
        The name of the file without its extension.
    """
    return file_name_with_extension[:-(len(get_file_extension(file_name_with_extension)))]


#####################
# Project directory #
#####################

def get_project_directory_path():
    """
    Get the (absolute) path of the project directory.

    Returns:
        The (absolute) path of the project directory.
    """
    current_working_directory = getcwd()
    if "/src" in current_working_directory:
        index = current_working_directory.find("/src")
        return current_working_directory[:index]
    else:
        return current_working_directory


def make_absolute_path_from_relative_one(relative_path: str):
    """
    Make an absolute path (path from root) from a relative path (path from project directory).

    Args:
        relative_path: A relative path.

    Returns:
        The absolute path corresponding to the relative path.
    """
    return f"{get_project_directory_path()}/{relative_path}"


def make_relative_path_from_absolute_one(absolute_path: str):
    """
    Make a relative path from an absolute path.

    Args:
        absolute_path: An absolute path.

    Returns:
        The relative path corresponding to the absolute path.
    """
    return absolute_path.replace(f"{get_project_directory_path()}/", '')


def get_file_name_from_path(file_path: str, with_extension: bool = True):
    """
    Get the file name from its path.

    Args:
        file_path: The path of the file.
        with_extension: True if the file name must have its extension, False otherwise.

    Returns:
        The file name.
    """
    file_name = PurePosixPath(file_path).name
    if not with_extension:
        if has_a_file_extension(file_name):
            file_name = remove_file_extension(file_name)
    return file_name


def get_default_inputs_directory_path():
    """
    Get the (absolute) path of the default inputs directory.

    Returns:
        The (absolute) path of the default inputs directory.
    """
    return make_absolute_path_from_relative_one(DEFAULT_INPUTS_DIRECTORY_RELATIVE_PATH)


def get_default_outputs_directory_path():
    """
    Get the (absolute) path of the default outputs directory.

    Returns:
        The (absolute) path of the default outputs directory.
    """
    return make_absolute_path_from_relative_one(DEFAULT_OUTPUTS_DIRECTORY_RELATIVE_PATH)


def make_inputs_file_relative_path_from_file_name(file_name_with_extension: str,
                                                  inputs_directory_relative_path: Optional[str] = None):
    """
    Make a relative path from an inputs file name (with its extension) and its directory relative path.

    NB: by default, the inputs directory relative path is the default one.

    Args:
        file_name_with_extension: The name of the file with its extension.
        inputs_directory_relative_path: The relative path of the directory containing the file.

    Returns:
        The relative path of the file.
    """
    if inputs_directory_relative_path is None:
        inputs_directory_relative_path = DEFAULT_INPUTS_DIRECTORY_RELATIVE_PATH
    file_path = f"{inputs_directory_relative_path}/{file_name_with_extension}"
    return file_path


def check_inputs_file_existence(file_name_with_extension: str, inputs_directory_relative_path: Optional[str] = None):
    """
    Check if an inputs file exists.

    Args:
        file_name_with_extension: The name of the file with its extension.
        inputs_directory_relative_path: The relative path of the directory containing the file.

    Returns:
        True if the file exists, False otherwise.
    """
    return path.exists(
        make_inputs_file_relative_path_from_file_name(file_name_with_extension, inputs_directory_relative_path)
    )
