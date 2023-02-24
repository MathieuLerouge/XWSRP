# Local libraries
from src.reading.instance import complete_instance_from_xlsx_file
from src.teaching.modeling.instance import InstanceForTeaching
from src.utils.constants import META_DATA_VERSION_KEY
from src.utils.files import identify_meta_data_in_instance_file_path, get_instance_name_in_instance_file_path


#############################
# Extraction from xlsx file #
#############################


def create_empty_teaching_instance_from_xlsx_file(file_path: str):
    """
    Create an empty teaching instance from the given .xlsx file path.
    Its name is based on the file name.

    :param file_path: the path of the .xlsx file (str)
    :return: the empty teaching instance (InstanceForTeaching)
    """
    instance_name = get_instance_name_in_instance_file_path(file_path)
    return InstanceForTeaching(instance_name)


def extract_teaching_instance_from_xlsx_file(file_path: str):
    """
    Extract a teaching instance from the given .xlsx file path.

    :param file_path: the path of the .xlsx file (str)
    :return: the teaching instance (InstanceForTeaching)
    """
    data = identify_meta_data_in_instance_file_path(file_path)
    instance_version = data[META_DATA_VERSION_KEY]
    ignore_employees_unavailabilities = False
    ignore_tasks_unavailabilities = (instance_version == 1)
    ignore_lunch_breaks = ignore_tasks_unavailabilities
    instance = create_empty_teaching_instance_from_xlsx_file(file_path)
    instance = complete_instance_from_xlsx_file(instance, file_path, ignore_employees_unavailabilities,
                                                ignore_tasks_unavailabilities, ignore_lunch_breaks)
    return instance


def extract_teaching_instance_from_file(file_path: str):
    """
    Extract a teaching instance from the given file path.

    :param file_path: the path of the file (str)
    :return: the teaching instance (InstanceForTeaching)
    """
    return extract_teaching_instance_from_xlsx_file(file_path)
