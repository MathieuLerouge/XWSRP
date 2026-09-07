# Local library
from src.utils.files.general import check_inputs_file_existence, get_default_inputs_directory_path, \
    get_default_outputs_directory_path, get_file_extension, get_file_name_from_path, get_project_directory_path, \
    has_a_file_extension, make_absolute_path_from_relative_one, make_inputs_file_relative_path_from_file_name, \
    make_relative_path_from_absolute_one, remove_file_extension
from src.utils.files.instances import create_instance_file_name, create_instance_file_path, \
    create_instance_file_paths_with_various_extensions, does_instance_file_name_mention_version, \
    get_core_in_instance_file_name, get_instance_file_name_case_type, get_instance_name_in_instance_file_name, \
    get_instance_name_in_instance_file_path, get_instance_version_in_instance_file_name, \
    get_path_of_directory_of_instances_of_given_version, get_paths_of_instances_files_in_given_directory, \
    identify_meta_data_in_instance_file_name, identify_meta_data_in_instance_file_path, \
    is_an_instance_file_name, is_an_instance_file_name_with_extension, remove_instance_file_name_prefix, \
    remove_instance_version_from_instance_file_name
from src.utils.files.matching import find_instance_file_path_corresponding_to_solution
from src.utils.files.solutions import does_solution_file_name_mention_solving_method, \
    does_solution_file_name_mention_solving_parameters, does_solution_file_name_mention_version, \
    does_solution_file_path_mention_solving_method, get_core_in_solution_file_name, get_demo_solution_path, \
    get_directory_of_solutions_of_given_version, get_instance_version_in_solution_file_name, \
    get_solution_file_name_case_type, get_solutions_files_paths_given_meta_data, \
    get_solving_method_in_solution_file_name, get_solving_method_in_solution_file_path, \
    get_solving_parameters_in_solution_file_name, get_paths_of_solutions_files_in_given_directory, \
    identify_meta_data_in_solution_file_name, identify_meta_data_in_solution_file_path, \
    is_a_solution_file_name, is_a_solution_file_name_with_extension, remove_instance_version_from_solution_file_name, \
    remove_solution_file_name_prefix, remove_solving_method_from_solution_file_name, \
    remove_solving_parameters_from_solution_file_name

__all__ = [
    "check_inputs_file_existence",
    "create_instance_file_name",
    "create_instance_file_path",
    "create_instance_file_paths_with_various_extensions",
    "does_instance_file_name_mention_version",
    "does_solution_file_name_mention_solving_method",
    "does_solution_file_name_mention_solving_parameters",
    "does_solution_file_name_mention_version",
    "does_solution_file_path_mention_solving_method",
    "find_instance_file_path_corresponding_to_solution",
    "get_core_in_instance_file_name",
    "get_core_in_solution_file_name",
    "get_default_inputs_directory_path",
    "get_default_outputs_directory_path",
    "get_demo_solution_path",
    "get_directory_of_solutions_of_given_version",
    "get_file_extension",
    "get_file_name_from_path",
    "get_instance_file_name_case_type",
    "get_instance_name_in_instance_file_name",
    "get_instance_name_in_instance_file_path",
    "get_instance_version_in_instance_file_name",
    "get_instance_version_in_solution_file_name",
    "get_path_of_directory_of_instances_of_given_version",
    "get_paths_of_instances_files_in_given_directory",
    "get_paths_of_solutions_files_in_given_directory",
    "get_project_directory_path",
    "get_solution_file_name_case_type",
    "get_solutions_files_paths_given_meta_data",
    "get_solving_method_in_solution_file_name",
    "get_solving_method_in_solution_file_path",
    "get_solving_parameters_in_solution_file_name",
    "has_a_file_extension",
    "identify_meta_data_in_instance_file_name",
    "identify_meta_data_in_instance_file_path",
    "identify_meta_data_in_solution_file_name",
    "identify_meta_data_in_solution_file_path",
    "is_a_solution_file_name",
    "is_a_solution_file_name_with_extension",
    "is_an_instance_file_name",
    "is_an_instance_file_name_with_extension",
    "make_absolute_path_from_relative_one",
    "make_inputs_file_relative_path_from_file_name",
    "make_relative_path_from_absolute_one",
    "remove_file_extension",
    "remove_instance_file_name_prefix",
    "remove_instance_version_from_instance_file_name",
    "remove_instance_version_from_solution_file_name",
    "remove_solution_file_name_prefix",
    "remove_solving_method_from_solution_file_name",
    "remove_solving_parameters_from_solution_file_name",
]
