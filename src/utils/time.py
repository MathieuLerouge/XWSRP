# Standard library
import datetime as dt

# Local libraries
from src.utils.language import LANGUAGE_ENGLISH_KEY, LANGUAGE_FRENCH_KEY


####################
# Global variables #
####################

TWELVE_HOURS_FORMAT = '12h'
TWENTY_FOUR_HOURS_FORMAT = '24h'


####################
# Global functions #
####################


def get_hour_format(time_string: str):
    if 'M' in time_string or 'm' in time_string:
        return TWELVE_HOURS_FORMAT
    elif 'h' in time_string:
        return TWENTY_FOUR_HOURS_FORMAT
    else:
        raise ValueError("Unknown hour format of: " + time_string)


def convert_time_string_to_nb_minutes(time_string: str):
    """
    Convert a given time as string to a number of minutes

    :param time_string: time string with format HH:MMam or HH:MMpm (str)
    :return: number of minutes (int)
    """
    if get_hour_format(time_string) == TWELVE_HOURS_FORMAT:
        return int((dt.datetime.strptime(time_string, '%I:%M%p') -
                    dt.datetime.strptime("00:00am", '%H:%M%p')).total_seconds()/60)
    elif get_hour_format(time_string) == TWENTY_FOUR_HOURS_FORMAT:
        return int((dt.datetime.strptime(time_string, '%Hh%M') -
                    dt.datetime.strptime("00:00", '%H:%M')).total_seconds() / 60)
    else:
        return int((dt.datetime.strptime(time_string, '%H:%M') -
                    dt.datetime.strptime("00:00", '%H:%M')).total_seconds()/60)


def convert_nb_minutes_to_time_string(nb_minutes: int, hour_format: str = TWELVE_HOURS_FORMAT):
    midnight = dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    time = midnight + dt.timedelta(0, 60*nb_minutes)
    if hour_format == TWELVE_HOURS_FORMAT:
        return time.strftime('%I:%M%p')
    elif hour_format == TWENTY_FOUR_HOURS_FORMAT:
        return time.strftime('%Hh%M')
    else:
        raise ValueError("Unknown hour format: " + hour_format)


def convert_time_string_in_given_format(time_string: str, hour_format: str):
    if get_hour_format(time_string) == hour_format:
        return time_string
    else:
        return convert_nb_minutes_to_time_string(convert_time_string_to_nb_minutes(time_string), hour_format)


def get_hour_format_associated_with_language(language: str):
    if language == LANGUAGE_ENGLISH_KEY:
        return TWELVE_HOURS_FORMAT
    elif language == LANGUAGE_FRENCH_KEY:
        return TWENTY_FOUR_HOURS_FORMAT
    else:
        raise NotImplementedError("Unknown language: " + language)


if __name__ == '__main__':
    print(convert_time_string_to_nb_minutes("11:59AM"))
    print(convert_time_string_to_nb_minutes("12:00PM"))
    print(convert_time_string_to_nb_minutes("12:01PM"))
    print(convert_time_string_to_nb_minutes("01:00PM"))
    print(convert_time_string_to_nb_minutes("11h59"))
    print(convert_time_string_to_nb_minutes("12h00"))
    print(convert_time_string_to_nb_minutes("12h01"))
    print(convert_time_string_to_nb_minutes("13h00"))
    print(convert_nb_minutes_to_time_string(719, TWELVE_HOURS_FORMAT))
    print(convert_nb_minutes_to_time_string(720, TWELVE_HOURS_FORMAT))
    print(convert_nb_minutes_to_time_string(721, TWELVE_HOURS_FORMAT))
    print(convert_nb_minutes_to_time_string(719, TWENTY_FOUR_HOURS_FORMAT))
    print(convert_nb_minutes_to_time_string(720, TWENTY_FOUR_HOURS_FORMAT))
    print(convert_nb_minutes_to_time_string(721, TWENTY_FOUR_HOURS_FORMAT))
    print(convert_time_string_in_given_format("11:59AM", TWELVE_HOURS_FORMAT))
    print(convert_time_string_in_given_format("11:59AM", TWENTY_FOUR_HOURS_FORMAT))
    print(convert_time_string_in_given_format("11:59PM", TWENTY_FOUR_HOURS_FORMAT))
