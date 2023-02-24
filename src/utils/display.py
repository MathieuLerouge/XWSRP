# Local library
from src.utils.constants import LINE_BREAK_STRING


def create_title_frame(title: str):
    """
    Create a title frame.

    :param title: title (str)
    :return: title frame (str)
    """
    symbol = "#"
    spaces = "  "
    nb_symbols = len(title) + 2 * len(spaces) + 2
    title_frame = symbol*nb_symbols + LINE_BREAK_STRING
    title_frame += symbol + spaces + title + spaces + symbol + LINE_BREAK_STRING
    title_frame += symbol*nb_symbols
    return title_frame


def print_title_frame(title: str):
    """
    Print a title frame.

    :param title: title (str)
    :return: None
    """
    print(create_title_frame(title))
