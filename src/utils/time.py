# Standard library
import datetime as dt

# Local libraries
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY


####################
# Global variables #
####################

TWELVE_HOURS_FORMAT = '12'
TWENTY_FOUR_HOURS_FORMAT_WITH_H = '24h'
TWENTY_FOUR_HOURS_FORMAT_WITH_DOTS = '24:'


####################
# Global functions #
####################


def get_hour_format(time_string: str):
    """
    Returns the hour format used by the given time string.

    Args:
        time_string: Time string to inspect.

    Returns:
        One of TWELVE_HOURS_FORMAT, TWENTY_FOUR_HOURS_FORMAT_WITH_H, or TWENTY_FOUR_HOURS_FORMAT_WITH_DOTS.

    Raises:
        ValueError: If time_string doesn't match any known hour format.
    """
    if 'M' in time_string or 'm' in time_string:
        return TWELVE_HOURS_FORMAT
    elif 'h' in time_string:
        return TWENTY_FOUR_HOURS_FORMAT_WITH_H
    elif ':' in time_string:
        return TWENTY_FOUR_HOURS_FORMAT_WITH_DOTS
    else:
        raise ValueError(f"Unknown hour format for: {time_string}")


def convert_time_string_to_nb_minutes(time_string: str):
    """
    Converts a given time string to a number of minutes since midnight.

    Args:
        time_string: Time string with format HH:MMam, HH:MMpm, HHhMM, or HH:MM.

    Returns:
        The number of minutes since midnight, as an int.

    Raises:
        ValueError: If time_string doesn't match any known hour format.
    """
    if get_hour_format(time_string) == TWELVE_HOURS_FORMAT:
        return int((dt.datetime.strptime(time_string, '%I:%M%p') -
                    dt.datetime.strptime("00:00am", '%H:%M%p')).total_seconds() / 60)
    elif get_hour_format(time_string) == TWENTY_FOUR_HOURS_FORMAT_WITH_H:
        if time_string[-1] == 'h':
            time_string += "00"
        return int((dt.datetime.strptime(time_string, '%Hh%M') -
                    dt.datetime.strptime("00:00", '%H:%M')).total_seconds() / 60)
    elif get_hour_format(time_string) == TWENTY_FOUR_HOURS_FORMAT_WITH_DOTS:
        return int((dt.datetime.strptime(time_string, '%H:%M') -
                    dt.datetime.strptime("00:00", '%H:%M')).total_seconds() / 60)
    else:
        raise ValueError(f"Unknown hour format for: {time_string}")


def convert_nb_minutes_to_time_string(nb_minutes: int, hour_format: str = TWELVE_HOURS_FORMAT):
    """
    Converts a given number of minutes since midnight to a time string.

    Args:
        nb_minutes: Number of minutes since midnight.
        hour_format: Hour format to use for the returned string.

    Returns:
        The corresponding time string.

    Raises:
        ValueError: If hour_format isn't a known hour format.
    """
    midnight = dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    time = midnight + dt.timedelta(0, 60 * nb_minutes)
    if hour_format == TWELVE_HOURS_FORMAT:
        return time.strftime('%I:%M%p')
    elif hour_format == TWENTY_FOUR_HOURS_FORMAT_WITH_H:
        return time.strftime('%Hh%M')
    elif hour_format == TWENTY_FOUR_HOURS_FORMAT_WITH_DOTS:
        return time.strftime('%H:%M')
    else:
        raise ValueError(f"Unknown hour format for: {hour_format}")


def convert_time_string_in_given_format(time_string: str, hour_format: str):
    """
    Converts a given time string to an equivalent time string in another hour format.

    Args:
        time_string: Time string to convert.
        hour_format: Hour format to convert time_string to.

    Returns:
        The time string converted to hour_format (or unchanged if it's already in that format).
    """
    if get_hour_format(time_string) == hour_format:
        return time_string
    else:
        return convert_nb_minutes_to_time_string(convert_time_string_to_nb_minutes(time_string), hour_format)


def get_hour_format_associated_with_language(language: str):
    """
    Returns the hour format conventionally associated with a given language.

    Args:
        language: Language key to look up.

    Returns:
        TWELVE_HOURS_FORMAT for English, TWENTY_FOUR_HOURS_FORMAT_WITH_H for French.

    Raises:
        NotImplementedError: If language isn't a supported language key.
    """
    if language == LANGUAGE_ENGLISH_KEY:
        return TWELVE_HOURS_FORMAT
    elif language == LANGUAGE_FRENCH_KEY:
        return TWENTY_FOUR_HOURS_FORMAT_WITH_H
    else:
        raise NotImplementedError(f"Unknown language: {language}")
