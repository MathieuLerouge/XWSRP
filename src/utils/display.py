# Local library
from src.utils.constants import LINE_BREAK_STRING


def create_title_frame(title: str):
    """
    Returns a boxed frame around the given title.

    Args:
        title: Text to display inside the frame.

    Returns:
        The multi-line framed title as a string.
    """
    symbol = "#"
    spaces = "  "
    nb_symbols = len(title) + 2 * len(spaces) + 2
    title_frame = symbol * nb_symbols + LINE_BREAK_STRING
    title_frame += symbol + spaces + title + spaces + symbol + LINE_BREAK_STRING
    title_frame += symbol * nb_symbols
    return title_frame


def print_title_frame(title: str):
    """
    Prints a boxed frame around the given title.

    Args:
        title: Text to display inside the frame.
    """
    print(create_title_frame(title))
